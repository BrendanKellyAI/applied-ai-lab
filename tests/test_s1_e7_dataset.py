"""The S1 E7 dataset builder (specification sections 6.2, 6.3, 6.4).

The builder never reaches the network here: a fake fetcher supplies book text, so these tests
check the parts the experiment depends on, which are determinism, lengths, and positions.
"""

import hashlib
import json
from pathlib import Path

import pytest

from lab.config import load_config
from lab.experiments import load_plan_function

FIELD_NOTE = Path("field-notes/s1-e7-lost-in-the-middle")
CONFIG_PATH = FIELD_NOTE / "config.yaml"

# Enough sentences to trim to any test length, with clear sentence boundaries to snap to.
SENTENCE = "The lamp on the quay burned low and the tide drew out past the harbour wall. "
FILLER = SENTENCE * 4000


def _filler_of(document, fact) -> str:
    """The document without its fact, ignoring the whitespace the join leaves behind."""
    return " ".join(document.text.replace(fact.sentence, "").split())


@pytest.fixture(scope="module")
def module():
    """The field note's build_dataset module."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "s1_e7_build_dataset", FIELD_NOTE / "build_dataset.py"
    )
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG_PATH)


@pytest.fixture
def fake_fetch(module):
    """Book text keyed by book id, with the checksum the config expects."""

    def fetch(url: str, _timeout: float = 0.0) -> bytes:
        body = f"*** START OF THE PROJECT GUTENBERG EBOOK 1 ***\n{FILLER}\n"
        body += "*** END OF THE PROJECT GUTENBERG EBOOK 1 ***\n"
        return body.encode("utf-8")

    return fetch


@pytest.fixture
def built(module, config, fake_fetch, tmp_path, monkeypatch):
    """A dataset built at small lengths, so tests stay fast."""
    monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
    monkeypatch.setattr(module, "verify_checksum", lambda book, raw: None)
    return module.build_dataset(
        config,
        tmp_path,
        lengths=(500, 1000),
        cache_dir=tmp_path / ".cache",
    )


class TestFacts:
    def test_facts_come_from_the_seed(self, module):
        assert module.make_facts(20260917, 6) == module.make_facts(20260917, 6)

    def test_a_different_seed_gives_different_facts(self, module):
        assert module.make_facts(1, 6) != module.make_facts(2, 6)

    def test_identifiers_and_values_are_unique(self, module):
        facts = module.make_facts(20260917, 6)

        assert len({fact.identifier for fact in facts}) == 6
        assert len({fact.value for fact in facts}) == 6

    def test_sentence_and_question_match_the_specification(self, module):
        fact = module.make_facts(20260917, 1)[0]

        assert fact.sentence == (
            f"The maintenance code for turbine {fact.identifier} is {fact.value}."
        )
        assert fact.question == (f"What is the maintenance code for turbine {fact.identifier}?")

    def test_values_are_four_digit_numbers(self, module):
        for fact in module.make_facts(20260917, 6):
            assert fact.value.isdigit()
            assert len(fact.value) == 4


class TestStripGutenberg:
    def test_removes_the_header_and_footer_markers(self, module):
        text = (
            "*** START OF THE PROJECT GUTENBERG EBOOK 1342 ***\nBody text here.\n"
            "*** END OF THE PROJECT GUTENBERG EBOOK 1342 ***\nLicence terms.\n"
        )

        assert module.strip_gutenberg(text).strip() == "Body text here."

    def test_refuses_text_without_markers(self, module):
        with pytest.raises(module.DatasetError, match="marker"):
            module.strip_gutenberg("No markers at all.")


class TestChecksum:
    def test_a_mismatch_fails_with_a_clear_message(self, module, config):
        book = module.Book.from_config(config.parameters["filler_books"][0])

        with pytest.raises(module.DatasetError, match="checksum"):
            module.verify_checksum(book, b"not the pinned text")

    def test_a_match_passes(self, module, config):
        book = module.Book.from_config(config.parameters["filler_books"][0])
        raw = b"some bytes"
        book = book.__class__(
            id=book.id,
            title=book.title,
            author=book.author,
            sha256=hashlib.sha256(raw).hexdigest(),
        )

        module.verify_checksum(book, raw)


class TestMirrorUrl:
    def test_splits_the_identifier_into_folders(self, module):
        assert module.mirror_url(1342).endswith("/1/3/4/1342/1342-0.txt")

    def test_handles_a_two_digit_identifier(self, module):
        assert module.mirror_url(84).endswith("/8/84/84-0.txt")

    def test_uses_a_mirror_not_the_main_site(self, module):
        # Project Gutenberg's robot policy: the main site is for human users only.
        assert "www.gutenberg.org" not in module.mirror_url(1342)


class TestBuiltDocuments:
    def test_covers_every_fact_length_and_position(self, built, config):
        expected = 6 * 2 * len(config.parameters["positions_percent"])

        assert len(built.documents) == expected

    def test_lengths_are_within_five_percent_of_target(self, built):
        for document in built.documents:
            target = document.context_length_tokens
            assert abs(document.actual_tokens - target) <= target * 0.05, document

    def test_positions_are_within_two_percent_of_target(self, built):
        for document in built.documents:
            assert abs(document.actual_position_percent - document.position_percent) <= 2.0

    def test_each_document_contains_its_fact_exactly_once(self, built, module):
        for document in built.documents:
            fact = built.facts[document.fact_index]
            assert document.text.count(fact.sentence) == 1

    def test_no_document_contains_another_fact(self, built):
        for document in built.documents:
            others = [f for i, f in enumerate(built.facts) if i != document.fact_index]
            assert all(other.value not in document.text for other in others)

    def test_the_fact_sits_at_a_sentence_boundary(self, built):
        for document in built.documents:
            fact = built.facts[document.fact_index]
            before = document.text.split(fact.sentence)[0]
            assert before == "" or before.rstrip().endswith((".", "!", "?", '"', "”"))

    def test_the_same_filler_carries_every_position(self, built):
        """Paired design: only the fact's position changes within a fact and length."""
        for fact_index in range(6):
            for length in (500, 1000):
                fillers = {
                    _filler_of(d, built.facts[fact_index])
                    for d in built.documents
                    if d.fact_index == fact_index and d.context_length_tokens == length
                }
                assert len(fillers) == 1

    def test_shorter_lengths_are_prefixes_of_longer_ones(self, built):
        """Shared prompt prefixes, which is also why provider caching cannot be ruled out."""
        for fact_index in range(6):
            short, long = (
                next(
                    d
                    for d in built.documents
                    if d.fact_index == fact_index
                    and d.context_length_tokens == length
                    and d.position_percent == 100
                )
                for length in (500, 1000)
            )
            filler_short = _filler_of(short, built.facts[fact_index])
            filler_long = _filler_of(long, built.facts[fact_index])
            assert filler_long.startswith(filler_short[:200])

    def test_position_zero_puts_the_fact_first(self, built):
        first = next(d for d in built.documents if d.position_percent == 0)

        assert first.text.startswith(built.facts[first.fact_index].sentence)

    def test_position_one_hundred_puts_the_fact_last(self, built):
        last = next(d for d in built.documents if d.position_percent == 100)

        assert last.text.rstrip().endswith(built.facts[last.fact_index].sentence)


