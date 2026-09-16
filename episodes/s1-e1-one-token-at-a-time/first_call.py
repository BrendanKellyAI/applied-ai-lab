"""S1 E1, One token at a time: your first call to a model.

Run from the repository root:

    uv run python episodes/s1-e1-one-token-at-a-time/first_call.py

Needs OPENAI_API_KEY set in your environment. See README.md in this folder.
"""

print("\n=== Part 1: first call ===\n")

from openai import OpenAI

# Reads OPENAI_API_KEY from the environment
client = OpenAI()

first = client.responses.create(
    model="gpt-6-astra",
    input="My name is Brendan.",
)
print(first.output_text)
print(first.usage.input_tokens,
      first.usage.output_tokens)

print("\n=== Part 2: second call, no history ===\n")

second = client.responses.create(
    model="gpt-6-astra",
    input="What is my name?",
)
print(second.output_text)

print("\n=== Part 3: third call, with history ===\n")

# The model remembers nothing between calls, so we send the conversation so far ourselves.
history = [
    {"role": "user", "content": "My name is Brendan."},
    {"role": "assistant", "content": first.output_text},
    {"role": "user", "content": "What is my name?"},
]

third = client.responses.create(
    model="gpt-6-astra",
    input=history,
)
print(third.output_text)
print("Input tokens:", third.usage.input_tokens)
