"""Render the neofetch-style profile card (dark_mode.svg, light_mode.svg).

  python neofetch/build.py            fetch GitHub stats (GH_TOKEN for GraphQL) and render
  python neofetch/build.py --offline  render with the cached stats in neofetch/stats.json
"""
import base64
import datetime as dt
import html
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
USER = "anurag-23werty"

FS = 14          # font size, px
CW = FS * 0.6    # IBM Plex Mono advance width
LH = 18          # line height, px
PAD = 22
ART_FS = 8.8     # the portrait uses a small font so it has enough characters to read as a picture
ART_LH = 10.6
ART_X = PAD
INFO_X = 438
INFO_COLS = 62   # characters available in the info column
W = 985

THEMES = {
    "dark": dict(bg="#0d1117", frame="#30363d", bar="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                 dots="#484f58", head="#7ee787", accent="#d2a8ff", art_gain=1.0),
    "light": dict(bg="#ffffff", frame="#d0d7de", bar="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                  dots="#afb8c1", head="#116329", accent="#8250df", art_gain=0.62),
}

# ---------------------------------------------------------------- profile text
INFO = [
    ("title", "anurag@outr"),
    ("kv", "OS", "macOS, Ubuntu (WSL), Windows 11"),
    ("kv", "Uptime", "{uptime}"),
    ("kv", "Host", "Odisha University of Technology & Research"),
    ("kv", "Kernel", "B.Tech CSE (AI & ML) · CGPA 9.26"),
    ("kv", "Shell", "zsh · Claude Code · Jupyter"),
    ("kv", "Location", "Bhubaneswar, India"),
    ("blank",),
    ("kv", "Languages.Code", "Python, SQL, TypeScript, C++"),
    ("kv", "Stack.AI", "LangGraph, LangChain, PyTorch, scikit-learn"),
    ("kv", "Stack.Data", "PostgreSQL, FalkorDB, Neo4j, pgvector, pandas"),
    ("kv", "Stack.Ops", "Docker, FastAPI, MLflow, DVC, AWS, Azure"),
    ("kv", "Hobbies", "Markets, politics, sports, rabbit holes"),
    ("section", "Projects"),
    ("kv", "sql-dwh", "PostgreSQL medallion data warehouse"),
    ("kv", "satpred", "Explainable satellite health monitoring"),
    ("kv", "fastframe", "Rewrites slow pandas code, up to 332x"),
    ("kv", "vulngraph", "Graph-aware vulnerability triage agent"),
    ("section", "Contact"),
    ("kv", "Email", "24110387@outr.ac.in"),
    ("kv", "LinkedIn", "anurag-choudhury-63a780206"),
    ("kv", "Portfolio", "personal-portfolio-swart-pi-92.vercel.app"),
    ("section", "GitHub Stats"),
    ("stats",),
    ("stats2",),
    ("blank",),
    ("prompt",),
]


# ---------------------------------------------------------------- data
def _get(url, token=None, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"User-Agent": "neofetch-profile", "Accept": "application/json"})
    if token:
        req.add_header("Authorization", f"bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


QUERY = """query($login:String!){user(login:$login){
  createdAt followers{totalCount}
  repositories(ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false, first:100){totalCount nodes{stargazerCount}}
  repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,ISSUE]){totalCount}
  contributionsCollection{totalCommitContributions contributionCalendar{totalContributions}}
}}"""


def fetch_stats():
    token = os.environ.get("GH_TOKEN")
    if token:
        u = _get("https://api.github.com/graphql", token, {"query": QUERY, "variables": {"login": USER}})["data"]["user"]
        return dict(created=u["createdAt"], followers=u["followers"]["totalCount"],
                    repos=u["repositories"]["totalCount"],
                    stars=sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
                    contributed=u["repositoriesContributedTo"]["totalCount"],
                    commits=u["contributionsCollection"]["totalCommitContributions"],
                    contributions=u["contributionsCollection"]["contributionCalendar"]["totalContributions"])
    # no token: public REST covers everything except the contribution counts
    prev = load_cache()
    u = _get(f"https://api.github.com/users/{USER}")
    repos = _get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    own = [r for r in repos if not r["fork"]]
    return dict(prev, created=u["created_at"], followers=u["followers"], repos=len(own),
                stars=sum(r["stargazers_count"] for r in own))


def load_cache():
    p = ROOT / "stats.json"
    return json.loads(p.read_text()) if p.exists() else {}


def uptime(created, today):
    """Years, months and days since the GitHub account was created."""
    c = dt.date.fromisoformat(created[:10])
    months = (today.year - c.year) * 12 + today.month - c.month - (today.day < c.day)
    anchor_y, anchor_m = c.year + (c.month - 1 + months) // 12, (c.month - 1 + months) % 12 + 1
    try:
        anchor = dt.date(anchor_y, anchor_m, c.day)
    except ValueError:
        anchor = dt.date(anchor_y, anchor_m, 28)
    days = (today - anchor).days
    y, m = divmod(months, 12)
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(y, 'year')}, {plural(m, 'month')}, {plural(days, 'day')} on GitHub"


# ---------------------------------------------------------------- svg
def esc(s):
    return html.escape(str(s), quote=False)


def font_css(text):
    chars = "".join(sorted(set(text + " 0123456789.,:-")))
    css = ""
    for weight, name in ((400, "ibm-plex-mono-latin-400-normal.woff2"), (600, "ibm-plex-mono-latin-600-normal.woff2")):
        font = TTFont(ROOT / "fonts" / name)
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.name_IDs = []
        sub = subset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        css += f"@font-face{{font-family:'Plex';font-weight:{weight};src:url(data:font/woff2;base64,{b64}) format('woff2')}}\n"
    return css


def shade(hexcol, gain):
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, int(c * gain)) for c in (r, g, b))


