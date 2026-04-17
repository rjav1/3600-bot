# CS3600 Spring 2026 Tournament — Agent Development

This repo is for the **CS3600 Spring 2026 Carpet/Rat tournament**. You (the AI agent reading this) are helping the user and their partner build a competitive Python bot that will be ranked on ELO at https://bytefight.org against other student agents and three staff reference bots (George, Albert, Carrie).

**Final submission deadline: 11:59pm on April 19, 2026.** Whatever is uploaded/activated on bytefight.org at that moment is what gets graded. Today is 2026-04-16 — so there are only a few days left.

---

## 1. The game — what the bot has to do

Two workers on an 8×8 board take alternating turns. Game ends after each player has had **40 turns** (so 80 plies total), or earlier if someone crashes / runs out of time / makes an invalid move. Whoever has the most points wins.

### Actions per turn (pick exactly one)
1. **Plain step** — move one square in a cardinal direction. Cannot step onto a primed square. (Carpeted squares are walkable by either player.)
2. **Prime step** — leave glue on the current square (now PRIMED, worth **+1 pt**) and step one square in a cardinal direction. Current square must not already be PRIMED or CARPET. Destination square must not be blocked or primed.
3. **Carpet roll** of length *k* (1 ≤ k ≤ 7) — roll over *k* contiguous primed squares in a straight line, converting them all to CARPET, ending on the *k*-th square. Point table:

   | k      | 1  | 2 | 3 | 4 | 5  | 6  | 7  |
   |--------|----|---|---|---|----|----|----|
   | Points | -1 | 2 | 4 | 6 | 10 | 15 | 21 |

   Rolling 1 is a **negative**; rolls of length ≥ 2 are the main point engine. Rolls of 5–7 are huge.
4. **Search move** — don't move; guess a square where the rat is. Correct → **+4 pts**, wrong → **−2 pts**. Expected value is positive iff P(rat in that cell) > 2/6 ≈ 0.333.

### Time budget
**4 minutes total** across all 40 of your moves (not per-move). Game overall can run up to 8 min. Running out of time = loss.

### Board geometry
- 8×8 grid; (0,0) is top-left; coords are (x, y).
- Each corner has a random blocked rectangle (2×3, 3×2, or 2×2).
- Players spawn **horizontally mirrored** in the inner 4×4 (x ∈ {2,3,4,5}, y ∈ {2,3,4,5}).
- Player A moves first.

