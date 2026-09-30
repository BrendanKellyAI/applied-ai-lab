"""The S2 E5 episode: the slide listing, the checks on built data, the grading, the claims, the
cache, and the whole pipeline end to end on a small invented library with a fake model.

No test calls the API or reaches the network.
"""

import copy
import hashlib
import re
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from lab.experiments import load_sibling

EPISODE = Path(__file__).parents[1] / "episodes" / "s2-e5-quiet-failures"
MARKER = "# Everything below this line matches the slides."
END_OF_LISTING = "\n# Not on the slides."
LISTING = '''import numpy as np


def search(query, index, allowed, k=5):
    """Top k entries this user may see, by cosine similarity.
    The metadata filter runs before ranking, so an entry
    the user may not see can never take a place in the top k."""
    keep = [i for i, entry in enumerate(index["entries"]) if allowed(entry)]
    vectors = index["vectors"][keep]
    q = query / np.linalg.norm(query)
    m = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    scores = m @ q
    best = np.argsort(-scores, kind="stable")[:k]
    return [index["entries"][keep[i]] for i in best], scores[best]'''


@pytest.fixture(scope="module")
def m():
    return SimpleNamespace(
        **{
            name: load_sibling(EPISODE / f"{name}.py")
            for name in ("library", "measure", "search", "chat", "build", "trials", "quiet")
        }
    )


@pytest.fixture(scope="module")
def config(m):
    return m.library.load_config()


# The slide listing --------------------------------------------------------------------------


def test_listing_matches_the_slide(m):
    source = (EPISODE / "search.py").read_text(encoding="utf-8")
    listing = source.split(MARKER, 1)[1].split(END_OF_LISTING, 1)[0].strip("\n")
    assert listing == LISTING
    body = listing.split("def search", 1)[1].splitlines()
    assert len(body) <= 16


def test_search_filters_before_ranking(m):
    entries = [m.library.entry(f"A{i}", f"text {i}") for i in range(6)]
    entries.insert(0, m.library.entry("N0", "secret", access="internal"))
    vectors = np.array([[1.0, 0.0]] + [[1.0, 0.1 * (i + 1)] for i in range(6)])
    index = m.library.make_index(entries, vectors)
    query = np.array([1.0, 0.0])
    everything, _ = m.search.search(query, index, m.search.everything, 5)
    assert everything[0]["article_id"] == "N0"
    public, scores = m.search.search(query, index, m.search.public, 5)
    assert len(public) == 5 and all(e["access"] == "public" for e in public)
    assert list(scores) == sorted(scores, reverse=True)


# Library checks -----------------------------------------------------------------------------

ARTICLE = "Brio kettle\n\nDescale it every 12 weeks. Use the 250 ml measure."


def test_value_must_be_unique_and_inside_the_copied_sentence(m):
    texts = [ARTICLE, "Other article, 3 weeks."]
    ok = m.library.value_problem
    assert ok(texts, ARTICLE, "Descale it every 12 weeks.", "12 weeks") is None
    assert "not copied" in ok(texts, ARTICLE, "Descale every 12 weeks.", "12 weeks")
    assert "not inside" in ok(texts, ARTICLE, "Descale it every 12 weeks.", "250 ml")
    assert "2 times" in ok(
        [*texts, "Wait 12 weeks."], ARTICLE, "Descale it every 12 weeks.", "12 weeks"
    )


def test_replacement_must_be_new_and_not_overlap(m):
    texts = [ARTICLE]
    ok = m.library.replacement_problem
    assert ok(texts, "12 weeks", "16 weeks") is None
    assert "unchanged" in ok(texts, "12 weeks", "12 weeks")
    assert "contain" in ok(texts, "12 weeks", "112 weeks")
    assert "already" in ok(texts, "12 weeks", "250 ml")
    assert "one line" in ok(texts, "12 weeks", "16 weeks\nor 20")