def art_rows(art, theme):
    """Each art row becomes one <text>; runs of the same colour share a <tspan>."""
    out = []
    for i, row in enumerate(art["rows"]):
        y = PAD + 34 + i * ART_LH
        parts, run, col = [], "", None
        for ch, c in zip(row["chars"], row["colors"]):
            c = shade(c, theme["art_gain"]) if ch != " " else col
            if c != col and run:
                parts.append(f'<tspan fill="{col}">{esc(run)}</tspan>')
                run = ""
            run, col = run + ch, c
        if run.strip():
            parts.append(f'<tspan fill="{col}">{esc(run.rstrip())}</tspan>')
        out.append(f'<text x="{ART_X}" y="{y}" class="art">{"".join(parts)}</text>')
    return out


def info_rows(stats, theme, today):
    rows, y = [], PAD + 40
    fmt = lambda n: f"{n:,}" if isinstance(n, int) else "—"

    def kv(key, value, y):
        # neofetch-style dotted leader: key, dots, value fill INFO_COLS exactly
        dots = INFO_COLS - len(key) - len(value) - 4
        k = ".".join(f'<tspan class="k">{esc(p)}</tspan>' for p in key.split("."))
        return (f'<text x="{INFO_X}" y="{y}"><tspan class="d">. </tspan>{k}:<tspan class="d"> {"." * max(1, dots)} </tspan>'
                f'<tspan class="v">{esc(value)}</tspan></text>')

    for item in INFO:
        kind = item[0]
        if kind == "title":
            rule = "─" * (INFO_COLS - len(item[1]) - 1)
            rows.append(f'<text x="{INFO_X}" y="{y}"><tspan class="h">{esc(item[1])}</tspan> <tspan class="d">{rule}</tspan></text>')
        elif kind == "kv":
            value = item[2].format(uptime=uptime(stats["created"], today) if stats.get("created") else "—")
            rows.append(kv(item[1], value, y))
        elif kind == "section":
            rule = "─" * (INFO_COLS - len(item[1]) - 4)
            rows.append(f'<text x="{INFO_X}" y="{y}"><tspan class="d">- </tspan><tspan class="h">{esc(item[1])}</tspan> <tspan class="d">{rule}</tspan></text>')
        elif kind == "stats":
            rows.append(pair("Repos", fmt(stats.get("repos")), "Stars", fmt(stats.get("stars")), y, extra=f" {{Contributed: {fmt(stats.get('contributed'))}}}"))
        elif kind == "stats2":
            rows.append(pair("Commits", fmt(stats.get("commits")), "Followers", fmt(stats.get("followers")), y,
                             extra=f" {{12m: {fmt(stats.get('contributions'))} contributions}}"))
        elif kind == "prompt":
            rows.append(f'<text x="{INFO_X}" y="{y}"><tspan class="h">anurag@outr</tspan>:<tspan class="v">~</tspan>$ '
                        f'<tspan class="cur">█</tspan></text>')
        y += LH
    return rows, y


