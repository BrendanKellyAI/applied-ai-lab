"""Prompts for the four Task B stages. Every reply is one JSON object.

1. The generator writes a customer question and a correct answer from one passage.
2. The checker (another provider) confirms the answer is supported and answers the question,
   or, for a not found item, that the passage does not answer it.
3. The generator rewrites the answer as a reply in the house style.
4. The checker confirms the reply keeps every fact of the answer and adds none.
"""

from lab.adapt.build_tasks.passages import NOT_FOUND, BSeed
from lab.adapt.style import NOT_FOUND as NOT_FOUND_SENTENCE
from lab.adapt.style import Source

NOT_FOUND_ANSWER = "The information is not available in Halvard Home's policies or help articles."

QA_SYSTEM = (
    "You write test questions for the support library of Halvard Home, an invented UK "
    "appliance maker. You are given one passage. Write a question a customer might send, in "
    "British English, and a short factual answer to it. Reply with one JSON object and nothing "
    'else: {"question": "...", "answer": "..."}'
)

CHECK_SYSTEM = (
    "You check test items for a customer support dataset. Judge only from the passage given. "
    "Do not explain your reasoning. Reply with one JSON object and nothing else."
)

REWRITE_SYSTEM = (
    "You write replies for Halvard Home's support agents, following the house style guide "
    "exactly. Reply with one JSON object and nothing else: "
    '{"reply": "<the reply, with \\n for line breaks>"}'
)


def qa_prompt(seed: BSeed) -> str:
    passage = seed.passage
    lines = [f"Passage ({_where(passage.source())}):", passage.text, ""]
    if seed.kind == NOT_FOUND:
        lines += [
            "Write a question on the same topic that this passage does not answer, so that a "
            "reader of the passage could not answer it. It must not be answerable from any "
            "detail in the passage.",
            f'Set the answer to exactly: "{NOT_FOUND_ANSWER}"',
        ]
    else:
        lines += [
            f"Ask about {seed.angle}.",
            "The answer must be fully supported by the passage, use its exact figures, and be "
            "one to three sentences. Do not add advice the passage does not give.",
        ]
    lines += [
        f"The customer's tone is {seed.tone}. The question is one to three sentences.",
        f"This is question {seed.variant + 1} about this passage; make it different from the "
        "most obvious question.",
    ]
    return "\n".join(lines)


def support_prompt(seed: BSeed, question: str, answer: str) -> str:
    passage = seed.passage
    head = f"Passage:\n{passage.text}\n\nQuestion: {question}\n"
    if seed.kind == NOT_FOUND:
        return (
            head + "\nCan the question be answered from the passage? Reply "
            '{"passage_answers": true or false}'
        )
    return (
        head + f"Answer: {answer}\n\nIs every statement in the answer supported by the passage, "
        "and does the answer answer the question? Reply "
        '{"supported": true or false, "answers_question": true or false}'
    )


def rewrite_prompt(seed: BSeed, question: str, answer: str, style_guide: str) -> str:
    source = seed.source()
    lines = [
        "House style guide:",
        style_guide,
        "",
        f"Customer question: {question}",
        f"Correct answer: {answer}",
        "",
    ]
    if source.kind == "not_found":
        lines.append(
            "The information is not available, so between the opening and the close write "
            f"exactly: {NOT_FOUND_SENTENCE}"
        )
    else:
        lines += [
            f"Cite the source in exactly this form: {source.citation()}",
            "Use only the facts in the correct answer. Add no reasons, benefits, advice, "
            "reassurance or offers of further help that the answer does not give. If the reply "
            "would be too short, reach the length by briefly restating the customer's question, "
            "never by adding a fact.",
        ]
    lines.append("Write the reply.")
    return "\n".join(lines)


def facts_prompt(question: str, answer: str, reply: str) -> str:
    return (
        f"Customer question: {question}\n\nSource answer: {answer}\n\nReply: {reply}\n\n"
        "Does the reply state every fact in the source answer, with the same figures? Then list "
        "each fact in the reply that is in neither the source answer nor the customer question, "
        "quoting the reply's words. These are not facts and are never listed: anything the "
        "customer question says (its product, its details, the problem it describes), [source] "
        "where the citation was, greetings and sign-offs, the fixed apology, the "
        "fixed safety sentence telling the customer to stop using the appliance and unplug it "
        "if it is safe to do so, and any rewording of a fact the source answer states. Reply "
        '{"all_facts_kept": true or false, "facts_added": ["quoted words", ...]} with an '
        "empty list when nothing is added."
    )


def _where(source: Source) -> str:
    if source.kind == "policy":
        return f'{source.name} policy, section "{source.section}"'
    return f'help article "{source.name}"'