def test_revision_is_the_one_value(m):
    revised = m.library.revise(ARTICLE, "Descale it every 12 weeks.", "12 weeks", "16 weeks")
    assert revised == ARTICLE.replace("12 weeks", "16 weeks")
    with pytest.raises(AssertionError):
        m.library.assert_minimal(ARTICLE, revised.replace("Use", "Try"), "12 weeks", "16 weeks")
    with pytest.raises(AssertionError):
        m.library.assert_minimal(ARTICLE, ARTICLE, "12 weeks", "16 weeks")


def test_question_may_not_give_the_value(m):
    assert m.library.question_problem("How often should I descale?", "12 weeks", "16 weeks") is None
    assert "12 weeks" in m.library.question_problem("Is it 12 WEEKS?", "12 weeks", "16 weeks")
    assert "empty" in m.library.question_problem(" ", "a", "b")


def test_absent_product_must_be_named_and_absent(m):
    ok = m.library.product_problem
    assert ok([ARTICLE], "Does the Pelham air fryer beep?", "Pelham air fryer") is None
    assert "does not name" in ok([ARTICLE], "Does it beep?", "Pelham air fryer")
    assert "appears" in ok([ARTICLE], "Is the brio kettle loud?", "Brio kettle")


def test_note_checks_length_and_copying(m, config):
    texts = [ARTICLE * 3]
    assert "tokens" in m.library.note_problem("short", texts, 10, config)
    assert "duplicates" in m.library.note_problem(texts[0], texts, 150, config)
    assert "copies" in m.library.note_problem("x " + ARTICLE * 2, texts, 150, config)
    assert m.library.note_problem("An internal note, nothing copied.", texts, 150, config) is None


def test_latest_flag_and_stale_hashes(m):
    entries = [
        m.library.entry("A1", "old", date="2025-03-01", version="old"),
        m.library.entry("A1", "new", date="2026-06-01", version="new"),
        m.library.entry("A2", "same", date="2025-03-01"),
    ]
    index = m.library.make_index(entries, np.eye(3))
    assert [e["latest"] for e in index["entries"]] == [False, True, True]
    assert m.library.stale_entries(index, {"A1": "new", "A2": "same"}) == ["A1:old"]


def test_answer_prompt_and_grading(m, config):
    passages = [{"text": "One.", "date": "2025-03-01"}, {"text": "Two.", "date": "2026-06-01"}]
    plain = m.library.answer_prompt(config, "Q?", passages)
    assert plain.startswith(config["prompts"]["answer"])
    assert plain.index("One.") < plain.index("Two.") and "Updated" not in plain
    assert "NOT_FOUND" not in plain
    dated = m.library.answer_prompt(config, "Q?", passages, dated=True, not_found=True)
    assert "Updated: 2026-06-01" in dated and config["prompts"]["not_found"] in dated
    grade = m.library.grade_value
    assert [
        grade(r, "12 weeks", "16 weeks")
        for r in ("12 weeks", "16 weeks", "12 weeks or 16 weeks", "no idea")
    ] == ["old", "new", "both", "neither"]
    assert m.library.is_not_found(" NOT_FOUND\n") and not m.library.is_not_found("NOT_FOUND.")
    assert m.library.judge_verdict("Assert.") == "assert"
    assert m.library.judge_verdict("maybe") == "unclear"


# Measures -----------------------------------------------------------------------------------


def test_best_cutoff(m):
    apart = m.measure.best_cutoff([0.8, 0.9], [0.3, 0.4])
    assert apart["misclassified"] == 0 and 0.4 < apart["cutoff"] < 0.8
    mixed = m.measure.best_cutoff([0.5, 0.9, 0.3], [0.6, 0.2])
    assert mixed["misclassified"] == 1 and mixed["accuracy"] == pytest.approx(0.8)
    assert mixed["answerable_range"] == [0.3, 0.9]