class TestDeterminism:
    def test_the_same_seed_gives_a_byte_identical_dataset(
        self, module, config, fake_fetch, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
        monkeypatch.setattr(module, "verify_checksum", lambda book, raw: None)
        monkeypatch.setattr(module, "GUTENBERG_CACHE", tmp_path / ".cache")
        digests = []
        for run in ("first", "second"):
            folder = tmp_path / run
            module.build_dataset(config, folder, lengths=(500,), cache_dir=tmp_path / ".cache")
            written = (folder / module.DATASET_DIR / module.DOCUMENTS_FILE).read_bytes()
            digests.append(hashlib.sha256(written).hexdigest())

        assert digests[0] == digests[1]

    def test_the_manifest_records_sources_and_the_seed(
        self, module, config, fake_fetch, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
        monkeypatch.setattr(module, "verify_checksum", lambda book, raw: None)
        monkeypatch.setattr(module, "GUTENBERG_CACHE", tmp_path / ".cache")
        module.build_dataset(config, tmp_path, lengths=(500,), cache_dir=tmp_path / ".cache")

        manifest = json.loads(
            (tmp_path / module.DATASET_DIR / module.MANIFEST_FILE).read_text(encoding="utf-8")
        )

        assert manifest["seed"] == config.seed
        assert len(manifest["books"]) == 6
        assert manifest["books"][0]["licence"].startswith("Public domain")


class TestPlanCalls:
    def test_plans_the_full_grid(self, module, config, fake_fetch, tmp_path, monkeypatch):
        monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
        monkeypatch.setattr(module, "verify_checksum", lambda book, raw: None)
        monkeypatch.setattr(module, "CONTEXT_LENGTH_OVERRIDE", (500,))
        monkeypatch.setattr(module, "GUTENBERG_CACHE", tmp_path / ".cache")

        calls = module.plan_calls(config, tmp_path)

        # 3 models x 1 length x 5 positions x 6 facts
        assert len(calls) == 90
        assert len({call.call_id for call in calls}) == 90

    def test_every_call_carries_the_cell_the_pilot_and_analysis_need(
        self, module, config, fake_fetch, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
        monkeypatch.setattr(module, "verify_checksum", lambda book, raw: None)
        monkeypatch.setattr(module, "CONTEXT_LENGTH_OVERRIDE", (500,))
        monkeypatch.setattr(module, "GUTENBERG_CACHE", tmp_path / ".cache")

        call = module.plan_calls(config, tmp_path)[0]

        assert set(call.cell) == {"context_length_tokens", "position_percent", "fact_index"}
        assert call.mode == "standard"

    def test_the_prompt_follows_the_specification(
        self, module, config, fake_fetch, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
        monkeypatch.setattr(module, "verify_checksum", lambda book, raw: None)
        monkeypatch.setattr(module, "CONTEXT_LENGTH_OVERRIDE", (500,))
        monkeypatch.setattr(module, "GUTENBERG_CACHE", tmp_path / ".cache")

        call = module.plan_calls(config, tmp_path)[0]

        assert call.request.system == (
            "Answer using only the document provided. Reply with the value only."
        )
        assert call.request.prompt.startswith("<document>\n")
        assert "</document>\n\nQuestion: What is the maintenance code for turbine" in (
            call.request.prompt
        )

    def test_all_three_models_see_the_same_document(
        self, module, config, fake_fetch, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
        monkeypatch.setattr(module, "verify_checksum", lambda book, raw: None)
        monkeypatch.setattr(module, "CONTEXT_LENGTH_OVERRIDE", (500,))
        monkeypatch.setattr(module, "GUTENBERG_CACHE", tmp_path / ".cache")

        calls = module.plan_calls(config, tmp_path)
        same_cell = [
            call
            for call in calls
            if call.cell == {"context_length_tokens": 500, "position_percent": 50, "fact_index": 0}
        ]

        assert len(same_cell) == 3
        assert len({call.request.prompt for call in same_cell}) == 1

    def test_reuses_a_dataset_already_built(
        self, module, config, fake_fetch, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
        monkeypatch.setattr(module, "verify_checksum", lambda book, raw: None)
        monkeypatch.setattr(module, "CONTEXT_LENGTH_OVERRIDE", (500,))
        monkeypatch.setattr(module, "GUTENBERG_CACHE", tmp_path / ".cache")
        module.plan_calls(config, tmp_path)

        def refuse(*args, **kwargs):
            raise AssertionError("the dataset should not be built twice")

        monkeypatch.setattr(module, "fetch_bytes", refuse)

        assert len(module.plan_calls(config, tmp_path)) == 90


class TestSentenceBoundaries:
    """A fact inserted after an abbreviation would split a name, as in "Mrs. <fact> Bennet"."""

    def test_a_full_stop_between_sentences_is_a_boundary(self, module):
        text = "She left the room. He stayed behind. "

        assert module.sentence_boundaries(text) == [19, 37]

    def test_a_title_is_not_a_boundary(self, module):
        assert module.sentence_boundaries("Mrs. Bennet was prevented. ") == [27]

    def test_every_listed_abbreviation_is_rejected(self, module):
        for abbreviation in ("Mr.", "Dr.", "Prof.", "St.", "Capt.", "Col.", "No.", "etc."):
            assert module.sentence_boundaries(f"{abbreviation} Smith went home. ") == [
                len(f"{abbreviation} Smith went home. ")
            ], abbreviation

    def test_an_initial_is_not_a_boundary(self, module):
        assert module.sentence_boundaries("J. Smith arrived late. ") == [23]

    def test_question_and_exclamation_marks_are_boundaries(self, module):
        text = "Who is there? Nobody! "

        assert module.sentence_boundaries(text) == [14, 22]

    def test_a_closing_quote_is_part_of_the_boundary(self, module):
        text = "He said “good evening.” The door closed. "

        assert text[: module.sentence_boundaries(text)[0]].endswith("” ")

    def test_a_built_document_never_splits_an_abbreviation(self, built, module):
        for document in built.documents:
            fact = built.facts[document.fact_index]
            before = document.text.split(fact.sentence)[0].rstrip()
            if not before:
                continue
            found = module.WORD_BEFORE_STOP.search(before + " ")
            if found is not None:
                word = found.group(1).lower()
                assert word not in module.ABBREVIATIONS, document
                assert len(word) > 1, document


class TestCacheLocation:
    def test_downloads_are_cached_outside_the_dataset(self, module):
        assert module.GUTENBERG_CACHE.parts[0] == ".cache"

    def test_the_cache_folder_is_used_when_none_is_given(
        self, module, config, fake_fetch, tmp_path, monkeypatch
    ):
        """Guards the repo's own cache: a build with no cache_dir must use GUTENBERG_CACHE."""
        monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
        monkeypatch.setattr(module, "verify_checksum", lambda book, raw: None)
        monkeypatch.setattr(module, "GUTENBERG_CACHE", tmp_path / "books")

        module.build_dataset(config, tmp_path, lengths=(500,))

        assert (tmp_path / "books" / "1342-0.txt").exists()


class TestDatasetSources:
    def test_lists_every_book_with_its_licence_and_checksum(self, module, config, tmp_path):
        sources = module.dataset_sources(config, tmp_path)

        assert len(sources) == 6
        assert all(source.licence.startswith("Public domain") for source in sources)
        assert all(source.checksum for source in sources)


class TestHarnessContract:
    def test_the_harness_can_load_plan_calls(self):
        assert callable(load_plan_function(CONFIG_PATH))
