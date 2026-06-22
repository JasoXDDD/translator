"""Interactively extract audio from a video using ffmpeg."""
import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Optional


AUDIO_CODECS = {
    "aac": "aac",
    "flac": "flac",
    "m4a": "aac",
    "mp3": "libmp3lame",
    "ogg": "libvorbis",
    "opus": "libopus",
    "wav": "pcm_s16le",
}


def extract_audio(video_path: str, audio_format: str, output_path: Optional[str] = None) -> Path:
    """Extract a video's audio stream and encode it in the requested format."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg was not found. Install ffmpeg and add it to your PATH.")

    source = Path(video_path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Video file not found: {source}")

    normalized_format = audio_format.lower().lstrip(".")
    if normalized_format not in AUDIO_CODECS:
        supported = ", ".join(sorted(AUDIO_CODECS))
        raise ValueError(f"Unsupported audio format '{audio_format}'. Choose one of: {supported}.")

    destination = Path(output_path).expanduser() if output_path else source.with_suffix(f".{normalized_format}")
    subprocess.run(
        [
            ffmpeg,
            "-n",
            "-i",
            str(source),
            "-vn",
            "-c:a",
            AUDIO_CODECS[normalized_format],
            str(destination),
        ],
        check=True,
    )
    return destination


def main(
    video_path: Optional[str] = None,
    audio_format: Optional[str] = None,
    output_path: Optional[str] = None,
) -> None:
    requested_video = (video_path or input("Video file path: ")).strip().strip('"')
    requested_format = (audio_format or input("Audio format (mp3, wav, flac, m4a, aac, ogg, or opus): ")).strip()

    if not requested_video:
        raise ValueError("A video file path is required.")
    if not requested_format:
        raise ValueError("An audio format is required.")

    destination = extract_audio(requested_video, requested_format, output_path)
    print(f"Saved extracted audio to {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract audio from a video using ffmpeg")
    parser.add_argument("video_file", nargs="?", help="Video file path; prompted for when omitted")
    parser.add_argument("--format", dest="audio_format", default=None, help="Output audio format")
    parser.add_argument("--output", default=None, help="Optional output audio path")
    args = parser.parse_args()
    main(args.video_file, args.audio_format, args.output)
