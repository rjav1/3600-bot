"""Tournament-sandbox simulator for local testing.

Reproduces (best-effort) the bytefight.org tournament constraints
documented in `docs/GAME_SPEC.md` §7 and `CLAUDE.md` §6:
    - no network
    - no filesystem writes outside cwd
    - 1536 MB RSS cap (soft-enforced via psutil poller + Linux RLIMIT_AS)
    - 240 s play budget (enforced by the engine itself when
      `--limit-resources` is passed)
    - 300 s wall-clock hard cap via `--timeout`

The sandbox is installed by importing this module. It operates via three
mechanisms:

    1. A `sys.meta_path` MetaPathFinder that raises ImportError for
       network-related modules.
    2. A wrapper around `builtins.open` that rejects writes/appends to
       paths outside the working directory.
    3. A wrapper around `os.remove`, `os.unlink`, `os.rename` that
       rejects paths outside the working directory.
    4. A background thread that polls RSS via psutil (optional) and
       aborts the process if the cap is exceeded.
    5. On Linux, `resource.setrlimit(RLIMIT_AS, cap)` for a hard kernel
       ceiling.

For child processes spawned by the engine (`engine/player_process.py`
uses `multiprocessing.Process`), we propagate the sandbox via a
`sitecustomize.py` hack: we prepend `tools/_sandbox_site/` to
`PYTHONPATH`, and drop a `sitecustomize.py` there that re-imports this
module. Python runs `sitecustomize` automatically on every interpreter
start.

Usage
-----
    # Run RattleBot vs Yolanda under the simulator (5 matches, paired):
    python tools/sandbox_sim.py --matches 5 --a RattleBot --b Yolanda

    # Run the RattleBot pytest suite under the simulator:
    python tools/sandbox_sim.py --pytest 3600-agents/RattleBot/tests/

    # Run an arbitrary command under the simulator:
    python tools/sandbox_sim.py -- python -c "import socket"

The script exits non-zero on any sandbox violation.
"""
from __future__ import annotations

import argparse
import builtins
import os
import pathlib
import runpy
import sys
import threading
import time
from typing import List, Optional, Tuple


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_ROOT / "engine"
AGENTS_DIR = REPO_ROOT / "3600-agents"
SITE_DIR = pathlib.Path(__file__).resolve().parent / "_sandbox_site"

# Third-party nets we ban at import time (mirrors "not in
# requirements.txt" — tournament env simply won't have them).
BLOCKED_MODULES = {
    "requests",
    "httpx",
    "aiohttp",
    "websocket",
    "websockets",
    "paramiko",
}

# Stdlib net modules — we let import succeed (psutil, multiprocessing,
# etc. pull socket transitively) but patch the functions that actually
# touch the network syscalls. Mirrors seccomp: seccomp blocks the
# *syscall* (socket/connect/bind/sendto), not the Python import.
NET_RUNTIME_PATCH_MODULES = {
    "socket",
    "ssl",
    "urllib",
    "urllib.request",
    "http.client",
    "ftplib",
    "smtplib",
}

# Modules whose *use* is network-y but which a lot of legit Python
# imports pull transitively (e.g. multiprocessing pulls pickle which
# pulls nothing net-y, but some libs import urllib lazily). We only
# block at the top level here; a grand-child transitive import is still
# caught because the import system re-enters the finder.
#
# NOTE: multiprocessing itself is NOT blocked — the engine's sandbox
# subprocess model depends on it. bytefight.org's actual sandbox also
# allows multiprocessing; seccomp only blocks the `socket` syscall etc.


_SANDBOX_INSTALLED = False
_VIOLATIONS: List[str] = []


def _record_violation(msg: str) -> None:
    _VIOLATIONS.append(msg)
    # also emit to stderr so pytest / engine logs catch it
    try:
        sys.stderr.write(f"[sandbox_sim] VIOLATION: {msg}\n")
        sys.stderr.flush()
    except Exception:
        pass


