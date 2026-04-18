"""Ephemeral loss analyzer (loss-forensics-dual, 2026-04-18).

Reads replay JSONs for specific Carrie/Michael LOSSES (where RattleBot was A, B_WIN).
Produces per-match narrative and aggregate stats.

RattleBot = side A for all analyzed matches (sub=RattleBot_v03_pureonly_*.zip).
So B_WIN = RattleBot LOSS. This script is invoked for a set of loss UUIDs only.

Schema reminder (per docs/intel/analyze_replays.py):
  a_pos[T+1], b_pos[T+1]       positions (ply 0 = pre-game spawn)
  a_points[T+1], b_points[T+1] cumulative pts
  left_behind[T]               "plain" | "prime" | "carpet" | "none" | "search"
  new_carpets[T]               list of [x,y] per ply (k = len)
  rat_caught[T]                [a_caught, b_caught]?  let's inspect
  rat_position_history[T]      rat pos over time
  result                       0 = A_WIN, 1 = B_WIN, 2 = DRAW
  reason                       POINTS | INVALID | TIMEOUT | ...

Ply i is side A if even, B if odd (A moves first).

Output: printable per-match dossier + aggregate rolling-stats across the loss set.
"""
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Force UTF-8 stdout on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

REPLAY = Path("C:/Users/rahil/downloads/3600-bot/docs/intel/replays")

# B_WIN (LOSS) match UUIDs — sub=RattleBot=A in every case.
CARRIE_LOSS = [
    "2e9fb89f",  # 2026-04-17 22:04 EDT (ours_vs_carrie_*)
    "d83a9b8b",  # 22:59
    "ab281352", "c89c9b0f",  # 01:19 batch
    "74765a32", "6dcdea8c", "132a3fbd", "b93942ed", "c78534cd", "503d8eb7", "e4eff274",  # 01:20 batch
]
CARRIE_WIN = ["14a319d3"]  # A_WIN

MICHAEL_LOSS = [
    "066fdae3", "c39d8154", "3df15113", "56a79715", "d71f7f02", "144a1826",  # 01:40 batch
    "3f5ceec9", "7f9c8909", "d59cc6ff", "2f4b19b2",                            # 01:56 batch
    "a3c9e9af", "cd536bc6",                                                    # 02:12 batch
]
MICHAEL_WIN = ["0a270755", "2c0babfa"]  # A_WIN
MICHAEL_DRAW = ["af017ebc"]


def classify_ply(rep, ply):
    a_pos = rep["a_pos"]; b_pos = rep["b_pos"]
    left = rep["left_behind"]
    nc = rep["new_carpets"]
    if ply >= len(left): return ("NONE", None)
    lb = left[ply]
    carpets = nc[ply] if ply < len(nc) else []
    k = len(carpets) if carpets else None
    mover_is_a = (ply % 2 == 0)
    pos_seq = a_pos if mover_is_a else b_pos
    before = tuple(pos_seq[ply])
    after = tuple(pos_seq[ply+1]) if ply+1 < len(pos_seq) else before
    moved = before != after
    if lb == "search": return ("SEARCH", None)
    if k and k >= 1: return ("CARPET", k)
    if lb == "prime": return ("PRIME", None)
    if lb == "plain": return ("PLAIN", None)
    if lb == "carpet" and k: return ("CARPET", k)
    if moved: return ("PLAIN", None)
    return ("NONE", None)


def rat_captures(rep):
    """Use rat_caught[t] boolean list if present; else fallback to rat_position_history heuristic.
    Attribute each capture to mover of ply t-1 (the previous ply that caused it)."""
    caps_a = []; caps_b = []
    caught = rep.get("rat_caught", [])
    if caught and all(isinstance(x, bool) for x in caught):
        # caught[t] == True means the rat was caught as of state t (after ply t-1).
        # find rising edges (False -> True) or True-after-reset.
        prev = False
        for t, c in enumerate(caught):
            if c and not prev:
                ply = t - 1  # the ply that caught
                if 0 <= ply:
                    (caps_a if ply % 2 == 0 else caps_b).append(ply)
            prev = c
        return caps_a, caps_b
    # fallback: detect rat respawn to (0,0)
    hist = rep.get("rat_position_history", [])
    prev = None
    for t, rp in enumerate(hist):
        if rp is None: continue
        rpt = tuple(rp)
        if prev is not None and prev != (0, 0) and rpt == (0, 0):
            ply = t - 1
            if 0 <= ply:
                (caps_a if ply % 2 == 0 else caps_b).append(ply)
        prev = rpt
    return caps_a, caps_b


