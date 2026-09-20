"""The 20 items for S1 E9, and how each was verified. Fixed before any call was made.

Two categories, five real items and five invented ones in each. Every real item was checked
against a primary record, and every invented item was searched for and not found. Nothing here
was replaced: no invented item turned out to exist or to be close to a real one.

Checked on 20 September 2026 (UTC), from records the sources themselves publish, never from the
model or from memory.

Acts: the Irish Statute Book, irishstatutebook.ie.
- A real Act was fetched by its number and year, and its page title read.
- An invented Act was searched for by scanning the list of every Act of the Oireachtas for every
  year from 1922 to 2026, not only the year it is named for, for its full title and for its
  distinctive words. The lists are at https://www.irishstatutebook.ie/eli/<year>/act/.

Papers: arXiv, Crossref, the NeurIPS proceedings, OpenAlex and Semantic Scholar.
- A real paper was fetched by its arXiv identifier, and where it has one by its Crossref DOI or
  its NeurIPS proceedings page. Its year is the year of its formal publication in that record,
  the same rule for every paper. The year of its first arXiv version is kept beside it, because
  for three of the five the two differ.
- An invented paper was searched for by title in Crossref (10 results), OpenAlex (10 results),
  and arXiv, twice: by the exact title phrase, and by all the distinctive title words at once. A
  search for the same words that finds a real paper is what shows the method can find one. Results
  were compared with the title by string similarity, and any result at or above 0.8, or anything
  that looked like the same paper, was to trigger a replacement. The closest result to each
  title is recorded.
- Semantic Scholar was also tried. It answered "too many requests" (HTTP 429) to four of the
  five titles, after repeated attempts over several minutes, and returned one unrelated result to
  the fifth. It is therefore not counted as a source for the four, and the three sources above are.
"""

CHECKED_UTC = "2026-09-20"
NOT_VERIFIED_SOURCE = (
    "Semantic Scholar: HTTP 429 (too many requests) after repeated attempts, so not counted."
)
SCANNED_YEARS = "1922 to 2026"
ISB = "https://www.irishstatutebook.ie/eli"


def _real_act(slug: str, name: str, year: int, number: int, note: str = "") -> dict:
    return {
        "id": slug,
        "category": "acts",
        "real": True,
        "name": name,
        "verification": {
            "checked_utc": CHECKED_UTC,
            "source": "Irish Statute Book",
            "url": f"{ISB}/{year}/act/{number}/enacted/en/html",
            "record": f"{name}, No. {number} of {year}. {note}".strip(),
        },
    }


def _invented_act(slug: str, name: str, words: list[str], nearest: str = "") -> dict:
    year = name[-4:]
    return {
        "id": slug,
        "category": "acts",
        "real": False,
        "name": name,
        "verification": {
            "checked_utc": CHECKED_UTC,
            "source": "Irish Statute Book, list of Acts for every year",
            "url": f"{ISB}/{year}/act/",
            "record": (
                f"Not found. No Act of any year from {SCANNED_YEARS} has this title"
                + (
                    f", and no Act title contains {', '.join(repr(word) for word in words)}."
                    if words
                    else "."
                )
                + (f" {nearest}" if nearest else "")
            ),
        },
    }


def _real_paper(
    slug: str, title: str, authors: str, year: int, record: str, first_arxiv: str, url: str
) -> dict:
    return {
        "id": slug,
        "category": "papers",
        "real": True,
        "title": title,
        "authors": authors,
        "year": year,
        "verification": {
            "checked_utc": CHECKED_UTC,
            "source": record,
            "url": url,
            "record": f"Exists. Year used: {year}, from its formal publication record. "
            f"First arXiv version: {first_arxiv}.",
        },
    }


def _invented_paper(
    slug: str, title: str, authors: str, year: int, crossref: str, openalex: str
) -> dict:
    return {
        "id": slug,
        "category": "papers",
        "real": False,
        "title": title,
        "authors": authors,
        "year": year,
        "verification": {
            "checked_utc": CHECKED_UTC,
            "source": "Crossref, OpenAlex, arXiv (Semantic Scholar unavailable)",
            "url": "https://api.crossref.org/works?query.title=",
            "record": (
                "Not found. No arXiv paper has this title as a phrase or has all its "
                f"distinctive words in its title. Closest Crossref result: {crossref}. "
                f"Closest OpenAlex result: {openalex}. Neither is this paper. "
                + NOT_VERIFIED_SOURCE
            ),
        },
    }