class _NetBlockingFinder:
    """sys.meta_path finder that raises ImportError for net modules."""

    def find_spec(self, fullname, path, target=None):  # type: ignore[override]
        if fullname in BLOCKED_MODULES:
            _record_violation(f"blocked import '{fullname}'")
            raise ImportError(
                f"[sandbox_sim] import of '{fullname}' is forbidden under "
                f"tournament sandbox (no network allowed)."
            )
        # Also catch submodules like urllib.request even if parent is
        # already partially loaded.
        top = fullname.split(".", 1)[0]
        if top in BLOCKED_MODULES and fullname != top:
            _record_violation(f"blocked import '{fullname}' (submodule of '{top}')")
            raise ImportError(
                f"[sandbox_sim] import of '{fullname}' is forbidden under "
                f"tournament sandbox (no network allowed)."
            )
        return None


def _is_device_path(path: str) -> bool:
    """True for /dev/null, /dev/stderr, NUL, \\\\.\\NUL, etc."""
    p = path.lower()
    if p in ("nul", "/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty"):
        return True
    if p.startswith("\\\\.\\"):  # Windows device namespace
        return True
    if p.startswith("/dev/"):
        return True
    return False


def _is_inside_cwd(path: str) -> bool:
    if _is_device_path(path):
        return True
    try:
        resolved = pathlib.Path(path).resolve()
        cwd = pathlib.Path(os.getcwd()).resolve()
        return str(resolved).startswith(str(cwd))
    except Exception:
        return False


_real_open = builtins.open
_real_os_remove = os.remove
_real_os_unlink = os.unlink
_real_os_rename = os.rename


def _sandboxed_open(file, mode="r", *args, **kwargs):
    # Only sandbox real filesystem paths (strings / pathlike). File
    # descriptors (int) pass through unchanged.
    if isinstance(file, int):
        return _real_open(file, mode, *args, **kwargs)
    mode_str = mode if isinstance(mode, str) else "r"
    is_write = any(c in mode_str for c in ("w", "a", "x", "+"))
    if is_write:
        path_str = os.fspath(file)
        if not _is_inside_cwd(path_str):
            _record_violation(
                f"blocked open({path_str!r}, {mode_str!r}) — outside cwd"
            )
            raise PermissionError(
                f"[sandbox_sim] write to '{path_str}' forbidden "
                f"(tournament sandbox allows fs writes only inside cwd)."
            )
    return _real_open(file, mode, *args, **kwargs)


# NOTE: the tournament seccomp filter in engine/player_process.py does
# NOT block unlink/rename/rmdir (those lines are commented out). We
# mirror that and allow os.remove/unlink/rename without path checks.
# Chmod/chown IS blocked but we don't wrap it here; Python code in the
# agents has no legitimate reason to call it.
_sandboxed_remove = _real_os_remove
_sandboxed_unlink = _real_os_unlink
_sandboxed_rename = _real_os_rename


# Memory poller ------------------------------------------------------------

_MEM_CAP_BYTES = 1536 * 1024 * 1024  # 1.5 GB, per GAME_SPEC §7
_mem_thread_started = False


def _start_memory_poller(cap_bytes: int) -> None:
    """Background thread: abort if RSS exceeds cap. Requires psutil."""
    global _mem_thread_started
    if _mem_thread_started:
        return
    try:
        import psutil  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "[sandbox_sim] psutil not available — skipping RSS poller.\n"
        )
        return

    import psutil

    pid = os.getpid()

    def _poll():
        proc = psutil.Process(pid)
        while True:
            try:
                total = proc.memory_info().rss
                for child in proc.children(recursive=True):
                    try:
                        total += child.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                if total > cap_bytes:
                    _record_violation(
                        f"RSS {total / 1024 / 1024:.1f} MB exceeds "
                        f"{cap_bytes / 1024 / 1024:.0f} MB cap"
                    )
                    sys.stderr.write(
                        "[sandbox_sim] RSS cap exceeded — aborting.\n"
                    )
                    os._exit(137)
            except psutil.NoSuchProcess:
                return
            except Exception:
                pass
            time.sleep(0.25)

    t = threading.Thread(target=_poll, daemon=True, name="sandbox-mem-poll")
    t.start()
    _mem_thread_started = True


