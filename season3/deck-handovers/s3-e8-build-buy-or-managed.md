# S3 E8 deck handover: Build, buy, or managed

For the content agent. No experiment: a teaching deck that adds sourcing as a setting, backed by Season 2's embedding swap and long-context results. Costs are not covered: they go to Season 6.

## Sources of truth

- `season3/case/rule.yaml` (the `sourcing` block: application build, buy or none; model access direct, managed, self hosted, vendor or none).
- `season3/case/scores.yaml` (each candidate's sourcing and its reason) and `season3/case/results/scorecard-e8.json`; chart `season3/case/results/charts/scorecard-e8-slide.svg`.
- `season3/case/candidates.yaml` (whether a vendor product already does it; whether the data carries personal information).
- `field-notes/s2-e12-embedding-swap/README.md` (the price of changing the embedding model).
- `field-notes/s2-e13-long-context-or-retrieval/README.md` (the pipeline against sending everything).
- `season2/reference.yaml` (the Season 2 system called each model maker's own API directly).

Branch `s3`.

## Names

| | Value |
|---|---|
| Episode code | S3 E8 |
| Title | Build, buy, or managed |
| Hub slug | `build-buy-or-managed` (proposed; confirm) |
| Deck file | `bk-s3-e8-build-buy-or-managed-v1.pdf` |
| Hub format | `explainer` |

## The argument

Two separate choices, which people often run together.

1. **The application: build or buy.** Driven by E6. Build the part that sets you apart (it rests on your own data and workflow). Buy the part that is table stakes: what every competitor can also buy.
2. **Model access: direct, managed or self hosted.** Driven by where your data may go (E4's data and regulatory needs), by how easily you can swap the model, and by how quickly you get new models.

Define the terms on the slide:

- **Direct:** call each model maker's own API.
- **Managed:** call models through a cloud platform's managed service, inside the firm's existing cloud account. **Amazon Bedrock** is one example. Name no other vendors.
- **Self hosted:** run open-weight models on infrastructure the firm controls.

Season 2 supplies two reasons to keep the model swappable. Changing the embedding model means re-embedding the whole library and rerunning every evaluation, and the bigger model was worse. And sending the whole library to a model removes the pipeline, but cost about ten times as much per question.

Close by handing costs, total cost of ownership and self-hosting break-even to Season 6. This episode does not cost anything.

## Case recap slide

Chart: `season3/case/results/charts/scorecard-e8-slide.svg` (from `lab strategy reveal --through E8`).

New column this episode adds: **Sourcing** (a setting, not a score): application and model access.

| Candidate | Application | Model access | Reason, from `scores.yaml` |
|---|---|---|---|
| C1 Website assistant | build | managed | The library is Halvard's own; customer questions carry personal data, so models are called inside the firm's existing cloud account |
| C2 Reply drafts for agents | build | managed | Same system as C1; contacts carry personal data |
| C3 Warranty claim triage | buy | vendor | Service desk products already route tickets; Halvard configures its queues |
| C4 Safety signal screening | build | managed | No product does this screen; contacts carry personal data |
| C5 Automatic refund approval | none | none | Redirected at G2: a rules engine over the order system |
| C6 Library consistency check | build | direct | Reads only Halvard's policies and articles, which hold no personal data; keep the model swappable |
| C7 Call and chat summaries | buy | vendor | A commodity feature of contact-centre products |
| C8 Spare parts demand forecast | none | none | Redirected at G2: a forecasting model or a bought planning product |

Earlier columns carry forward from `scorecard-e8.json`. Time to evidence is not shown until E11.

Measured versus assumed: sourcing is a **setting with a stated reason**, not a measurement. The case recommends it; no experiment compared managed with direct access. The reasons draw on facts about each candidate recorded in `candidates.yaml` (for example, which candidates carry personal data), which are invented.

## Evidence

| Figure | What it measures | Source | Status |
|---|---|---|---|
| 354 to 337 of 400 | Answerable questions answered right after swapping the embedding model for a larger one (17 fewer) | `field-notes/s2-e12-embedding-swap/README.md` | Measured |
| 344 to 326 of 400 | Passages found by search after the same swap (18 fewer) | same | Measured |
| 288,666 tokens | The size of the library to re-embed; cheap at this size, and the cost scales with the library | same | Measured; cost is a ratio only here |
| 75 against 71 of 80 | Hard items answered right with all 304 documents in the prompt against retrieval; intervals overlap | `field-notes/s2-e13-long-context-or-retrieval/README.md` | Measured |
| About 10 times | Cost per question, long context against retrieval, in the mean | same | Measured, one model, no prompt caching |
| 11 times | Input tokens per question, long context against retrieval (medians 160,398 against 14,598) | same | Measured |
| 1.9 against 2.5 seconds | Median time per question, long context against retrieval | same | Measured; run in different batch sizes |

Do not show prices. Show the ratios.

## Slide ideas

Follow the deck rules: teach before compressing, step one example through before any statistics, a reader prediction revealed on the very next slide, varied visual forms, one-line titles, little text, no claim-verdict slides, and the last slide is the series map.

1. **Two layers.** A two-layer diagram: the application on top (build or buy), model access underneath (direct, managed, self hosted).
2. **One use case, both layers.** Step one example all the way through, no statistics: take C2, reply drafts for agents. The application is built because the library is Halvard's own. Model access is managed because the contacts carry personal data and the models should be called inside Halvard's existing cloud account.
3. **What managed means.** One slide, one definition, with Amazon Bedrock named as an example. A simple picture: your data stays in your cloud account, models are called from there.
4. **Prediction.** "Of Halvard's eight candidates, which two should be bought, not built?" Reader picks.
5. **Reveal.** C3 and C7, bought as products, because service desks and contact-centre tools already do the job and what you add is configuration (they have the lowest Durable advantage scores from E6).
6. **Keep the model swappable.** Prediction: "Swapping to a bigger, pricier embedding model: better, worse or the same?" Reader picks.
7. **Reveal.** Worse: 17 fewer right answers of 400. Re-embedding the library was cheap at this size; the real cost is rerunning every evaluation and the risk.
8. **The pipeline or everything.** A two-bar slide: long context against retrieval, 75 against 71 of 80 hard items (overlapping), about ten times the cost per question. Fits the window today; scoping, change and size are the limits.
9. **Choose model access by three questions.** Where may our data go? How easily can we swap? How soon do we need new models? A small decision grid for direct, managed and self hosted.
10. **The sixth column.** Reveal `scorecard-e8-slide.svg`: build with managed for C1, C2 and C4, build with direct access for C6, buy for C3 and C7, none for C5 and C8.
11. **Where the money goes.** One closing slide: costs, total cost of ownership and the self-hosting break-even are Season 6.
12. **Series map** (last slide), Season 3 highlighted, E8 marked.

## For leaders

**Ask your team:** "If our model provider doubled its price tomorrow, what would it take to move?"

## Decision rule (proposed)

**"Own the layer that sets you apart and rent the rest. Choose model access by where your data may go, and keep the model swappable."**

## Next

E9, Field note: does it survive a model change? A measured test of what breaks when the model changes under a working system.

## Careful with

- **Costs and total cost of ownership belong to Season 6.** Do not compare managed, direct and self hosted on price, and do not show a break-even. Season 6 also owns self-hosting.
- **No experiment compared managed with direct.** The sourcing settings are recommendations with reasons. Say "recommend", not "show".
- **Name no vendor except Amazon Bedrock as the one managed example.** Do not rank providers or products.
- **The long-context figures are one model and one library of 160,000 tokens.** The arm was handed only current public documents. It cannot scope documents per user or keep up with a library that changes.
- **The embedding swap is two models from one provider, with no retuning.** Another provider's model might do better.
- **Do not show totals, ranks or the first pick.**
- **Halvard Home is invented.** No legal claims beyond "consumer protection, product safety and data protection law". Where data may go is a question for the firm's own legal and data protection advice.
- **Boundaries.** Costs and TCO are S6, people and operating model S9, policy and controls S15.

## From practice

_Brendan to add one anonymised line from his own practice._
