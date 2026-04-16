# GAME_SPEC — Authoritative Game Specification

**Source of truth:** the engine Python source in `engine/`. Where this document disagrees with `CLAUDE.md`, trust this document. Where it disagrees with the engine source, report a bug. Citations use `file:line` — click to jump.

All line numbers refer to the repo at the commit present on disk on 2026-04-16.

---

## 1. Coordinate system and board geometry

- **Board size:** 8×8 — `BOARD_SIZE = 8` (`engine/game/enums.py:5`).
- **Coordinates:** `(x, y)` tuples. `(0, 0)` is the **upper-left** corner; `x` increases rightward, `y` increases downward (`assignment.pdf` §6; `engine/game/enums.py:42-51`).
- **Bitmask layout:** bit index = `y * 8 + x`, i.e. bit 0 = (0,0), bit 7 = (7,0), bit 8 = (0,1), bit 63 = (7,7) (`engine/game/board.py:46-47, 402-412`).
- **Four disjoint cell masks** on each `Board` — exactly one bit of the four masks is set per cell (`engine/game/board.py:48-53, 491-505`):
  - `_space_mask` — SPACE
  - `_primed_mask` — PRIMED
  - `_carpet_mask` — CARPET
  - `_blocked_mask` — BLOCKED
- **Direction convention** (`engine/game/enums.py:36-53`):
  - `UP  → (x, y-1)`
  - `DOWN → (x, y+1)`
  - `LEFT → (x-1, y)`
  - `RIGHT → (x+1, y)`
  - (So `UP` decreases `y` — the visual "up" on the printed board.)

### Blocked-corner generation

Per-game in `play_game` (`engine/gameplay.py:254-262`):

```
shapes = [(2, 3), (3, 2), (2, 2)]
for ox, oy in [(0, 0), (1, 0), (0, 1), (1, 1)]:   # TL, TR, BL, BR
    w, h = random.choice(shapes)
    for dx in range(w):
        for dy in range(h):
            x = dx if ox == 0 else BOARD_SIZE - 1 - dx
            y = dy if oy == 0 else BOARD_SIZE - 1 - dy
            board.set_cell((x, y), Cell.BLOCKED)
```

- Each of the **four** corners independently picks one of three rectangle shapes: 2×3, 3×2, or 2×2.
- The rectangle is anchored at the corner, extending inward (toward the opposite edge) along both axes.
- RNG source: module-level `random` (`engine/gameplay.py:3`). Not independently seeded — games are not reproducible without external seeding.
- Edge case: opposing corners can have overlapping footprints? No — at maximum they extend 3 squares from each corner, so the inner 2×2 (x∈{3,4}, y∈{3,4}) is always free. But spawns live in the 4×4 inner box (§1.1), which *can* intersect blocked corners — see spawn generation below.

### Spawn generation

`board_utils.generate_spawns` (`engine/board_utils.py:186-190`):

```python
def generate_spawns(board: Board):
    x = random.randint(BOARD_SIZE // 2 - 2, BOARD_SIZE // 2 - 1)  # 2 or 3
    y = random.randint(BOARD_SIZE // 2 - 2, BOARD_SIZE // 2 + 1)  # 2..5
    return (x, y), (BOARD_SIZE - 1 - x, y)
```

- Player A spawn: `x ∈ {2, 3}`, `y ∈ {2, 3, 4, 5}` — 8 possible cells.
- Player B spawn: horizontally mirrored: `(7-x, y)` — so B is at `x ∈ {4, 5}`, same `y`.
- Both spawns on the **same row**.
- **IMPORTANT GOTCHA:** `generate_spawns` does **not** check whether the chosen cells are blocked. If a corner blocker extends into `(x, y) = (2, 2)` or similar, the spawn can land on a BLOCKED cell — neither `generate_spawns` nor `play_game` re-rolls or sanitizes. The blocked-mask is then overwritten by player position in any rendering/movement check (`is_cell_blocked` returns `True` for a worker-occupied cell via the worker check). Practically this rarely matters because spawn `y ∈ {2..5}` but corners are 3-deep max, so `y ∈ {0..2}` on top and `{5..7}` on bottom — **spawn at y=2 or y=5 can collide with a 2×3/3×2 corner block.** Flag: CLAUDE.md says "inner 4×4" without noting the overlap risk.

### Player A goes first

- `is_player_a_turn = True` at `Board.__init__` (`engine/game/board.py:39`).
- In `play_game`, this flips at every `end_turn` (`engine/game/board.py:280`).

---

## 2. Move types — exact preconditions, effects, point deltas

Entry: a `Move` object with fields `move_type`, `direction`, `roll_length`, `search_loc` (`engine/game/move.py:3-13`). Validation in `Board.is_valid_move` (`engine/game/board.py:73-127`); execution in `Board.apply_move` (`engine/game/board.py:218-264`).

**All preconditions and effects below are from the perspective of `player_worker` (`self`).** The engine does not reverse perspective during `apply_move`. `is_valid_move(enemy=True)` is the only way to check the opponent's move.

### 2.1 PLAIN

**Constructor:** `Move.plain(direction)` (`engine/game/move.py:14-26`).

**Preconditions** (`engine/game/board.py:94-96`):
- `next_loc = loc_after_direction(my_loc, direction)` must satisfy `not board.is_cell_blocked(next_loc)`.
- `is_cell_blocked` (`engine/game/board.py:526-550`) returns `True` if **any** of:
  - `next_loc` out of bounds;
  - `next_loc == opponent_worker.position`;
  - `next_loc == player_worker.position` (self — irrelevant in practice);
  - bit set in `_blocked_mask | _primed_mask`.