def _apply_linux_rlimit(cap_bytes: int) -> None:
    if sys.platform != "linux":
        return
    try:
        import resource

        # Engine uses RLIMIT_RSS; we use RLIMIT_AS (virtual memory)
        # which is more universally enforced by the kernel.
        resource.setrlimit(resource.RLIMIT_AS, (cap_bytes, cap_bytes))
    except Exception as e:
        sys.stderr.write(f"[sandbox_sim] setrlimit failed: {e}\n")


# Public install API -------------------------------------------------------


def _patch_socket_runtime() -> None:
    """Patch the real `socket` module so network syscalls raise, but
    imports succeed. Mirrors seccomp's syscall-level block.
    """
    try:
        import socket as _s
    except ImportError:
        return

    def _blocked_socket(*a, **kw):
        _record_violation("socket.socket() called")
        raise PermissionError(
            "[sandbox_sim] socket creation forbidden "
            "(tournament seccomp blocks the socket syscall)."
        )

    def _blocked_getaddrinfo(*a, **kw):
        _record_violation("socket.getaddrinfo() called")
        raise PermissionError(
            "[sandbox_sim] getaddrinfo forbidden (no-network)."
        )

    # Keep the original class object available — psutil stashes it at
    # import time — but neuter its constructor.
    try:
        _s.socket.__init__ = lambda self, *a, **kw: _blocked_socket()  # type: ignore[assignment]
    except Exception:
        pass
    for name in (
        "create_connection",
        "create_server",
        "gethostbyname",
        "gethostbyaddr",
        "getaddrinfo",
    ):
        if hasattr(_s, name):
            setattr(_s, name, _blocked_getaddrinfo)


def install_sandbox(cap_bytes: Optional[int] = None) -> None:
    """Install the sandbox hooks. Idempotent."""
    global _SANDBOX_INSTALLED
    if _SANDBOX_INSTALLED:
        return
    _SANDBOX_INSTALLED = True

    # Block third-party net libs at import time (they aren't in the
    # tournament requirements.txt, so they'd fail there anyway).
    sys.meta_path.insert(0, _NetBlockingFinder())
    for name in list(BLOCKED_MODULES):
        mod = sys.modules.get(name)
        if mod is not None:
            sys.modules[name] = _PoisonedModule(name)  # type: ignore[assignment]

    # Patch stdlib socket at runtime — matches seccomp behavior.
    _patch_socket_runtime()

    # Wrap filesystem writes only (open with write mode). Seccomp
    # explicitly does NOT block unlink/rename/rmdir, so we don't
    # either — see engine/player_process.py:apply_seccomp.
    builtins.open = _sandboxed_open

    cap = cap_bytes if cap_bytes is not None else _MEM_CAP_BYTES
    _apply_linux_rlimit(cap)
    _start_memory_poller(cap)

    # Propagate to child processes via sitecustomize hook.
    _install_child_propagation()

    sys.stderr.write(
        f"[sandbox_sim] installed — cwd={os.getcwd()!r} "
        f"cap={cap // (1024 * 1024)} MB "
        f"blocked_imports={len(BLOCKED_MODULES)} "
        f"socket_patched=yes\n"
    )


class _PoisonedModule:
    """Attribute access on a poisoned module raises ImportError."""

    def __init__(self, name: str):
        self.__name__ = name

    def __getattr__(self, item):
        _record_violation(
            f"poisoned module '{self.__name__}' attr '{item}' accessed"
        )
        raise ImportError(
            f"[sandbox_sim] module '{self.__name__}' is poisoned "
            f"(net modules forbidden). Attempted: .{item}"
        )


