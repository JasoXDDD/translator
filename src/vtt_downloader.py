"""Download WebVTT subtitles directly from a video link using yt-dlp."""
import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def download_vtt(
    url: str,
    language: str = "en",
    output_template: Optional[str] = None,
    auto_subs: bool = False,
) -> None:
    """Download available subtitles from a video link and convert them to VTT."""
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        raise RuntimeError("yt-dlp was not found. Install it with `python -m pip install yt-dlp`.")

    requested_url = url.strip()
    requested_language = language.strip()
    if not requested_url:
        raise ValueError("A video link is required.")
    if not requested_language:
        raise ValueError("A subtitle language is required.")

    command = [
        yt_dlp,
        "--skip-download",
        "--sub-langs",
        requested_language,
        "--convert-subs",
        "vtt",
    ]
    command.append("--write-auto-subs" if auto_subs else "--write-subs")

    if output_template:
        command.extend(["--output", str(Path(output_template).expanduser())])
    else:
        command.extend(["--output", "%(title)s.%(ext)s"])

    command.append(requested_url)
    subprocess.run(command, check=True)


def main(
    url: Optional[str] = None,
    language: Optional[str] = None,
    output_template: Optional[str] = None,
    auto_subs: bool = False,
) -> None:
    requested_url = (url or input("Video link: ")).strip()
    requested_language = (language or input("Subtitle language (for example en, ja, or all): ")).strip()
    requested_output = output_template
    if requested_output is None:
        requested_output = input("Output template (press Enter for video title): ").strip().strip('"') or None
    requested_auto_subs = auto_subs
    if not requested_auto_subs:
        auto_choice = input("Use auto-generated subtitles if needed? [y/N]: ").strip().lower()
        requested_auto_subs = auto_choice in {"y", "yes"}

    download_vtt(
        requested_url,
        requested_language,
        output_template=requested_output,
        auto_subs=requested_auto_subs,
    )
    print("VTT subtitle download completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download VTT subtitles from a video link using yt-dlp")
    parser.add_argument("url", nargs="?", help="Video link; prompted for when omitted")
    parser.add_argument("--language", default=None, help="Subtitle language code, or all")
    parser.add_argument("--output", default=None, help="yt-dlp output template; default is video title")
    parser.add_argument("--auto-subs", action="store_true", help="Download auto-generated subtitles")
    args = parser.parse_args()
    main(args.url, args.language, args.output, args.auto_subs)
