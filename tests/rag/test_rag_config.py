import pytest
import yaml

from lab.config import ConfigError
from lab.rag.chunk import FixedChunker, StructureChunker
from lab.rag.config import config_id, load_episode, load_pipeline
from tests.rag.mini_corpus import REFERENCE


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture
def reference(tmp_path):
    return _write(tmp_path / "season2" / "reference.yaml", REFERENCE)


def _episode(tmp_path, conditions, **extra):
    data = {
        "episode": "s2-e4-chunking",
        "base": "../../season2/reference.yaml",
        "library": "../../datasets/halvard",
        "conditions": conditions,
        **extra,
    }
    return _write(tmp_path / "episodes" / "s2-e4-chunking" / "config.yaml", data)


def test_reference_loads_with_typed_stages(reference):
    pipeline = load_pipeline(reference)

    assert pipeline.chunk == FixedChunker(size=256)
    assert pipeline.answer.reasoning == "low"
    assert pipeline.judge.reasoning == "off"


def test_yaml_off_is_read_as_the_word_off(tmp_path):
    raw = yaml.safe_dump(REFERENCE).replace("reasoning: 'off'", "reasoning: off")
    path = tmp_path / "reference.yaml"
    path.write_text(raw, encoding="utf-8")

    assert load_pipeline(path).judge.reasoning == "off"


def test_config_id_is_stable_and_changes_with_any_setting(reference):
    pipeline = load_pipeline(reference)
    changed = pipeline.model_copy(update={"prompt": pipeline.prompt.model_copy(update={"k": 3})})

    assert config_id(pipeline) == config_id(load_pipeline(reference))
    assert config_id(pipeline) != config_id(changed)
    assert len(config_id(pipeline)) == 12


def test_conditions_override_one_stage(tmp_path, reference):
    path = _episode(
        tmp_path,
        [
            {"name": "reference"},
            {"name": "overlap-64", "changes": {"chunk": {"overlap": 64}}},
            {
                "name": "structure",
                "changes": {"chunk": {"kind": "structure", "max_tokens": 512}},
                "measure": "search",
            },
        ],
    )
    episode = load_episode(path)
    by_name = {c.name: c for c in episode.conditions}

    assert by_name["reference"].changed == ()
    assert by_name["overlap-64"].pipeline.chunk == FixedChunker(size=256, overlap=64)
    assert by_name["overlap-64"].changed == ("chunk",)
    # A change of kind replaces the block rather than merging into it.
    assert by_name["structure"].pipeline.chunk == StructureChunker(max_tokens=512)
    assert by_name["structure"].measure == "search"
    assert episode.library == (tmp_path / "datasets" / "halvard").resolve()
    assert episode.base_id == config_id(load_pipeline(reference))


def test_a_condition_changing_two_stages_is_refused(tmp_path, reference):
    path = _episode(
        tmp_path,
        [{"name": "two", "changes": {"chunk": {"size": 128}, "prompt": {"k": 3}}}],
    )

    with pytest.raises(ConfigError, match="two.*chunk.*prompt"):
        load_episode(path)


def test_two_stages_allowed_with_a_stated_reason(tmp_path, reference):
    path = _episode(
        tmp_path,
        [
            {
                "name": "long-context",
                "changes": {"chunk": {"kind": "whole"}, "prompt": {"k": 50}},
                "changes_more_than_one_stage": "Sends the whole pack instead of retrieving.",
            }
        ],
    )

    assert load_episode(path).conditions[0].changed == ("chunk", "prompt")


def test_a_change_to_an_unknown_stage_is_refused(tmp_path, reference):
    path = _episode(tmp_path, [{"name": "x", "changes": {"chunker": {"size": 1}}}])

    with pytest.raises(ConfigError, match="chunker"):
        load_episode(path)


def test_an_invalid_setting_is_refused(tmp_path, reference):
    path = _episode(tmp_path, [{"name": "x", "changes": {"chunk": {"overlap": 300}}}])

    with pytest.raises(ConfigError, match="overlap"):
        load_episode(path)


def test_condition_names_must_be_unique(tmp_path, reference):
    path = _episode(tmp_path, [{"name": "a"}, {"name": "a"}])

    with pytest.raises(ConfigError, match="unique"):
        load_episode(path)


def test_missing_file_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_pipeline(tmp_path / "nope.yaml")
