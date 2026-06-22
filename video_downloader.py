"""Interactively download a video in a requested container using yt-dlp."""
import argparse
import shutil
import subprocess
from typing import Optional


SUPPORTED_VIDEO_FORMATS = {"mp4", "mkv", "webm"}


def download_video(url: str, video_format: str) -> None:
    """Download and remux a video into the requested container."""
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        raise RuntimeError("yt-dlp was not found. Install it with `python -m pip install yt-dlp`.")

    normalized_format = video_format.lower().lstrip(".")
    if normalized_format not in SUPPORTED_VIDEO_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_VIDEO_FORMATS))
        raise ValueError(f"Unsupported video format '{video_format}'. Choose one of: {supported}.")

    subprocess.run(
        [
            yt_dlp,
            "--format",
            "bestvideo*+bestaudio/best",
            "--merge-output-format",
            normalized_format,
            "--remux-video",
            normalized_format,
            "--output",
            "%(title)s.%(ext)s",
            url,
        ],
        check=True,
    )


def main(url: Optional[str] = None, video_format: Optional[str] = None) -> None:
    requested_url = (url or input("Video link: ")).strip()
    requested_format = (video_format or input("Expected video format (mp4, mkv, or webm): ")).strip()

    if not requested_url:
        raise ValueError("A video link is required.")
    if not requested_format:
        raise ValueError("A video format is required.")

    download_video(requested_url, requested_format)
    print("Video download completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a video using yt-dlp")
    parser.add_argument("url", nargs="?", help="Video link; prompted for when omitted")
    parser.add_argument("--format", dest="video_format", default=None, help="Output container: mp4, mkv, or webm")
    args = parser.parse_args()
    main(args.url, args.video_format)
