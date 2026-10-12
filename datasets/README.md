# Datasets

Sources and licences for every dataset used in the field notes.

Each field note's `build_dataset.py` builds its own data, byte for byte, from the seed in its
`config.yaml`.

A dataset is committed only when every part of it is ours. S1 E10's task items are, so they are
committed and every question can be read in the repository. S1 E7's documents contain Project
Gutenberg text, so they are not: they land in `field-notes/<episode>/dataset/`, which is
gitignored, and are rebuilt on demand.

## S1 E7: lost in the middle

**What it contains.** Passages from six public-domain novels, each with one invented fact
inserted at a measured position. The facts are generated from the config seed, so they cannot
have appeared in any model's training data.

**Source.** Project Gutenberg, via the mirror `https://gutenberg.pglaf.org`.

| Gutenberg ID | Title | Author |
|---|---|---|
| 1342 | Pride and Prejudice | Jane Austen |
| 2701 | Moby Dick; or, The Whale | Herman Melville |
| 1400 | Great Expectations | Charles Dickens |
| 98 | A Tale of Two Cities | Charles Dickens |
| 345 | Dracula | Bram Stoker |
| 84 | Frankenstein; Or, The Modern Prometheus | Mary Wollstonecraft Shelley |

**Licence.** All six works are in the public domain in the United States. Project Gutenberg
grants no permission and withholds none for public-domain items, because nobody can. The name
"Project Gutenberg" is a registered trademark, and the licence in each eBook's header and footer
governs its use. `build_dataset.py` strips that header and footer, so the extracted text carries
neither the trademark nor its licence conditions. Verified on 17 September 2026 against
[the permission how-to](https://www.gutenberg.org/policy/permission.html).

Readers outside the United States should confirm the copyright status of these works where they
are, as Project Gutenberg's policy notes.

**How it is downloaded.** Project Gutenberg's
[robot policy](https://www.gutenberg.org/policy/robot_access.html) states that the main website
is for human users only and that automated access there will get an IP address blocked. The
builder therefore downloads from a mirror, never from `www.gutenberg.org`, and caches each file
in `.cache/gutenberg/` so a rebuild makes no new requests.

**Integrity.** Each book is pinned in `config.yaml` by identifier and by the SHA-256 of the
mirror file. A download whose checksum does not match fails the build with a message naming the
book and both digests, rather than quietly producing a different dataset. Checksums were taken on
17 September 2026; if a mirror file legitimately changes, check the text and update the checksum
in the config.

## S1 E10: reasoning versus standard

**What it contains.** 120 generated questions with known correct answers, in four families:
extraction from a short operations log, short arithmetic word problems, warehouse state tracking,
and seven-job ordering puzzles.

**Source.** None. Every item, including the prose in the extraction passages, is generated from
the seed in the field note's `config.yaml`, so no question can have appeared in a model's
training data.

**Licence.** Wholly ours, under the repository's MIT licence. No third-party content is involved,
which is why these items are the one dataset in the repository that **is committed**: they live in
`field-notes/s1-e10-reasoning-vs-standard/tasks/items.jsonl`, so readers can inspect every
question rather than take the results on trust.

**Integrity.** `tasks/manifest.json` records the seed, the task list, the number of items, and the
SHA-256 of `items.jsonl`. A file that no longer matches the config is rebuilt rather than used, so
a run can never send questions the committed config does not describe.

**Correctness.** The test suite re-solves every item independently from the published prompt:
the arithmetic is worked out again, the warehouse movements are replayed, and each puzzle is brute
forced over all 5,040 orderings to confirm that exactly one fits its clues and that it is the
recorded answer.

## Season 2: the Halvard library

**What it contains.** The one library and test set every Season 2 episode runs on, in
`datasets/halvard/`, corpus version `halvard-v2`. Halvard Home is an invented maker of home
appliances. There are 344 document versions:

- 300 short support articles, kept byte for byte from v1 S2 E3;
- four long policies (warranty, returns, safety, servicing), about 27,500 tokens each, and an
  earlier version of each whose terms differ only where the version questions look;
- four staff-only documents;
- 32 withdrawn notices, marked deleted.

There are 520 test items and 100 dev items of 16 types. Each answerable item points to the
exact characters that answer it, so it can be scored under any chunking. The current public
library is 155,413 tokens (`o200k_base`), more than a 128,000-token window holds.

**Source.** None outside this repository. Every fact and value is generated from the seed in
`config.yaml`. `gpt-6-astra` wrote the prose around sentences it was given word for word, and
`claude-sonnet-5-5` checked that no public passage answers an unanswerable question. Every
call is logged in `generation/`.

**Licence.** Wholly ours, under the repository's MIT licence, so it is committed.

**Integrity.** `manifest.json` pins every document by SHA-256 and records its token counts, and
the loader refuses a file that does not match. The library was **frozen on 12 October 2026**,
before any episode ran: `tests/rag/test_rag_frozen_corpus.py` pins the manifest and both item
files, so any change fails the test suite. A change means a new corpus version and a rerun of
every episode.

**Correctness.** Code checked every generated section: each required sentence appears exactly
once, no other number, amount or product name appears, and the length is within bounds. A
failed section went back to the model with the reason. Every planted value is unique in the
whole library, including the v1 articles, so a value found in an answer can only have come from
its own passage. Brendan read three items of every type beside their evidence
(`review.md`) before the library was frozen.

**Rebuild.** `uv run lab rag build-corpus --estimate` prices a build with no key. A rebuild
with keys is served from the response cache and sends nothing.
