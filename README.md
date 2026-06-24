# Translator: Keywords Extractor

This module reads a plain text file and sends it to an OpenAI-style LLM to
extract important keywords and relevant information. The LLM is asked to
respond with parseable JSON: an array of objects with `keyword` and `info`.

Quickstart

1. Install dependencies:

```bash
python -m pip install -r translator/requirements.txt
```

2. Set your API key in your environment:

```bash
$env:DEEPSEEK_API_KEY="your_api_key_here"  # Windows PowerShell
export DEEPSEEK_API_KEY="your_api_key_here"  # macOS / Linux shell
```

Copy `.env.example` to `.env` if you prefer keeping local environment values
in a file. `.env` is ignored by Git; never commit real API keys.

3. Run the extractor from Python:

```python
from translator import extract_keywords_from_file
results = extract_keywords_from_file('notes.txt')
print(results)
```

Or run as a script:

```bash
python keyword_extractor.py notes.txt
```

The extracted keywords are saved to the configured `keywords_output_path`
(`keywords.json` by default). You can override it per run:

```bash
python keyword_extractor.py notes.txt --output my_keywords.json
```

4. Edit the request configuration:

```bash
python configure_keyword_extractor.py
```

The extractor loads request settings from `keyword_extractor_config.json` by
default. You can point either program at another config file with `--config`.
The config stores the name of the API key environment variable
(`DEEPSEEK_API_KEY` by default), not the secret value itself.

5. Translate a VTT file using the stored keyword context:

```bash
python vtt_translator.py captions.vtt --keywords keywords.json --output translated.vtt
```

The translator reads the VTT file, finds keywords that appear in it, sends those
keyword notes along with the VTT to the LLM, and saves the returned VTT text.
The target language is controlled by `translation_target_language` in the config
or by `--target-language`.

## Media Utilities

Download a video with `yt-dlp`. Running without arguments prompts for the link
and optional video format. Leave the format blank to use yt-dlp's default file
mode:

```bash
python video_downloader.py
python video_downloader.py "https://example.com/video"
python video_downloader.py "https://example.com/video" --format mp4
```

Download WebVTT subtitles directly from a video link:

```bash
python vtt_downloader.py
python vtt_downloader.py "https://example.com/video" --language en
python vtt_downloader.py "https://example.com/video" --language en --auto-subs
```

Extract audio from a video with `ffmpeg`. The output is saved beside the video
using the requested audio extension:

```bash
python audio_extractor.py
python audio_extractor.py video.mp4 --format mp3
```

Generate WebVTT subtitles from an audio file using the OpenAI transcription
model configured by `transcription_model`:

```bash
python subtitle_generator.py
python subtitle_generator.py audio.mp3 --output subtitles.vtt
```

Add subtitles to a video with `ffmpeg`. By default this embeds a selectable
subtitle track and saves the result beside the source video with `_subtitled`
appended to the filename. Burn-in mode detects VTT color cue classes such as
`<c.colorFEFEFE>` and renders them with the matching colors from the VTT
`Style:` block:

```bash
python subtitle_integrator.py video.mp4 subtitles.vtt
python subtitle_integrator.py video.mp4 subtitles.vtt --output subtitled.mp4
python subtitle_integrator.py video.mp4 subtitles.vtt --burn-in
```

Notes
- The code expects the `openai` Python package and an OpenAI-compatible API key.
- `video_downloader.py` requires `yt-dlp`. Install Python dependencies with
  `python -m pip install -r requirements.txt`.
- `video_downloader.py`, `audio_extractor.py`, and `subtitle_integrator.py`
  require `ffmpeg` installed and available on `PATH`.
- Request settings such as `model`, `temperature`, `max_tokens`,
  `system_message`, `prompt_template`, keyword output, and VTT translation
  settings live in the JSON config file.
- Non-secret config values can also be overridden with environment variables:
  `TRANSLATOR_MODEL`, `TRANSLATOR_TEMPERATURE`, `TRANSLATOR_MAX_TOKENS`,
  `TRANSLATOR_API_KEY_ENV`, `TRANSLATOR_BASE_URL`,
  `TRANSLATOR_KEYWORDS_OUTPUT_PATH`, `TRANSLATOR_TARGET_LANGUAGE`,
  `TRANSLATOR_TRANSLATION_OUTPUT_PATH`, and `TRANSLATOR_TRANSCRIPTION_MODEL`.
- The module attempts to parse JSON out of the model's response; if parsing
  fails it will return the raw response content for troubleshooting.

## GitHub CI

This repo includes `.github/workflows/ci.yml`. On pushes and pull requests to
`main`, GitHub Actions installs dependencies, compiles the Python files, and
runs the unit tests.

The CI workflow does not call the external LLM API, so it does not need your
API key. If you later add integration tests that do call the API, add
`DEEPSEEK_API_KEY` under GitHub repository settings:

Settings -> Secrets and variables -> Actions -> New repository secret.
