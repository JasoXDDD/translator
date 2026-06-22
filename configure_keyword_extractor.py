"""Interactive editor for keyword_extractor_config.json."""
import json
from typing import Any, Callable, Dict

from keyword_extractor import DEFAULT_CONFIG, DEFAULT_CONFIG_PATH, load_config


def _prompt_value(label: str, current: Any, parser: Callable[[str], Any] = str) -> Any:
    """Prompt for a config value, keeping the current value on blank input."""
    raw = input(f"{label} [{current}]: ").strip()
    if not raw:
        return current

    try:
        return parser(raw)
    except ValueError as exc:
        print(f"Invalid value: {exc}")
        return _prompt_value(label, current, parser)


def _prompt_multiline(label: str, current: str) -> str:
    """Prompt for multiline text, ending input with a line containing only END."""
    print(f"\n{label}")
    print("Current value:")
    print(current)
    print("\nEnter a new value. Finish with a line containing only END.")
    print("Press Enter immediately to keep the current value.")

    first_line = input("> ")
    if not first_line:
        return current

    lines = [first_line]
    while True:
        line = input("> ")
        if line == "END":
            break
        lines.append(line)

    return "\n".join(lines)


def _parse_float(raw: str) -> float:
    value = float(raw)
    if value < 0:
        raise ValueError("must be zero or greater")
    return value


def _parse_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise ValueError("must be greater than zero")
    return value


def edit_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Prompt the user for config values and save the JSON config file."""
    config = load_config(config_path)

    print(f"Editing request config: {config_path}")
    print("Press Enter to keep the current value.\n")

    config["model"] = _prompt_value("Model", config["model"])
    config["temperature"] = _prompt_value("Temperature", config["temperature"], _parse_float)
    config["max_tokens"] = _prompt_value("Max tokens", config["max_tokens"], _parse_int)
    config["api_key_env"] = _prompt_value("API key environment variable", config["api_key_env"])
    config["base_url"] = _prompt_value("API base URL", config["base_url"])
    config["keywords_output_path"] = _prompt_value("Keywords output path", config["keywords_output_path"])
    config["translation_target_language"] = _prompt_value(
        "Translation target language",
        config["translation_target_language"],
    )
    config["translation_output_path"] = _prompt_value("Translation output path", config["translation_output_path"])
    config["transcription_model"] = _prompt_value("Audio transcription model", config["transcription_model"])
    config["system_message"] = _prompt_multiline("System message", config["system_message"])
    config["prompt_template"] = _prompt_multiline("Prompt template", config["prompt_template"])
    config["translation_system_message"] = _prompt_multiline(
        "Translation system message",
        config["translation_system_message"],
    )
    config["translation_prompt_template"] = _prompt_multiline(
        "Translation prompt template",
        config["translation_prompt_template"],
    )

    if "{text}" not in config["prompt_template"]:
        print("\nThe prompt template must include {text}; adding it at the end.")
        config["prompt_template"] = config["prompt_template"].rstrip() + "\n\nTEXT:\n{text}"

    required_translation_placeholders = ("{target_language}", "{keyword_context}", "{vtt_text}")
    missing_placeholders = [
        placeholder
        for placeholder in required_translation_placeholders
        if placeholder not in config["translation_prompt_template"]
    ]
    if missing_placeholders:
        print("\nThe translation prompt is missing required placeholders; adding them at the end.")
        config["translation_prompt_template"] = (
            config["translation_prompt_template"].rstrip()
            + "\n\nTarget language: {target_language}\n\nKeyword context:\n{keyword_context}\n\nWEBVTT INPUT:\n{vtt_text}"
        )

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return config


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create or edit the keyword extractor request config")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to the JSON request config file")
    args = parser.parse_args()

    saved = edit_config(args.config)
    print(f"\nSaved {args.config}")
    print(json.dumps({key: saved[key] for key in DEFAULT_CONFIG}, indent=2, ensure_ascii=False))