- **Carpet is walkable** (bit is in `_carpet_mask`, which is NOT in the or'd test).

**Effects** (`engine/game/board.py:241-242`):
- `player_worker.position = next_loc`.
- Cell masks unchanged.
- No point delta.

### 2.2 PRIME

**Constructor:** `Move.prime(direction)` (`engine/game/move.py:28-39`).

**Preconditions** (`engine/game/board.py:98-106`):
- `next_loc` not blocked (same `is_cell_blocked` check as PLAIN — so destination cannot be BLOCKED, PRIMED, or a worker, but CARPET destination is fine).
- Current cell (`my_loc`) must **not** be PRIMED or CARPET: `(_primed_mask | _carpet_mask) & bit == 0`.
  - So PRIME is only legal from a SPACE cell (BLOCKED is impossible anyway since you can't stand on BLOCKED).

**Effects** (`engine/game/board.py:243-246`):
- `set_cell(my_loc, Cell.PRIMED)` — leaves current cell PRIMED.
- `player_worker.position = next_loc`.
- `player_worker.increment_points(1)` — **+1 point**.

### 2.3 CARPET

**Constructor:** `Move.carpet(direction, roll_length)` where `roll_length ∈ [1, 7]` (`engine/game/move.py:41-53`).

**Preconditions** (`engine/game/board.py:108-120`):
- `1 ≤ roll_length ≤ BOARD_SIZE - 1 = 7`.
- Walking `roll_length` steps in `direction` from `my_loc`, **every intermediate cell** (including the final landing cell) must pass `is_cell_carpetable` (`engine/game/board.py:552-575`):
  - in bounds;
  - **not** equal to `opponent_worker.position`;
  - not equal to `player_worker.position`;
  - bit set in `_primed_mask` (must be PRIMED — already-CARPET cells are NOT carpetable again, BLOCKED/SPACE not either).

**Effects** (`engine/game/board.py:247-255`):
- For `i = 1..roll_length`: `current_loc = loc_after_direction(current_loc, direction)`; `set_cell(current_loc, Cell.CARPET)`.
- `player_worker.position = current_loc` (the final k-th square).
- `player_worker.increment_points(CARPET_POINTS_TABLE[roll_length])`.

**Point table** (`engine/game/enums.py:6-14`):

| k        | 1  | 2 | 3 | 4 | 5  | 6  | 7  |
|----------|----|---|---|---|----|----|----|
| Points   | −1 | 2 | 4 | 6 | 10 | 15 | 21 |

Edge cases:
- `roll_length = 1` costs **−1 point** (penalty).
- Carpet ends the worker's turn on a CARPET cell — subsequent PRIME from this cell is illegal (PRIME requires current cell be SPACE).
- Can you roll **onto** the opponent's square? **No** — `is_cell_carpetable` explicitly rejects it.
- Can you roll **through** your own starting square? Irrelevant — the carpet walk starts by stepping *once* before checking, so `my_loc` itself is never tested.
- CARPET does **not** verify the starting cell — so you can stand on CARPET, PRIMED, or SPACE and still roll, as long as the ray is all PRIMED.

### 2.4 SEARCH

**Constructor:** `Move.search(search_loc)` where `search_loc = (x, y)` (`engine/game/move.py:55-66`).

**Preconditions** (`engine/game/board.py:122-125`):
- `is_valid_cell(search_loc)` — only checks in-bounds (0..7 on each axis).
- **No other validation.** You can SEARCH any in-bounds cell, including:
  - BLOCKED cells (the rat can hide under blocks, so this is meaningful);
  - your own cell;
  - the opponent's cell;
  - a cell that you just failed to search last turn.

**Effects inside `apply_move`** (`engine/game/board.py:256-258`):
- **Nothing.** The case `MoveType.SEARCH` explicitly does `pass` and delegates to the game runner.
- `apply_move` still calls `end_turn` — so turn count advances, `turns_left` decrements, `time_left` decrements.

**Effects in `play_game`** (`engine/gameplay.py:434-445`, executed **after** `apply_move`):
- If `move.search_loc == rat.get_position()`: **+4** (`RAT_BONUS`, `engine/game/enums.py:16`). Rat is respawned (`rat.spawn()` — new 1000-step headstart from (0,0)).
- Else: **−2** (`RAT_PENALTY`).
- `search_loc` and `search_result` are queued into a `deque(maxlen=2)` of all searches, then dispatched to `board.player_search` / `board.opponent_search` **after** perspective reversal (`engine/gameplay.py:457-460`). See §5 below.

Worker position is **not** changed by SEARCH.

Gotcha: a SEARCH on an out-of-bounds `search_loc` is invalid. `apply_move` returns False → INVALID_TURN → you lose.

---

## 3. The rat — initialization, movement, observations

Source: `engine/game/rat.py`.

### 3.1 Transition matrix `T`

- Loaded by `_load_transition_matrix` (`engine/gameplay.py:10-30`):
  1. Pick one `.pkl` file uniformly at random from `engine/transition_matrices/` (files present: `bigloop.pkl`, `hloops.pkl`, `quadloops.pkl`, `twoloops.pkl`).
  2. Convert to a `jax.numpy` float32 array.
  3. Sample a **uniform multiplicative noise** `η ∈ [-0.1, +0.1]` **per entry** of the 64×64 matrix: `T ← max(T * (1 + η), 0)`.
  4. Row-renormalize: `T[i,:] /= T[i,:].sum()` (zero rows are guarded by replacing the denominator with 1 — in practice no row is fully zero unless the original pkl had a zero row).
- **Result:** `T` is a row-stochastic 64×64 matrix. Each row has at most 5 nonzero entries (stay + 4 cardinal neighbors), with off-edge probabilities already zero in the pickled tables. The noise step can turn a zero into a tiny positive — but only if the ORIGINAL entry was nonzero (because `T * (1 + η) = 0 * (1 + η) = 0`). So **sparsity pattern is preserved**.
- `T` is passed to `Rat.__init__(T)` (`engine/game/rat.py:39`) *and* to the player's `__init__` via `run_timed_constructor(..., T)` (`engine/gameplay.py:337-346`, `engine/player_process.py:324`).
- The transition matrix does **not change** during a game (`assignment.pdf` §2).
- `_load_transition_matrix` uses `jax.random.PRNGKey(random.randint(0, 2**32 - 1))` — so the noise draw is derived from Python's `random` state.

### 3.2 Rat spawn / headstart

`Rat.spawn` (`engine/game/rat.py:127-131`):

```python
def spawn(self):
    self.position = (0,0)
    for _ in range(HEADSTART_MOVES):
        self.move()
```

- `HEADSTART_MOVES = 1000` (`engine/game/rat.py:6`).
- Called **once** before the first turn (`engine/gameplay.py:269`) — so the rat's initial-turn position is effectively a sample from `δ_{(0,0)} · T^1000`.
- Called **again** every time the rat is captured (`engine/gameplay.py:439`) — so the post-capture prior is *also* `δ_{(0,0)} · T^1000`. This matters for agents tracking belief after a successful SEARCH.

### 3.3 Rat movement each turn

`Rat.move` (`engine/game/rat.py:83-101`):

- Called at the **top of each ply**, before the current player's agent is invoked (`engine/gameplay.py:386`). So the sensor readings always reflect the rat **after** moving, i.e. the rat's current position at the moment you observe.
- Sampling: inverse-CDF draw from row `T[current_index, :]` using a uniform `random.random()`.
- Precomputed in `__init__` as `cumT[i][j] = sum(T[i][0..j])` (`engine/game/rat.py:51-59`).

### 3.4 Noise emission

Table from `NOISE_PROBS` (`engine/game/rat.py:10-15`):

| Cell under rat | SQUEAK | SCRATCH | SQUEAL |
|----------------|--------|---------|--------|
| BLOCKED        | 0.5    | 0.3     | 0.2    |
| SPACE          | 0.7    | 0.15    | 0.15   |
| PRIMED         | 0.1    | 0.8     | 0.1    |
| CARPET         | 0.1    | 0.1     | 0.8    |

- Enum indexing: `SQUEAK=0, SCRATCH=1, SQUEAL=2` (`engine/game/enums.py:31-34`).
- Implemented as a 3-way CDF draw (`Rat._sample3`, `Rat.make_noise`, `engine/game/rat.py:77-110`).
- Cell type for the noise draw uses `board.get_cell(rat.position)`, so the rat reads the **current** cell type (post any carpeting done by the player this turn? No — the rat moves *before* the player's turn is resolved, and the sensor is sampled *before* the player's move, so noise reflects the cell type at the start of the player's turn).
- Noise is i.i.d. conditional on cell type and rat position.

### 3.5 Distance estimation

`Rat.estimate_distance` (`engine/game/rat.py:112-125`):

- True value: `actual = |wx - rx| + |wy - ry|` (Manhattan distance).
- Additive error offset drawn from a 4-way CDF with offsets `(-1, 0, +1, +2)` and probabilities `(0.12, 0.7, 0.12, 0.06)` (`engine/game/rat.py:21-22`).

| Reported offset | Probability |
|-----------------|-------------|
| actual − 1      | 0.12        |
| actual          | 0.70        |
| actual + 1      | 0.12        |
| actual + 2      | 0.06        |

- Clamped: `d if d > 0 else 0` (`engine/game/rat.py:125`) — so a reported distance of `0` means true distance is `0` or `1` (since `actual − 1 → 0` when `actual = 1`, and `actual = 0` maps to reported `0` via the `+0` branch). **Reported distances are always ≥ 0, never negative.**
- The distance is computed from the **current `player_worker`'s** position (`engine/game/rat.py:138-141`, `Rat.sample`). After perspective reversal between plies, this is always "your worker's distance to the rat" for whoever is acting.

### 3.6 Respawn after capture

- Done in `play_game` right after the winning SEARCH: `rat.spawn()` (`engine/gameplay.py:439`). This re-initializes `rat.position = (0, 0)` and executes 1000 more silent moves.
- There is **no observation** given to either player that the rat respawned beyond the fact that `search_result == True` is attached to the next turn's `player_search`. The 1000 intermediate moves are silent — no noise/distance samples are emitted during them.

---

## 4. The per-turn observation stream

Signature (`engine/player_process.py:280-282`, `3600-agents/Yolanda/agent.py:28-33`):

```python
def play(self, board: Board, sensor_data: Tuple[Noise, int], time_left: Callable[[], float]) -> Move:
```

### 4.1 `board` — a fresh deep copy

- `play_game` passes a deep copy (via `get_copy(False)` in `run_timed_play`, `engine/player_process.py:434`). Mutating it does not affect the engine's board.
- `get_copy` copies masks, worker states, search tuples, `is_player_a_turn`, `turn_count`, `winner` — but does **not** copy the `history` object (`engine/game/board.py:318-353`). History will be `None` in copies.
- Perspective is already set: on player A's turn, `board.player_worker` **is A**; on player B's turn, `board.player_worker` **is B**. This is because `play_game` calls `board.reverse_perspective()` between plies (`engine/gameplay.py:457`).

Accessible state on `board`:
- `player_worker` — `Worker` with `.position` (tuple), `.points` (int), `.turns_left` (int), `.time_left` (float), `.is_player_a` (bool), `.is_player_b` (bool) (`engine/game/worker.py`).
- `opponent_worker` — same fields, for the opponent.
- Four 64-bit masks: `_blocked_mask`, `_space_mask`, `_primed_mask`, `_carpet_mask`.
- `turn_count` — total plies completed so far (so a player observes with `turn_count` even on their first call to `play` when `turn_count == 0` for A or `1` for B).
- `is_player_a_turn` — **bool telling you who is currently acting in the absolute A/B frame**, not whose perspective the board is in.
- `opponent_search`, `player_search` — see §5.
- `MAX_TURNS = MAX_TURNS_PER_PLAYER * 2 = 80`.

### 4.2 `sensor_data`

A 2-tuple `(noise: Noise, estimated_distance: int)` produced by `Rat.sample` (`engine/game/rat.py:136-141`).

- `noise` — one of `Noise.SQUEAK` (0), `Noise.SCRATCH` (1), `Noise.SQUEAL` (2). See §3.4 for the emission probabilities conditional on the cell under the rat.
- `estimated_distance` — non-negative integer; noisy Manhattan distance from `board.player_worker.position` to the rat (see §3.5).

### 4.3 `time_left`

- A closure that returns `time_left - (get_cur_time() - start)` where `time_left` is `board.player_worker.time_left` and `start` is `time.perf_counter()` when `play` entered (`engine/player_process.py:268-282`).
- So `time_left()` is **seconds remaining in your total 240-second (or 360-second, see §7) budget** — not per-move. It ticks continuously as you compute.

### 4.4 Return value

- Must be a `Move` instance. Anything else or a crash → `play_game` assigns loss conditions (see §8).
- If `play` raises, the process returns `(None, -1, traceback)` and you lose with `CODE_CRASH` (`engine/player_process.py:285-288`; `engine/gameplay.py:408-415`).
- If you take longer than `time_left` available: returned move is discarded, `timer >= timeout` → you lose with TIMEOUT (`engine/player_process.py:459-461`).

---

## 5. Search visibility — what you see about the opponent's searches

State lives on the board (`engine/game/board.py:66-68`):

```python
self.opponent_search = (None, False)  # Last (Search Location, Search Result) for current opponent
self.player_search  = (None, False)   # Last (Search Location, Search Result) for current player
```

**Tuple shape:** `(search_loc, search_result)` where:
- `search_loc: Optional[Tuple[int,int]]` — the cell searched, or `None` if no search happened on that ply;
- `search_result: bool` — `True` iff rat was caught, `False` otherwise (including "they didn't search").

**Update procedure** in `play_game` after each ply (`engine/gameplay.py:434-460`):

```python
searches = deque([(None, False), (None, False)], maxlen=2)
# ... per-ply:
if move.move_type == MoveType.SEARCH:
    search_loc = move.search_loc
    if search_loc == rat.get_position():
        search_result = True
        rat.spawn()
        board.player_worker.increment_points(RAT_BONUS)
    else:
        search_result = False
        board.player_worker.decrement_points(RAT_PENALTY)
searches.append((search_loc, search_result))   # Note: unconditional for non-search too, using the `= None` defaults

if not board.is_game_over():
    board.reverse_perspective()
    board.opponent_search = searches[-1]   # Latest — the player who JUST moved
    board.player_search   = searches[-2]   # Previous — whoever moves next
```

**Interpretation from the perspective of the player about to move:**
- `board.opponent_search` reflects **the opponent's most recent move** (the ply that just ended). If they searched, you see their `(search_loc, success)`; if they didn't, `(None, False)`.
- `board.player_search` reflects **your own most recent move** — i.e. the ply you took two plies ago. If you searched and it's now your turn again, you see `(your_search_loc, your_success)`.
- On the very first ply of the game, both tuples are `(None, False)` because the deque is initialized that way.

**Subtle gotcha:** because `searches` tracks every ply, not just SEARCH plies, `(None, False)` in `opponent_search` always means "opponent did not search", not "opponent searched and missed on cell None". Treat the `None` in the first element as the sentinel.

**Rat capture signaling:** on the next ply after a successful capture, the acting player sees `opponent_search = (capture_loc, True)` (if opponent captured) or `player_search = (your_loc, True)` (if you captured two plies ago and it's now your turn again). The rat has already been respawned (1000 silent steps from (0,0)). You do not see the new rat's position.

---

## 6. Perspective conventions

`Board.reverse_perspective` (`engine/game/board.py:395-400`):

```python
def reverse_perspective(self):
    self.player_worker, self.opponent_worker = self.opponent_worker, self.player_worker
```

**That is the only thing it does.** It does **not**:
- swap `is_player_a_turn`;
- swap `player_search` / `opponent_search`;
- swap or mutate any cell masks;
- swap `turn_count`.

`play_game` augments this by *also* swapping `opponent_search` / `player_search` via the `deque` pattern shown in §5 (`engine/gameplay.py:459-460`). **Your own game-tree code must swap the searches manually** if you walk forward through multiple plies.

### Perspective at each stage of a ply

Let "acting" = the player whose turn it is.
1. Top of ply: `board.player_worker = acting`, `board.opponent_worker = other`, `board.is_player_a_turn = (acting == A)`.
2. Rat moves, sample drawn (`engine/gameplay.py:386-387`). No perspective change.
3. Engine calls `acting.play(board_copy, sensor, time_left)`. The agent receives the copy with `acting` as `player_worker`.
4. Agent returns a `Move`.
5. Engine calls `board.apply_move(move, timer)`. **`apply_move` does NOT swap perspective** (`engine/game/board.py:266-280`). It calls `end_turn`, which increments `turn_count`, decrements `acting.turns_left` and `acting.time_left`, and flips `is_player_a_turn`. The worker labels (`player_worker`/`opponent_worker`) are **still pointing at `acting`**.
6. Engine handles the SEARCH-specific point deltas/rat respawn *against* `board.player_worker` — which is still `acting` — correctly adding/subtracting points to the acting player (`engine/gameplay.py:434-445`).
7. History recording (if enabled) happens here. `history.record_turn` infers which player just moved by inverting `is_player_a_turn` (since `end_turn` flipped it) (`engine/game/history.py:34-59`).
8. `board.reverse_perspective()` is called (`engine/gameplay.py:457`). Now `player_worker = other` (who is about to act next), `opponent_worker = acting`.
9. `opponent_search`/`player_search` reassigned from the deque so that `opponent_search` = what the just-previous player did (`engine/gameplay.py:459-460`).

### `forecast_move` / `apply_move` perspective

Both operate entirely in `player_worker`'s frame. Neither swaps:
- `forecast_move` = `get_copy()` + `apply_move(check_ok)` on the copy (`engine/game/board.py:199-216`). Returns `None` if invalid.
- `apply_move` mutates the board, calls `end_turn`, returns `bool` (`engine/game/board.py:218-264`). Catches any exception and returns `False`, but on exception the board may be in a partially-mutated state (the docstring warns).

**If you build a game tree:**
- After every `apply_move`/`forecast_move` call, call `reverse_perspective()` *on the resulting board* before generating the next player's moves.
- If the previous ply was a SEARCH, also manually update `opponent_search` / `player_search` — the engine does this in `play_game`, but neither `apply_move` nor `forecast_move` does.
- If you care about the rat/belief inside your tree, you must track it separately — the engine's board has **no** rat state (it's held by `play_game`/`Rat`).

---

## 7. Time accounting

- **Per-worker time budget** lives on `Worker.time_left` (`engine/game/worker.py:10`), initialized to `ALLOWED_TIME = 240` by default (`engine/game/enums.py:15`).
- **Actual budget given to your process** depends on `limit_resources` (`engine/gameplay.py:232-238`):
  - `limit_resources=True` (tournament / bytefight.org): `play_time = 240` seconds total (not per move).
  - `limit_resources=False` (local self-play via `run_local_agents.py`): `play_time = 360` seconds total.
  - This `play_time` is passed to `Board(time_to_play=play_time)`, which sets `player_worker.time_left = time_to_play` and likewise for opponent (`engine/game/board.py:58-60`).
- **Per-move accounting:** `apply_move(move, timer=...)` → `end_turn(timer)` → `player_worker.time_left -= timer` (`engine/game/board.py:266-280`). `timer` is the elapsed wall time measured in `run_timed_play` via `time.perf_counter()` (`engine/player_process.py:207-208, 274-284, 304`).
- **Time check for loss:** `check_win` (`engine/game/board.py:282-306`):
  - If `player_worker.time_left <= 0`:
    - if `opponent_worker.time_left <= 0.5`: TIE by TIMEOUT;
    - else: ENEMY wins by TIMEOUT.
  - If `opponent_worker.time_left <= 0`:
    - if `player_worker.time_left <= 0.5`: TIE by TIMEOUT;
    - else: PLAYER wins by TIMEOUT.
  - (Called inside `end_turn` so a time overrun can end the game mid-ply.)
- **Initialization time budget** (`engine/gameplay.py:234, 237`):
  - `init_timeout = 10` seconds under `limit_resources=True`;
  - `init_timeout = 20` seconds under `limit_resources=False`.
  - Does **not** count against your 240s play budget. Enforced in `run_timed_constructor` via a queue timeout of `init_timeout + extra_ret_time = init_timeout + 5` (`engine/player_process.py:398-429`). If `timer >= init_timeout`, you lose with FAILED_INIT.
- **`extra_ret_time = 5`** is IPC slack; the game still calls your timeout a TIMEOUT loss if your recorded `timer >= timeout`, so that slack doesn't help you compute — it just protects against message-queue jitter (`engine/player_process.py:459-461`).
- **`limit_resources` also** applies memory rlimit of 1536 MB RSS, VRAM cap of 4 GB, seccomp syscall filtering (no network, no chdir, no chmod, no execve, etc.), and UID drop (`engine/player_process.py:160-218`). Bytefight.org machines run with `limit_resources=True`.

---

## 8. Game-over conditions and win-reason codes

`Result` enum — what `board.winner` stores **from the acting player's perspective** in the middle of the game, then rewritten to the absolute frame (`ResultArbiter`) at the end of `play_game`:

- `Result.PLAYER = 0`
- `Result.ENEMY  = 1`
- `Result.TIE    = 2`
- `Result.ERROR  = 3`

`ResultArbiter` — the **absolute** frame at end of game (`engine/game/enums.py:61-65`):
- `ResultArbiter.PLAYER_A = 0`
- `ResultArbiter.PLAYER_B = 1`
- `ResultArbiter.TIE      = 2`
- `ResultArbiter.ERROR    = 3`

`WinReason` enum (`engine/game/enums.py:67-73`):
- `POINTS = 0`
- `TIMEOUT = 1`
- `INVALID_TURN = 2`
- `CODE_CRASH = 3`
- `MEMORY_ERROR = 4`
- `FAILED_INIT = 5`

### All termination pathways

1. **Points exhausted** — `turn_count >= 80` **or** both `turns_left == 0`. Winner = higher `points`. Reason = `POINTS`. Ties allowed (`engine/game/board.py:299-305`).
2. **Timeout** — see §7; set inside `check_win` (`engine/game/board.py:289-298`). Reason = `TIMEOUT`.
3. **Invalid move** — `apply_move(..., check_ok=True)` returned `False` (`engine/gameplay.py:419-425`). Winner = ENEMY, reason = `INVALID_TURN`.
4. **Code crash** — `play` raised an exception. `(move, timer) = (None, -1)` → winner = ENEMY, reason = `CODE_CRASH` (`engine/gameplay.py:408-410`).
5. **Memory error** — RLIMIT_RSS or `checkMemory()` cap of 1536 MB exceeded (`engine/player_process.py:292-295`). `timer = -2` → winner = ENEMY, reason = `MEMORY_ERROR` (`engine/gameplay.py:411-412`).
6. **Ret-timeout** — `play_game`'s queue timed out waiting for your move (`engine/player_process.py:463`). `timer = -1` → winner = ENEMY, reason = `TIMEOUT`.
7. **Failed init** — both agents fail: TIE by FAILED_INIT. One agent fails: the other wins by FAILED_INIT (`engine/gameplay.py:348-365`).

**Frame remapping at end of game** (`engine/gameplay.py:462-476`): because `is_player_a_turn` has been toggled by `end_turn`, the engine converts the PLAYER/ENEMY result back into the absolute A/B frame using the current `is_player_a_turn` value. The final winner stored on `board` is a `ResultArbiter`, not a `Result`.

---

## 9. Non-obvious edge cases (discovered by reading the source)

1. **Carpet onto opponent** — illegal. `is_cell_carpetable` rejects the opponent's cell (`engine/game/board.py:564-566`). This is a subtle way the opponent can block your big rolls.
2. **Carpet onto your own standing cell** — impossible because `is_cell_carpetable` also rejects `player_worker.get_location()` (`engine/game/board.py:568-570`), and the walk only tests cells *after* stepping, so this only bites on loops-back-to-self (not reachable with straight-line rolls on an 8×8 board from your own square).
3. **Stepping onto CARPET** — allowed. `is_cell_blocked` checks `_blocked_mask | _primed_mask` plus workers, but not `_carpet_mask` (`engine/game/board.py:547-550`). So either player can walk on any CARPET cell.
4. **Priming from a CARPET cell** — illegal. `is_valid_move(PRIME)` rejects if `_primed_mask | _carpet_mask` covers the current cell (`engine/game/board.py:103-106`).
5. **Priming toward a CARPET destination** — legal. The destination check is `is_cell_blocked`, which does not include `_carpet_mask`.
6. **Rolling length 1** — legal but costs −1 point. Use only to convert a single stranded PRIMED square if absolutely necessary.
7. **SEARCH onto a BLOCKED cell** — legal. The rat can hide under blocked squares (`assignment.pdf` §2), and `is_valid_move` only checks bounds (`engine/game/board.py:122-125`).
8. **SEARCH onto your own cell** — legal. Same rationale.
9. **SEARCH onto the opponent's cell** — legal. The rat is under the floor, not on the surface.
10. **Invalid SEARCH location** — `is_valid_cell(search_loc)` returns `False` for out-of-bounds. `apply_move(SEARCH)` returns `False`. You lose by INVALID_TURN. A `None` `search_loc` also fails validation — `is_valid_cell` would crash on `None[0]`, but `apply_move` catches any exception and returns `False`, so the practical result is still INVALID_TURN. No point delta is applied because the SEARCH point handling in `play_game` happens *after* `apply_move`, and the game has already ended by then.
11. **SEARCH point delta is applied outside `apply_move`** — `apply_move(SEARCH)` does not touch points. Points are awarded/deducted in `play_game` after `apply_move`. If you rely on `forecast_move` to predict the score after a SEARCH, **you will not see the +4 / −2 delta** — your own code must apply it.
12. **`forecast_move` / `apply_move` do NOT handle rat state** — the rat is owned by `play_game`/`Rat`, not `Board`. In your tree, track belief separately.
13. **`apply_move` swallows all exceptions** — if something internal throws, it returns `False` and the board may be partially mutated (`engine/game/board.py:263-264`). Docstring acknowledges this; don't rely on the board being recoverable after a failed `apply_move`.
14. **`get_valid_moves(exclude_search=True)` by default** — iterate with `exclude_search=False` if you want SEARCH candidates included (`engine/game/board.py:130, 194-195`). This is also stored in `board.valid_search_moves` — 64 precomputed `Move.search(loc)` objects (`engine/game/board.py:70-71`).
15. **CARPET validation loops over `range(1, roll_length+1)`** while the apply loop uses `range(1, move.roll_length + 1)` — both match, but the validator re-walks the ray, so CARPET validation is O(k). Not a perf concern at k ≤ 7.
16. **`is_cell_blocked` includes your own cell** — `board.is_cell_blocked(player_worker.position)` returns `True` (`engine/game/board.py:543-545`). Be careful when using it as a "not safe to stand on" check — any position test that happens to equal the querying player's position will look blocked.
17. **Spawn collision with blocked corner** — see §1. `generate_spawns` doesn't check blockers. A bot should not assume `get_cell(player_worker.position)` is always SPACE at game start.
18. **`check_win` can declare the game over mid-`apply_move`** — it's called inside `end_turn`. So the loop guard `while (not board.is_game_over())` in `play_game` can exit before the normal reverse-perspective step (`engine/gameplay.py:456-460`). The final `ResultArbiter` remap at the end relies on whatever state `is_player_a_turn` is in.
19. **Noise is drawn BEFORE the player's move resolves** — so priming/carpeting a cell *this turn* won't affect the noise the *same-turn* sensor emitted. It can, however, affect the **opponent's** next sensor reading.
20. **Rat position doesn't change during capture respawn** — the rat "teleports" back to (0,0) and takes 1000 silent moves; no sensor data is generated for those moves, so there is no information leakage.
21. **Board deep-copy drops history** — `get_copy` always constructs with `build_history` defaulting to False and does not clone history (`engine/game/board.py:318-333`). This is fine for game-tree simulation but worth knowing.
22. **No tie-breaking for `Result.TIE` by POINTS** — a perfectly tied score on turn 80 is a genuine tie, not a secondary tiebreak (`engine/game/board.py:300-305`).

---

## 10. Discrepancies / additions vs. CLAUDE.md

Line references below are to the current `CLAUDE.md` on disk.

1. **CLAUDE.md (line 11)** says the game ends "after each player has had 40 turns (so 80 plies total), or earlier if someone crashes / runs out of time / makes an invalid move." — accurate, but additionally the engine terminates on **MEMORY_ERROR** (1536 MB RAM cap, 4 GB VRAM cap) and on **FAILED_INIT**. Not mentioned in CLAUDE.md. See §8.
2. **CLAUDE.md (line 14)** says plain step "cannot step onto a primed square. (Carpeted squares are walkable by either player.)" — correct, and the full blocker set is `BLOCKED ∪ PRIMED ∪ both workers ∪ out_of_bounds`; CLAUDE.md doesn't mention that the opponent's worker also blocks.
3. **CLAUDE.md (line 15)** says PRIME's current square "must not already be PRIMED or CARPET. Destination square must not be blocked or primed." — correct, but should add that destination may be CARPET or SPACE (it cannot be BLOCKED, PRIMED, or either worker). Also the current square effectively cannot be BLOCKED because you cannot stand on BLOCKED.
4. **CLAUDE.md (line 16)** says carpet roll "ending on the k-th square" — correct; just re-emphasizing that `player_worker.position` is updated to the k-th square, so after CARPET you are standing on a CARPET cell (prevents chaining further PRIME from that position without moving first).
5. **CLAUDE.md (line 26)** "4 minutes total across all 40 of your moves... Game overall can run up to 8 min." — in **tournament** mode (`limit_resources=True`). In local mode (`run_local_agents.py` default `limit_resources=False`), you actually get **6 minutes** each (`play_time = 360`). This means local-self-play benchmarks run with 50% more CPU than the tournament. Tune accordingly. See `engine/gameplay.py:236-238`.
6. **CLAUDE.md (line 30)** "Each corner has a random blocked rectangle (2×3, 3×2, or 2×2)." — correct. It does not note that these corners can overlap spawns (see §1) — a bot should not assume a clean center.
7. **CLAUDE.md (line 31)** "Players spawn **horizontally mirrored** in the inner 4×4 (x ∈ {2,3,4,5}, y ∈ {2,3,4,5})." — *slightly inaccurate.* The engine actually picks `x ∈ {2, 3}` for A and then uses `(7 - x, y)` for B — so A is always on the **left half** (x=2 or 3) and B on the **right half** (x=4 or 5). Spawns are not uniform over `{2..5}×{2..5}` — A is uniform over `{2,3}×{2..5}` (8 cells) and B mirrors. See `engine/board_utils.py:186-190`.
8. **CLAUDE.md (line 36)** "Edges clip. Rat can pass under blocked squares." — correct. Also worth noting: the transition matrix's row is **not** regenerated to zero out off-edge transitions dynamically; instead the pickled tables are expected to already encode this, and the ±10% noise preserves sparsity (zero × (1+η) = 0).
9. **CLAUDE.md (line 37)** "The rat spawns at (0,0) and takes 1000 silent headstart moves before the game begins (and again every time it's caught — always from (0,0) with 1000 moves)." — correct and important. Add: **no sensor readings are emitted during those 1000 moves**, so the post-capture prior is again `δ_{(0,0)} · T^1000` and belief collapses to exactly that distribution.
10. **CLAUDE.md (line 38)** "`T` is **passed into `__init__` as `transition_matrix`**." — correct. It is a **JAX array** (`jnp.float32`), not a numpy array (`engine/gameplay.py:19`). Be aware of jax-numpy interop if your HMM code uses numpy — you may need to `np.asarray(T)` on entry.
11. **CLAUDE.md (line 52-57)** for `estimated_distance`: correct table. Add: "Clamped to ≥ 0" means the error distribution is *asymmetric* at small true distances — if actual == 0, you can only report 0, 1, or 2 (the −1 branch is clipped to 0), so P(reported=0 | actual=0) ≈ 0.12 + 0.70 = 0.82.
12. **CLAUDE.md (line 86)** "`board.forecast_move(move, check_ok=True)` — returns a deep-copied Board with the move applied; does **not** reverse perspective." — correct. Also returns `None` on invalid move; callers must handle `None`.
13. **CLAUDE.md (line 96)** "Direction.UP=0, RIGHT=1, DOWN=2, LEFT=3" — correct enum order. The order `get_valid_moves` iterates is `UP, DOWN, LEFT, RIGHT` (`engine/game/board.py:161-167`) — *not* enum order. This matters for deterministic move ordering / ties.
14. **CLAUDE.md (line 134)** "`ALLOWED_TIME=240`" — correct; but the actual per-game budget the engine uses depends on `limit_resources`. Tournament = 240; local = 360.
15. **CLAUDE.md (line 208)** "`get_valid_moves` excludes search by default" — correct. Reminder: the 64 SEARCH candidates are precomputed as `board.valid_search_moves` (`engine/game/board.py:70-71`).
16. **CLAUDE.md (line 213)** search EV threshold of 1/3 — correct for the raw point EV (P > 2/(4+2) = 1/3). Not mentioned: SEARCH also costs you a turn (you do not advance your worker, do not prime, do not roll). The true opportunity cost is ≈ max-alternative-move-value + 2 − 6·P(rat).
17. **CLAUDE.md (line 214)** "Priming is +1/square but blocks your own future plain-steps onto it (you can only walk over carpet once it's rolled)." — correct and important. Plain step and prime step both test `is_cell_blocked`, which flags PRIMED cells as blocked.
18. **CLAUDE.md (line 215)** "Opponent can walk on your carpet — don't carpet in places that gift them mobility." — correct; CARPET is in neither the movement blocker mask nor the carpetable mask, so it's a free walk surface for both.
19. **Not in CLAUDE.md:** the **exact** update path for `opponent_search` / `player_search` uses a 2-element `deque` and is reassigned after `reverse_perspective`. See §5. Important when walking a custom game tree — you must replicate this.
20. **Not in CLAUDE.md:** `apply_move(SEARCH)` **does not** adjust points; `play_game` does, *after* `apply_move`. `forecast_move(SEARCH)` therefore will NOT reflect rat-catch points on the resulting board.
21. **Not in CLAUDE.md:** `Board.get_copy()` intentionally drops the history object (docstring does say "without history" but the rationale — that history serialization is expensive and copies can be used inside search — may not be obvious).
22. **Not in CLAUDE.md:** Memory cap is 1536 MB RSS (not "1 GB" as the code comment claims). See `engine/player_process.py:166-167` — the `limit_mb = 1536` constant with `# set limit to 1 gb` comment is misleading; 1536 MB = 1.5 GB.
23. **Not in CLAUDE.md:** SIGSTOP/SIGCONT is used to freeze the player process between turns under `limit_resources=True` (`engine/player_process.py:532-627`). Agents cannot rely on background threads doing work between plies — they are suspended.

---

## 11. Quick reference — constants, file map

| Constant | Value | Source |
|----------|-------|--------|
| `BOARD_SIZE` | 8 | `engine/game/enums.py:5` |
| `MAX_TURNS_PER_PLAYER` | 40 | `engine/game/enums.py:4` |
| Total plies | 80 | `2 * MAX_TURNS_PER_PLAYER` |
| `ALLOWED_TIME` (default) | 240 s | `engine/game/enums.py:15` |
| Tournament `play_time` | 240 s | `engine/gameplay.py:232` |
| Local `play_time` | 360 s | `engine/gameplay.py:238` |
| `init_timeout` (tournament) | 10 s | `engine/gameplay.py:234` |
| `init_timeout` (local) | 20 s | `engine/gameplay.py:237` |
| `extra_ret_time` | 5 s | `engine/gameplay.py:233` |
| `HEADSTART_MOVES` | 1000 | `engine/game/rat.py:6` |
| `RAT_BONUS` | +4 | `engine/game/enums.py:16` |
| `RAT_PENALTY` | −2 | `engine/game/enums.py:17` |
| CARPET points `k=1..7` | −1,2,4,6,10,15,21 | `engine/game/enums.py:6-14` |
| Memory cap (RSS) | 1536 MB | `engine/player_process.py:166` |
| VRAM cap | 4 GB | `engine/player_process.py:184` |
| Transition noise amplitude | ±10% per entry | `engine/gameplay.py:22-24` |
| Number of T pkl files | 4 | `engine/transition_matrices/` |

| Need to find... | File:function |
|-----------------|---------------|
| Valid-move check | `engine/game/board.py:is_valid_move` (line 73) |
| Apply move | `engine/game/board.py:apply_move` (line 218) |
| Forecast | `engine/game/board.py:forecast_move` (line 199) |
| Reverse perspective | `engine/game/board.py:reverse_perspective` (line 395) |
| Valid moves list | `engine/game/board.py:get_valid_moves` (line 130) |
| Rat move | `engine/game/rat.py:Rat.move` (line 83) |
| Rat spawn | `engine/game/rat.py:Rat.spawn` (line 127) |
| Noise emission | `engine/game/rat.py:NOISE_PROBS, make_noise` |
| Distance emission | `engine/game/rat.py:DISTANCE_ERROR_PROBS, estimate_distance` |
| Game loop | `engine/gameplay.py:play_game` (line 207) |
| `T` loading + noise | `engine/gameplay.py:_load_transition_matrix` (line 10) |
| Spawn generation | `engine/board_utils.py:generate_spawns` (line 186) |
| Blocked corner setup | `engine/gameplay.py:254-262` |
| Per-move timing | `engine/player_process.py:run_timed_play` (line 432) |
| Constructor signature | `engine/player_process.py:324` |
| Seccomp / resource caps | `engine/player_process.py:apply_seccomp` (line 44), `checkMemory` (line 169) |
