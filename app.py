#!/usr/bin/env python3
"""Generate stakeholder updates from rough data analysis notes."""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_PROVIDER = "groq"
DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
}

PROMPTS: Dict[str, str] = {
    "v1": textwrap.dedent(
        """
        You are a business writing assistant.
        Write a short stakeholder update from the notes below.
        Return only the finished update.
        """
    ).strip(),
    "v2": textwrap.dedent(
        """
        You are a business writing assistant helping data analysts summarize findings for business stakeholders.

        Requirements:
        - Write a concise stakeholder update.
        - Include the main metrics, trends, and risks from the notes.
        - Use clear business language for a non-technical audience.
        - Do not invent facts.
        - End with a simple recommendation or next step if one is provided.

        Return only the finished update.
        """
    ).strip(),
    "v3": textwrap.dedent(
        """
        You are a business writing assistant helping data analysts turn rough findings into polished stakeholder updates.

        Write a complete stakeholder update from the notes below.

        Requirements:
        - Start with `Subject: ...`
        - Write for a business audience, not a technical audience.
        - Include the most important metrics, trends, anomalies, risks, and recommendations that appear in the notes.
        - Use plain, professional business English.
        - Do not guess, exaggerate, or add unsupported conclusions.
        - If the notes mention data quality issues or limitations, include them clearly.
        - Keep the output concise and readable as an email or written update.

        Return only the finished update with no commentary.
        """
    ).strip(),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default="eval_set.json")
    parser.add_argument("--case-id")
    parser.add_argument("--prompt-version", choices=sorted(PROMPTS.keys()), default="v3")
    parser.add_argument("--provider", choices=["gemini", "groq"], default=DEFAULT_PROVIDER)
    parser.add_argument("--model")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_cases(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Evaluation set must be a list of cases.")
    return data


def normalize_api_key(value: str | None, env_name: str) -> str | None:
    if value is None:
        return None
    cleaned = (
        value.strip()
        .replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\ufeff", "")
        .replace("“", "")
        .replace("”", "")
        .replace("‘", "")
        .replace("’", "")
    )
    try:
        cleaned.encode("ascii")
    except UnicodeEncodeError as exc:
        raise RuntimeError(
            f"{env_name} contains non-ASCII characters. Re-copy the key and export it again."
        ) from exc
    return cleaned


def build_user_prompt(case: Dict[str, Any]) -> str:
    return (
        f"CASE ID: {case['id']}\n"
        "TASK: Summarize data analysis findings into a stakeholder update.\n\n"
        "NOTES:\n"
        f"{case['notes'].strip()}"
    )


def call_gemini(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.3, "topP": 0.9},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error calling Gemini API: {exc}") from exc

    candidates = parsed.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"No candidates returned: {parsed}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [part.get("text", "") for part in parts if "text" in part]
    if not text_parts:
        raise RuntimeError(f"No text returned: {parsed}")
    return "\n".join(text_parts).strip()


def call_groq(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Groq API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error calling Groq API: {exc}") from exc

    choices = parsed.get("choices") or []
    if not choices:
        raise RuntimeError(f"No choices returned: {parsed}")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not content:
        raise RuntimeError(f"No text returned: {parsed}")
    return content.strip()


def save_output(
    output_dir: Path,
    case: Dict[str, Any],
    prompt_version: str,
    model: str,
    response: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{case['id']}_{prompt_version}.json"
    payload = {
        "case_id": case["id"],
        "case_type": case.get("case_type"),
        "prompt_version": prompt_version,
        "model": model,
        "task": case.get("task"),
        "good_output_should_do": case.get("good_output_should_do"),
        "response": response,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    cases = load_cases(args.eval_set)
    if args.case_id:
        cases = [case for case in cases if case["id"] == args.case_id]
        if not cases:
            print(f"No case found for id {args.case_id}", file=sys.stderr)
            return 1

    system_prompt = PROMPTS[args.prompt_version]
    model = args.model or DEFAULT_MODELS[args.provider]

    if args.provider == "gemini":
        api_key = normalize_api_key(
            os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "GEMINI_API_KEY/GOOGLE_API_KEY",
        )
    else:
        api_key = normalize_api_key(os.getenv("GROQ_API_KEY"), "GROQ_API_KEY")

    if not args.dry_run and not api_key:
        if args.provider == "gemini":
            print("Missing GEMINI_API_KEY or GOOGLE_API_KEY.", file=sys.stderr)
        else:
            print("Missing GROQ_API_KEY.", file=sys.stderr)
        return 1

    for case in cases:
        user_prompt = build_user_prompt(case)
        if args.dry_run:
            print("=" * 80)
            print(f"CASE: {case['id']}")
            print(f"CASE TYPE: {case.get('case_type', 'unknown')}")
            print(f"PROVIDER: {args.provider}")
            print(f"MODEL: {model}")
            print("SYSTEM PROMPT:")
            print(system_prompt)
            print("\nUSER PROMPT:")
            print(user_prompt)
            continue

        if args.provider == "gemini":
            response = call_gemini(api_key, model, system_prompt, user_prompt)
        else:
            response = call_groq(api_key, model, system_prompt, user_prompt)
        output_path = save_output(
            Path(args.output_dir),
            case,
            args.prompt_version,
            model,
            response,
        )
        print("=" * 80)
        print(f"CASE: {case['id']}")
        print(f"CASE TYPE: {case.get('case_type', 'unknown')}")
        print(f"PROVIDER: {args.provider}")
        print(f"MODEL: {model}")
        print("GENERATED UPDATE:")
        print(response)
        print(f"\nSAVED TO: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
