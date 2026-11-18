# Migration: gpt-4o-mini → gpt-6-luna

## What changed

This API takes a YouTube video, downloads its transcript, and asks an OpenAI
model to add punctuation and formatting. It used the model **`gpt-4o-mini`**.
It now uses **`gpt-6-luna`**.

Two things in the code depended on the model name:

1. **The API call** that sends each piece of the transcript to OpenAI.
2. **The token counter** (`tiktoken`) that splits long transcripts into pieces
   of about 16,000 tokens.

Both have been updated. No Python packages were changed.

## Why

OpenAI is retiring `gpt-4o-mini` (and also `gpt-4o`, `gpt-4.1` and `gpt-4.1-mini`)
from the API on **January 14, 2027**. After that date, any request that asks for
`gpt-4o-mini` will fail, and this API would return "OpenAI API error" instead
of the formatted transcript.

OpenAI's official deprecations page lists `gpt-6-luna` as the recommended
replacement:

- Page: <https://developers.openai.com/api/docs/deprecations>
  (the old link <https://platform.openai.com/docs/deprecations> redirects there)
- Row in the "Upcoming deprecations" table:

  | Shutdown date | Affected model | Status | Recommended replacement | Notice date |
  |---|---|---|---|---|
  | Jan 14, 2027 | GPT-4o mini (`gpt-4o-mini-2024-07-18`) | Deprecated | `gpt-6-luna` | Oct 14, 2026 |

Model page: <https://developers.openai.com/api/docs/models/gpt-6-luna>

## The tiktoken problem (and the fix)

`tiktoken` is OpenAI's library for counting tokens. The old code did this:

```python
tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
```

`encoding_for_model` looks up the model name in a list built into tiktoken.
We tested whether tiktoken knows the new name:

| tiktoken version | `encoding_for_model("gpt-4o-mini")` | `encoding_for_model("gpt-6-luna")` |
|---|---|---|
| 0.7.0 (the version this project pins) | `o200k_base` ✅ | **KeyError** ❌ |
| 0.14.0 (newest at the time of writing) | `o200k_base` ✅ | **KeyError** ❌ |

So just changing the name would **crash the app**, and upgrading tiktoken does
not help either.

**The fix:** ask tiktoken for the new model first. If it doesn't know the model,
fall back to `o200k_base`, the same encoding `gpt-4o-mini` used:

```python
try:
    tokenizer = tiktoken.encoding_for_model(OPENAI_MODEL)
except KeyError:
    tokenizer = tiktoken.get_encoding(FALLBACK_ENCODING)  # "o200k_base"
```

Why this is the safest choice:

- **It can't crash on the model name.** Unknown model → fallback, not an error.
- **Chunks stay exactly the same size as before**, because the app keeps
  counting tokens the same way `gpt-4o-mini` did.
- **The count is only used to decide where to cut the transcript.** It is not
  sent to OpenAI and nothing is billed from it. If gpt-6-luna counts tokens a
  little differently, chunks are only slightly bigger or smaller, and they
  are far below the model's limits (1,050,000 input tokens, 128,000 output tokens).
- **It upgrades itself.** If a future tiktoken version learns the name
  `gpt-6-luna`, the `try` line will start using it automatically.

## Every file and line changed

Line numbers are for the new version of each file.

| File | Line(s) | Before | After |
|---|---|---|---|
| `app.py` | 15–17 | *(nothing)* | New setting `OPENAI_MODEL = "gpt-6-luna"` with a comment saying why |
| `app.py` | 19–22 | *(nothing)* | New setting `FALLBACK_ENCODING = "o200k_base"` with a comment saying why |
| `app.py` | 52–55 | `tiktoken.encoding_for_model("gpt-4o-mini")` | `try` the new model, `except KeyError` use `o200k_base` |
| `app.py` | 85 | `model="gpt-4o-mini",` | `model=OPENAI_MODEL,` |
| `app.py` | 97 | `async def improve_text_with_gpt4(text):` | `async def improve_text_with_openai(text):` |
| `app.py` | 125 | `asyncio.run(improve_text_with_gpt4(...))` | `asyncio.run(improve_text_with_openai(...))` |
| `README.md` | 3 | "GPT-4o-mini to enhance punctuation" | "OpenAI's GPT-6 Luna (`gpt-6-luna`) to enhance punctuation" |
| `README.md` | 13 | "the default GPT-4o-mini output limit" | "the model's output limit" |
| `MIGRATION.md` | all | *(new file)* | This document |

The function was renamed because its name said "gpt4", which was already wrong
and would be more wrong now. It is only used inside `app.py`, so nothing
else breaks.

## What did NOT change, and why

- **`requirements.txt`**: no upgrade needed.
  - `openai==1.39.0` works with gpt-6-luna. The request sends only `model`
    and `messages`, and the old library correctly reads a reply that includes
    reasoning-token details (tested, see below).
  - `tiktoken==0.7.0`: the newest version does not know `gpt-6-luna` either,
    so upgrading would not help. The fallback above fixes it for every version.
- **The prompt, the chunk size (16,000 tokens), the Flask route, and the
  authentication**: unchanged.

## Things to know about the new model

- `gpt-6-luna` is a **reasoning model**. It "thinks" before it answers, using
  `medium` effort by default. For simple work like adding punctuation, this may
  be **slower** than before, and long videos are split into many chunks.
- Reasoning tokens are billed as output tokens. Price at the time of writing:
  $0.10 per 1M input tokens and $0.50 per 1M output tokens.
- **Optional speed-up (not done in this migration):** the model page says it
  supports `reasoning_effort="none"`, which skips the thinking step. That is
  closest to how `gpt-4o-mini` behaved. With the pinned `openai==1.39.0` you
  would pass it like this:

  ```python
  response = await client.chat.completions.create(
      model=OPENAI_MODEL,
      messages=[...],
      extra_body={"reasoning_effort": "none"},
  )
  ```

  Try it only after the basic migration works, and compare the output quality.

## How it was tested (without an API key)

We ran the real `app.py` using the exact versions in `requirements.txt`, with
two fake pieces:

- **A fake OpenAI server** running on this computer at `127.0.0.1`. It records
  what the app sends and replies like OpenAI would, including the
  `reasoning_tokens` field that reasoning models return.
- **A fake YouTube transcript** of 14,000 numbered phrases (about 42,000
  words), long enough to force the app to split it into several chunks.

Results:

| Check | Result |
|---|---|
| Request with no secret header is rejected | 401 ✅ |
| Request with the secret header works | 200 ✅ |
| Transcript was split into chunks | 7 requests sent ✅ |
| Model name sent to OpenAI | `gpt-6-luna` only ✅ |
| Fields sent | only `model` and `messages` ✅ |
| tiktoken fallback used (no crash) | ✅ |
| Any "OpenAI API error" in the result | none ✅ |
| All 14,000 numbered phrases present in the result, nothing lost | ✅ |

**Limits of this test:** it proves the code and packages work together. It does
**not** test real answer quality, real speed, or real YouTube downloads.
It was run on Python 3.12, while `runtime.txt` says 3.9.16, but the new code
uses nothing that 3.9 lacks.

## How to test it for real (when you have an API key)

1. **Install the packages** (inside this folder, ideally in a virtual environment):

   ```bash
   pip install -r requirements.txt
   ```

2. **Create a `.env` file** (git ignores it, so it won't be uploaded):

   ```
   OPENAI_API_KEY=sk-...your key...
   SECRET_CODE=pick-any-password
   PROXY=
   ```

   Leave `PROXY` empty if YouTube doesn't block your connection.

3. **Start the API:**

   ```bash
   python app.py
   ```

4. **Send a request** from a second terminal (use a short video first):

   ```bash
   curl -X POST http://localhost:8080/transcribe -H "Content-Type: application/json" -H "X-YTAPI-Secret: pick-any-password" -d "{\"url\": \"https://www.youtube.com/watch?v=VIDEO_ID\"}"
   ```

5. **Check the result:**
   - You get `{"result": "..."}` with punctuated text.
   - The words are the same as the original transcript. Only punctuation and
     formatting should change.
   - There is no `"OpenAI API error"` text in the result.

6. **Confirm the new model was used:** open
   <https://platform.openai.com/usage> and check that the requests show
   `gpt-6-luna`, not `gpt-4o-mini`.
