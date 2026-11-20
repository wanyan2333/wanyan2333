"""Issue-driven Connect Four for the profile README.

A visitor clicks a column link -> opens an issue titled "c4|drop|<1-7>" (or "c4|new").
The workflow runs this script, which updates the game state, redraws the board
(dark + light SVG, last piece animated), rewrites the README section, then
comments on and closes the issue.

Local test:  python .github/scripts/connect4.py --local "c4|drop|4" someuser
Init:        python .github/scripts/connect4.py --init
"""

import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

ROWS, COLS = 6, 7
DIR = "assets/c4"
STATE = f"{DIR}/state.json"
README = "README.md"
START, END = "<!--C4_START-->", "<!--C4_END-->"
NAMES = {1: "Purple", 2: "Green"}
REPO = os.environ.get("GITHUB_REPOSITORY", "wanyan2333/wanyan2333")
RAW = f"https://raw.githubusercontent.com/{REPO}/main"

THEMES = {
    "dark": dict(board="#161b22", edge="#30363d", hole="#0d1117", p1="#a371f7", p2="#3fb950", ring="#f0f6fc", btn="#8b949e", btnoff="#30363d"),
    "light": dict(board="#f6f8fa", edge="#d0d7de", hole="#ffffff", p1="#8250df", p2="#1a7f37", ring="#24292f", btn="#57606a", btnoff="#d0d7de"),
}
CELL, PAD = 56, 12
W, H = COLS * CELL + PAD * 2, ROWS * CELL + PAD * 2


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def new_state(prev=None):
    s = {"board": [[0] * COLS for _ in range(ROWS)], "turn": 1, "moves": [], "status": "playing", "win": [],
         "game": 1, "history": [], "players": {}}
    if prev:
        s.update(game=prev["game"] + 1, history=prev["history"], players=prev["players"])
    return s


def load():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return new_state()


def save(s):
    os.makedirs(DIR, exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=1)


def winner_cells(b, r, c):
    p = b[r][c]
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        cells = [(r, c)]
        for sign in (1, -1):
            rr, cc = r + dr * sign, c + dc * sign
            while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == p:
                cells.append((rr, cc))
                rr, cc = rr + dr * sign, cc + dc * sign
        if len(cells) >= 4:
            return cells
    return []


def play(s, cmd, user):
    """Apply a command. Returns (state, message, ok)."""
    parts = cmd.strip().split("|")
    if len(parts) >= 2 and parts[1] == "new":
        if s["status"] == "playing" and s["moves"]:
            return s, "A game is still in progress — finish it first!", False
        return new_state(s), f"New game #{s['game'] + 1} started. Purple moves first.", True
    if len(parts) != 3 or parts[1] != "drop" or not parts[2].isdigit() or not 1 <= int(parts[2]) <= COLS:
        return s, "Unknown move. Use the column links on the profile page.", False
    if s["status"] != "playing":
        return s, "This game is over. Start a new one from the profile page.", False
    c = int(parts[2]) - 1
    b = s["board"]
    r = next((r for r in range(ROWS - 1, -1, -1) if b[r][c] == 0), None)
    if r is None:
        return s, f"Column {c + 1} is full — try another one.", False
    p = s["turn"]
    b[r][c] = p
    s["moves"].append({"col": c + 1, "row": r, "player": p, "user": user, "at": now()})
    s["players"][user] = s["players"].get(user, 0) + 1
    win = winner_cells(b, r, c)
    if win:
        s.update(status="won", win=win)
        s["history"].append({"game": s["game"], "result": f"{NAMES[p]} won", "moves": len(s["moves"]), "at": now()})
        msg = f"Four in a row! **{NAMES[p]}** wins game #{s['game']} with your move in column {c + 1}. 🎉"
    elif all(b[0][cc] for cc in range(COLS)):
        s["status"] = "draw"
        s["history"].append({"game": s["game"], "result": "Draw", "moves": len(s["moves"]), "at": now()})
        msg = "The board is full — it's a draw!"
    else:
        s["turn"] = 3 - p
        msg = f"You dropped a **{NAMES[p]}** piece in column {c + 1}. Now it's {NAMES[3 - p]}'s turn."
    return s, msg, True


def board_svg(s, theme):
    t = THEMES[theme]
    b, last = s["board"], (s["moves"][-1] if s["moves"] else None)
    win = {tuple(x) for x in s["win"]}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           "<style>.w{animation:pulse 1.4s ease-in-out infinite}@keyframes pulse{50%{opacity:.25}}"
           "@media (prefers-reduced-motion:reduce){.w{animation:none}}</style>",
           f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="{t["board"]}" stroke="{t["edge"]}"/>']
    for r in range(ROWS):
        for c in range(COLS):
            cx, cy, v = PAD + c * CELL + CELL / 2, PAD + r * CELL + CELL / 2, b[r][c]
            out.append(f'<circle cx="{cx}" cy="{cy}" r="21" fill="{t["hole"]}"/>')
            if not v:
                continue
            fill = t["p1"] if v == 1 else t["p2"]
            if last and last["row"] == r and last["col"] - 1 == c:
                dy = -(cy + 30)
                out.append(f'<circle cx="{cx}" cy="{cy}" r="21" fill="{fill}">'
                           f'<animateTransform attributeName="transform" type="translate" values="0 {dy};0 0;0 -10;0 0" '
                           f'keyTimes="0;.6;.8;1" dur=".9s" calcMode="spline" '
                           f'keySplines=".55 0 1 .45;0 .55 .45 1;.55 0 1 .45" fill="freeze"/></circle>')
            else:
                out.append(f'<circle cx="{cx}" cy="{cy}" r="21" fill="{fill}"/>')
            if (r, c) in win:
                out.append(f'<circle class="w" cx="{cx}" cy="{cy}" r="25" fill="none" stroke="{t["ring"]}" stroke-width="2.5"/>')
    out.append("</svg>")
    return "\n".join(out)


