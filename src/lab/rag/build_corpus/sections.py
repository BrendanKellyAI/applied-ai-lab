"""Section prompts and the checks every written section must pass.

The model must include each required sentence word for word, once; write no other number,
amount, duration or measurement, in figures or in words; name no product but its own; and
stay within the token bounds. A failed section is sent back with the reason.
"""

import re

from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.generate import Task
from lab.rag.build_corpus.outline import DocumentPlan, SectionPlan
from lab.rag.chunk import count_tokens

_UNITS = (
    r"days?|weeks?|months?|years?|hours?|minutes?|seconds?|miles?|metres?|centimetres?|"
    r"pounds?|per ?cent|percent|degrees?"
)
_NUMBER_WORDS = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
    r"fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundred|dozen|a few|several"
)
_SPELLED = re.compile(rf"\b(?:{_NUMBER_WORDS})(?:[- ]\w+)?[- ](?:{_UNITS})\b", re.IGNORECASE)
_FIGURES = re.compile(r"[0-9£%]")
_HEADING = re.compile(r"^\s*#", re.MULTILINE)

WORDS = {"intro": "120 to 200", "policy": "400 to 600", "internal": "300 to 450"}


def bounds(config: CorpusConfig, section: SectionPlan) -> tuple[int, int]:
    return {
        "intro": (100, 400),
        "policy": config.section_tokens,
        "internal": config.internal_section_tokens,
        "deleted": config.article_tokens,
    }[section.kind]


def section_task(config: CorpusConfig, document: DocumentPlan, section: SectionPlan) -> Task:
    listed = "\n".join(f'{n}. "{block}"' for n, block in enumerate(section.blocks, start=1))
    path = " > ".join(p for p in (document.title, section.group, section.heading) if p)
    if section.kind == "intro":
        prompt = config.prompt("intro", title=document.title, words=WORDS["intro"])
    elif section.kind == "internal":
        prompt = config.prompt(
            "internal",
            title=document.title,
            path=path,
            entity=section.entity,
            words=WORDS["internal"],
            sentences=listed,
        )
    elif section.kind == "deleted":
        prompt = config.prompt(
            "deleted", accessory=section.accessory, entity=section.entity, sentences=listed
        )
    else:
        together = (
            "Where a numbered item has two sentences, keep them together, in that order, with "
            "a single space between them.\n"
            if any(_sentences(b) > 1 for b in section.blocks)
            else ""
        )
        products = (
            f"other than the {section.entity}" if section.entity in config.products else "at all"
        )
        prompt = config.prompt(
            "section",
            title=document.title,
            path=path,
            words=WORDS["policy"],
            sentences=listed,
            together=together,
            products=products,
        )
    return Task(id=section.key, prompt=prompt)


def _sentences(text: str) -> int:
    return len(re.findall(r"[.!?](?:\s|$)", text))


def check_section(config: CorpusConfig, section: SectionPlan, text: str) -> str | None:
    """The first rule the text breaks, worded for the model, or None if it passes."""
    text = text.strip()
    if not text:
        return "The reply was empty."
    if section.kind != "deleted" and _HEADING.search(text):
        return "Do not write any heading or title; write the text under the heading only."
    remainder = text
    for block in section.blocks:
        count = text.count(block)
        if count == 0:
            return f'It must include this, word for word: "{block}"'
        if count > 1:
            return f'It includes "{block}" more than once; include it once.'
        remainder = remainder.replace(block, " ")
    figure = _FIGURES.search(remainder)
    if figure:
        return (
            f'It contains another number or amount near "{_around(remainder, figure.start())}". '
            "Remove every number except those in the given sentences."
        )
    spelled = _SPELLED.search(remainder)
    if spelled:
        return (
            f'It contains another amount in words: "{spelled.group(0)}". Remove every amount '
            "except those in the given sentences."
        )
    named = _other_product(config, section, remainder)
    if named:
        allowed = f"the {section.entity}" if section.entity in config.products else "no product"
        return f"It names the {named}; it may name {allowed} only."
    low, high = bounds(config, section)
    tokens = count_tokens(text)
    if not low <= tokens <= high:
        words = WORDS.get(section.kind, "90 to 130")
        return f"It is {tokens} tokens long; it must be {low} to {high}. Aim for {words} words."
    return None


def _other_product(config: CorpusConfig, section: SectionPlan, text: str) -> str | None:
    for product in config.products:
        if product == section.entity:
            continue
        brand = product.split()[0]
        if re.search(rf"\b{re.escape(brand)}\b", text):
            return product
    return None


def _around(text: str, index: int, width: int = 30) -> str:
    return " ".join(text[max(0, index - width) : index + width].split())
