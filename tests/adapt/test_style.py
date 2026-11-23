"""The house style checks pass a reply that follows the guide and catch each rule broken."""

import pytest

from lab.adapt.style import (
    CHECKS,
    NOT_FOUND,
    RULES,
    Source,
    american_words,
    body_of,
    check_reply,
)

POLICY = Source(kind="policy", name="Warranty", section="Brio kettle: Cover period")
ARTICLE = Source(kind="article", name="Resetting your Ashby tumble dryer")
MISSING = Source(kind="not_found", name="")

GOOD = (
    "Thank you for getting in touch.\n\n"
    'Our Warranty policy, section "Brio kettle: Cover period", says the kettle is covered for 24 '
    "months from the date of delivery. Cover starts on the day it is delivered, not the day it "
    "was ordered, so please keep your delivery note somewhere safe in case you need it.\n\n"
    "Kind regards,\nThe Halvard Home team"
)


def test_a_reply_that_follows_the_guide_passes_every_check():
    report = check_reply(GOOD, POLICY)
    assert report.all_pass, report.failures()
    assert report.failures() == ()
    assert 40 <= report.words <= 120
    assert report.mean_sentence_words > 0


@pytest.mark.parametrize(
    ("reply", "failed"),
    [
        (GOOD.replace("Thank you for getting in touch.", "Hello."), "opening"),
        (GOOD.replace("Kind regards,", "Best,"), "close"),
        (GOOD.replace("so please keep", "so please " + "really " * 80 + "keep"), "length"),
        (GOOD.replace("Our Warranty", "- Our Warranty"), "plain"),
        (GOOD.replace("months from", "**months** from"), "plain"),
        (GOOD.replace("in case", "\U0001f600 in case"), "plain"),
        (GOOD.replace("\n\nKind", "\n\nA.\n\nB.\n\nC.\n\nKind"), "plain"),
        (GOOD.replace('section "Brio kettle: Cover period"', 'section "Cover"'), "citation"),
        (GOOD.replace("so please keep", "we promise to keep"), "no_banned"),
        (GOOD.replace("somewhere safe", "somewhere safe at the center"), "british"),
        (GOOD.replace("in case you need it.", f"in case you need it. {NOT_FOUND}"), "not_found"),
    ],
)
def test_each_broken_rule_is_caught(reply, failed):
    report = check_reply(reply, POLICY)
    assert failed in report.failures()
    assert not report.all_pass


def test_not_found_reply_must_be_the_fixed_sentence_only():
    reply = (
        f"Thank you for getting in touch.\n\n{NOT_FOUND}\n\nKind regards,\nThe Halvard Home team"
    )
    assert "not_found" not in check_reply(reply, MISSING).failures()
    padded = reply.replace(NOT_FOUND, NOT_FOUND + " Sorry again.")
    assert "not_found" in check_reply(padded, MISSING).failures()


def test_article_citation_and_curly_apostrophes():
    reply = GOOD.replace(
        'Our Warranty policy, section "Brio kettle: Cover period", says',
        'our help article "Resetting your Ashby tumble dryer" says',
    )
    assert check_reply(reply, ARTICLE).citation
    curly = f"Thank you for getting in touch.\n\n{NOT_FOUND.replace(chr(39), chr(0x2019))}\n\n"
    assert body_of(curly + "Kind regards,\nThe Halvard Home team") == NOT_FOUND


def test_helpers():
    assert american_words("The colour and the color") == ["color"]
    assert set(RULES) == set(CHECKS)
    assert check_reply("", MISSING).mean_sentence_words == 0.0