def button_svg(col, theme, enabled):
    t = THEMES[theme]
    col_c = t["btn"] if enabled else t["btnoff"]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{CELL}" height="34" viewBox="0 0 {CELL} 34">'
            f'<text x="{CELL/2}" y="13" text-anchor="middle" font-family="ui-monospace,Menlo,Consolas,monospace" '
            f'font-size="11" fill="{col_c}">{col}</text>'
            f'<path d="M{CELL/2-7} 19l7 7 7-7" fill="none" stroke="{col_c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def issue_url(title):
    from urllib.parse import quote
    body = "Just press **Create** — the move is made automatically within a minute. You don't need to write anything."
    return f"https://github.com/{REPO}/issues/new?title={quote(title)}&body={quote(body)}"


def render(s):
    os.makedirs(DIR, exist_ok=True)
    v = len(s["moves"]) + s["game"] * 1000
    playing = s["status"] == "playing"
    for theme in THEMES:
        with open(f"{DIR}/board-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(board_svg(s, theme))
        for c in range(1, COLS + 1):
            ok = playing and s["board"][0][c - 1] == 0
            with open(f"{DIR}/col{c}-{theme}.svg", "w", encoding="utf-8") as f:
                f.write(button_svg(c, theme, ok))

    btns = "".join(
        f'<a href="{issue_url(f"c4|drop|{c}")}"><picture>'
        f'<source media="(prefers-color-scheme: dark)" srcset="{RAW}/{DIR}/col{c}-dark.svg?v={v}">'
        f'<img src="{RAW}/{DIR}/col{c}-light.svg?v={v}" width="{CELL}" alt="Drop in column {c}"></picture></a>'
        for c in range(1, COLS + 1))
    board = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{RAW}/{DIR}/board-dark.svg?v={v}">'
             f'<img src="{RAW}/{DIR}/board-light.svg?v={v}" width="{W}" alt="Connect Four board"></picture>')

    last = s["moves"][-1] if s["moves"] else None
    if s["status"] == "won":
        status = (f'<b>{NAMES[last["player"]]} wins game #{s["game"]}!</b> &nbsp;·&nbsp; '
                  f'<a href="{issue_url("c4|new")}">Start a new game</a>')
    elif s["status"] == "draw":
        status = f'<b>It\'s a draw.</b> &nbsp;·&nbsp; <a href="{issue_url("c4|new")}">Start a new game</a>'
    else:
        status = f'Game #{s["game"]} &nbsp;·&nbsp; <b>{NAMES[s["turn"]]}</b> to move &nbsp;·&nbsp; click a column to drop a piece'
    lastline = (f'Last move: <a href="https://github.com/{html.escape(last["user"])}">@{html.escape(last["user"])}</a> '
                f'→ column {last["col"]}' if last else "No moves yet — be the first!")

    recent = "\n".join(f'| {m["at"][:10]} | {NAMES[m["player"]]} | {m["col"]} | [@{m["user"]}](https://github.com/{m["user"]}) |'
                       for m in reversed(s["moves"][-5:])) or "| – | – | – | – |"
    top = sorted(s["players"].items(), key=lambda kv: -kv[1])[:5]
    tops = "\n".join(f'| [@{u}](https://github.com/{u}) | {n} |' for u, n in top) or "| – | – |"

    section = f"""{START}
<p align="center">{btns}</p>
<p align="center">{board}</p>
<p align="center"><sub>{status}</sub><br><sub>{lastline}</sub></p>

<details>
<summary><sub>Recent moves &amp; top players</sub></summary>

| When | Piece | Column | Player |
| :--- | :--- | :---: | :--- |
{recent}

| Player | Moves |
| :--- | ---: |
{tops}

</details>
{END}"""
    with open(README, encoding="utf-8") as f:
        readme = f.read()
    pat = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not pat.search(readme):
        sys.exit(f"{README} is missing the {START} ... {END} markers")
    with open(README, "w", encoding="utf-8") as f:
        f.write(pat.sub(lambda _: section, readme))


def api(method, path, body):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}{path}", method=method,
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                                          "Accept": "application/vnd.github+json", "User-Agent": "connect4"})
    urllib.request.urlopen(req, timeout=30).read()


def main():
    if "--init" in sys.argv:
        s = new_state()
        save(s), render(s)
        print("initialised")
        return
    if "--local" in sys.argv:
        i = sys.argv.index("--local")
        title, user, number = sys.argv[i + 1], sys.argv[i + 2], None
    else:
        title, user, number = os.environ["ISSUE_TITLE"], os.environ["ISSUE_USER"], os.environ["ISSUE_NUMBER"]
    s = load()
    s, msg, ok = play(s, title, user)
    if ok:
        save(s), render(s)
    print(msg)
    if number:
        api("POST", f"/issues/{number}/comments",
            {"body": f"{msg}\n\n[Back to the board ↩](https://github.com/{REPO.split('/')[0]})"})
        api("PATCH", f"/issues/{number}", {"state": "closed", "state_reason": "completed" if ok else "not_planned"})


if __name__ == "__main__":
    main()