def analyze(uuid):
    """Return dict with per-match stats."""
    matches = list(REPLAY.glob(f"*{uuid}.json"))
    if not matches:
        return None
    path = matches[0]
    with open(path) as f:
        raw = json.load(f)
    # Some replays wrap the match data inside a 'pgn' key
    if "pgn" in raw and isinstance(raw["pgn"], dict):
        rep = raw["pgn"]
        # some top-level fields may have extra info we want (final_score, etc.)
        if "final_score" in raw and raw["final_score"]:
            rep.setdefault("_fs_a", raw["final_score"].get("a"))
            rep.setdefault("_fs_b", raw["final_score"].get("b"))
    else:
        rep = raw
    turn_count = rep["turn_count"]
    result = rep["result"]
    reason = rep["reason"]
    a_pts = rep["a_points"][-1]
    b_pts = rep["b_points"][-1]
    # per-side move mix
    per_side = {"a": Counter(), "b": Counter()}
    roll_ks = {"a": [], "b": []}
    # opening 5 plies per side
    opening = {"a": [], "b": []}
    # per-phase breakdown
    phase_actions = {"a": {"early": Counter(), "mid": Counter(), "late": Counter()},
                     "b": {"early": Counter(), "mid": Counter(), "late": Counter()}}
    search_plies = {"a": [], "b": []}
    score_trajectory = []  # (ply, a_pts, b_pts)
    for ply in range(turn_count):
        side = "a" if ply % 2 == 0 else "b"
        kind, k = classify_ply(rep, ply)
        per_side[side][kind] += 1
        if kind == "CARPET" and k:
            roll_ks[side].append(k)
        if kind == "SEARCH":
            search_plies[side].append(ply)
        if len(opening[side]) < 5:
            opening[side].append((kind, k))
        phase = "early" if ply < 27 else ("mid" if ply < 54 else "late")
        phase_actions[side][phase][kind] += 1
        # pts after this ply
        score_trajectory.append((ply,
                                 rep["a_points"][min(ply+1, len(rep["a_points"])-1)],
                                 rep["b_points"][min(ply+1, len(rep["b_points"])-1)]))
    caps_a, caps_b = rat_captures(rep)
    # find the turn where the delta opened (first ply where loser trails by >= 8 and never recovers)
    delta_open_ply = None
    for ply, ap, bp in score_trajectory:
        if ap - bp <= -8:
            delta_open_ply = ply
            break
    return {
        "uuid": uuid,
        "path": str(path),
        "turn_count": turn_count,
        "result": result,
        "reason": reason,
        "a_pts": a_pts,
        "b_pts": b_pts,
        "per_side": {s: dict(per_side[s]) for s in ("a","b")},
        "roll_ks": roll_ks,
        "opening": opening,
        "phase_actions": {s: {p: dict(phase_actions[s][p]) for p in ("early","mid","late")} for s in ("a","b")},
        "search_plies": search_plies,
        "score_trajectory": score_trajectory,
        "caps_a": caps_a,
        "caps_b": caps_b,
        "delta_open_ply": delta_open_ply,
    }


