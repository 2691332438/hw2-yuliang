#!/usr/bin/env python3
"""Generate onboarding follow-up emails from rough HR notes."""

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


DEFAULT_MODEL = "gemini-2.5-flash"

PROMPTS: Dict[str, str] = {
    "v1": textwrap.dedent(
        """
        You are a business writing assistant.
        Write a professional onboarding follow-up email from the notes below.
        Return only the email.
        """
    ).strip(),
    "v2": textwrap.dedent(
        """
        You are a business writing assistant helping HR teams draft onboarding follow-up emails.

        Requirements:
        - Include a subject line.
        - Greet the employee by name.
        - Include the important logistics from the notes.
        - Keep the tone warm and professional.
        - Do not invent facts.

        Return only the finished email.
        """
    ).strip(),
    "v3": textwrap.dedent(
        """
        You are a business writing assistant helping HR teams turn rough notes into polished onboarding emails.

        Write a complete onboarding follow-up email from the notes below.

        Requirements:
        - Start with `Subject: ...`
        - Use the employee's name in the greeting.
        - Include every concrete logistical detail that appears in the notes.
        - Use plain, professional business English.
        - Do not guess or add placeholders.
        - End with a short offer to answer questions.

        Return only the finished email with no commentary.
        """
    ).strip(),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default="eval_set.json")
    parser.add_argument("--case-id")
    parser.add_argument("--prompt-version", choices=sorted(PROMPTS.keys()), default="v3")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_cases(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Evaluation set must be a list of cases.")
    return data


def build_user_prompt(case: Dict[str, Any]) -> str:
    return (
        f"CASE ID: {case['id']}\n"
        "TASK: Draft an onboarding follow-up email for a new employee.\n\n"
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


def save_output(output_dir: Path, case_id: str, prompt_version: str, model: str, response: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{case_id}_{prompt_version}.json"
    payload = {
        "case_id": case_id,
        "prompt_version": prompt_version,
        "model": model,
        "response": response,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    cases = load_cases(args.eval_set)
    if args.case_id:
        cases = [case for case in cases if case["id"] == args.case_id]
        if not cases:
            print(f"No case found for id {args.case_id}", file=sys.stderr)
            return 1

    system_prompt = PROMPTS[args.prompt_version]
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not args.dry_run and not api_key:
        print("Missing GEMINI_API_KEY or GOOGLE_API_KEY.", file=sys.stderr)
        return 1

    for case in cases:
        user_prompt = build_user_prompt(case)
        if args.dry_run:
            print("=" * 80)
            print(f"CASE: {case['id']}")
            print("SYSTEM PROMPT:")
            print(system_prompt)
            print("\nUSER PROMPT:")
            print(user_prompt)
            continue

        response = call_gemini(api_key, args.model, system_prompt, user_prompt)
        save_output(Path(args.output_dir), case["id"], args.prompt_version, args.model, response)
        print(f"Saved output for {case['id']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