def _counts(m, **hits):
    return {name: m.measure.count(h, 40) for name, h in hits.items()}


def test_claims_a_at_the_pass_marks(m, config):
    marks = config["pass_marks"]
    summary = {
        "fresh": _counts(m, recall=38, current=36, old=0),
        "stale": _counts(m, recall=36, current=4, old=30),
        "hash": {"stale_total": 40, "flagged_stale": 40, "flagged_other": 0},
    }
    claims = m.measure.claims_a(summary, marks)
    assert all(c["verdict"] == "Held" for c in claims.values())
    summary["stale"] = _counts(m, recall=35, current=5, old=30)
    summary["hash"]["flagged_other"] = 1
    claims = m.measure.claims_a(summary, marks)
    assert (
        claims["A1"]["verdict"] == claims["A2"]["verdict"] == claims["A3"]["verdict"] == ("Failed")
    )


def test_claims_d(m, config):
    summary = {
        "D-none": {"leaks": m.measure.count(40, 120), "recall": m.measure.count(90, 120)},
        "D-post": {"leaks": m.measure.count(0, 120), "recall": m.measure.count(90, 120)},
        "D-pre": {"leaks": m.measure.count(0, 120), "recall": m.measure.count(95, 120)},
    }
    claims = m.measure.claims_d(summary, config["pass_marks"], 95)
    assert [c["verdict"] for c in claims.values()] == ["Held"] * 3
    summary["D-pre"]["recall"] = m.measure.count(94, 120)
    claims = m.measure.claims_d(summary, config["pass_marks"], 95)
    assert claims["D2"]["verdict"] == "Failed" and claims["D3"]["verdict"] == "Failed"


# The cache ----------------------------------------------------------------------------------


class FakeResponses:
    def __init__(self, reply):
        self.reply, self.sent = reply, []

    def create(self, **request):
        self.sent.append(request)
        text = self.reply(request["input"])
        usage = SimpleNamespace(
            input_tokens=len(request["input"].split()),
            output_tokens=len(text.split()) + 5,
            output_tokens_details=SimpleNamespace(reasoning_tokens=5),
        )
        return SimpleNamespace(
            output_text=text, status="completed", model=request["model"], usage=usage
        )


def test_chat_caches_by_model_and_request(m, tmp_path):
    fake = FakeResponses(lambda prompt: "ok")
    client = SimpleNamespace(responses=fake)
    chat = m.chat.Chat(client, "model-a", 100, tmp_path / "c.sqlite")
    assert chat("hello", "answering") == chat("hello", "answering") == "ok"
    assert len(fake.sent) == 1 and chat.usage["answering"]["calls"] == 2
    other = m.chat.Chat(client, "model-b", 100, tmp_path / "c.sqlite")
    other("hello", "answering")
    assert len(fake.sent) == 2
    with pytest.raises(ValueError):
        chat("hello", "lunch")


def test_parse_json_and_retry(m):
    assert m.chat.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert m.chat.parse_json("no json") is None
    assert m.chat.with_retry("P", [], "{problem}") == "P"
    retried = m.chat.with_retry("P", [{"reply": "R", "problem": "bad."}], "Fix: {problem}")
    assert retried == "P\n\nYour last reply: R\nFix: bad."


# End to end on a small invented library -----------------------------------------------------

WORDS = re.compile(r"[a-z0-9]+")
N_ARTICLES = 24


def fake_embed(texts):
    """Hashed bag of words: texts sharing words point the same way."""
    out = np.full((len(texts), 1024), 0.01)
    for row, text in enumerate(texts):
        for word in WORDS.findall(text.lower()):
            out[row, int(hashlib.md5(word.encode()).hexdigest(), 16) % 1024] += 1
    return out


