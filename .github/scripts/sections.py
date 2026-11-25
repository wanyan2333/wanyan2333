"""Render terminal-style section dividers (dark + light SVG) into assets/sections/.

Each divider is a hairline across the page with a soft light sweeping along it,
and a centred path label such as `~/arcade` followed by a blinking cursor.

Edit LABELS, then run:  python .github/scripts/sections.py
"""

import html
import os

LABELS = {
    "stack": "~/stack",
    "arcade": "~/arcade",
    "footer": "exit 0  ·  thanks for stopping by",
}
W, H = 985, 44
FS, CHAR_W = 13, 13 * 0.6

THEMES = {
    "dark": dict(line="#30363d", text="#8b949e", accent="#FF8A3D", accent2="#FF4F8B", bg="#0d1117"),
    "light": dict(line="#d0d7de", text="#57606a", accent="#F76B15", accent2="#E8457A", bg="#ffffff"),
}


def svg(label, t):
    text_w = len(label) * CHAR_W
    gap = 18
    left_end = W / 2 - text_w / 2 - gap
    right_start = W / 2 + text_w / 2 + gap + CHAR_W  # leave room for the cursor
    cy = H / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="sweep" x1="0" x2="1">
    <stop offset="0" stop-color="{t['accent']}" stop-opacity="0"/>
    <stop offset=".45" stop-color="{t['accent']}" stop-opacity="1"/>
    <stop offset=".55" stop-color="{t['accent2']}" stop-opacity="1"/>
    <stop offset="1" stop-color="{t['accent2']}" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="lines">
    <rect x="0" y="{cy - 1}" width="{left_end:.1f}" height="2"/>
    <rect x="{right_start:.1f}" y="{cy - 1}" width="{W - right_start:.1f}" height="2"/>
  </clipPath>
</defs>
<style>
  .glow{{animation:sweep 5.5s cubic-bezier(.45,0,.55,1) infinite}}
  @keyframes sweep{{from{{transform:translateX(-260px)}}to{{transform:translateX({W + 60}px)}}}}
  .cur{{animation:blink 1.1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}
  .lbl{{opacity:0;animation:in .6s ease .2s forwards}}@keyframes in{{to{{opacity:1}}}}
  @media (prefers-reduced-motion:reduce){{.glow{{animation:none;opacity:0}}.cur{{animation:none}}.lbl{{animation:none;opacity:1}}}}
</style>
<g clip-path="url(#lines)">
  <rect x="0" y="{cy - 0.5}" width="{W}" height="1" fill="{t['line']}"/>
  <rect class="glow" x="0" y="{cy - 1}" width="200" height="2" fill="url(#sweep)"/>
</g>
<g class="lbl" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FS}">
  <text x="{W / 2 - CHAR_W / 2:.1f}" y="{cy + 4.5:.1f}" text-anchor="middle" fill="{t['text']}" xml:space="preserve">{html.escape(label)}</text>
  <rect class="cur" x="{W / 2 + text_w / 2 - CHAR_W / 2 + 3:.1f}" y="{cy - 7:.1f}" width="{CHAR_W - 1:.1f}" height="14" fill="{t['accent2']}"/>
</g>
</svg>
"""


def main():
    os.makedirs("assets/sections", exist_ok=True)
    for key, label in LABELS.items():
        for name, t in THEMES.items():
            with open(f"assets/sections/{key}-{name}.svg", "w", encoding="utf-8") as f:
                f.write(svg(label, t))
    print("wrote", len(LABELS) * len(THEMES), "dividers to assets/sections/")


if __name__ == "__main__":
    main()
