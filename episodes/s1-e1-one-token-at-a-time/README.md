# S1 E1: One token at a time

The code behind the first API call shown in [S1 E1, One token at a time](https://brendankellyai.github.io/episodes/s1-e1-one-token-at-a-time/). Parts 1 and 2 match the slides line for line.

This sample does not use the lab harness. It calls the OpenAI Python SDK directly, so you can see exactly what a raw API call looks like.

## What it does

Every part prints the reply, then three labelled token counts from the usage fields:

- **Input tokens:** what you sent, including a little formatting the API adds around each message.
- **Output tokens:** what the model produced. You are billed for input and output.
- **Reasoning tokens (included in output):** hidden thinking before the reply. `gpt-6-astra` always reasons a little, so output tokens can be higher than the visible reply suggests. It can also be 0.

**Part 1: first call.** Sends "My name is Brendan." to the model and prints the reply and its token counts.

**Part 2: second call, no history.** Sends "What is my name?" on its own. The model cannot answer, because it has no memory between calls. Each call starts from nothing.

**Part 3: third call, with history.** Sends the first exchange and the question together, as one input. The model now answers correctly, and the input token count has grown, because you paid to send the conversation again. This is the bridge to [S1 E2, Tokens](https://brendankellyai.github.io/episodes/s1-e2-tokens/).

Responses vary between runs, so your wording and token counts will differ from the slides.

## Run it

You need Python 3.12 or later, [uv](https://docs.astral.sh/uv/), and an OpenAI API key.

1. From the repository root, install dependencies:

   ```bash
   uv sync
   ```

2. Add your API key to a file named `.env` in the repository root, the same file the rest of the lab uses:

   ```bash
   OPENAI_API_KEY=your-key-here
   ```

   If `.env` does not exist yet, copy `.env.example` to `.env` first. The script loads the key from `.env` in its first few lines, above the code shown on the slides. A key already set as an environment variable takes priority.

3. Run the script:

   ```bash
   uv run python episodes/s1-e1-one-token-at-a-time/first_call.py
   ```

Never paste your key into the script. `.env` is listed in `.gitignore`, so it is never committed.

## Cost

Three short calls. The exact cost depends on current OpenAI pricing and on how many tokens the model uses. The script makes new calls every time it runs.