def fake_reply(prompt: str) -> str:
    """Rule-based stand-in for the chat model, keyed on each prompt's wording."""
    first = prompt.split("\n")[0]
    article = prompt.split("Article:\n", 1)[-1]
    if first.startswith("Below is a support article. Choose one sentence"):
        found = re.search(r"The Widget\d+ needs (\d+ minutes) to warm up\.", article)
        return f'{{"sentence": "{found.group(0)}", "value": "{found.group(1)}"}}'
    if first.startswith("Below is a sentence"):
        return f"{int(re.search(r'Value: (\d+)', prompt).group(1)) + 50} minutes"
    if first.startswith("Below is a support article. Write one question a customer might ask that"):
        return f"How long does {re.search(r'Widget\d+', article).group(0)} take to warm up?"
    if first.startswith("Halvard Home is an invented"):
        category = re.search(r"Invent a Halvard Home (.+?) with", prompt.replace("\n", " "))
        name = f"Zorblax {category.group(1)}"
        return f'{{"question": "Is the {name} safe?", "product": "{name}"}}'
    if first.startswith("Below is a support article. Write one question a customer might ask on"):
        return f"What voltage does {re.search(r'Widget\d+', article).group(0)} use?"
    if first.startswith("Does any passage"):
        return "no"
    if first.startswith("You write internal notes"):
        widget = re.search(r"Widget\d+", article).group(0)
        return f"Internal: {widget} service bulletin\n\n" + " ".join(
            f"step{n} torque" for n in range(60)
        )
    if first.startswith("Below is an internal service note"):
        return f"What is the {re.search(r'Widget\d+', prompt).group(0)} service bulletin torque?"
    if first.startswith("Below is a question and a reply"):
        return "decline" if "NOT_FOUND" in prompt or "know" in prompt else "assert"
    if first.startswith("Answer the customer"):
        question = prompt.rsplit("Question: ", 1)[1]
        if "NOT_FOUND" in prompt.split("\n")[1] and (
            "voltage" in question or "Zorblax" in question
        ):
            return "NOT_FOUND"
        found = re.search(r"(\d+ minutes)", prompt.split("Passage 1", 1)[1])
        return f"It takes {found.group(1)}." if found else "I do not know."
    raise AssertionError(f"Unexpected prompt: {first}")


@pytest.fixture(scope="module")
def small(m, config, tmp_path_factory):
    cfg = copy.deepcopy(config)
    cfg.update(
        values=6,
        absent_product=3,
        absent_detail=3,
        notes_per_type=2,
        judge_audit_rows=4,
        e3_vector_hits=6,
        note_tokens=[20, 400],
    )
    articles = [
        {
            "article_id": f"A{i:03d}",
            "text": f"Widget{i} warm up\n\nThe Widget{i} needs {10 + i} minutes to warm up. "
            f"Keep the widget{i} base dry.",
        }
        for i in range(N_ARTICLES)
    ]
    types = ("identifier", "paraphrase", "shared")
    questions = [
        {
            "type": types[i % 3],
            "article_id": f"A{i:03d}",
            "question": f"How do I keep the widget{i} base dry?",
        }
        for i in range(N_ARTICLES)
    ]
    e3 = {"articles": articles, "questions": questions, "products": ["Brio kettle"]}
    chat = m.chat.Chat(
        SimpleNamespace(responses=FakeResponses(fake_reply)),
        "fake",
        100,
        tmp_path_factory.mktemp("cache") / "chat.sqlite",
    )
    size = {"values": 6, "absent_product": 3, "absent_detail": 3, "notes": 6}
    data = m.quiet.build_data(cfg, chat, _Embed(), e3, size, tmp_path_factory.mktemp("data"))
    out = m.quiet.run(cfg, chat, _Embed(), e3, data, pilot=False)
    return SimpleNamespace(cfg=cfg, e3=e3, data=data, out=out, chat=chat)


class _Embed:
    inner = SimpleNamespace(model_returned=None)

    def count(self, text):
        return len(text.split())

    def __call__(self, texts):
        return fake_embed(texts)


