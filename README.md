# Translator Utilities

This repository is a small command-line toolkit for downloading media,
extracting or generating subtitles, extracting keyword context with an
OpenAI-compatible chat model, and translating WebVTT subtitles with that
context.

The project is intentionally script-friendly: the Python modules live in
`src/`, configuration stays at the repository root, and tests live in `tests/`.

## Directory Overview

```text
.
├── .github/workflows/ci.yml       GitHub Actions workflow for compile and unit tests
├── src/                           Application modules and CLI entry points
├── tests/                         Unit tests and the CI-friendly test runner
├── keyword_extractor_config.json  Default non-secret model and workflow settings
├── requirements.txt               Python dependencies
├── .env.example                   Example local environment variables
└── README.md                      Project overview and usage notes
```

## Source Modules

`src/main.py` is the interactive menu launcher for the whole toolkit. It
connects the individual utilities into one prompt-driven workflow.

`src/video_downloader.py` downloads videos with `yt-dlp`.

`src/vtt_downloader.py` downloads WebVTT subtitles from a video link with
`yt-dlp`.

`src/audio_extractor.py` extracts audio from a local video file with `ffmpeg`.

`src/subtitle_generator.py` generates WebVTT subtitles from audio using the
configured OpenAI transcription model.

`src/keyword_extractor.py` reads text, sends it to an OpenAI-compatible chat
model, parses keyword JSON, and saves the result.

`src/configure_keyword_extractor.py` edits the shared JSON configuration
interactively.

`src/vtt_translator.py` translates WebVTT files with keyword context while
preserving cue structure.

`src/subtitle_integrator.py` embeds subtitles as a selectable track or burns
them into a video with `ffmpeg`.

`src/__init__.py` exposes the core keyword extraction helpers for package-style
imports.

## Setup

Install Python dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

For media commands, also install these command-line tools and make sure they
are available on `PATH`:

```text
yt-dlp
ffmpeg
```

Set the API key expected by `keyword_extractor_config.json`. The default config
uses `DEEPSEEK_API_KEY`.

```powershell
$env:DEEPSEEK_API_KEY="your_api_key_here"
```

```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

You can copy `.env.example` to `.env` for local notes, but the scripts read
environment variables from the shell. Do not commit real API keys.

## Common Workflows

Start the interactive menu:

```bash
python src/main.py
```

Download a video:

```bash
python src/video_downloader.py "https://example.com/video"
python src/video_downloader.py "https://example.com/video" --format mp4
```

Download subtitles:

```bash
python src/vtt_downloader.py "https://example.com/video" --language en
python src/vtt_downloader.py "https://example.com/video" --language en --auto-subs
```

Extract audio:

```bash
python src/audio_extractor.py video.mp4 --format mp3
```

Generate subtitles from audio:

```bash
python src/subtitle_generator.py audio.mp3 --output subtitles.vtt
```

Extract keyword context from text:

```bash
python src/keyword_extractor.py notes.txt --output keywords.json
```

Translate a VTT file with keyword context:

```bash
python src/vtt_translator.py captions.vtt --keywords keywords.json --output translated.vtt
```

Add subtitles to a video:

```bash
python src/subtitle_integrator.py video.mp4 subtitles.vtt --output subtitled.mp4
python src/subtitle_integrator.py video.mp4 subtitles.vtt --burn-in
```

## Configuration

Shared settings live in `keyword_extractor_config.json`. The config controls
the chat model, transcription model, temperature, token limit, API key
environment variable name, output paths, translation target language, and prompt
templates.

Edit the config interactively:

```bash
python src/configure_keyword_extractor.py
```

Non-secret config values can also be overridden with environment variables:

```text
TRANSLATOR_MODEL
TRANSLATOR_TEMPERATURE
TRANSLATOR_MAX_TOKENS
TRANSLATOR_API_KEY_ENV
TRANSLATOR_BASE_URL
TRANSLATOR_KEYWORDS_OUTPUT_PATH
TRANSLATOR_TARGET_LANGUAGE
TRANSLATOR_TRANSLATION_OUTPUT_PATH
TRANSLATOR_TRANSCRIPTION_MODEL
```

## Importing Helpers

The `src` directory can be added to `PYTHONPATH` for direct module imports:

```python
from keyword_extractor import extract_keywords_from_file

results = extract_keywords_from_file("notes.txt")
```

You can also import the convenience package when the repository root is on
`PYTHONPATH`:

```python
from src import extract_keywords_from_file

results = extract_keywords_from_file("notes.txt")
```

## Tests and CI

Run the unit tests with progress output:

```bash
python tests/run_with_progress.py
```

Compile all Python files:

```bash
python -m compileall -q .
```

The GitHub Actions workflow in `.github/workflows/ci.yml` installs
dependencies, compiles the repository, and runs the unit tests on pushes and
pull requests to `main`. The tests do not call external LLM APIs, so CI does
not need an API key unless future integration tests add live API calls.
