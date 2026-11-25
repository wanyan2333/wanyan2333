"""Render the animated hero banner (dark + light SVG) into assets/.

Run once after editing NAME / TAGLINE:  python .github/scripts/hero.py
"""

import os

NAME = "wanyan"
TAGLINE = "AI  ·  Web  ·  IoT  —  building things that think"
W, H = 985, 220

THEMES = {
    "dark": dict(bg="#0d1117", edge="#30363d", dot="#21262d", sub="#8b949e", glow1="#FF8A3D", glow2="#FF4F8B", stroke="#c9d1d9"),
    "light": dict(bg="#ffffff", edge="#d0d7de", dot="#eaeef2", sub="#57606a", glow1="#F76B15", glow2="#E8457A", stroke="#24292f"),
}


def svg(t):
    font = "'Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="ink" x1="0" x2="1">
    <stop offset="0" stop-color="{t['glow1']}"/><stop offset="1" stop-color="{t['glow2']}"/>
  </linearGradient>
  <radialGradient id="glow" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="{t['glow1']}" stop-opacity=".28"/>
    <stop offset=".55" stop-color="{t['glow2']}" stop-opacity=".10"/>
    <stop offset="1" stop-color="{t['bg']}" stop-opacity="0"/>
  </radialGradient>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="{t['dot']}"/></pattern>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="12"/></clipPath>
  <clipPath id="name"><text x="{W/2}" y="122" text-anchor="middle" font-family="{font}" font-size="96" font-weight="800" letter-spacing="-2">{NAME}</text></clipPath>
  <linearGradient id="shine" x1="0" x2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
</defs>
<style>
  .draw{{fill:transparent;stroke:url(#ink);stroke-width:1.6;stroke-dasharray:900;stroke-dashoffset:900;
        animation:draw 2.4s cubic-bezier(.65,0,.35,1) forwards}}
  @keyframes draw{{to{{stroke-dashoffset:0}}}}
  .fill{{opacity:0;animation:show .9s ease 2.0s forwards}}
  @keyframes show{{to{{opacity:1}}}}
  .sub{{opacity:0;animation:up .8s ease 2.6s forwards}}
  @keyframes up{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
  .glint{{transform:translateX(-200px);animation:glint 6s cubic-bezier(.45,0,.55,1) 3.2s infinite}}
  @keyframes glint{{0%{{transform:translateX(-200px) skewX(-20deg)}}35%,100%{{transform:translateX({W+60}px) skewX(-20deg)}}}}
  .orb{{animation:drift 9s ease-in-out infinite alternate}}
  @keyframes drift{{from{{transform:translateX(-260px)}}to{{transform:translateX(260px)}}}}
  .line{{stroke-dasharray:6 10;animation:flow 1.2s linear infinite}}
  @keyframes flow{{to{{stroke-dashoffset:-16}}}}
  @media (prefers-reduced-motion:reduce){{.draw{{animation:none;stroke-dashoffset:0}}.fill{{animation:none;opacity:1}}.sub{{animation:none;opacity:1}}.orb,.line,.glint{{animation:none}}.glint{{display:none}}}}
</style>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="{t['bg']}"/>
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <ellipse class="orb" cx="{W/2}" cy="{H/2}" rx="300" ry="150" fill="url(#glow)"/>
  <line class="line" x1="0" y1="{H-28}" x2="{W}" y2="{H-28}" stroke="{t['edge']}" stroke-width="1"/>
</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{t['edge']}"/>
<text class="fill" fill="url(#ink)" x="{W/2}" y="122" text-anchor="middle" font-family="{font}" font-size="96" font-weight="800" letter-spacing="-2">{NAME}</text>
<text class="draw" x="{W/2}" y="122" text-anchor="middle" font-family="{font}" font-size="96" font-weight="800" letter-spacing="-2">{NAME}</text>
<g clip-path="url(#name)"><rect class="glint" x="0" y="20" width="140" height="130" fill="url(#shine)"/></g>
<text class="sub" x="{W/2}" y="164" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="15" fill="{t['sub']}" letter-spacing=".5">{TAGLINE}</text>
</svg>
"""


def main():
    os.makedirs("assets", exist_ok=True)
    for name, t in THEMES.items():
        with open(f"assets/hero-{name}.svg", "w", encoding="utf-8") as f:
            f.write(svg(t))
    print("wrote assets/hero-dark.svg, assets/hero-light.svg")


if __name__ == "__main__":
    main()
