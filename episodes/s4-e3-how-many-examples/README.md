# S4 E3: How many examples?

Worked examples are paid for on every call. How many does Task A need before the score stops
rising, and does it matter which examples, or their order? Claims and pass marks:
[`PREREGISTRATION.md`](PREREGISTRATION.md). Amendment 1 put the examples on E1's one-line prompt,
not on E2's best: E2's definitions left only one dev item to gain.

**Result: 8 well-chosen examples do as much as written definitions; 8 random ones do not.** The
8 most similar examples took the one-line prompt from 521 to 593 of 600. Random examples needed
32 to reach 583, at five times the prompt length. All four claims held. E3's best arm scored
above the reference but did not clear it, so the reference is unchanged.

## The design

- **Data:** Task A. Examples come from train only; dev 200 to choose, test 600 to report.
- **Answer model:** `gpt-6-luna`, reasoning off, output limit 200, free text output.
- **Base prompt:** E1's one-line prompt (Amendment 1). Examples go in the system prompt after it,
  each as the message and its label as JSON.
- **Arms.** Random examples are drawn once from train with seed 0 and nested: the 2 are the first
  2 of the 8, and the 8 the first 8 of the 32.

  | Arm | Examples |
  |---|---|
  | `e3-n0` | None: E1's arm, the reference (cached) |
  | `e3-random-2` | 2 random |
  | `e3-random-8` | 8 random |
  | `e3-similar-8` | The 8 train messages nearest each item (`text-embedding-3-small`, cosine), nearest last |
  | `e3-random-8-shuffled` | The same 8 random, in another order |
  | `e3-random-32` | 32 random |

- **Statistics:** Wilson intervals; exact McNemar against `e3-n0`, Holm corrected across the
  five.
- **The choice:** on dev, the highest fully right; ties go to fewer examples, then random, then
  unshuffled. Dev: n0 170, random-2 179, random-8 189, **similar-8 196**, random-32 192 of 200.

## Results (test, 600 items)

| Arm | Fully right | False alarms (535) | Input tokens per call | Wrong to right | Right to wrong | Holm p |
|---|---|---|---|---|---|---|
| `e3-n0` (reference) | 521 (84% to 89%) | 68 | 308 | | | |
| `e3-random-2` | 527 (85% to 90%) | 41 | 668 | 31 | 25 | 0.50 |
| `e3-random-8` | 562 (91% to 95%) | 20 | 1,512 | 52 | 11 | below 0.0001 |
| **`e3-similar-8`** | **593 (98% to 99%)** | **3** | 1,345 | 75 | 3 | below 0.0001 |
| `e3-random-8-shuffled` | 561 (91% to 95%) | 19 | 1,512 | 55 | 15 | |
| `e3-random-32` | 583 (96% to 98%) | 12 | 4,654 | 65 | 3 | below 0.0001 |

Two random examples barely moved the total: they fixed 31 items and broke 25. The hard case E1
failed worst, `safe_use_question` (6 of 40), shows what the examples carry: 20 with 2 random, 29
with 8, 31 with 32, and 40 of 40 with the 8 similar ones. The likely reason: a similar example
to a question about safe use is another question about safe use, with its label showing no
incident; a random draw may hold none.

### Beside E2, as context (not a claim)

| Arm | Fully right | Input tokens per call |
|---|---|---|
| `e2-definitions` (written definitions) | 587 | 947 |
| `e3-similar-8` (8 similar examples) | 593 | 1,345 |
| `e3-random-32` (32 random examples) | 583 | 4,654 |

Well-chosen examples can stand in for written rules, at about 40% more prompt and an embedding
step per message. Random examples need many more tokens to come close.

## The claims

**C1 held: examples help.** Random-8, similar-8 and random-32 each beat no examples with a
Holm-corrected p below 0.0001. Random-2 did not (p 0.50).

**C2 held: returns shrink.** 0 to 8 random examples gained 41 items; 8 to 32 gained 21, for 2.6
times the extra tokens.

**C3 held: similar examples beat random ones.** 593 against 562 at 8 examples: 32 items only
similar got right, 1 only random got right (exact McNemar p below 0.0001).

**C4 held: order alone moves answers.** The same 8 random examples in another order changed the
result on 27 of 600 items (4.5%, against a pass mark of 2%): 14 one way, 13 the other. The total
barely moved (562 against 561), so order is noise on single answers, not a bias in the score.

## The scoreboard

`e3-similar-8` is E3's candidate and does not join: its interval (98% to 99%) overlaps the
reference's, `e2-definitions` (96% to 99%). The Task A reference stays `e2-definitions`.

## What this does not show

- **One draw of random examples.** Another draw could score differently; only the order of this
  draw was varied, and that alone moved 27 answers.
- Similar examples are found by an embedding of the message alone, the Season 2 code.
- The base prompt was chosen on dev after E2's run (Amendment 1); the examples were not tuned
  on anything.

## Charts

`results/charts/`: **`fully_right`**, dev and test, as a slide (SVG and PNG) and an article image.

## Cost

Costs are ratios to `e3-n0`, answer calls only; the embedding calls for similar examples are
left out (they cost a small fraction of an answer call).

| Arm | Input tokens per call | Cost per item | Cost per fully right item |
|---|---|---|---|
| `e3-random-2` | 2.2 times | 1.81 times | 1.79 times |
| `e3-random-8` | 4.9 times | 0.85 times | 0.79 times |
| `e3-similar-8` | 4.4 times | 3.33 times | 2.93 times |
| `e3-random-32` | 15.1 times | 1.57 times | 1.40 times |

**Caching decides these ratios.** Fixed random examples make every call's system prompt the
same, so above the provider's minimum length most of it is billed at the cached rate (about 93%
of random-8's input tokens and 98% of random-32's). Similar examples differ for every message,
so nothing is cached and the shorter prompt costs four times as much as random-8. Random-2's
prompt is below the caching minimum. In a steady service the gap would be about this size.

## Run it

```bash
uv run lab adapt analyse episodes/s4-e3-how-many-examples/config.yaml
uv run python episodes/s4-e3-how-many-examples/claims.py test
```

To call the model again (replies are cached): `uv run lab adapt run
episodes/s4-e3-how-many-examples/config.yaml`. The dev run is `config.dev.yaml`; `ceiling.yaml`
and `ceiling.dev.yaml` are the approved cost ceilings and were never run.
