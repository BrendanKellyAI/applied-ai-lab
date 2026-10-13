"""The 300 v1 S2 E3 articles and their 120 questions, kept as they were.

The articles are copied byte for byte. Their questions get span labels: for identifier
questions, code finds the sentence holding the code; for the rest, the model quotes the
answering sentence and code accepts it only if it is copied exactly from the article.
"""

import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from lab.rag.build_corpus.catalogue import CorpusConfig
from lab.rag.build_corpus.generate import Task

# v1 type names, as the season's item types.
TYPES = {"identifier": "identifier", "paraphrase": "paraphrase", "shared": "shared"}
CODES = {"identifier": "IDENT", "paraphrase": "PARA", "shared": "SHARED"}
MIN_QUOTE_WORDS = 4


class Article(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    article_id: str
    product: str
    identifier: str | None = None
    role: str | None = None
    group: int | None = None
    text: str

    @property
    def title(self) -> str:
        return self.text.split("\n", 1)[0].strip()


class Question(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    type: str
    article_id: str
    question: str


class V1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    articles: tuple[Article, ...]
    questions: tuple[Question, ...]

    def article(self, article_id: str) -> Article:
        return next(a for a in self.articles if a.article_id == article_id)

    def item_id(self, question: Question) -> str:
        same = [q for q in self.questions if q.type == question.type]
        return f"{CODES[question.type]}-{same.index(question):03d}"


def load_v1(folder: Path) -> V1:
    corpus = json.loads((folder / "corpus.json").read_text(encoding="utf-8"))
    questions = json.loads((folder / "questions.json").read_text(encoding="utf-8"))
    return V1(articles=corpus["articles"], questions=questions["questions"])


def sentence_around(text: str, index: int) -> tuple[int, int]:
    """Character range of the sentence holding `index`: from after the previous full stop or
    line break to the next one, inclusive of its own full stop."""
    starts = [m.end() for m in re.finditer(r"(?<=[.!?])\s+|\n", text[:index])]
    start = starts[-1] if starts else 0
    end_match = re.search(r"[.!?](?=\s|$)|\n", text[index:])
    end = index + (end_match.end() if end_match else len(text) - index)
    if text[end - 1 : end] == "\n":
        end -= 1
    return start, end


def identifier_span(article: Article) -> tuple[int, int]:
    return sentence_around(article.text, article.text.index(article.identifier))


def lookalikes(v1: V1, article: Article) -> list[Article]:
    return [
        a
        for a in v1.articles
        if a.group == article.group and a.role == "lookalike" and a.identifier
    ]


def quote_tasks(config: CorpusConfig, v1: V1) -> list[Task]:
    return [
        Task(
            id=v1.item_id(q),
            prompt=config.prompt(
                "quote", article=v1.article(q.article_id).text, question=q.question
            ),
        )
        for q in v1.questions
        if q.type != "identifier"
    ]


def check_quote(article: Article, text: str) -> str | None:
    quote = clean_quote(text)
    if len(quote.split()) < MIN_QUOTE_WORDS:
        return "Reply with the whole sentence that answers the question."
    count = article.text.count(quote)
    if count == 0:
        return "That sentence is not copied exactly from the article. Copy it word for word."
    if count > 1:
        return "That text appears more than once; copy the whole sentence."
    if "\n" in quote:
        return "Copy one sentence only."
    return None


def clean_quote(text: str) -> str:
    return text.strip().strip('"').strip("“”").strip()
