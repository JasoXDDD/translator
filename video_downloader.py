"""Interactively download a video using yt-dlp."""
import argparse
import shutil
import subprocess
from typing import Optional


SUPPORTED_VIDEO_FORMATS = {"mp4", "mkv", "webm"}
FORMAT_SORTS = {
    "mp4": "vcodec:h264,lang,quality,res,fps,hdr:12,acodec:aac",
}


def build_download_command(yt_dlp: str, url: str, video_format: Optional[str] = None) -> list[str]:
    command = [
        yt_dlp,
        "--format",
        "bestvideo*+bestaudio/best",
        "--output",
        "%(title)s.%(ext)s",
    ]
    if video_format:
        command.extend(
            [
                "--merge-output-format",
                video_format,
                "--remux-video",
                video_format,
            ]
        )
        format_sort = FORMAT_SORTS.get(video_format)
        if format_sort:
            command.extend(["--format-sort", format_sort])
    command.append(url)
    return command


def download_video(url: str, video_format: Optional[str] = None) -> None:
    """Download a video, optionally remuxing it into the requested container."""
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        raise RuntimeError("yt-dlp was not found. Install it with `python -m pip install yt-dlp`.")

    normalized_format = video_format.lower().lstrip(".") if video_format else None
    if normalized_format and normalized_format not in SUPPORTED_VIDEO_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_VIDEO_FORMATS))
        raise ValueError(f"Unsupported video format '{video_format}'. Choose one of: {supported}, or leave it blank.")

    subprocess.run(build_download_command(yt_dlp, url, normalized_format), check=True)


def main(url: Optional[str] = None, video_format: Optional[str] = None) -> None:
    requested_url = (url or input("Video link: ")).strip()
    if video_format is not None:
        requested_format = video_format.strip()
    elif url is None:
        requested_format = input("Expected video format (mp4, mkv, webm, or blank for default): ").strip()
    else:
        requested_format = ""

    if not requested_url:
        raise ValueError("A video link is required.")

    download_video(requested_url, requested_format or None)
    print("Video download completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a video using yt-dlp")
    parser.add_argument("url", nargs="?", help="Video link; prompted for when omitted")
    parser.add_argument("--format", dest="video_format", default=None, help="Optional output container: mp4, mkv, or webm")
    args = parser.parse_args()
    main(args.url, args.video_format)
