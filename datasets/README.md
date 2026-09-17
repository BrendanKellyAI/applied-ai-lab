# Datasets

Sources and licences for every dataset used in the field notes.

Datasets are **not committed**. Each field note's `build_dataset.py` rebuilds its own, byte for
byte, from the seed in its `config.yaml`. Built files land in `field-notes/<episode>/dataset/`,
which is gitignored.

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

To follow. Its generated task items are committed alongside the generator, because they are
wholly ours and readers should be able to see every question.
