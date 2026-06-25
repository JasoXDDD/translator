"""Generate a VTT subtitle file from audio using OpenAI transcription."""
import argparse
import os
from pathlib import Path
from typing import Any, Dict, Optional

from keyword_extractor import DEFAULT_CONFIG_PATH, load_config, openai


def _api_key(config: Dict[str, Any], explicit_api_key: Optional[str]) -> str:
    key = explicit_api_key or os.getenv(config.get("api_key_env", "OPENAI_API_KEY"))
    if not key:
        raise RuntimeError(
            "No OpenAI API key set. Provide --api-key or set "
            f"{config.get('api_key_env', 'OPENAI_API_KEY')}."
        )
    return key


def _transcribe(audio_path: Path, model: str, api_key: str, base_url: Optional[str] = None) -> str:
    if openai is None:
        raise RuntimeError("openai package not installed; install with `python -m pip install openai`.")

    normalized_base_url = base_url.strip() if base_url else None

    with audio_path.open("rb") as audio_file:
        if hasattr(openai, "OpenAI"):
            client_kwargs = {"api_key": api_key}
            if normalized_base_url:
                client_kwargs["base_url"] = normalized_base_url
            client = openai.OpenAI(**client_kwargs)
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="vtt",
            )
        else:
            openai.api_key = api_key
            if normalized_base_url:
                openai.api_base = normalized_base_url
            response = openai.Audio.transcribe(
                model,
                audio_file,
                response_format="vtt",
            )

    if isinstance(response, str):
        return response
    if hasattr(response, "text"):
        return response.text
    return str(response)


def generate_subtitles(
    audio_path: str,
    output_path: Optional[str] = None,
    config_path: str = DEFAULT_CONFIG_PATH,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> Path:
    """Transcribe an audio file and save the result as WebVTT subtitles."""
    source = Path(audio_path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Audio file not found: {source}")

    config = load_config(config_path)
    transcription_model = model or config["transcription_model"]
    request_base_url = base_url if base_url is not None else config.get("base_url")
    destination = Path(output_path).expanduser() if output_path else source.with_suffix(".vtt")
    subtitles = _transcribe(source, transcription_model, _api_key(config, api_key), request_base_url).strip()

    destination.write_text(subtitles + "\n", encoding="utf-8")
    return destination


def main(
    audio_path: Optional[str] = None,
    output_path: Optional[str] = None,
    config_path: str = DEFAULT_CONFIG_PATH,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> None:
    requested_audio = (audio_path or input("Audio file path: ")).strip().strip('"')
    if not requested_audio:
        raise ValueError("An audio file path is required.")

    destination = generate_subtitles(
        requested_audio,
        output_path=output_path,
        config_path=config_path,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )
    print(f"Saved subtitles to {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate VTT subtitles from an audio file")
    parser.add_argument("audio_file", nargs="?", help="Audio file path; prompted for when omitted")
    parser.add_argument("--output", default=None, help="Optional output VTT path")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to the JSON request config file")
    parser.add_argument("--api-key", default=None, help="OpenAI API key (overrides configured env var)")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible API base URL (overrides config)")
    parser.add_argument("--model", default=None, help="Transcription model (overrides config)")
    args = parser.parse_args()
    main(args.audio_file, args.output, args.config, args.api_key, args.base_url, args.model)
