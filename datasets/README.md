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
and five-job ordering puzzles.

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
forced over all 120 orderings to confirm that exactly one fits its clues and that it is the
recorded answer.
