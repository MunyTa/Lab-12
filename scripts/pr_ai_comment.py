"""Публикует комментарий в PR: краткое описание diff через OpenAI или fallback."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


def git_diff(base: str, head: str, max_bytes: int = 14_000) -> str:
    out = subprocess.check_output(
        ["git", "diff", "--unified=1", f"{base}...{head}"],
        text=True,
        errors="replace",
    )
    if len(out) > max_bytes:
        return out[:max_bytes] + "\n…(truncated)"
    return out or "(пустой diff)"


def openai_summary(api_key: str, diff: str) -> str:
    payload = {
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты senior code reviewer. Кратко (до 180 слов) на русском: "
                    "что меняется в PR, риски, что проверить вручную."
                ),
            },
            {"role": "user", "content": f"Diff:\n{diff}"},
        ],
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    return str(data["choices"][0]["message"]["content"] or "").strip()


def post_github_comment(token: str, repo: str, pr_number: int, body: str) -> None:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    req = urllib.request.Request(
        url,
        data=json.dumps({"body": body}).encode(),
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        resp.read()


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ["GITHUB_REPOSITORY"]
    pr = int(os.environ["PR_NUMBER"])
    base = os.environ["BASE_SHA"]
    head = os.environ["HEAD_SHA"]
    api_key = os.environ.get("OPENAI_API_KEY", "")

    diff = git_diff(base, head)
    if api_key:
        try:
            summary = openai_summary(api_key, diff)
        except (urllib.error.URLError, OSError, KeyError, IndexError, ValueError) as e:
            summary = f"OpenAI недоступен или вернул неожиданный ответ: `{e}`\n\n```\n{diff}\n```"
    else:
        summary = (
            "**Секрет `OPENAI_API_KEY` не задан** — включите его в настройках репозитория "
            "для генерации текста через OpenAI. Ниже сырой diff (усечённо).\n\n"
            f"```\n{diff}\n```"
        )

    body = "## Автоматический комментарий (Lab 12, задание повышенной сложности №4)\n\n" + summary
    if not token:
        print("No GITHUB_TOKEN", file=sys.stderr)
        return 1
    post_github_comment(token, repo, pr, body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
