"""The rule for whether a reply is in French, fixed before any reply was seen.

A reply is counted as French when it contains at least three words from a fixed list of common
French words and more of them than words from a fixed list of common English ones. Both lists
are function words: the small words every sentence in the language leans on, which a short reply
cannot avoid. Words that are ordinary in both languages ("on", "plus", "son", "par", "a") are on
neither list.

The rule is applied mechanically, and it answers only "is this reply written in French", not
"is the French good". It uses no library, so it gives the same answer on every machine. An empty
reply, which is what a reply cut off by hidden reasoning looks like, is not French.
"""

import re

MINIMUM_FRENCH_WORDS = 3
# Stored in the results, so the rule applied is on record beside the replies it was applied to.
RULE = (
    "French if the reply has at least 3 words from a fixed list of common French function "
    "words and more of them than words from a fixed list of common English ones; an empty "
    "reply is not French"
)

FRENCH_WORDS = frozenset(
    {
        "le", "la", "les", "un", "une", "des", "du", "de", "et", "est", "sont", "dans", "pour",
        "que", "qui", "pas", "au", "aux", "ce", "cette", "ces", "il", "elle", "ils", "elles",
        "nous", "vous", "je", "tu", "sur", "avec", "mais", "ou", "où", "ses", "être", "très",
        "comme", "donc", "peut", "quand", "ont", "ne", "se", "en", "votre", "vos", "notre",
        "nos", "leur", "leurs", "mes", "tes",
    }
)
ENGLISH_WORDS = frozenset(
    {
        "the", "is", "are", "and", "of", "to", "in", "that", "it", "for", "with", "as", "this",
        "was", "be", "by", "or", "an", "at", "from", "which", "can", "not", "but", "you", "your",
        "its", "have", "has", "will", "they", "their", "them", "these", "those", "there", "what",
        "when", "who", "how",
    }
)

# A word is a run of letters, accents included. An apostrophe splits one, so that "l'eau" is
# "l" and "eau" and "it's" is "it" and "s".
WORD = re.compile(r"[^\W\d_]+")


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def french_hits(text: str) -> int:
    return sum(word in FRENCH_WORDS for word in words(text))


def english_hits(text: str) -> int:
    return sum(word in ENGLISH_WORDS for word in words(text))


def is_french(text: str) -> bool:
    french = french_hits(text)
    return french >= MINIMUM_FRENCH_WORDS and french > english_hits(text)
