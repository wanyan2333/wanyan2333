"""Render a neofetch-style terminal card (dark + light SVG) from live GitHub stats.

Usage:
  python .github/scripts/neofetch_card.py            # needs GITHUB_TOKEN + GH_USER
  python .github/scripts/neofetch_card.py --mock     # sample data, for local preview

Standard library only. Edit PROFILE below to change the static lines.
"""

import datetime as dt
import html
import json
import os
import sys
import urllib.request
from collections import Counter

OUT_DIR = "assets"

PROFILE = {
    "Role": "AI x Web x IoT Developer",
    "Focus": "RAG, LLM apps, full-stack web, IoT, games",
    "AI.Stack": "Claude, GPT, Copilot, Cursor",
    "Editor": "VS Code",
    "Motto": "Prompt -> Code -> Ship",
}

ART_DIR = "assets/art"

QUERY = """
query($login: String!) {
  user(login: $login) {
    login name createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100, isFork: false) {
      totalCount
      nodes { stargazerCount forkCount languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
    contributionsCollection {
      totalCommitContributions totalPullRequestContributions totalIssueContributions
      contributionCalendar { totalContributions }
    }
  }
}"""


def fetch(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "neofetch-card"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    u = data["data"]["user"]
    repos = u["repositories"]["nodes"]
    langs = Counter()
    for r in repos:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]
    cc = u["contributionsCollection"]
    return {
        "login": u["login"],
        "created": u["createdAt"][:10],
        "followers": u["followers"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "forks": sum(r["forkCount"] for r in repos),
        "langs": [n for n, _ in langs.most_common(4)],
        "commits": cc["totalCommitContributions"],
        "prs": cc["totalPullRequestContributions"],
        "issues": cc["totalIssueContributions"],
        "contrib": cc["contributionCalendar"]["totalContributions"],
    }


def mock():
    return {"login": "wanyan2333", "created": "2023-02-10", "followers": 12, "repos": 9, "stars": 23, "forks": 4,
            "langs": ["TypeScript", "Python", "JavaScript", "C++"], "commits": 412, "prs": 37, "issues": 15, "contrib": 538}


def uptime(created):
    start = dt.date.fromisoformat(created)
    today = dt.date.today()
    months = (today.year - start.year) * 12 + today.month - start.month - (today.day < start.day)
    y, m = divmod(max(months, 0), 12)
    anchor = start.replace(year=start.year + y)
    mm = anchor.month + m
    anchor = anchor.replace(year=anchor.year + (mm - 1) // 12, month=(mm - 1) % 12 + 1, day=min(start.day, 28))
    d = (today - anchor).days
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(y, 'year')}, {plural(m, 'month')}, {plural(d, 'day')}"


THEMES = {
    "dark": dict(bg="#0d1117", bar="#161b22", border="#30363d", fg="#c9d1d9", key="#ffa657", dots="#484f58",
                 val="#a5d6ff", head="#ff7a9c", mute="#8b949e", prompt="#ff8a3d", light=False),
    "light": dict(bg="#ffffff", bar="#f6f8fa", border="#d0d7de", fg="#24292f", key="#953800", dots="#afb8c1",
                  val="#0a3069", head="#d6336c", mute="#57606a", prompt="#e8590c", light=True),
}

W, LH, FS = 985, 20, 14
CHAR_W = FS * 0.6
ART_X, INFO_X, TOP = 22, 360, 74
INFO_COLS = 56


def build_lines(s):
    rows = [("head", f"{s['login']}@github"), ("rule", "-" * len(s["login"] + "@github"))]
    kv = [
        ("OS", f"GitHub, member since {s['created'][:4]}"),
        ("Uptime", uptime(s["created"])),
        ("Role", PROFILE["Role"]),
        ("Focus", PROFILE["Focus"]),
        ("", ""),
        ("Languages.Top", ", ".join(s["langs"]) or "n/a"),
        ("AI.Stack", PROFILE["AI.Stack"]),
        ("Editor", PROFILE["Editor"]),
        ("", ""),
        ("Repos", f"{s['repos']}  |  Stars: {s['stars']}  |  Forks: {s['forks']}"),
        ("Followers", str(s["followers"])),
        ("Commits (1y)", f"{s['commits']}  |  PRs: {s['prs']}  |  Issues: {s['issues']}"),
        ("Contributions", f"{s['contrib']} in the last year"),
        ("Motto", PROFILE["Motto"]),
    ]
    for k, v in kv:
        rows.append(("blank", "") if not k else ("kv", (k, v)))
    return rows


def art_svg(t, x0, y0, w, h, delay):
    """Avatar portrait as full-colour LED-style dots, revealed top-to-bottom.

    assets/art/avatar-color.txt: first line is the palette (hex colours), then one
    row per line where each character indexes the palette and "." is empty.
    """
    lines = open(f"{ART_DIR}/avatar-color.txt", encoding="utf-8").read().split("\n")
    palette, rows = lines[0].split(), lines[1:]
    palette = [shade(c) if t["light"] else brighten(c) for c in palette]
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    sx, sy = 3.6, 4.3
    ox = x0 + (w - len(rows[0]) * sx) / 2 + sx / 2
    oy = y0 + (h - len(rows) * sy) / 2 + sy / 2
    out = []
    for r, line in enumerate(rows):
        d = f'style="animation-delay:{delay + r * 0.02:.3f}s"'
        for i, colour in enumerate(palette):
            pts = "".join(f"M{ox + c * sx:.1f} {oy + r * sy:.1f}h0" for c, v in enumerate(line) if v == chars[i])
            if pts:
                out.append(f'<path class="l" {d} d="{pts}" stroke="{colour}" stroke-width="3.3" stroke-linecap="round"/>')
    return out


def brighten(hex_colour):
    """Lift colours a little on the dark card: dots with gaps read darker than solid fills."""
    import colorsys
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v < 0.3:  # keep eyes / ribbon dark
        return hex_colour
    r, g, b = colorsys.hsv_to_rgb(h, min(1, s * 1.08), min(1, v * 1.18 + 0.04))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def shade(hex_colour):
    """Darken very light colours a touch so they still read on a white card."""
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    if 0.299 * r + 0.587 * g + 0.114 * b > 200:
        r, g, b = (round(v * 0.9) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def svg(s, theme):
    t = THEMES[theme]
    e = html.escape
    rows = build_lines(s)
    H = TOP + (len(rows) + 2) * LH + 48
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,Liberation Mono,monospace" font-size="{FS}">',
           "<style>",
           ".l{opacity:0;animation:in .35s ease-out forwards}",
           "@keyframes in{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}",
           ".cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}",
           ".typed{clip-path:inset(0 100% 0 0);animation:type 1.1s steps(16) .2s forwards}",
           "@keyframes type{to{clip-path:inset(0 0 0 0)}}",
           "@media (prefers-reduced-motion:reduce){.l,.typed{animation:none;opacity:1;clip-path:none}.cur{animation:none}}",
           "</style>",
           f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
           f'<path d="M.5 12.5a12 12 0 0 1 12-12h{W-25}a12 12 0 0 1 12 12V36H.5z" fill="{t["bar"]}"/>',
           f'<line x1="0" y1="36" x2="{W}" y2="36" stroke="{t["border"]}"/>']
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{22 + i * 20}" cy="18" r="6" fill="{c}"/>')
    out.append(f'<text x="{W/2}" y="23" text-anchor="middle" fill="{t["mute"]}" font-size="13">{e(s["login"])}@github: ~</text>')

    # prompt line with typing effect
    y = 60
    out.append(f'<text x="{ART_X}" y="{y}" fill="{t["prompt"]}">{e(s["login"])}@github<tspan fill="{t["mute"]}">:</tspan>'
               f'<tspan fill="{t["val"]}">~</tspan><tspan fill="{t["mute"]}">$ </tspan>'
               f'<tspan fill="{t["fg"]}" class="typed">neofetch --ai</tspan></text>')

    # portrait
    out += art_svg(t, ART_X, TOP - 4, INFO_X - ART_X - 24, (len(rows) + 1) * LH, 1.2)

    # info lines
    for i, (kind, val) in enumerate(rows):
        yy = TOP + 14 + i * LH
        d = f'style="animation-delay:{1.4 + i*0.09:.2f}s"'
        if kind == "head":
            out.append(f'<text class="l" {d} x="{INFO_X}" y="{yy}" fill="{t["head"]}" font-weight="700">{e(val)}</text>')
        elif kind == "rule":
            out.append(f'<text class="l" {d} x="{INFO_X}" y="{yy}" fill="{t["mute"]}">{e(val)}</text>')
        elif kind == "kv":
            k, v = val
            dots = "." * max(2, INFO_COLS - len(k) - len(v) - 3)
            out.append(f'<text class="l" {d} x="{INFO_X}" y="{yy}" xml:space="preserve"><tspan fill="{t["key"]}">{e(k)}</tspan>'
                       f'<tspan fill="{t["mute"]}">:</tspan> <tspan fill="{t["dots"]}">{dots}</tspan> '
                       f'<tspan fill="{t["val"]}">{e(v)}</tspan></text>')

    # palette blocks
    by = TOP + 14 + (len(rows) + 1) * LH - 12
    pal = ["#484f58", "#ff7b72", "#7ee787", "#ffa657", "#79c0ff", "#d2a8ff", "#a5d6ff", "#f0f6fc"]
    for i, c in enumerate(pal):
        out.append(f'<rect class="l" style="animation-delay:{1.4 + len(rows)*0.09:.2f}s" x="{INFO_X + i*26}" y="{by}" width="24" height="16" fill="{c}"/>')

    # final prompt with cursor
    fy = H - 22
    out.append(f'<text x="{ART_X}" y="{fy}" fill="{t["prompt"]}">{e(s["login"])}@github<tspan fill="{t["mute"]}">:</tspan>'
               f'<tspan fill="{t["val"]}">~</tspan><tspan fill="{t["mute"]}">$ </tspan></text>')
    cx = ART_X + (len(s["login"]) + len("@github:~$ ")) * CHAR_W
    out.append(f'<rect class="cur" x="{cx:.1f}" y="{fy - 13}" width="{CHAR_W:.1f}" height="17" fill="{t["fg"]}"/>')
    upd = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out.append(f'<text x="{W - 22}" y="{fy}" text-anchor="end" fill="{t["mute"]}" font-size="11">updated {upd}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    if "--mock" in sys.argv:
        stats = mock()
    else:
        user, token = os.environ.get("GH_USER"), os.environ.get("GITHUB_TOKEN")
        if not user or not token:
            sys.exit("GH_USER and GITHUB_TOKEN are required (or pass --mock)")
        stats = fetch(user, token)
    os.makedirs(OUT_DIR, exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(OUT_DIR, f"neofetch-{theme}.svg"), "w", encoding="utf-8") as f:
            f.write(svg(stats, theme))
    print("wrote", ", ".join(f"{OUT_DIR}/neofetch-{t}.svg" for t in THEMES), json.dumps(stats))
    if "--mock" not in sys.argv:
        bust_readme_cache()


def bust_readme_cache():
    """Give the card URLs in README a fresh ?v= so GitHub's image cache shows the new card."""
    import re, time
    with open("README.md", encoding="utf-8") as f:
        readme = f.read()
    new = re.sub(r"(assets/neofetch-(?:dark|light)\.svg)(\?v=\d+)?", rf"\g<1>?v={int(time.time())}", readme)
    if new != readme:
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new)


if __name__ == "__main__":
    main()
