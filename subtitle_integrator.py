"""Add subtitles to a video using ffmpeg."""
import argparse
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional


TEXT_SUBTITLE_EXTENSIONS = {".ass", ".srt", ".ssa", ".vtt"}
MOV_TEXT_CONTAINERS = {".m4v", ".mov", ".mp4"}


def _ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg was not found. Install ffmpeg and add it to your PATH.")
    return ffmpeg


def _default_output_path(video_path: Path) -> Path:
    return video_path.with_name(f"{video_path.stem}_subtitled{video_path.suffix}")


def _subtitle_filter_path(subtitle_path: Path) -> str:
    """Escape a subtitle path for ffmpeg's subtitles filter."""
    normalized = subtitle_path.resolve().as_posix()
    normalized = re.sub(r"^([A-Za-z]):", r"\1\:", normalized)
    normalized = normalized.replace("'", r"\'")
    normalized = normalized.replace(",", r"\,")
    normalized = normalized.replace("[", r"\[")
    normalized = normalized.replace("]", r"\]")
    return f"filename='{normalized}'"


def integrate_subtitles(
    video_path: str,
    subtitle_path: str,
    output_path: Optional[str] = None,
    burn_in: bool = False,
    language: Optional[str] = None,
    overwrite: bool = False,
) -> Path:
    """Create a video with subtitles embedded as a track or burned into the image."""
    ffmpeg = _ffmpeg()
    source = Path(video_path).expanduser()
    subtitles = Path(subtitle_path).expanduser()

    if not source.is_file():
        raise FileNotFoundError(f"Video file not found: {source}")
    if not subtitles.is_file():
        raise FileNotFoundError(f"Subtitle file not found: {subtitles}")

    subtitle_extension = subtitles.suffix.lower()
    if subtitle_extension not in TEXT_SUBTITLE_EXTENSIONS:
        supported = ", ".join(sorted(TEXT_SUBTITLE_EXTENSIONS))
        raise ValueError(f"Unsupported subtitle format '{subtitle_extension}'. Choose one of: {supported}.")

    destination = Path(output_path).expanduser() if output_path else _default_output_path(source)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {destination}. Pass overwrite=True or --overwrite.")

    replace_flag = "-y" if overwrite else "-n"
    if burn_in:
        command = [
            ffmpeg,
            replace_flag,
            "-i",
            str(source),
            "-vf",
            f"subtitles={_subtitle_filter_path(subtitles)}",
            "-c:a",
            "copy",
            str(destination),
        ]
    else:
        command = [
            ffmpeg,
            replace_flag,
            "-i",
            str(source),
            "-i",
            str(subtitles),
            "-map",
            "0",
            "-map",
            "1:0",
            "-c",
            "copy",
        ]
        if destination.suffix.lower() in MOV_TEXT_CONTAINERS:
            command.extend(["-c:s", "mov_text"])
        if language:
            command.extend(["-metadata:s:s:0", f"language={language}"])
        command.append(str(destination))

    subprocess.run(command, check=True)
    return destination


def main(
    video_path: Optional[str] = None,
    subtitle_path: Optional[str] = None,
    output_path: Optional[str] = None,
    burn_in: bool = False,
    language: Optional[str] = None,
    overwrite: bool = False,
) -> None:
    requested_video = (video_path or input("Video file path: ")).strip().strip('"')
    requested_subtitles = (subtitle_path or input("Subtitle file path: ")).strip().strip('"')

    if not requested_video:
        raise ValueError("A video file path is required.")
    if not requested_subtitles:
        raise ValueError("A subtitle file path is required.")

    destination = integrate_subtitles(
        requested_video,
        requested_subtitles,
        output_path=output_path,
        burn_in=burn_in,
        language=language,
        overwrite=overwrite,
    )
    print(f"Saved subtitled video to {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add subtitles to a video using ffmpeg")
    parser.add_argument("video_file", nargs="?", help="Video file path; prompted for when omitted")
    parser.add_argument("subtitle_file", nargs="?", help="Subtitle file path; prompted for when omitted")
    parser.add_argument("--output", default=None, help="Optional output video path")
    parser.add_argument("--burn-in", action="store_true", help="Hardcode subtitles into the video image")
    parser.add_argument("--language", default=None, help="Optional subtitle language metadata, for example eng")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite the output file if it already exists")
    args = parser.parse_args()
    main(args.video_file, args.subtitle_file, args.output, args.burn_in, args.language, args.overwrite)
