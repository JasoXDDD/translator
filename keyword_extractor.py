"""keywords_extractor

Module to read a text file and send its contents to an OpenAI-style LLM
to extract important keywords and relevant information.

Usage example:
from translator.keywords_extractor import extract_keywords_from_file
results = extract_keywords_from_file("example.txt")
"""
import os
import json
from typing import Any, Dict, Optional

try:
    import openai
except Exception:  # pragma: no cover - graceful fallback when openai not installed
    openai = None


DEFAULT_CONFIG_PATH = "keyword_extractor_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "model": "gpt-4o-mini",
    "temperature": 0.0,
    "max_tokens": 1500,
    "api_key_env": "OPENAI_API_KEY",
    "base_url": "",
    "keywords_output_path": "keywords.json",
    "translation_target_language": "English",
    "translation_output_path": "translated.vtt",
    "transcription_model": "whisper-1",
    "system_message": "You are a helpful extraction assistant.",
    "prompt_template": (
        "You are an extraction assistant. Read the provided text and extract the "
        "most important keywords or short phrases. For each extracted keyword, "
        "include a short `info` field describing the relevant information found "
        "in the text about that keyword. Return ONLY valid JSON: a top-level array "
        "of objects, each object containing at least the keys `keyword` and `info`. "
        "Example output format:\n"
        "[ {\n  \"keyword\": \"Topic A\",\n  \"info\": \"Relevant details about Topic A extracted from the text.\"\n}, ... ]\n"
        "Do not add any extra prose or explanation outside the JSON.\n\n"
        "TEXT:\n{text}"
    ),
    "translation_system_message": "You are a careful subtitle translator.",
    "translation_prompt_template": (
        "Translate the WEBVTT subtitles into {target_language}.\n"
        "Preserve the WEBVTT format exactly: keep cue timings, cue identifiers, "
        "blank lines, NOTE/STYLE/REGION blocks, and tags. Translate only human "
        "readable subtitle text.\n\n"
        "Use this keyword context where relevant. Keep translations consistent "
        "with the provided meanings:\n{keyword_context}\n\n"
        "Return ONLY the translated WEBVTT file content, with no explanation.\n\n"
        "WEBVTT INPUT:\n{vtt_text}"
    ),
}


ENV_CONFIG_OVERRIDES = {
    "TRANSLATOR_MODEL": ("model", str),
    "TRANSLATOR_TEMPERATURE": ("temperature", float),
    "TRANSLATOR_MAX_TOKENS": ("max_tokens", int),
    "TRANSLATOR_API_KEY_ENV": ("api_key_env", str),
    "TRANSLATOR_BASE_URL": ("base_url", str),
    "TRANSLATOR_KEYWORDS_OUTPUT_PATH": ("keywords_output_path", str),
    "TRANSLATOR_TARGET_LANGUAGE": ("translation_target_language", str),
    "TRANSLATOR_TRANSLATION_OUTPUT_PATH": ("translation_output_path", str),
    "TRANSLATOR_TRANSCRIPTION_MODEL": ("transcription_model", str),
}