def report(title, uuids, label_a="A=RattleBot"):
    print(f"\n{'='*70}\n{title}\n{'='*70}")
    summaries = []
    for u in uuids:
        r = analyze(u)
        if r is None:
            print(f"  (no replay for {u})")
            continue
        summaries.append(r)
        a, b = r["a_pts"], r["b_pts"]
        mix_a = r["per_side"]["a"]
        mix_b = r["per_side"]["b"]
        ks_a = r["roll_ks"]["a"]
        ks_b = r["roll_ks"]["b"]
        kdist_a = Counter(ks_a)
        kdist_b = Counter(ks_b)
        search_a = len(r["search_plies"]["a"])
        search_b = len(r["search_plies"]["b"])
        caps_a = len(r["caps_a"])  # caught the rat
        caps_b = len(r["caps_b"])
        big_a = sum(1 for k in ks_a if k >= 4)
        big_b = sum(1 for k in ks_b if k >= 4)
        delta = r["delta_open_ply"]
        print(f"\n--- {r['uuid']}  final A={a}  B={b}  (Δ={a-b}, reason={r['reason']}) ---")
        print(f"  {label_a}:  mix={dict(mix_a)}  k-rolls={dict(sorted(kdist_a.items()))}  "
              f"searches={search_a}  ratCaught={caps_a}  bigRolls(k>=4)={big_a}")
        print(f"  B=Opp:      mix={dict(mix_b)}  k-rolls={dict(sorted(kdist_b.items()))}  "
              f"searches={search_b}  ratCaught={caps_b}  bigRolls(k>=4)={big_b}")
        print(f"  delta-open (ply A trails by >=8): {delta}")
        # score trajectory sample: every 10 plies
        traj = [(p, ap, bp) for p, ap, bp in r["score_trajectory"] if p % 10 == 9 or p == r["turn_count"]-1]
        print(f"  pts@plies: {traj}")
        # opening mix
        print(f"  A opening: {r['opening']['a']}")
        print(f"  B opening: {r['opening']['b']}")
        # phase
        print(f"  A phases: {r['phase_actions']['a']}")
        print(f"  B phases: {r['phase_actions']['b']}")

    # aggregate
    if summaries:
        print(f"\n--- AGGREGATE over {len(summaries)} matches ---")
        all_a_pts = [s["a_pts"] for s in summaries]
        all_b_pts = [s["b_pts"] for s in summaries]
        mean_a = sum(all_a_pts) / len(all_a_pts)
        mean_b = sum(all_b_pts) / len(all_b_pts)
        print(f"  mean A pts={mean_a:.1f}, B pts={mean_b:.1f}, Δ={mean_a-mean_b:.1f}")
        agg_mix_a = Counter(); agg_mix_b = Counter()
        agg_ks_a = []; agg_ks_b = []
        agg_search_a = 0; agg_search_b = 0
        agg_caps_a = 0; agg_caps_b = 0
        for s in summaries:
            agg_mix_a.update(s["per_side"]["a"])
            agg_mix_b.update(s["per_side"]["b"])
            agg_ks_a.extend(s["roll_ks"]["a"])
            agg_ks_b.extend(s["roll_ks"]["b"])
            agg_search_a += len(s["search_plies"]["a"])
            agg_search_b += len(s["search_plies"]["b"])
            agg_caps_a += len(s["caps_a"])
            agg_caps_b += len(s["caps_b"])
        kdist_a = Counter(agg_ks_a)
        kdist_b = Counter(agg_ks_b)
        avg_k_a = sum(agg_ks_a)/len(agg_ks_a) if agg_ks_a else 0
        avg_k_b = sum(agg_ks_b)/len(agg_ks_b) if agg_ks_b else 0
        print(f"  {label_a} aggregate mix: {dict(agg_mix_a)}")
        print(f"  B=Opp aggregate mix: {dict(agg_mix_b)}")
        print(f"  {label_a} k-dist: {dict(sorted(kdist_a.items()))}  avgK={avg_k_a:.2f}  total_k={len(agg_ks_a)}")
        print(f"  B=Opp k-dist: {dict(sorted(kdist_b.items()))}  avgK={avg_k_b:.2f}  total_k={len(agg_ks_b)}")
        # big-roll rate
        big_a = sum(1 for k in agg_ks_a if k >= 4); big_b = sum(1 for k in agg_ks_b if k >= 4)
        print(f"  {label_a} big rolls (k>=4): {big_a}/{len(agg_ks_a)} = {big_a/max(len(agg_ks_a),1):.1%}")
        print(f"  B=Opp big rolls (k>=4): {big_b}/{len(agg_ks_b)} = {big_b/max(len(agg_ks_b),1):.1%}")
        k1_a = sum(1 for k in agg_ks_a if k == 1); k1_b = sum(1 for k in agg_ks_b if k == 1)
        print(f"  {label_a} k=1 rolls: {k1_a}/{len(agg_ks_a)} = {k1_a/max(len(agg_ks_a),1):.1%}")
        print(f"  B=Opp k=1 rolls: {k1_b}/{len(agg_ks_b)} = {k1_b/max(len(agg_ks_b),1):.1%}")
        # carpet pts estimate (points from carpet rolls)
        CARPET_POINTS = {1: -1, 2: 2, 3: 4, 4: 6, 5: 10, 6: 15, 7: 21}
        cp_a = sum(CARPET_POINTS.get(k, 0) for k in agg_ks_a)
        cp_b = sum(CARPET_POINTS.get(k, 0) for k in agg_ks_b)
        print(f"  {label_a} total carpet pts: {cp_a}  (avg per game: {cp_a/len(summaries):.1f})")
        print(f"  B=Opp total carpet pts: {cp_b}  (avg per game: {cp_b/len(summaries):.1f})")
        # prime counts
        prime_a = agg_mix_a.get("PRIME", 0); prime_b = agg_mix_b.get("PRIME", 0)
        print(f"  {label_a} primes placed (+{prime_a} pts direct): {prime_a}, avg/game={prime_a/len(summaries):.1f}")
        print(f"  B=Opp primes placed: {prime_b}, avg/game={prime_b/len(summaries):.1f}")
        # search
        print(f"  {label_a} searches: total={agg_search_a}, avg/game={agg_search_a/len(summaries):.2f}")
        print(f"  B=Opp searches: total={agg_search_b}, avg/game={agg_search_b/len(summaries):.2f}")
        # captures
        print(f"  {label_a} rat captures: {agg_caps_a} across {len(summaries)} games (avg {agg_caps_a/len(summaries):.2f}/game)")
        print(f"  B=Opp rat captures: {agg_caps_b} across {len(summaries)} games (avg {agg_caps_b/len(summaries):.2f}/game)")
        # delta open
        opens = [s["delta_open_ply"] for s in summaries if s["delta_open_ply"] is not None]
        if opens:
            print(f"  delta-open (A trails by >=8) ply mean: {sum(opens)/len(opens):.1f}  min={min(opens)} max={max(opens)} n={len(opens)}/{len(summaries)}")
    return summaries


if __name__ == "__main__":
    s_c_loss = report("CARRIE — LOSSES (RattleBot=A, B_WIN)", CARRIE_LOSS)
    s_c_win = report("CARRIE — WINS (RattleBot=A, A_WIN) [for contrast]", CARRIE_WIN)
    s_m_loss = report("MICHAEL/RUSTY-v2.1 — LOSSES (RattleBot=A, B_WIN)", MICHAEL_LOSS)
    s_m_win = report("MICHAEL — WINS/DRAW (for contrast)", MICHAEL_WIN + MICHAEL_DRAW)