### The rat (hidden Markov tracking problem)
- Hidden in one of the 64 cells under the floor; moves silently before every turn.
- Given a per-game 64×64 transition matrix `T` where `T[i, j]` = P(rat goes from cell `i` to cell `j`). Only ≤5 nonzeros per row (stay or step in 4 cardinal dirs). Edges clip. Rat can pass under blocked squares.
- The rat spawns at (0,0) and takes 1000 silent headstart moves before the game begins (and again every time it's caught — always from (0,0) with 1000 moves). This means the rat's prior is essentially the stationary-ish distribution of `T` after many steps from (0,0), **not** uniform.
- `T` is **passed into `__init__` as `transition_matrix`**. The user can precompute everything about it — stationary distribution, mixing time, reachability — in `__init__` before the clock starts on `play()`.

### The noise model (what the sensor tells you each turn)
Each turn the agent receives `sensor_data = (noise, estimated_distance)`:

- `noise ∈ {SQUEAK, SCRATCH, SQUEAL}` depends on the cell type the rat is currently under:

  |         | Squeak | Scratch | Squeal |
  |---------|--------|---------|--------|
  | Blocked | 0.5    | 0.3     | 0.2    |
  | Space   | 0.7    | 0.15    | 0.15   |
  | Primed  | 0.1    | 0.8     | 0.1    |
  | Carpet  | 0.1    | 0.1     | 0.8    |

  *(Useful: a SCRATCH strongly implies primed; a SQUEAL strongly implies carpet.)*

- `estimated_distance` is a **noisy Manhattan distance** from your worker to the rat:

  | Offset | −1   | 0    | +1   | +2   |
  |--------|------|------|------|------|
  | P      | 0.12 | 0.7  | 0.12 | 0.06 |

  Clamped to ≥ 0. These are the Bayesian-update likelihoods — you almost certainly want a full HMM belief grid.

### Game-end conditions
- Invalid move → you lose
- Out of time → you lose
- Both out of turns → higher points wins (ties allowed)

---

## 2. The state your agent gets each turn

Signature of the entry point:

```python
def play(self, board: board.Board, sensor_data: Tuple, time_left: Callable): ...
```

From `board` you can read:
- `board.player_worker` (you) and `board.opponent_worker` — each has `.position`, `.points`, `.turns_left`, `.time_left`.
- Bit masks: `_blocked_mask`, `_space_mask`, `_primed_mask`, `_carpet_mask` (each a 64-bit int, bit `y*8+x`).
- `board.opponent_search` and `board.player_search` = `((x,y), bool)` — last search loc and result for each side. `(None, False)` means no search happened.
- `board.turn_count`, `board.is_player_a_turn`.

Key methods (see `engine/game/board.py`):
- `board.get_valid_moves(enemy=False, exclude_search=True)` — handy but **excludes search by default**.
- `board.forecast_move(move, check_ok=True)` — returns a deep-copied Board with the move applied; does **not** reverse perspective.
- `board.apply_move(move, timer=0, check_ok=True)` — mutates in place.
- `board.reverse_perspective()` — swaps `player_worker` and `opponent_worker`. Call between plies when building a game tree.
- `board.get_copy()` — deep copy without history.
- `board.get_cell((x,y))`, `board.is_cell_blocked((x,y))`, `board.is_cell_carpetable((x,y))`, `board.is_valid_cell((x,y))`.

`time_left()` returns remaining seconds for this turn — **call it often** in any iterative deepening / MCTS loop.

`sensor_data` is `(Noise, int)`. Enums in `engine/game/enums.py`:
- `Noise.SQUEAK=0, SCRATCH=1, SQUEAL=2`
- `Cell.SPACE=0, PRIMED=1, CARPET=2, BLOCKED=3`
- `Direction.UP=0, RIGHT=1, DOWN=2, LEFT=3` (note: this is the enum order; `loc_after_direction` handles the math)
- `MoveType.PLAIN=0, PRIME=1, CARPET=2, SEARCH=3`

Return a `Move` (see `engine/game/move.py`): `Move.plain(dir)`, `Move.prime(dir)`, `Move.carpet(dir, roll_length)`, `Move.search((x,y))`.

---

## 3. Repo layout

```
3600-bot/
├── assignment.pdf              # full spec (authoritative)
├── requirements.txt            # jax, scikit-learn, flax, numpy, numba, psutil, cython, torch, pynvml
├── 3600-agents/
│   ├── Yolanda/                # reference random-mover starter agent (DO NOT EDIT as baseline)
│   │   └── agent.py
│   ├── <our-agent>/            # <-- our bot lives here (create a new folder)
│   │   ├── __init__.py         # needed if splitting into multiple files — see §5 below
│   │   └── agent.py            # must contain class PlayerAgent with __init__, play, commentate
│   └── matches/                # run_local_agents.py writes JSON game logs here (gitignore this)
└── engine/
    ├── run_local_agents.py     # driver: `python3 engine/run_local_agents.py <A> <B>`
    ├── gameplay.py             # main game loop; runs each agent in its own sandboxed process
    ├── player_process.py       # subprocess isolation, seccomp, timing, IPC
    ├── board_utils.py          # pretty-printer + history JSON serializer + spawn generator
    ├── transition_matrices/    # bigloop.pkl, hloops.pkl, quadloops.pkl, twoloops.pkl
    │                           # One is picked at random per game and ±10% noise is applied per entry,
    │                           # then rows are renormalized. So the T your bot sees is NOT identical
    │                           # to any of these files — don't hard-code rat strategies to them.
    └── game/
        ├── board.py            # Board class + bitmask tricks
        ├── enums.py            # MoveType, Cell, Noise, Direction, Result, WinReason, constants
        ├── move.py             # Move class
        ├── worker.py           # Worker class
        ├── rat.py              # Rat simulator — HEADSTART_MOVES=1000, noise probs, distance probs
        └── history.py          # per-turn logging for replay
```

Key constants in `enums.py`: `BOARD_SIZE=8`, `MAX_TURNS_PER_PLAYER=40`, `ALLOWED_TIME=240`, `RAT_BONUS=4`, `RAT_PENALTY=2`, `CARPET_POINTS_TABLE`.

---

## 4. Running the game locally

From the repo root (`3600-bot/`):

```bash
python3 engine/run_local_agents.py Yolanda Yolanda
python3 engine/run_local_agents.py <our-agent> Yolanda
```

Game logs land in `3600-agents/matches/<A>_<B>_<n>.json`. **Add `3600-agents/matches/` to `.gitignore`.**

The board is stochastic (random `T`, random spawns, random blocked corners, random rat) — a single match means almost nothing. Run **many matches** (50+) when evaluating a change. Parallelize where possible.

> The user can also test live strategies against real bots on **https://bytefight.org/compete/cs3600_sp2026** — this is the actual tournament site where agents can be uploaded and scrimmaged. Use it to sanity-check the real strength of a candidate submission, not just local self-play.

### Agent contract

`agent.py` must expose `class PlayerAgent` with:
- `__init__(self, board, transition_matrix=None, time_left=None)` — setup. **Precompute here**: stationary distribution of `T`, initial belief after 1000 headstart moves, any lookup tables. This doesn't count against your 4-minute budget (but has its own `init_timeout` ≈ 10–20 s — keep it tight).
- `play(self, board, sensor_data, time_left)` — return a `Move`.
- `commentate(self)` — optional; returns a string printed at game end.

### Multi-file agents

Python's import rules bite if you split `agent.py` into multiple files. Fix by adding `__init__.py` in the agent folder:

```python
# __init__.py
from .agent import PlayerAgent
from . import rat_belief  # etc.
```

And inside `agent.py`:

```python
from .rat_belief import RatBelief
```

---

## 5. Grading tiers (reference bots)

Everyone's ELO resets to 1500 when final submissions lock. Grade is based on where you land relative to the staff bots:

| Reference bot | Floor | How it plays                                                                                     |
|---------------|-------|--------------------------------------------------------------------------------------------------|
| George        | ≥ 70% | No lookahead; greedily extends primes + rolls carpet; opportunistic rat search when EV is high. |
| Albert        | ≥ 80% | Expectiminimax + HMM rat tracker + **very** simple heuristic.                                    |
| Carrie        | ≥ 90% | Same expectiminimax + HMM, but smarter heuristic (cell potential × distance from bot).           |

Within a tier, grade is scaled linearly by ELO distance to the bounding bots. Top team wins $150 Amazon gift cards + lunch with the instructors.

### Strategic implication
Beating Albert/Carrie essentially requires **expectiminimax with alpha-beta + an HMM rat belief grid + a thoughtful heuristic**. MCTS / AlphaZero-style bots are allowed and overkill for 8×8/40-turn games, but training data/time is limiting. Realistic path to 90%+: solid expectiminimax, good heuristic on prime/carpet potential, tight HMM tracker that converts belief mass into smart search-move timing.

---

## 6. Submission

1. Zip the agent folder so the zip contains a directory with `agent.py` inside (e.g. `MyBot.zip` containing `MyBot/agent.py`).
2. Zip must be ≤ 200 MB.
3. Tournament machine: x86_64 Linux, Python 3.12, libs in `requirements.txt`. **No network**, no FS writes outside cwd, no reading outside cwd.
4. Upload at https://bytefight.org. Account email is **rjavid3@gatech.edu** (display name "Rjav"). Team URL: https://bytefight.org/compete/cs3600_sp2026/team. (Earlier drafts of this doc said rahiljav@gmail.com based on the session `userEmail` context — that's the user's general email, not the tournament account. Use rjavid3@gatech.edu.)
5. Only one submission per team is active at a time — pick carefully before 11:59pm April 19, 2026.

---

## 7. Key constraints / gotchas to remember

- **Time is global, not per-move**: 240 s total across 40 moves ≈ 6 s/move budget on average. But the hard search problems happen when the board is crowded — you may want to spend more time late. Keep a running per-move adaptive cap.
- **`get_valid_moves` excludes search by default**. Pass `exclude_search=False` when considering searches.
- **`forecast_move` / `apply_move` do NOT reverse perspective**. Call `reverse_perspective()` manually when walking the game tree.
- **`T` is noisy per-game**: don't hardcode rat behavior against `bigloop.pkl`, etc. Always infer from the `T` passed into `__init__`.
- **Rat's prior distribution**: the rat has taken 1000 silent steps from (0,0) before the game starts. The initial belief should be `e_{(0,0)} @ T^1000`, **not** uniform.
- **Noise leaks floor type**: SCRATCH ⇒ likely primed; SQUEAL ⇒ likely carpet; SQUEAK ⇒ likely space (or blocked). Combine with the distance estimate for a sharp posterior.
- **Search EV threshold**: search is worth +4/-2, so it's +EV iff P(rat there) > 1/3. But a single search is also an information-gathering action that updates the belief — sometimes worth taking at lower probabilities late in the game.
- **Priming is +1/square but blocks your own future plain-steps onto it** (you can only walk over carpet once it's rolled). Plan contiguous prime-lines that you can actually roll.
- **Opponent can walk on your carpet** — don't carpet in places that gift them mobility.
- **Invalid move = instant loss**. When writing custom move generation, double-check against `board.is_valid_move` in tests.

---

## 8. Where to look in the code

| Question                                    | File                                 |
|---------------------------------------------|--------------------------------------|
| What's a valid move?                        | `engine/game/board.py::is_valid_move`, `get_valid_moves` |
| How do I simulate a move?                   | `engine/game/board.py::forecast_move` |
| What's the rat's noise model?               | `engine/game/rat.py::NOISE_PROBS`, `DISTANCE_ERROR_PROBS` |
| How does the rat spawn/headstart work?      | `engine/game/rat.py::Rat.spawn`      |
| Where does the game loop live?              | `engine/gameplay.py::play_game`      |
| How are moves scored?                       | `engine/game/board.py::apply_move` + `CARPET_POINTS_TABLE` in `enums.py` |
| Game JSON format for replay/analysis        | `engine/board_utils.py::get_history_dict` |
| Starter agent template                      | `3600-agents/Yolanda/agent.py`       |

---

## 9. What "done" looks like

A submission is only complete when:
1. It runs cleanly in a self-play match (`python3 engine/run_local_agents.py <ours> Yolanda` → no crashes, no timeouts, no invalid moves) across many runs.
2. It beats Yolanda ≫ 50% and beats George consistently (for ≥70%).
3. It has been uploaded to bytefight.org and scrimmaged against ≥ one reference bot with sane results.
4. The active submission on the tournament site at the April 19 11:59pm deadline is the one we want graded.