ITEMS = [
    _real_act("acts-real-1", "Data Protection Act 2018", 2018, 7),
    _real_act("acts-real-2", "Companies Act 2014", 2014, 38),
    _real_act("acts-real-3", "Freedom of Information Act 2014", 2014, 30),
    _real_act("acts-real-4", "Consumer Protection Act 2007", 2007, 19),
    _real_act(
        "acts-real-5",
        "Employment Equality Act 1998",
        1998,
        21,
        "The Statute Book titles it 'Employment Equality Act, 1998', with a comma.",
    ),
    _invented_act(
        "acts-invented-1",
        "Algorithmic Accountability (Public Bodies) Act 2019",
        ["algorithmic", "accountability (public bodies)"],
    ),
    _invented_act(
        "acts-invented-2",
        "Digital Records Stewardship Act 2016",
        ["stewardship", "digital records"],
    ),
    _invented_act(
        "acts-invented-3",
        "Consumer Credit (Automated Decisions) Act 2021",
        ["automated decision", "consumer credit (automated"],
    ),
    _invented_act(
        "acts-invented-4",
        "Data Portability and Interoperability Act 2020",
        ["portability", "interoperability"],
    ),
    _invented_act(
        "acts-invented-5",
        "Artificial Intelligence (Registration) Act 2022",
        [],
        "Each distinctive phrase was also searched alone. 'artificial intelligence' appears in "
        "one Act title, the Regulation of Artificial Intelligence Act 2026 (No. 31 of 2026), and "
        "'(registration)' in one, the Perpetual Funds (Registration) Act, 1933. Neither is close "
        "to this title or year, so this item was kept.",
    ),
    _real_paper(
        "papers-real-1",
        "Attention Is All You Need",
        "Vaswani et al.",
        2017,
        "NeurIPS 2017 proceedings, and arXiv 1706.03762",
        "2017-06-12",
        "https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html",
    ),
    _real_paper(
        "papers-real-2",
        "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "Devlin et al.",
        2019,
        "Crossref DOI 10.18653/v1/N19-1423 (NAACL-HLT 2019), and arXiv 1810.04805",
        "2018-10-11",
        "https://doi.org/10.18653/v1/N19-1423",
    ),
    _real_paper(
        "papers-real-3",
        "Deep Residual Learning for Image Recognition",
        "He et al.",
        2016,
        "Crossref DOI 10.1109/CVPR.2016.90 (CVPR 2016), and arXiv 1512.03385",
        "2015-12-10",
        "https://doi.org/10.1109/CVPR.2016.90",
    ),
    _real_paper(
        "papers-real-4",
        "Language Models are Few-Shot Learners",
        "Brown et al.",
        2020,
        "NeurIPS 2020 proceedings, and arXiv 2005.14165",
        "2020-05-28",
        "https://proceedings.neurips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html",
    ),
    _real_paper(
        "papers-real-5",
        "Lost in the Middle: How Language Models Use Long Contexts",
        "Liu et al.",
        2024,
        "Crossref DOI 10.1162/tacl_a_00638 (TACL), and arXiv 2307.03172",
        "2023-07-06",
        "https://doi.org/10.1162/tacl_a_00638",
    ),
    _invented_paper(
        "papers-invented-1",
        "Recurrent Sparsity in Mixture-of-Heads Transformers",
        "Okafor and Lindqvist",
        2021,
        "'Exploring sparsity in graph transformers' (2024), similarity 0.66",
        "'Axial Attention in Multidimensional Transformers' (2019), similarity 0.53",
    ),
    _invented_paper(
        "papers-invented-2",
        "Calibrated Refusal in Instruction-Tuned Language Models",
        "Brennan, Takahashi and Moreau",
        2022,
        "'Speechworthy Instruction-tuned Language Models' (2024), similarity 0.73",
        "'Aya Model: An Instruction Finetuned Open-Access Multilingual Language Model' (2024), "
        "similarity 0.61",
    ),
    _invented_paper(
        "papers-invented-3",
        "Gradient Echoes: Memory Traces in Long-Context Decoders",
        "Varga and Osei",
        2023,
        "'Competition between two memory traces for long-term recognition memory' (2009), "
        "similarity 0.55",
        "'Prediction and memory: A predictive coding account' (2020), similarity 0.45",
    ),
    _invented_paper(
        "papers-invented-4",
        "Token Drift Under Repeated Paraphrase",
        "Nakamura and Fitzgerald",
        2020,
        "'Ether Drift Experiment Is Repeated with Success' (1938), similarity 0.57",
        "'Monolingual plagiarism detection and paraphrase type identification' (2020), "
        "similarity 0.33",
    ),
    _invented_paper(
        "papers-invented-5",
        "Sparse Anchors for Faithful Summarisation",
        "Delacroix and Mbeki",
        2022,
        "'In-browser summarisation' (2008), similarity 0.55",
        "'Learning Sentence-internal Temporal Relations' (2006), similarity 0.40",
    ),
]

# What was replaced after checking. Empty: every item was kept as first written.
REPLACEMENTS: list[dict] = []