def _apply_environment_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    for env_name, (config_key, parser) in ENV_CONFIG_OVERRIDES.items():
        raw_value = os.getenv(env_name)
        if raw_value is None:
            continue

        try:
            config[config_key] = parser(raw_value)
        except ValueError as exc:
            raise ValueError(f"Invalid value for {env_name}: {raw_value!r}") from exc

    return config


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load request configuration from a JSON file.

    Missing config values are filled from DEFAULT_CONFIG so old config files can
    keep working as new options are added.
    """
    config = DEFAULT_CONFIG.copy()

    if not os.path.exists(config_path):
        return _apply_environment_overrides(config)

    with open(config_path, "r", encoding="utf-8") as f:
        file_config = json.load(f)

    if not isinstance(file_config, dict):
        raise ValueError(f"Config file must contain a JSON object: {config_path}")

    config.update(file_config)
    return _apply_environment_overrides(config)


def read_text_file(path: str, encoding: str = "utf-8") -> str:
    """Read and return the contents of a text file."""
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def save_result_to_file(result: Any, path: str) -> None:
    """Save an LLM result as JSON when possible, otherwise as plain text."""
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(result, (dict, list)):
            json.dump(result, f, indent=2, ensure_ascii=False)
            f.write("\n")
        else:
            f.write(str(result))
            if not str(result).endswith("\n"):
                f.write("\n")


def build_prompt(file_text: str, prompt_template: Optional[str] = None) -> str:
    """Build the instruction prompt to send to the LLM.

    The LLM is asked to return strictly parseable JSON: an array of objects
    with at minimum the keys `keyword` and `info`.
    """
    template = prompt_template or DEFAULT_CONFIG["prompt_template"]
    return template.replace("{text}", file_text)


def _extract_json_from_text(text: str) -> Any:
    """Try to locate a JSON structure in `text` and parse it.

    This helps handle cases where the LLM wraps the JSON in backticks or adds
    leading/trailing commentary.
    """
    text = text.strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to find the first JSON array/object in the text
    for open_b, close_b in (("[", "]"), ("{", "}")):
        if open_b in text and close_b in text:
            start = text.find(open_b)
            end = text.rfind(close_b)
            if start != -1 and end != -1 and end > start:
                candidate = text[start : end + 1]
                try:
                    return json.loads(candidate)
                except Exception:
                    continue

    # As a last resort, try to extract content between ```json and ```
    marker = "```json"
    if marker in text:
        start = text.find(marker) + len(marker)
        end = text.find("```", start)
        if end != -1:
            candidate = text[start:end].strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass

    # If we can't parse JSON, return the raw text to allow the caller to decide
    return text


def create_chat_completion(
    api_key: str,
    model: str,
    messages: Any,
    temperature: float,
    max_tokens: int,
    base_url: Optional[str] = None,
) -> str:
    """Create a chat completion with either the current or legacy OpenAI client."""
    if openai is None:
        raise RuntimeError("openai package not installed; install with `pip install openai`")

    normalized_base_url = base_url.strip() if base_url else None

    if hasattr(openai, "OpenAI"):
        client_kwargs = {"api_key": api_key}
        if normalized_base_url:
            client_kwargs["base_url"] = normalized_base_url
        client = openai.OpenAI(**client_kwargs)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content

    openai.api_key = api_key
    if normalized_base_url:
        openai.api_base = normalized_base_url
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp["choices"][0]["message"]["content"]


def extract_keywords_from_text(
    text: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    config_path: str = DEFAULT_CONFIG_PATH,
) -> Any:
    """Send `text` to an OpenAI-style LLM and return parsed JSON results.

    Requires the `openai` package and `OPENAI_API_KEY` env var or an explicit
    `api_key` argument.
    """
    config = load_config(config_path)
    request_model = model or config["model"]
    request_base_url = base_url if base_url is not None else config.get("base_url")
    request_temperature = config["temperature"] if temperature is None else temperature
    request_max_tokens = config["max_tokens"] if max_tokens is None else max_tokens

    prompt = build_prompt(text, config.get("prompt_template"))

    if openai is None:
        raise RuntimeError("openai package not installed; install with `pip install openai`")

    openai_api_key = api_key or os.getenv(config.get("api_key_env", "OPENAI_API_KEY"))
    if not openai_api_key:
        raise RuntimeError(
            "No OpenAI API key set. Provide api_key or set "
            f"{config.get('api_key_env', 'OPENAI_API_KEY')} env var."
        )

    messages = [
        {"role": "system", "content": config["system_message"]},
        {"role": "user", "content": prompt},
    ]

    content = create_chat_completion(
        api_key=openai_api_key,
        model=request_model,
        messages=messages,
        temperature=request_temperature,
        max_tokens=request_max_tokens,
        base_url=request_base_url,
    )

    parsed = _extract_json_from_text(content)
    return parsed


def extract_keywords_from_file(
    path: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    config_path: str = DEFAULT_CONFIG_PATH,
    output_path: Optional[str] = None,
) -> Any:
    """Read a text file, extract keywords by the LLM, and save the results."""
    text = read_text_file(path)
    result = extract_keywords_from_text(
        text,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        config_path=config_path,
    )
    save_path = output_path
    if save_path is None:
        save_path = load_config(config_path).get("keywords_output_path")
    if save_path:
        save_result_to_file(result, save_path)
    return result


if __name__ == "__main__":  # pragma: no cover - simple manual run
    import argparse

    parser = argparse.ArgumentParser(description="Extract keywords from a text file using an OpenAI-style LLM")
    parser.add_argument("file", help="Path to the input .txt file")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to the JSON request config file")
    parser.add_argument("--model", default=None, help="Model name to use (overrides config)")
    parser.add_argument("--api-key", default=None, help="OpenAI API key (overrides OPENAI_API_KEY env var)")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible API base URL (overrides config)")
    parser.add_argument("--temperature", type=float, default=None, help="Sampling temperature (overrides config)")
    parser.add_argument("--max-tokens", type=int, default=None, help="Maximum output tokens (overrides config)")
    parser.add_argument("--output", default=None, help="Path to save extracted keywords (overrides config)")
    parser.add_argument("--no-save", action="store_true", help="Print the result without saving it")
    args = parser.parse_args()

    out = extract_keywords_from_file(
        args.file,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        config_path=args.config,
        output_path="" if args.no_save else args.output,
    )
    # Print nicely if it's JSON-like
    try:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    except Exception:
        print(out)
