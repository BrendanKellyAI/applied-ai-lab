# S4 E4: Making output a contract

Code reads Task A's output. Does asking the provider to enforce the format, with JSON mode or a
strict schema, make the output safer to read, and does it change the answers? Claims and pass
marks: [`PREREGISTRATION.md`](PREREGISTRATION.md), with two dated amendments.

**Result: with this model and prompt, the format was never the problem.** All three arms
returned valid output on all 600 items, and accuracy did not move: 593, 594 and 593 of 600.
Both claims held. A schema is cheap insurance here, not a fix.

## The design

- **Data:** Task A, dev 200 to choose, test 600 to report.
- **Answer model:** `gpt-6-luna`, reasoning off, output limit 200.
- **Prompt and examples:** E3's best arm, the one-line prompt with the 8 similar examples
  (Amendment 1).
- **Arms:**

  | Arm | Output |
  |---|---|
  | `e4-text` | Free text, then the parser: E3's best arm, the reference (cached) |
  | `e4-json-mode` | The provider's JSON mode, then the same parser |
  | `e4-schema` | A strict JSON schema of the four fields and their allowed values, then the same parser |

- **The parser is the same for every arm** and still validates: a reply that is not one JSON
  object with four allowed values is invalid and wrong on every field.
- **Statistics:** Wilson intervals; exact McNemar against `e4-text`, Holm corrected across the
  two.
- **The choice:** on dev, the highest fully right; a tie goes to the stronger contract. Dev:
  text 196, **JSON mode 197**, schema 195 of 200; all 200 valid in every arm.
- **The first JSON mode run failed** (Amendment 2): every call was rejected, at no charge,
  because JSON mode needs the word "json" in the input messages and the system prompt was sent
  where it does not count. The adapter now sends it as a developer message, and rejected
  requests are no longer retried. That arm was rerun; the others were not.

## Results (test, 600 items)

| Arm | Valid | Fully right | Accuracy among valid | Wrong to right | Right to wrong | Holm p | Output tokens per call |
|---|---|---|---|---|---|---|---|
| `e4-text` (reference) | 600 | 593 (98% to 99%) | 98.8% | | | | 27.3 |
| **`e4-json-mode`** | 600 | **594 (98% to 100%)** | 99.0% | 3 | 2 | 1.0 | 30.3 |
| `e4-schema` | 600 | 593 (98% to 99%) | 98.8% | 2 | 2 | 1.0 | 31.3 |

Safety recall was 65 of 65 and false alarms 3 of 535 in every arm. The few items that flipped
did so both ways, as noise does.

**Why validity did not change:** the free text replies were already valid on every item, in E1
and here. The prompt asks for one JSON object and lists the allowed values, and this model
follows that. The schema's guarantee matters for a model or prompt that does not, and for the
day a model is changed (S3 E9).

## The claims

**C1 held: a schema makes every reply readable.** 600 of 600 valid.

**C2 held: constraining the format does not change accuracy.** Neither JSON mode nor the schema
differs from free text (Holm-corrected p 1.0 for both).

## The scoreboard

`e4-json-mode` is E4's candidate and does not join: its interval (98% to 100%) overlaps the
reference's, `e2-definitions` (96% to 99%). The Task A reference stays `e2-definitions`, which
is also the arm E5 tunes against: the best prompted arm on dev across E2 to E4 (199 of 200),
under E4 Amendment 1.

## What this does not show

- One provider's JSON mode and schema support; others enforce formats differently.
- **JSON mode sent the same words a different way.** With JSON mode the system prompt goes as a
  developer message, not as instructions (Amendment 2), so the comparison with text changes
  the transport as well as the format.
- Strict schemas fix the allowed values, so they also stop invented routes; validity and
  accuracy cannot be fully separated.
- Validity was already 100%, so this run cannot show how much a schema rescues a model that
  breaks the format.

## Charts

`results/charts/`: **`fully_right`**, dev and test, as a slide (SVG and PNG) and an article image.

## Cost

Costs are ratios to `e4-text`, answer calls only.

| Arm | Input tokens per call | Cost per item |
|---|---|---|
| `e4-json-mode` | the same | 0.24 times |
| `e4-schema` | 1.14 times | 1.14 times |

The schema adds about 180 input tokens a call and 4 output tokens. JSON mode's low ratio is
caching, not the format: `e4-text`'s replies came from E3's run with nothing cached, and JSON
mode, run later with the same prompts, had about 94% of its input billed at the cached rate.
In a steady service the three would cost about the same, with the schema slightly higher.

## Run it

```bash
uv run lab adapt analyse episodes/s4-e4-making-output-a-contract/config.yaml
uv run python episodes/s4-e4-making-output-a-contract/claims.py test
```

To call the model again (replies are cached): `uv run lab adapt run
episodes/s4-e4-making-output-a-contract/config.yaml`. The dev run is `config.dev.yaml`;
`ceiling.yaml` and `ceiling.dev.yaml` are the approved cost ceilings and were never run.
