"""
Analyze top-5 student team replays for competitive intel.

Schema (per bytefight_client.get_replay):
  a_pos[T+1], b_pos[T+1]        - worker positions, turn 0 = initial state
  a_points[T+1], b_points[T+1]  - running cumulative scores
  left_behind[T]                - "plain" | "prime" | "carpet" | "none" | "search" (per mover, 0-indexed by ply)
  new_carpets[T]                - list of [x,y] cells carpet-converted on that ply
  turn_count, result, reason, final_score, blocked_positions

Ply i (0-indexed) is mover A if i even else B (Player A moves first per CLAUDE.md §1).
len(new_carpets[i]) = k (carpet roll length) when left_behind[i] == "carpet".

Move classification per ply:
  - SEARCH: position unchanged AND left_behind == "none" AND no new_carpets.
            (Player A's search result is revealed via board.player_search metadata on next ply,
             but for move-classification we infer: pos unchanged + no carpet + no prime.)
  - CARPET: len(new_carpets[i]) >= 1  (k = that length)
  - PRIME:  left_behind[i] == "prime"
  - PLAIN:  left_behind[i] == "plain" (position changed, no prime, no carpet)
  - NONE:   fallback

Opening: first 5 plies per side (so first 10 plies total).
Search cadence: count SEARCH moves per game, bucket by turn phase (early 1-27, mid 28-53, late 54-80).
Points/turn: final_score / 40 for each side.
"""
import json
import os
from collections import Counter, defaultdict
from pathlib import Path


REPLAY_DIR = Path("docs/intel/replays")


def classify_ply(replay, ply_idx):
    """Classify move on ply_idx (0-indexed). Returns (kind, k_or_none)."""
    a_pos = replay["a_pos"]
    b_pos = replay["b_pos"]
    left = replay["left_behind"]
    nc = replay["new_carpets"]

    if ply_idx >= len(left):
        return ("NONE", None)

    lb = left[ply_idx]
    carpets = nc[ply_idx] if ply_idx < len(nc) else []
    k = len(carpets) if carpets else None

    # worker position before & after this ply
    mover_is_a = (ply_idx % 2 == 0)
    pos_seq = a_pos if mover_is_a else b_pos
    before = tuple(pos_seq[ply_idx])
    after = tuple(pos_seq[ply_idx + 1]) if ply_idx + 1 < len(pos_seq) else before
    moved = before != after

    if lb == "search":
        return ("SEARCH", None)
    if k and k >= 1:
        return ("CARPET", k)
    if lb == "prime":
        return ("PRIME", None)
    if lb == "plain":
        return ("PLAIN", None)
    if lb == "carpet" and k:
        return ("CARPET", k)
    if moved:
        return ("PLAIN", None)
    return ("NONE", None)


def analyze_one(replay_path):
    """Return per-game stats keyed by side ('a' or 'b')."""
    with open(replay_path) as f:
        rep = json.load(f)

    turn_count = rep["turn_count"]
    final = {"a": rep["a_points"][-1], "b": rep["b_points"][-1]}
    result = rep["result"]
    reason = rep["reason"]

    per_side = {"a": defaultdict(int), "b": defaultdict(int)}
    roll_ks = {"a": [], "b": []}
    opening_actions = {"a": [], "b": []}
    search_plies = {"a": [], "b": []}
    all_actions = {"a": [], "b": []}

    # total plies = turn_count (each ply is half-turn)
    for ply in range(turn_count):
        side = "a" if ply % 2 == 0 else "b"
        kind, k = classify_ply(rep, ply)
        per_side[side][kind] += 1
        all_actions[side].append((ply, kind, k))
        if kind == "CARPET" and k is not None:
            roll_ks[side].append(k)
        if kind == "SEARCH":
            search_plies[side].append(ply)
        # opening: first 5 plies per side
        if len(opening_actions[side]) < 5:
            opening_actions[side].append(kind)

    return {
        "path": str(replay_path),
        "turn_count": turn_count,
        "final_score": final,
        "result": result,
        "reason": reason,
        "per_side": {s: dict(per_side[s]) for s in ("a", "b")},
        "roll_ks": roll_ks,
        "opening_actions": opening_actions,
        "search_plies": search_plies,
    }


def aggregate_team(team_prefix, all_stats):
    """Aggregate stats for replays starting with team_prefix.
    Need to figure out which side was the top-team in each replay.
    For our top-team replays we queried by team-UUID; but the team could be A or B.
    We need the team name mapping - re-read the replay's match metadata.
    Simpler: aggregate BOTH sides since our corpus is of top-team-involved matches.
    But that biases stats with their opponents. To properly attribute:
    - For each replay, we'd ideally know the team we queried = A or B.
    - The replay JSON itself doesn't embed team names (PGN is bot-agnostic).
    - As proxy: aggregate "winner" patterns (more accurate intel: what wins).

    For this corpus, alternative: aggregate both sides and flag.
    """
    # Simplified: aggregate both sides for all matches with team_prefix
    games = [s for s in all_stats if os.path.basename(s["path"]).startswith(team_prefix)]
    totals = {
        "games": len(games),
        "roll_ks_all": [],
        "roll_ks_winner": [],
        "opening_primary": Counter(),
        "search_count_per_side": [],
        "pts_winner": [],
        "pts_loser": [],
        "bigroll_count": 0,  # k >= 4
        "allroll_count": 0,
        "action_counts": Counter(),
    }
    for g in games:
        for side in ("a", "b"):
            totals["roll_ks_all"].extend(g["roll_ks"][side])
            for k in g["roll_ks"][side]:
                totals["allroll_count"] += 1
                if k >= 4:
                    totals["bigroll_count"] += 1
            totals["action_counts"].update(g["per_side"][side])
            totals["search_count_per_side"].append(g["per_side"][side].get("SEARCH", 0))
            for a in g["opening_actions"][side]:
                totals["opening_primary"][a] += 1
        # winner side
        if g["result"] == 0:
            winner, loser = "a", "b"
        elif g["result"] == 1:
            winner, loser = "b", "a"
        else:
            continue  # draw
        totals["roll_ks_winner"].extend(g["roll_ks"][winner])
        totals["pts_winner"].append(g["final_score"][winner])
        totals["pts_loser"].append(g["final_score"][loser])
    return totals


