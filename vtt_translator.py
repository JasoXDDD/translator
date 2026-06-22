"""Translate a VTT file using extracted keyword context."""
import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional

from keyword_extractor import (
    DEFAULT_CONFIG_PATH,
    create_chat_completion,
    load_config,
    read_text_file,
)


def _replace_template_values(template: str, values: Dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template


def _load_api_key(config: Dict[str, Any], api_key: Optional[str]) -> str:
    openai_api_key = api_key or os.getenv(config.get("api_key_env", "OPENAI_API_KEY"))
    if not openai_api_key:
        raise RuntimeError(
            "No OpenAI API key set. Provide api_key or set "
            f"{config.get('api_key_env', 'OPENAI_API_KEY')} env var."
        )
    return openai_api_key


def load_keywords(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _keyword_entries(data: Any) -> Iterable[Dict[str, str]]:
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                keyword = item.get("keyword") or item.get("term") or item.get("phrase")
                info = item.get("info") or item.get("description") or item.get("meaning") or ""
                if keyword:
                    yield {"keyword": str(keyword), "info": str(info)}
            elif item:
                yield {"keyword": str(item), "info": ""}
    elif isinstance(data, dict):
        if data.get("keyword"):
            yield {
                "keyword": str(data["keyword"]),
                "info": str(data.get("info") or data.get("description") or data.get("meaning") or ""),
            }
        else:
            for keyword, info in data.items():
                if isinstance(info, dict):
                    info_text = info.get("info") or info.get("description") or info.get("meaning") or ""
                else:
                    info_text = info
                yield {"keyword": str(keyword), "info": str(info_text)}


def find_keywords_in_vtt(vtt_text: str, keywords_data: Any) -> List[Dict[str, str]]:
    """Return keyword entries whose keyword text appears in the VTT."""
    matches: List[Dict[str, str]] = []
    seen = set()
    for entry in _keyword_entries(keywords_data):
        keyword = entry["keyword"].strip()
        if not keyword:
            continue

        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        if pattern.search(vtt_text) and keyword.casefold() not in seen:
            matches.append(entry)
            seen.add(keyword.casefold())
    return matches


def format_keyword_context(entries: List[Dict[str, str]]) -> str:
    if not entries:
        return "No stored keywords were found in this VTT file."

    lines = []
    for entry in entries:
        info = entry["info"].strip() or "No extra information provided."
        lines.append(f"- {entry['keyword']}: {info}")
    return "\n".join(lines)


def _clean_vtt_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def translate_vtt_text(
    vtt_text: str,
    keyword_context: str,
    config_path: str = DEFAULT_CONFIG_PATH,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    target_language: Optional[str] = None,
) -> str:
    config = load_config(config_path)
    request_model = model or config["model"]
    request_base_url = base_url if base_url is not None else config.get("base_url")
    request_temperature = config["temperature"] if temperature is None else temperature
    request_max_tokens = config["max_tokens"] if max_tokens is None else max_tokens
    request_target_language = target_language or config["translation_target_language"]

    prompt = _replace_template_values(
        config["translation_prompt_template"],
        {
            "target_language": request_target_language,
            "keyword_context": keyword_context,
            "vtt_text": vtt_text,
        },
    )

    messages = [
        {"role": "system", "content": config["translation_system_message"]},
        {"role": "user", "content": prompt},
    ]

    content = create_chat_completion(
        api_key=_load_api_key(config, api_key),
        model=request_model,
        messages=messages,
        temperature=request_temperature,
        max_tokens=request_max_tokens,
        base_url=request_base_url,
    )
    return _clean_vtt_response(content)


def translate_vtt_file(
    vtt_path: str,
    keywords_path: Optional[str] = None,
    output_path: Optional[str] = None,
    config_path: str = DEFAULT_CONFIG_PATH,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    target_language: Optional[str] = None,
) -> str:
    config = load_config(config_path)
    vtt_text = read_text_file(vtt_path)
    keywords_data = load_keywords(keywords_path or config["keywords_output_path"])
    matching_keywords = find_keywords_in_vtt(vtt_text, keywords_data)
    keyword_context = format_keyword_context(matching_keywords)

    translated_vtt = translate_vtt_text(
        vtt_text,
        keyword_context,
        config_path=config_path,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        target_language=target_language,
    )

    save_path = output_path or config["translation_output_path"]
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(translated_vtt)
        if not translated_vtt.endswith("\n"):
            f.write("\n")

    return translated_vtt


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Translate a VTT file using stored keyword context")
    parser.add_argument("vtt_file", help="Path to the input .vtt file")
    parser.add_argument("--keywords", default=None, help="Path to extracted keywords JSON (overrides config)")
    parser.add_argument("--output", default=None, help="Path to save translated VTT (overrides config)")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to the JSON request config file")
    parser.add_argument("--target-language", default=None, help="Target language (overrides config)")
    parser.add_argument("--model", default=None, help="Model name to use (overrides config)")
    parser.add_argument("--api-key", default=None, help="OpenAI API key (overrides configured env var)")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible API base URL (overrides config)")
    parser.add_argument("--temperature", type=float, default=None, help="Sampling temperature (overrides config)")
    parser.add_argument("--max-tokens", type=int, default=None, help="Maximum output tokens (overrides config)")
    args = parser.parse_args()

    translate_vtt_file(
        args.vtt_file,
        keywords_path=args.keywords,
        output_path=args.output,
        config_path=args.config,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        target_language=args.target_language,
    )
    print(f"Saved translated VTT to {args.output or load_config(args.config)['translation_output_path']}")
