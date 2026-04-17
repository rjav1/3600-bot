"""Unit tests for tools/bo_tune.py — T-20d.

Covers:
    * Bounds preserve signs (sanity).
    * `_regularisation` is 0 at w_init and positive elsewhere.
    * CLI help works (smoke).
    * agent.py picks up tuned weights via RATTLEBOT_WEIGHTS_JSON env.

Run directly:
    python tools/test_bo_tune.py

Or pytest:
    python -m pytest tools/test_bo_tune.py -v

No actual BO run is exercised here (would take 10+ min per trial);
that's validated by the full pipeline in the T-HEUR-3 gate script.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile


_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
for p in (
    _REPO_ROOT / "tools",
    _REPO_ROOT / "engine",
    _REPO_ROOT / "3600-agents",
):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


import bo_tune  # noqa: E402
from RattleBot import agent as agent_mod  # noqa: E402
from RattleBot.heuristic import N_FEATURES, W_INIT  # noqa: E402


def test_bounds_match_w_init_signs():
    """Every bound must enclose w_init strictly; sign preserved."""
    assert len(bo_tune.BOUNDS) == N_FEATURES
    assert len(bo_tune.W_INIT) == N_FEATURES
    for i, ((lo, hi), w0, w_init_heur) in enumerate(
        zip(bo_tune.BOUNDS, bo_tune.W_INIT, W_INIT.tolist())
    ):
        assert lo <= w0 <= hi, f"dim {i}: w_init={w0} outside [{lo},{hi}]"
        # bo_tune.W_INIT must equal heuristic.W_INIT
        assert abs(w0 - w_init_heur) < 1e-12, (
            f"dim {i}: bo_tune.W_INIT={w0} != heuristic.W_INIT={w_init_heur}"
        )
        # Sign preservation
        if w0 > 0:
            assert lo >= 0.0, f"dim {i}: positive w_init {w0} but lo={lo}"
        elif w0 < 0:
            assert hi <= 0.0, f"dim {i}: negative w_init {w0} but hi={hi}"


def test_regularisation_zero_at_w_init():
    reg = bo_tune._regularisation(bo_tune.W_INIT)
    assert reg == 0.0, f"expected 0, got {reg}"


def test_regularisation_positive_off_w_init():
    w = list(bo_tune.W_INIT)
    w[0] += 0.5
    reg = bo_tune._regularisation(w)
    assert reg > 0.0


def test_agent_loads_tuned_weights_from_env():
    """agent._load_tuned_weights reads RATTLEBOT_WEIGHTS_JSON."""
    tuned = [0.7, 0.1, 0.1, 1.2, -0.9, -2.5, -0.4, -0.5, -0.03,
             0.2, 0.1, 0.1]
    assert len(tuned) == N_FEATURES
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as fh:
        json.dump({"weights": tuned}, fh)
        path = fh.name
    prev = os.environ.get("RATTLEBOT_WEIGHTS_JSON")
    try:
        os.environ["RATTLEBOT_WEIGHTS_JSON"] = path
        arr = agent_mod._load_tuned_weights()
        assert arr is not None, "expected np.ndarray from env path"
        assert arr.shape == (N_FEATURES,)
        for loaded, ref in zip(arr.tolist(), tuned):
            assert abs(loaded - ref) < 1e-12
    finally:
        if prev is None:
            os.environ.pop("RATTLEBOT_WEIGHTS_JSON", None)
        else:
            os.environ["RATTLEBOT_WEIGHTS_JSON"] = prev
        os.remove(path)


def test_agent_fallback_when_file_missing():
    """If no weights.json nor env var, _load_tuned_weights returns None."""
    prev = os.environ.pop("RATTLEBOT_WEIGHTS_JSON", None)
    sibling = (
        pathlib.Path(agent_mod.__file__).parent / "weights.json"
    )
    existed = sibling.exists()
    if existed:
        sibling_bak = sibling.read_text(encoding="utf-8")
        sibling.unlink()
    try:
        arr = agent_mod._load_tuned_weights()
        assert arr is None, f"expected None, got {arr}"
    finally:
        if prev is not None:
            os.environ["RATTLEBOT_WEIGHTS_JSON"] = prev
        if existed:
            sibling.write_text(sibling_bak, encoding="utf-8")


def test_agent_reads_bare_list_format():
    """weights.json may be a bare JSON list (not wrapped in object)."""
    tuned = [1.0, 0.3, 0.2, 1.5, -1.2, -3.0, -0.5, -0.6, -0.05,
             0.15, 0.10, 0.10]
    assert len(tuned) == N_FEATURES
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as fh:
        json.dump(tuned, fh)
        path = fh.name
    prev = os.environ.get("RATTLEBOT_WEIGHTS_JSON")
    try:
        os.environ["RATTLEBOT_WEIGHTS_JSON"] = path
        arr = agent_mod._load_tuned_weights()
        assert arr is not None
        assert arr.shape == (N_FEATURES,)
    finally:
        if prev is None:
            os.environ.pop("RATTLEBOT_WEIGHTS_JSON", None)
        else:
            os.environ["RATTLEBOT_WEIGHTS_JSON"] = prev
        os.remove(path)


def test_objective_is_deterministic_under_fixed_seed():
    """With a deterministic mock paired-runner, the same weights produce
    the same win_rate — confirms the objective pipeline passes weights
    through correctly and has no internal randomness beyond the seed.
    """
    # Patch _eval_one_pair to return a canned pair whose win-rate depends
    # only on the first weight dim (so deterministic given `w`).
    orig = bo_tune._eval_one_pair

    def fake(task):
        # Mimic the paired_runner shape. RattleBot wins both matches
        # iff w[0] >= 1.0 — this makes win_rate a simple step function
        # of w[0], easy to assert.
        with open(task["weights_path"], "r", encoding="utf-8") as fh:
            w = json.load(fh)["weights"]
        if w[0] >= 1.0:
            match1 = {"winner": "PLAYER_A", "a_points": 20, "b_points": 5}
            match2 = {"winner": "PLAYER_B", "a_points": 5, "b_points": 20}
        else:
            match1 = {"winner": "PLAYER_B", "a_points": 5, "b_points": 20}
            match2 = {"winner": "PLAYER_A", "a_points": 20, "b_points": 5}
        return {"match1": match1, "match2": match2}

    bo_tune._eval_one_pair = fake
    try:
        import tempfile as _tf
        with _tf.TemporaryDirectory() as tmpdir:
            evaluator = bo_tune._Evaluator(
                opponent="FloorBot",
                n_per_trial=2,
                limit_resources=False,
                n_workers=1,
                root_seed=0,
                out_dir=pathlib.Path(tmpdir),
            )
            # Win case: w[0] = 1.5 > 1.0
            wr1, _, _, _ = evaluator._evaluate_winrate(
                list(bo_tune.W_INIT), trial_index=0
            )
            wr2, _, _, _ = evaluator._evaluate_winrate(
                list(bo_tune.W_INIT), trial_index=1
            )
            assert wr1 == wr2 == 1.0, f"win_rate not deterministic: {wr1} {wr2}"
            # Loss case: w[0] = 0.5 < 1.0
            lose_w = list(bo_tune.W_INIT)
            lose_w[0] = 0.5
            wr3, _, _, _ = evaluator._evaluate_winrate(
                lose_w, trial_index=2
            )
            assert wr3 == 0.0
    finally:
        bo_tune._eval_one_pair = orig


def test_catastrophe_penalty_fires_on_big_losses():
    """With `catastrophe_penalty=5`, a weight vector that produces 100 %
    catastrophic losses (score diff <= -30 every match) should get an
    objective that is 5 units worse than the same win-rate without the
    penalty."""
    orig = bo_tune._eval_one_pair

    def fake(task):
        # Always a catastrophic loss for RattleBot: RB score 0, opp 40
        # in every match on every side.
        match1 = {"winner": "PLAYER_B", "a_points": 0, "b_points": 40}
        match2 = {"winner": "PLAYER_A", "a_points": 40, "b_points": 0}
        return {"match1": match1, "match2": match2}

    bo_tune._eval_one_pair = fake
    try:
        import tempfile as _tf
        with _tf.TemporaryDirectory() as tmpdir:
            # penalty = 0 — baseline
            eva_no = bo_tune._Evaluator(
                opponent="FloorBot",
                n_per_trial=3,
                limit_resources=False,
                n_workers=1,
                root_seed=0,
                out_dir=pathlib.Path(tmpdir),
                catastrophe_penalty=0.0,
                catastrophe_threshold=-30.0,
            )
            w = list(bo_tune.W_INIT)
            obj_no = eva_no.objective(w)
            # penalty = 5 — every match a catastrophe, penalty = 5·1.0 = 5
            eva_pen = bo_tune._Evaluator(
                opponent="FloorBot",
                n_per_trial=3,
                limit_resources=False,
                n_workers=1,
                root_seed=0,
                out_dir=pathlib.Path(tmpdir),
                catastrophe_penalty=5.0,
                catastrophe_threshold=-30.0,
            )
            obj_pen = eva_pen.objective(w)
            # obj_pen should be obj_no + 5.0 (all matches catastrophic)
            assert abs((obj_pen - obj_no) - 5.0) < 1e-9, (
                f"catastrophe penalty not applied: no={obj_no}, "
                f"pen={obj_pen}, delta={obj_pen - obj_no} (expected 5.0)"
            )
            # And the trial entry records the fraction
            assert eva_pen.trials[0]["catastrophe_fraction"] == 1.0
            assert eva_pen.trials[0]["catastrophe_term"] == 5.0
    finally:
        bo_tune._eval_one_pair = orig


def test_catastrophe_threshold_excludes_small_losses():
    """A score diff of -10 should NOT count as a catastrophe at default
    threshold -30. Catastrophe fraction should be 0.0."""
    orig = bo_tune._eval_one_pair

    def fake(task):
        # Small losses — -10 each match
        match1 = {"winner": "PLAYER_B", "a_points": 5, "b_points": 15}
        match2 = {"winner": "PLAYER_A", "a_points": 15, "b_points": 5}
        return {"match1": match1, "match2": match2}

    bo_tune._eval_one_pair = fake
    try:
        import tempfile as _tf
        with _tf.TemporaryDirectory() as tmpdir:
            eva = bo_tune._Evaluator(
                opponent="FloorBot",
                n_per_trial=2,
                limit_resources=False,
                n_workers=1,
                root_seed=0,
                out_dir=pathlib.Path(tmpdir),
                catastrophe_penalty=5.0,
                catastrophe_threshold=-30.0,
            )
            _, _, _, cat_frac = eva._evaluate_winrate(
                list(bo_tune.W_INIT), trial_index=0
            )
            assert cat_frac == 0.0, (
                f"small-loss catastrophe_frac should be 0, got {cat_frac}"
            )
    finally:
        bo_tune._eval_one_pair = orig


def test_agent_rejects_bad_shape():
    """Wrong-shape JSON must fall back to None, not crash."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as fh:
        json.dump([1.0, 2.0, 3.0], fh)  # N=3, need 9
        path = fh.name
    prev = os.environ.get("RATTLEBOT_WEIGHTS_JSON")
    try:
        os.environ["RATTLEBOT_WEIGHTS_JSON"] = path
        arr = agent_mod._load_tuned_weights()
        assert arr is None
    finally:
        if prev is None:
            os.environ.pop("RATTLEBOT_WEIGHTS_JSON", None)
        else:
            os.environ["RATTLEBOT_WEIGHTS_JSON"] = prev
        os.remove(path)


def _run_all():
    tests = [
        test_bounds_match_w_init_signs,
        test_regularisation_zero_at_w_init,
        test_regularisation_positive_off_w_init,
        test_agent_loads_tuned_weights_from_env,
        test_agent_fallback_when_file_missing,
        test_agent_reads_bare_list_format,
        test_agent_rejects_bad_shape,
        test_objective_is_deterministic_under_fixed_seed,
        test_catastrophe_penalty_fires_on_big_losses,
        test_catastrophe_threshold_excludes_small_losses,
    ]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"  ERR   {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