def pair(k1, v1, k2, v2, y, extra=""):
    """Two key/value pairs on one line, the second right-aligned to the column edge."""
    left = f". {k1}: {v1}{extra}"
    right = f"{k2}: {v2}"
    gap = INFO_COLS - len(left) - len(right) - 3
    return (f'<text x="{INFO_X}" y="{y}"><tspan class="d">. </tspan><tspan class="k">{k1}</tspan>: <tspan class="v">{esc(v1)}</tspan>'
            f'<tspan class="d">{esc(extra)} </tspan><tspan class="d">{"." * max(1, gap)}</tspan><tspan class="d"> | </tspan>'
            f'<tspan class="k">{k2}</tspan>: <tspan class="v">{esc(v2)}</tspan></text>')


def render(theme_name, art, stats, today):
    t = THEMES[theme_name]
    art_svg = art_rows(art, t)
    info_svg, info_end = info_rows(stats, t, today)
    art_end = PAD + 34 + len(art["rows"]) * ART_LH
    h = round(max(art_end, info_end) + PAD - LH // 2)
    body = "\n".join(art_svg + info_svg)
    bar = (f'<rect x="0.5" y="0.5" width="{W - 1}" height="30" rx="10" fill="{t["bar"]}"/>'
           f'<rect x="0.5" y="20" width="{W - 1}" height="11" fill="{t["bar"]}"/>'
           f'<line x1="0" x2="{W}" y1="30.5" y2="30.5" stroke="{t["frame"]}"/>'
           f'<circle cx="20" cy="15.5" r="6" fill="#ff5f57"/><circle cx="40" cy="15.5" r="6" fill="#febc2e"/>'
           f'<circle cx="60" cy="15.5" r="6" fill="#28c840"/>'
           f'<text x="{W / 2}" y="20" text-anchor="middle" class="d" font-size="12">anurag@outr: ~ — neofetch</text>')
    css = f"""
text{{font-family:'Plex',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:{FS}px;fill:{t['text']};white-space:pre}}
.art{{font-weight:600;font-size:{ART_FS}px}}
.k{{fill:{t['key']}}} .v{{fill:{t['value']}}} .d{{fill:{t['dots']}}} .h{{fill:{t['head']};font-weight:600}}
.cur{{fill:{t['text']};animation:blink 1.1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.cur{{animation:none}}}}
"""
    text_for_font = "".join(r["chars"] for r in art["rows"]) + body + "anurag@outr: ~ — neofetch"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" '
            f'aria-label="Anurag Choudhury: neofetch-style profile card">\n<title>Anurag Choudhury · neofetch</title>\n'
            f'<style>\n{font_css(html.unescape(text_for_font))}{css}</style>\n'
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="10" fill="{t["bg"]}" stroke="{t["frame"]}"/>\n'
            f'{bar}\n{body}\n</svg>\n')


def main():
    offline = "--offline" in sys.argv
    stats = load_cache() if offline else fetch_stats()
    (ROOT / "stats.json").write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n")
    art = json.loads((ROOT / "art.json").read_text())
    today = dt.date.today()
    for name in THEMES:
        out = ROOT.parent / f"{name}_mode.svg"
        out.write_text(render(name, art, stats, today))
        print(f"wrote {out.name}")


if __name__ == "__main__":
    main()
