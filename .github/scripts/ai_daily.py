"""读取最近的 GitHub 公开动态，请 Claude（或 OpenAI）写一段 AI 日报，替换 README 里的标记区块。

只用 Python 标准库，无需 pip install。
"""

import datetime as dt
import json
import os
import re
import sys
import urllib.request

README = "README.md"
START, END = "<!--AI_DAILY_START-->", "<!--AI_DAILY_END-->"

PROMPT = """你是一个幽默但专业的 AI 助手，正在为开发者 {user} 的 GitHub 主页写「AI 日报」。
下面是 TA 最近的 GitHub 公开动态（JSON 摘要）：

{events}

请用中文写 2～3 句话：
1. 概括 TA 最近在忙什么（具体提到仓库名）；
2. 给一句俏皮的鼓励或观察。
如果动态为空，就写一句关于“今天适合写代码”的轻松短句。
只输出这几句话本身，不要标题，不要 Markdown 列表，总长度不超过 120 个汉字。"""


def http_json(url, headers=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def recent_events(user, token):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-daily"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    events = http_json(f"https://api.github.com/users/{user}/events/public?per_page=30", headers)
    out = []
    for e in events:
        item = {"type": e.get("type"), "repo": e.get("repo", {}).get("name"), "at": e.get("created_at")}
        p = e.get("payload", {})
        if e.get("type") == "PushEvent":
            item["commits"] = [c.get("message", "").splitlines()[0][:80] for c in p.get("commits", [])][:3]
        elif e.get("type") in ("PullRequestEvent", "IssuesEvent"):
            obj = p.get("pull_request") or p.get("issue") or {}
            item["action"] = p.get("action")
            item["title"] = (obj.get("title") or "")[:80]
        out.append(item)
    return out[:15]


def ask_claude(prompt, key, model):
    res = http_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        {"model": model, "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]},
    )
    return "".join(b.get("text", "") for b in res.get("content", []) if b.get("type") == "text"), "Claude"


def ask_openai(prompt, key, model):
    res = http_json(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {key}", "content-type": "application/json"},
        {"model": model, "messages": [{"role": "user", "content": prompt}]},
    )
    return res["choices"][0]["message"]["content"], "GPT"


def render_block(text, who):
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d")
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    body = "\n>\n".join(f"> {l}" for l in lines)
    return f"{START}\n> 🤖 **AI 日报 · {today}** · _由 {who} 生成_\n>\n{body}\n{END}"


def replace_block(readme, block):
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(readme):
        sys.exit(f"README 里没找到 {START} ... {END} 标记")
    return pattern.sub(lambda _: block, readme)


def main():
    user = os.environ.get("GH_USER", "")
    a_key, o_key = os.environ.get("ANTHROPIC_API_KEY"), os.environ.get("OPENAI_API_KEY")
    o_model = os.environ.get("OPENAI_MODEL")
    if not a_key and not (o_key and o_model):
        print("没有配置 ANTHROPIC_API_KEY（或 OPENAI_API_KEY + OPENAI_MODEL），跳过。")
        return

    events = recent_events(user, os.environ.get("GITHUB_TOKEN"))
    prompt = PROMPT.format(user=user, events=json.dumps(events, ensure_ascii=False, indent=1))
    if a_key:
        text, who = ask_claude(prompt, a_key, os.environ.get("CLAUDE_MODEL") or "claude-haiku-5-5")
    else:
        text, who = ask_openai(prompt, o_key, o_model)

    with open(README, encoding="utf-8") as f:
        readme = f.read()
    new = replace_block(readme, render_block(text, who))
    if new != readme:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("README 已更新")


if __name__ == "__main__":
    main()