def main():
    all_stats = []
    for path in sorted(REPLAY_DIR.glob("*.json")):
        try:
            stats = analyze_one(path)
            all_stats.append(stats)
        except Exception as e:
            print(f"FAIL {path.name}: {e}")

    print(f"\n=== Analyzed {len(all_stats)} replays ===\n")

    # Per-team aggregates
    for prefix in ("team61_", "michael_", "autobots_", "team44_", "team12_", "ours_"):
        agg = aggregate_team(prefix, all_stats)
        if agg["games"] == 0:
            continue
        print(f"\n--- {prefix.rstrip('_')} ({agg['games']} games) ---")
        print(f"  action totals (both sides, aggregated): {dict(agg['action_counts'])}")
        ks = agg["roll_ks_all"]
        ks_w = agg["roll_ks_winner"]
        kdist = Counter(ks)
        kdist_w = Counter(ks_w)
        print(f"  roll-k distribution (all): {dict(sorted(kdist.items()))}  (n={len(ks)})")
        print(f"  roll-k distribution (winners only): {dict(sorted(kdist_w.items()))}  (n={len(ks_w)})")
        print(f"  avg k (all): {sum(ks)/len(ks):.2f}" if ks else "  avg k: n/a")
        print(f"  big-roll (k>=4) rate: {agg['bigroll_count']}/{agg['allroll_count']} = {agg['bigroll_count']/max(agg['allroll_count'],1):.1%}")
        print(f"  searches/side: avg={sum(agg['search_count_per_side'])/max(len(agg['search_count_per_side']),1):.2f}, "
              f"max={max(agg['search_count_per_side']) if agg['search_count_per_side'] else 0}")
        print(f"  pts (winner): mean={sum(agg['pts_winner'])/max(len(agg['pts_winner']),1):.1f}, "
              f"pts/turn={sum(agg['pts_winner'])/max(len(agg['pts_winner'])*40,1):.2f}")
        print(f"  pts (loser):  mean={sum(agg['pts_loser'])/max(len(agg['pts_loser']),1):.1f}")
        print(f"  opening actions (first 5 plies/side): {dict(agg['opening_primary'])}")

    # Overall corpus (top 5 teams only, excluding ours_vs_*)
    print("\n\n=== CORPUS OVERALL (excl. ours_*) ===")
    top5 = [s for s in all_stats if not os.path.basename(s["path"]).startswith("ours_")]
    all_ks = []
    all_opening = Counter()
    all_search = []
    all_pts_winner = []
    for g in top5:
        for side in ("a", "b"):
            all_ks.extend(g["roll_ks"][side])
            all_search.append(g["per_side"][side].get("SEARCH", 0))
            for a in g["opening_actions"][side]:
                all_opening[a] += 1
        if g["result"] == 0:
            all_pts_winner.append(g["final_score"]["a"])
        elif g["result"] == 1:
            all_pts_winner.append(g["final_score"]["b"])
    kdist = Counter(all_ks)
    print(f"  games: {len(top5)}")
    print(f"  total rolls: {len(all_ks)}")
    print(f"  roll-k distribution: {dict(sorted(kdist.items()))}")
    kdist_pct = {k: f"{v/max(len(all_ks),1):.1%}" for k, v in sorted(kdist.items())}
    print(f"  roll-k pct: {kdist_pct}")
    if all_ks:
        big = sum(1 for k in all_ks if k >= 4)
        med = sum(1 for k in all_ks if 2 <= k <= 3)
        print(f"  k=1 pct:   {sum(1 for k in all_ks if k == 1)/len(all_ks):.1%}")
        print(f"  k=2-3 pct: {med/len(all_ks):.1%}")
        print(f"  k>=4 pct:  {big/len(all_ks):.1%}")
        print(f"  avg k:     {sum(all_ks)/len(all_ks):.2f}")
    print(f"  opening action mix: {dict(all_opening)}")
    print(f"  searches/side: mean={sum(all_search)/max(len(all_search),1):.2f}")
    print(f"  winner pts: mean={sum(all_pts_winner)/max(len(all_pts_winner),1):.1f}, pts/turn={sum(all_pts_winner)/max(len(all_pts_winner)*40,1):.2f}")

    # Search timing breakdown
    print("\n=== SEARCH TIMING (top 5, both sides) ===")
    early = mid = late = 0
    for g in top5:
        for side in ("a", "b"):
            for ply in g["search_plies"][side]:
                if ply < 27:
                    early += 1
                elif ply < 54:
                    mid += 1
                else:
                    late += 1
    tot = early + mid + late
    if tot:
        print(f"  total searches: {tot}")
        print(f"  early (plies 0-26): {early} ({early/tot:.1%})")
        print(f"  mid   (plies 27-53): {mid} ({mid/tot:.1%})")
        print(f"  late  (plies 54-79): {late} ({late/tot:.1%})")
    else:
        print("  zero searches in the corpus (!)")


if __name__ == "__main__":
    main()