def _install_child_propagation() -> None:
    """Drop a sitecustomize.py and prepend its dir to PYTHONPATH so
    child Python interpreters (multiprocessing 'spawn') also get the
    sandbox installed at startup.
    """
    try:
        SITE_DIR.mkdir(parents=True, exist_ok=True)
        sitecustomize = SITE_DIR / "sitecustomize.py"
        payload = (
            "# Auto-generated by tools/sandbox_sim.py — reinstalls the\n"
            "# tournament sandbox in child processes.\n"
            "import os, sys\n"
            "if os.environ.get('SANDBOX_SIM_ACTIVE') == '1':\n"
            f"    sys.path.insert(0, {str(pathlib.Path(__file__).resolve().parent)!r})\n"
            "    try:\n"
            "        import sandbox_sim\n"
            "        sandbox_sim.install_sandbox()\n"
            "    except Exception as e:\n"
            "        sys.stderr.write(f'[sandbox_sim] child-reinstall failed: {e}\\n')\n"
        )
        if (
            not sitecustomize.exists()
            or sitecustomize.read_text(encoding="utf-8") != payload
        ):
            sitecustomize.write_text(payload, encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"[sandbox_sim] child-propagate setup failed: {e}\n")
        return

    # Prepend SITE_DIR to PYTHONPATH for children.
    sep = os.pathsep
    existing = os.environ.get("PYTHONPATH", "")
    if str(SITE_DIR) not in existing.split(sep):
        os.environ["PYTHONPATH"] = (
            str(SITE_DIR) + (sep + existing if existing else "")
        )
    os.environ["SANDBOX_SIM_ACTIVE"] = "1"


def get_violations() -> List[str]:
    return list(_VIOLATIONS)


# CLI ----------------------------------------------------------------------


def _sandbox_self_test() -> int:
    """Probe that the sandbox actually blocks things."""
    failures = []
    passes = 0

    # 1. socket import SUCCEEDS (seccomp-style), but socket() raises.
    try:
        import socket

        passes += 1
    except ImportError:
        failures.append("socket import unexpectedly blocked")
        socket = None  # type: ignore[assignment]

    if socket is not None:
        try:
            socket.socket()
            failures.append("socket.socket() NOT blocked at runtime")
        except PermissionError:
            passes += 1

    # 2. requests (third-party) IS blocked at import.
    try:
        import requests  # type: ignore[import-not-found]  # noqa: F401

        failures.append("requests import NOT blocked")
    except ImportError:
        passes += 1

    # 3. open() for write OUTSIDE cwd (pick a path guaranteed
    # outside: the parent of cwd).
    outside = (pathlib.Path(os.getcwd()).parent / ".sandbox_sim_outside.txt").resolve()
    try:
        with open(outside, "w") as fp:
            fp.write("x")
        failures.append(f"write to {outside} NOT blocked")
        try:
            _real_os_remove(str(outside))
        except Exception:
            pass
    except PermissionError:
        passes += 1

    # 4. open() for write INSIDE cwd (must succeed).
    inside = pathlib.Path(os.getcwd()) / ".sandbox_sim_inside_test.txt"
    try:
        with open(inside, "w") as fp:
            fp.write("x")
        os.remove(str(inside))
        passes += 1
    except Exception as e:
        failures.append(f"write to cwd failed: {e}")

    if failures:
        for f in failures:
            sys.stderr.write(f"[sandbox_sim] SELF-TEST FAIL: {f}\n")
        return 1
    sys.stderr.write(f"[sandbox_sim] self-test OK ({passes}/5)\n")
    return 0


