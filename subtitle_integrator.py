"""Add subtitles to a video using ffmpeg."""
import argparse
import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


TEXT_SUBTITLE_EXTENSIONS = {".ass", ".srt", ".ssa", ".vtt"}
MOV_TEXT_CONTAINERS = {".m4v", ".mov", ".mp4"}
TIMESTAMP_PATTERN = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3})(?P<settings>.*)$"
)
STYLE_COLOR_PATTERN = re.compile(
    r"::cue\(c\.([A-Za-z0-9_-]+)\)\s*\{\s*color:\s*([^;}\n]+)",
    re.IGNORECASE,
)
CLASS_TAG_PATTERN = re.compile(r"<c\.([A-Za-z0-9_-]+)>|</c>", re.IGNORECASE)
TAG_PATTERN = re.compile(r"<[^>]+>")
CSS_COLOR_NAMES = {
    "black": (0, 0, 0),
    "blue": (0, 0, 255),
    "cyan": (0, 255, 255),
    "gray": (128, 128, 128),
    "green": (0, 128, 0),
    "lime": (0, 255, 0),
    "magenta": (255, 0, 255),
    "red": (255, 0, 0),
    "silver": (192, 192, 192),
    "white": (255, 255, 255),
    "yellow": (255, 255, 0),
}


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


def _parse_css_color(value: str) -> Optional[tuple[int, int, int]]:
    color = value.strip().lower()
    rgb_match = re.fullmatch(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", color)
    if rgb_match:
        red, green, blue = (int(part) for part in rgb_match.groups())
        if all(0 <= channel <= 255 for channel in (red, green, blue)):
            return red, green, blue
        return None

    hex_match = re.fullmatch(r"#?([0-9a-f]{6})", color)
    if hex_match:
        raw = hex_match.group(1)
        return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)

    return CSS_COLOR_NAMES.get(color)


def _ass_color(rgb: tuple[int, int, int]) -> str:
    red, green, blue = rgb
    return f"&H{blue:02X}{green:02X}{red:02X}&"


def _extract_vtt_color_styles(vtt_text: str) -> dict[str, tuple[int, int, int]]:
    colors: dict[str, tuple[int, int, int]] = {}
    for class_name, raw_color in STYLE_COLOR_PATTERN.findall(vtt_text):
        parsed = _parse_css_color(raw_color)
        if parsed:
            colors[class_name] = parsed
    return colors


def _ass_timestamp(vtt_timestamp: str) -> str:
    hours, minutes, seconds = vtt_timestamp.split(":")
    whole_seconds, milliseconds = seconds.split(".")
    centiseconds = int(milliseconds[:2])
    return f"{int(hours)}:{minutes}:{whole_seconds}.{centiseconds:02d}"


def _ass_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")


def _vtt_text_to_ass(text: str, colors: dict[str, tuple[int, int, int]]) -> str:
    parts: list[str] = []
    cursor = 0

    for match in CLASS_TAG_PATTERN.finditer(text):
        parts.append(_ass_escape(html.unescape(TAG_PATTERN.sub("", text[cursor : match.start()]))))
        class_name = match.group(1)
        if class_name and class_name in colors:
            parts.append(r"{\c" + _ass_color(colors[class_name]) + "}")
        elif match.group(0).lower() == "</c>":
            parts.append(r"{\c&HFFFFFF&}")
        cursor = match.end()

    parts.append(_ass_escape(html.unescape(TAG_PATTERN.sub("", text[cursor:]))))
    return "".join(parts).strip()


def _vtt_to_ass(vtt_path: Path, ass_path: Path) -> bool:
    vtt_text = vtt_path.read_text(encoding="utf-8-sig")
    colors = _extract_vtt_color_styles(vtt_text)
    if not colors:
        return False

    lines = vtt_text.splitlines()
    events: list[tuple[str, str, str]] = []
    index = 0

    while index < len(lines):
        timestamp_match = TIMESTAMP_PATTERN.match(lines[index].strip())
        if not timestamp_match:
            index += 1
            continue

        cue_lines: list[str] = []
        index += 1
        while index < len(lines) and lines[index].strip():
            cue_lines.append(lines[index])
            index += 1

        text = _vtt_text_to_ass("\n".join(cue_lines), colors)
        if text:
            events.append(
                (
                    _ass_timestamp(timestamp_match.group("start")),
                    _ass_timestamp(timestamp_match.group("end")),
                    text,
                )
            )

    if not events:
        return False

    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.709",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,42,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,40,40,36,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    ass_lines.extend(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}" for start, end, text in events)
    ass_path.write_text("\n".join(ass_lines) + "\n", encoding="utf-8")
    return True


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
        with tempfile.TemporaryDirectory(prefix="subtitle_integrator_") as temp_dir:
            filter_subtitles = subtitles
            if subtitle_extension == ".vtt":
                ass_path = Path(temp_dir) / f"{subtitles.stem}.ass"
                if _vtt_to_ass(subtitles, ass_path):
                    filter_subtitles = ass_path

            command = [
                ffmpeg,
                replace_flag,
                "-i",
                str(source),
                "-vf",
                f"subtitles={_subtitle_filter_path(filter_subtitles)}",
                "-c:a",
                "copy",
                str(destination),
            ]
            subprocess.run(command, check=True)
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