def test_build_gives_checked_items(small):
    values, notes = small.data["values"], small.data["notes"]
    assert len(values) == 6 and len(small.data["unanswerable"]) == 6 and len(notes) == 6
    for v in values:
        assert v["old"] in v["sentence"] and v["new"] in v["revised"]
    assert len({n["article_id"] for n in notes}) == 6


def test_pipeline_reaches_every_claim_and_check(small):
    out = small.out
    assert set(out["claims"]) == {
        "A1",
        "A2",
        "A control",
        "A3",
        "B1",
        "B2",
        "B3",
        "B4",
        "C1",
        "C2",
        "C3",
        "D1",
        "D2",
        "D3",
    }
    checks = out["checks"]
    assert checks["1 same index twice"]["identical"] == len(small.e3["questions"])
    assert checks["4 and 5 values"] == {"unique": 6, "minimal": 6, "n": 6}
    assert checks["6 notes reachable"]["reachable"] == 6
    assert checks["7 judge audit"]["flagged"] == 4


def test_stale_index_and_hash_check(small):
    a = small.out["A"]["summary"]
    assert a["hash"] == {**a["hash"], "stale_total": 6, "flagged_stale": 6, "flagged_other": 0}
    assert a["fresh"]["current"]["hits"] == 6 and a["stale"]["old"]["hits"] == 6
    assert small.out["claims"]["A3"]["verdict"] == "Held"


def test_latest_filter_removes_the_old_version(small):
    rows = small.out["B"]["rows"]
    assert all(not tid.endswith(":old") for r in rows for tid in r["latest_top"])
    assert small.out["B"]["summary"]["B-latest"]["any_old"]["hits"] == 0


def test_scope_prefilter_never_leaks(small):
    d = small.out["D"]["summary"]
    assert d["D-pre"]["leaks"]["hits"] == 0 and d["D-post"]["leaks"]["hits"] == 0
    assert d["D-pre"]["fewer_than_k"] == 0
    assert d["D-post"]["mean_delivered"] <= d["D-pre"]["mean_delivered"]


def test_not_found_prompt_declines_on_unanswerable(small):
    c = small.out["C"]["summary"]
    assert c["P2"]["unanswerable_not_found"]["hits"] == 6
    assert c["P2"]["unanswerable_asserted_for_c3"]["hits"] == 0
    audit = small.out["audit"]
    assert all(row["prompt"] == "P1" for row in audit)


def test_rerun_sends_nothing(m, small):
    before = small.chat.sent
    m.quiet.run(small.cfg, small.chat, _Embed(), small.e3, small.data, pilot=False)
    assert small.chat.sent == before


# Pre-registration ---------------------------------------------------------------------------


def test_preregistration_states_the_config_pass_marks(config):
    text = (EPISODE / "PREREGISTRATION.md").read_text(encoding="utf-8")
    for value in config["pass_marks"].values():
        assert re.search(rf"\b{value}\b", text), value


def test_charts_render_from_a_summary(m, small, tmp_path):
    chart = load_sibling(EPISODE / "chart.py")
    size = {"values": 6, "absent_product": 3, "absent_detail": 3, "notes": 6}
    summ = m.quiet.summary(small.cfg, small.out, small.chat, _Embed(), size, pilot=True)
    written = chart.render(summ, tmp_path)
    names = sorted(p.name for p in written if p.suffix == ".svg")
    assert names == [f"{n}-slide.svg" for n in ("prompts", "scope", "scores", "stale", "versions")]


def test_clears_needs_intervals_apart(m):
    chart = load_sibling(EPISODE / "chart.py")
    low, high = m.measure.count(2, 40), m.measure.count(30, 40)
    assert chart.clears([low, high], 1) and chart.clears([low, high], 0)
    assert not chart.clears([m.measure.count(20, 40), m.measure.count(24, 40)], 1)
