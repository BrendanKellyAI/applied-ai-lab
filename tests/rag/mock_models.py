"""A mock answer model and judge for pipeline tests, keyed off the prompts they receive."""

import json
import re

from lab.rag.judge import judge_instructions

GARBAGE = "I am not JSON."


def respond(always_garbage=(), garbage_once=()):
    def respond(request):
        if request.system == judge_instructions():
            question = re.search(r"Question: (.*)", request.prompt).group(1)
            retry = "could not be read as a verdict" in request.prompt
            if question in always_garbage or (question in garbage_once and not retry):
                return GARBAGE
            answerable = "answered from the documents: yes" in request.prompt
            declined = "could not find" in request.prompt.split("System's answer:")[-1]
            correct = answerable != declined
            return json.dumps(
                {"declined": declined, "correct": correct, "faithful": True, "reason": "r"}
            )
        if "Fenwick" in request.prompt or "colour" in request.prompt:
            return "I could not find that in the passages."
        first = request.prompt.split("[P1] ", 1)[1].split("\n", 2)[1]
        return first

    return respond
