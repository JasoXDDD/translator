"""Menu launcher for the translator utilities."""
from typing import Callable, Optional

import audio_extractor
import configure_keyword_extractor
import keyword_extractor
import subtitle_generator
import subtitle_integrator
import video_downloader
import vtt_downloader
import vtt_translator


MenuAction = Callable[[], None]


def _prompt_optional(label: str) -> Optional[str]:
    value = input(f"{label} (press Enter to skip): ").strip().strip('"')
    return value or None


def _pause() -> None:
    input("\nPress Enter to return to the menu...")


def _run_video_downloader() -> None:
    print("\nDownload Video")
    url = input("Video link: ").strip()
    video_format = input("Expected video format (mp4, mkv, or webm): ").strip()
    video_downloader.main(url, video_format)


def _run_vtt_downloader() -> None:
    print("\nDownload VTT Subtitles")
    url = input("Video link: ").strip()
    language = input("Subtitle language (for example en, ja, or all): ").strip()
    output_template = _prompt_optional("Output template")
    auto_choice = input("Use auto-generated subtitles if needed? [y/N]: ").strip().lower()
    vtt_downloader.download_vtt(
        url,
        language=language,
        output_template=output_template,
        auto_subs=auto_choice in {"y", "yes"},
    )
    print("VTT subtitle download completed.")


def _run_audio_extractor() -> None:
    print("\nExtract Audio")
    video_path = input("Video file path: ").strip().strip('"')
    audio_format = input("Audio format (mp3, wav, flac, m4a, aac, ogg, or opus): ").strip()
    output_path = _prompt_optional("Output audio path")
    audio_extractor.main(video_path, audio_format, output_path)


def _run_subtitle_generator() -> None:
    print("\nGenerate Subtitles")
    audio_path = input("Audio file path: ").strip().strip('"')
    output_path = _prompt_optional("Output VTT path")
    config_path = _prompt_optional("Config path") or keyword_extractor.DEFAULT_CONFIG_PATH
    model = _prompt_optional("Transcription model")
    api_key = _prompt_optional("OpenAI API key")
    base_url = _prompt_optional("API base URL")
    subtitle_generator.main(
        audio_path,
        output_path=output_path,
        config_path=config_path,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


def _run_subtitle_integrator() -> None:
    print("\nAdd Subtitles to Video")
    video_path = input("Video file path: ").strip().strip('"')
    subtitle_path = input("Subtitle file path: ").strip().strip('"')
    output_path = _prompt_optional("Output video path")
    burn_choice = input("Burn subtitles into the image? [y/N]: ").strip().lower()
    language = _prompt_optional("Subtitle language metadata, for example eng")
    overwrite_choice = input("Overwrite output file if it exists? [y/N]: ").strip().lower()
    subtitle_integrator.main(
        video_path,
        subtitle_path,
        output_path=output_path,
        burn_in=burn_choice in {"y", "yes"},
        language=language,
        overwrite=overwrite_choice in {"y", "yes"},
    )


def _run_keyword_extractor() -> None:
    print("\nExtract Keywords")
    text_path = input("Text file path: ").strip().strip('"')
    output_path = _prompt_optional("Keywords output path")
    config_path = _prompt_optional("Config path") or keyword_extractor.DEFAULT_CONFIG_PATH
    model = _prompt_optional("Model")
    api_key = _prompt_optional("OpenAI API key")
    base_url = _prompt_optional("API base URL")
    temperature = _prompt_float_optional("Temperature")
    max_tokens = _prompt_int_optional("Max tokens")

    result = keyword_extractor.extract_keywords_from_file(
        text_path,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        config_path=config_path,
        output_path=output_path,
    )
    print("\nExtracted keywords:")
    try:
        import json

        print(json.dumps(result, indent=2, ensure_ascii=False))
    except TypeError:
        print(result)


def _run_vtt_translator() -> None:
    print("\nTranslate VTT")
    vtt_path = input("VTT file path: ").strip().strip('"')
    keywords_path = _prompt_optional("Keywords JSON path")
    output_path = _prompt_optional("Output VTT path")
    config_path = _prompt_optional("Config path") or keyword_extractor.DEFAULT_CONFIG_PATH
    target_language = _prompt_optional("Target language")
    model = _prompt_optional("Model")
    api_key = _prompt_optional("OpenAI API key")
    base_url = _prompt_optional("API base URL")
    temperature = _prompt_float_optional("Temperature")
    max_tokens = _prompt_int_optional("Max tokens")

    vtt_translator.translate_vtt_file(
        vtt_path,
        keywords_path=keywords_path,
        output_path=output_path,
        config_path=config_path,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        target_language=target_language,
    )
    saved_path = output_path or keyword_extractor.load_config(config_path)["translation_output_path"]
    print(f"Saved translated VTT to {saved_path}")


def _run_config_editor() -> None:
    print("\nEdit Configuration")
    config_path = _prompt_optional("Config path") or keyword_extractor.DEFAULT_CONFIG_PATH
    configure_keyword_extractor.edit_config(config_path)
    print(f"\nSaved {config_path}")


def _prompt_float_optional(label: str) -> Optional[float]:
    raw = _prompt_optional(label)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        print(f"Invalid {label.lower()}; leaving it unset.")
        return None


def _prompt_int_optional(label: str) -> Optional[int]:
    raw = _prompt_optional(label)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        print(f"Invalid {label.lower()}; leaving it unset.")
        return None


MENU_OPTIONS: tuple[tuple[str, str, MenuAction], ...] = (
    ("1", "Download video", _run_video_downloader),
    ("2", "Download VTT subtitles from link", _run_vtt_downloader),
    ("3", "Extract audio from video", _run_audio_extractor),
    ("4", "Generate VTT subtitles from audio", _run_subtitle_generator),
    ("5", "Add subtitles to video", _run_subtitle_integrator),
    ("6", "Extract keywords from text", _run_keyword_extractor),
    ("7", "Translate VTT using keywords", _run_vtt_translator),
    ("8", "Edit keyword extractor config", _run_config_editor),
)


def print_menu() -> None:
    print("\nTranslator Utilities")
    for key, label, _ in MENU_OPTIONS:
        print(f"{key}. {label}")
    print("0. Exit")


def main() -> None:
    actions = {key: action for key, _, action in MENU_OPTIONS}

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == "0":
            print("Goodbye.")
            return

        action = actions.get(choice)
        if action is None:
            print("Invalid choice. Try again.")
            continue

        try:
            action()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
        except Exception as exc:
            print(f"\nError: {exc}")
        finally:
            _pause()


if __name__ == "__main__":
    main()
