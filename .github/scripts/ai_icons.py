"""Build assets/ai-icons.svg: AI logos as tiles matching skillicons.dev, with a staggered pop-in.

Logos come from two npm packages (download once into a temp folder):
  npm pack @lobehub/icons-static-svg   (MIT)  -> AI brands, many in colour
  npm pack simple-icons                (CC0)  -> ML tooling
Then:  python .github/scripts/ai_icons.py /path/to/lobe/package/icons /path/to/simple-icons/package/icons

Edit ROWS to add / remove / reorder logos. Each entry: (source, file, colour override or None).
"""

import re
import sys

ROWS = [
    # LLMs
    [("lobe", "openai", None), ("lobe", "claude-color", None), ("lobe", "gemini-color", None), ("lobe", "deepseek-color", None),
     ("lobe", "qwen-color", None), ("lobe", "grok", None), ("lobe", "mistral-color", None), ("lobe", "meta-color", None),
     ("lobe", "kimi-color", None), ("lobe", "zhipu-color", None), ("lobe", "doubao-color", None), ("lobe", "minimax-color", None),
     ("lobe", "perplexity-color", None), ("lobe", "cohere-color", None)],
    # AI dev tools
    [("lobe", "claudecode-color", None), ("lobe", "codex-color", None), ("lobe", "githubcopilot", None), ("lobe", "cursor", None),
     ("lobe", "windsurf", None), ("lobe", "trae-color", None), ("lobe", "v0", None), ("lobe", "huggingface-color", None),
     ("lobe", "ollama", None), ("lobe", "lmstudio", None), ("lobe", "openrouter-color", None), ("lobe", "langchain-color", None),
     ("lobe", "llamaindex-color", None), ("lobe", "dify-color", None)],
    # ML stack
    [("si", "pytorch", "#EE4C2C"), ("si", "tensorflow", "#FF6F00"), ("si", "keras", "#D00000"), ("si", "scikitlearn", "#F7931E"),
     ("si", "jupyter", "#F37626"), ("si", "googlecolab", "#F9AB00"), ("si", "kaggle", "#20BEFF"), ("si", "numpy", "#4DABCF"),
     ("si", "pandas", "#E70488"), ("si", "nvidia", "#76B900"), ("si", "opencv", "#5C3EE8"), ("lobe", "gradio-color", None),
     ("si", "streamlit", "#FF4B4B"), ("si", "weightsandbiases", "#FFBE00")],
]

# geometry copied from skillicons.dev so this grid lines up with the tech-icon row
TILE, STRIDE, SCALE = 256, 300, 48 / 256
BG, RADIUS, PAD = "#242938", 60, 52


def inner(path, prefix):
    raw = open(path, encoding="utf-8").read()
    root = re.match(r"<svg[^>]*>", raw).group(0)
    body = raw[len(root):raw.rindex("</svg>")]
    body = re.sub(r"<title>.*?</title>", "", body)
    ids = re.findall(r'id="([^"]+)"', body)
    for i in ids:  # namespace gradient ids so icons don't clash
        body = body.replace(f'id="{i}"', f'id="{prefix}{i}"').replace(f"url(#{i})", f"url(#{prefix}{i})")
    vb = re.search(r'viewBox="([^"]+)"', root).group(1)
    rule = re.search(r'fill-rule="([^"]+)"', root)
    return vb, body, (f' fill-rule="{rule.group(1)}"' if rule else "")


def main(lobe_dir, si_dir):
    cols = max(len(r) for r in ROWS)
    w = (cols * STRIDE - (STRIDE - TILE)) * SCALE
    h = (len(ROWS) * STRIDE - (STRIDE - TILE)) * SCALE
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}" height="{h:.2f}" viewBox="0 0 {w / SCALE:.0f} {h / SCALE:.0f}">',
           "<style>.t{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.2,.9,.3,1.25) forwards}"
           "@keyframes pop{from{opacity:0;transform:scale(.6)}to{opacity:1;transform:none}}"
           "@media (prefers-reduced-motion:reduce){.t{animation:none;opacity:1}}</style>"]
    n = 0
    for r, row in enumerate(ROWS):
        for c, (src, name, colour) in enumerate(row):
            x, y = c * STRIDE, r * STRIDE
            path = f"{lobe_dir if src == 'lobe' else si_dir}/{name}.svg"
            vb, body, rule = inner(path, f"i{n}_")
            fill = colour or "#ffffff"
            out.append(f'<g class="t" style="animation-delay:{0.15 + (r * cols + c) * 0.035:.3f}s">'
                       f'<rect x="{x}" y="{y}" width="{TILE}" height="{TILE}" rx="{RADIUS}" fill="{BG}"/>'
                       f'<svg x="{x + PAD}" y="{y + PAD}" width="{TILE - 2 * PAD}" height="{TILE - 2 * PAD}" viewBox="{vb}" '
                       f'fill="{fill}" color="{fill}"{rule}>{body}</svg></g>')
            n += 1
    out.append("</svg>")
    with open("assets/ai-icons.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote assets/ai-icons.svg ({n} logos)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