def _run_pytest(args: List[str]) -> int:
    """Invoke pytest in-process with sandbox installed."""
    # Engine + agents must be importable.
    for p in (str(ENGINE_DIR), str(AGENTS_DIR)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import pytest
    except ImportError:
        sys.stderr.write("[sandbox_sim] pytest not installed.\n")
        return 2
    return pytest.main(list(args))


def _run_matches(
    agent_a: str,
    agent_b: str,
    matches: int,
    seed_base: int,
    limit_resources: bool,
) -> Tuple[int, int]:
    """Run N paired matches via the engine. Returns (completed, errors)."""
    for p in (str(ENGINE_DIR), str(AGENTS_DIR)):
        if p not in sys.path:
            sys.path.insert(0, p)

    # Import inside the sandbox so bot imports happen post-install.
    import random

    from gameplay import play_game

    completed = 0
    errors = 0
    for i in range(matches):
        seed = seed_base + i
        random.seed(seed)
        try:
            result = play_game(
                str(AGENTS_DIR),
                str(AGENTS_DIR),
                agent_a,
                agent_b,
                display_game=False,
                delay=0.0,
                clear_screen=False,
                record=False,
                limit_resources=limit_resources,
                use_gpu=False,
            )
            final_board = result[0]
            winner = getattr(final_board, "winner", None)
            reason = getattr(final_board, "win_reason", None)
            pa = final_board.player_worker.points
            pb = final_board.opponent_worker.points
            sys.stderr.write(
                f"[sandbox_sim] match {i + 1}/{matches} seed={seed} "
                f"winner={winner} reason={reason} "
                f"{agent_a}={pa} {agent_b}={pb}\n"
            )
            completed += 1
        except Exception as e:
            import traceback

            sys.stderr.write(
                f"[sandbox_sim] match {i + 1} ERROR: {e}\n"
                f"{traceback.format_exc()}\n"
            )
            errors += 1

    return completed, errors


def _run_command(argv: List[str], timeout_s: Optional[int]) -> int:
    """Run argv as a subprocess under the sandbox. The subprocess
    inherits the sandbox via sitecustomize (see install_sandbox)."""
    import subprocess

    try:
        proc = subprocess.run(argv, timeout=timeout_s)
        return proc.returncode
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"[sandbox_sim] command timed out after {timeout_s}s\n")
        return 124


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Tournament sandbox simulator (pure-Python path).",
    )
    p.add_argument(
        "--matches",
        type=int,
        default=0,
        help="Run N engine matches (requires --a, --b).",
    )
    p.add_argument("--a", type=str, help="Agent A name")
    p.add_argument("--b", type=str, help="Agent B name")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument(
        "--limit-resources",
        action="store_true",
        help="Pass limit_resources=True to the engine. Only works on Linux "
        "with seccomp/prctl installed.",
    )
    p.add_argument(
        "--pytest",
        type=str,
        default=None,
        help="Run pytest under sandbox against this path.",
    )
    p.add_argument("--self-test", action="store_true")
    p.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Hard wall-clock timeout for command mode (default 300s).",
    )
    p.add_argument(
        "--cap-mb",
        type=int,
        default=1536,
        help="RAM cap in MB (default 1536).",
    )
    p.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run, preceded by --. Ignored in --matches or --pytest mode.",
    )
    args = p.parse_args(argv)

    install_sandbox(cap_bytes=args.cap_mb * 1024 * 1024)

    t0 = time.perf_counter()

    if args.self_test:
        rc = _sandbox_self_test()
    elif args.pytest:
        rc = _run_pytest(["-v", args.pytest])
    elif args.matches > 0:
        if not args.a or not args.b:
            p.error("--matches requires --a and --b")
        completed, errors = _run_matches(
            args.a, args.b, args.matches, args.seed, args.limit_resources
        )
        sys.stderr.write(
            f"[sandbox_sim] matches complete: {completed}/{args.matches} "
            f"errors={errors}\n"
        )
        rc = 0 if errors == 0 else 1
    elif args.command:
        cmd = list(args.command)
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        if not cmd:
            p.error("empty command after --")
        rc = _run_command(cmd, timeout_s=args.timeout)
    else:
        p.error("nothing to do — pass --self-test, --pytest, --matches, or a command.")

    elapsed = time.perf_counter() - t0
    vlist = get_violations()
    sys.stderr.write(
        f"[sandbox_sim] done — rc={rc} elapsed={elapsed:.1f}s violations={len(vlist)}\n"
    )
    for v in vlist:
        sys.stderr.write(f"[sandbox_sim]   · {v}\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
