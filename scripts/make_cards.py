"""Generate the animated project cards used in the profile README.

Run:  python3 scripts/make_cards.py
Writes assets/cards/<slug>.svg. Pure CSS/SMIL animation, no external fonts or
scripts, so GitHub renders them through <img>. Respects prefers-reduced-motion.
"""
from pathlib import Path
from xml.sax.saxutils import escape as esc

OUT = Path(__file__).resolve().parent.parent / "assets" / "cards"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 520, 270
BG, BORDER = "#0D1424", "#1F2B45"
INK, MUTED, DIM = "#E6EDF3", "#9FB0C3", "#5F7089"
CYAN, AMBER, VIOLET, RED, GREEN = "#3DD9E3", "#F0A93B", "#9B8CFF", "#FF6B6B", "#4ADE80"
SANS = "'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def base_css(accent: str) -> str:
    return f"""
    .t{{font-family:{SANS};}} .m{{font-family:{MONO};}}
    .in{{animation:fade .7s ease-out backwards;}}
    @keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
    .glow{{animation:glow 3.2s ease-in-out infinite;}}
    @keyframes glow{{0%,100%{{stroke-opacity:.35}}50%{{stroke-opacity:.9}}}}
    .accent{{fill:{accent};}}
    @media (prefers-reduced-motion: reduce){{*{{animation:none!important;opacity:1!important}}}}
    """


def card(slug, label, title, desc, metrics, stack, accent, art, art_css=""):
    desc_svg = "".join(
        f'<text class="t" x="28" y="{104 + i * 20}" font-size="14" fill="{MUTED}">{esc(line)}</text>'
        for i, line in enumerate(desc)
    )
    mx = ""
    for i, (big, small) in enumerate(metrics):
        x = 28 + i * 118
        mx += (
            f'<g class="in" style="animation-delay:{0.35 + i * 0.18:.2f}s">'
            f'<text class="t" x="{x}" y="200" font-size="24" font-weight="700" fill="{INK}">{esc(big)}</text>'
            f'<text class="m" x="{x}" y="219" font-size="11" fill="{DIM}">{esc(small)}</text></g>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}: {esc(' '.join(desc))}">
<style>{base_css(accent)}{art_css}</style>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="none" stroke="{accent}" stroke-width="1.5" class="glow"/>
<circle cx="34" cy="34" r="4" class="accent"/>
<text class="m" x="46" y="38" font-size="11" letter-spacing="1.4" fill="{accent}">{esc(label)}</text>
<text class="t" x="28" y="76" font-size="27" font-weight="700" fill="{INK}">{esc(title)}</text>
{desc_svg}
{mx}
<line x1="28" y1="236" x2="{W-28}" y2="236" stroke="{BORDER}"/>
<text class="m" x="28" y="255" font-size="11.5" fill="{DIM}">{esc(stack)}</text>
<g transform="translate(330,24)">{art}</g>
</svg>"""
    (OUT / f"{slug}.svg").write_text(svg)


# ---------- illustrations (drawn in a ~165x150 box at x=330,y=24) ----------

fastframe_art = f"""
<text class="m" x="0" y="22" font-size="10.5" fill="{DIM}">iterrows + append</text>
<rect x="0" y="30" width="160" height="14" rx="4" fill="{AMBER}" opacity=".85"/>
<text class="m" x="0" y="62" font-size="10.5" fill="{DIM}">0.8203 s</text>
<text class="m" x="0" y="92" font-size="10.5" fill="{DIM}">fastframe fix</text>
<rect x="0" y="100" width="160" height="14" rx="4" fill="{CYAN}" class="shrink"/>
<text class="m after" x="0" y="132" font-size="10.5" fill="{CYAN}">0.0025 s  ✓ verified</text>
"""
fastframe_css = """
.shrink{transform-box:fill-box;transform-origin:left center;animation:shrink 5s ease-in-out infinite;}
@keyframes shrink{0%,12%{transform:scaleX(1)}45%,85%{transform:scaleX(.03)}100%{transform:scaleX(1)}}
.after{animation:after 5s ease-in-out infinite;}
@keyframes after{0%,40%{opacity:0}50%,85%{opacity:1}95%,100%{opacity:0}}
"""

churn_art = f"""
<line x1="10" y1="140" x2="160" y2="140" stroke="{DIM}"/>
<line x1="10" y1="140" x2="10" y2="10" stroke="{DIM}"/>
<line x1="10" y1="140" x2="160" y2="10" stroke="{DIM}" stroke-dasharray="3 4"/>
<path d="M10 140 C 14 60, 40 28, 90 18 S 150 11, 160 10" fill="none" stroke="{VIOLET}" stroke-width="2.5" class="roc"/>
<path d="M10 140 C 14 60, 40 28, 90 18 S 150 11, 160 10 L160 140 Z" fill="{VIOLET}" opacity=".10"/>
<text class="m" x="70" y="100" font-size="12" fill="{INK}">AUC 0.896</text>
<text class="m" x="70" y="116" font-size="10" fill="{DIM}">out-of-time</text>
"""
churn_css = """
.roc{stroke-dasharray:260;stroke-dashoffset:0;animation:draw 5s ease-out infinite;}
@keyframes draw{0%{stroke-dashoffset:260}55%,100%{stroke-dashoffset:0}}
"""

sat_pts = "0,80 12,76 24,82 36,74 48,79 60,72 72,78 84,75 96,40 104,108 112,70 124,77 136,73 148,79 160,74"
sat_art = f"""
<text class="m" x="0" y="14" font-size="10" fill="{DIM}">SMAP · channel A-4</text>
<rect x="88" y="26" width="28" height="100" rx="4" fill="{AMBER}" opacity=".12" class="zone"/>
<polyline points="{sat_pts}" fill="none" stroke="{CYAN}" stroke-width="2" transform="translate(0,6)"/>
<line x1="0" y1="24" x2="0" y2="130" stroke="{INK}" stroke-opacity=".5" class="scan"/>
<circle cx="96" cy="46" r="5" fill="{AMBER}" class="ping"/>
<text class="m alert" x="0" y="148" font-size="10" fill="{AMBER}">⚠ drift on A-4 since t=96</text>
"""
sat_css = """
.scan{animation:scan 4s linear infinite;}
@keyframes scan{from{transform:translateX(0)}to{transform:translateX(160px)}}
.ping{transform-box:fill-box;transform-origin:center;animation:ping 4s ease-out infinite;}
@keyframes ping{0%,55%{opacity:0;transform:scale(.4)}62%{opacity:1;transform:scale(1.3)}100%{opacity:.25;transform:scale(1)}}
.alert,.zone{animation:alert 4s ease-out infinite;}
@keyframes alert{0%,58%{opacity:0}66%,100%{opacity:1}}
"""

sql_nodes = [("question", 0), ("LLM draft", 36), ("AST guard", 72), ("fresh SQL", 108)]
sql_art = f'<path id="sqlp" d="M20 14 V122" stroke="{BORDER}" stroke-width="2"/>'
for name, y in sql_nodes:
    col = AMBER if name == "AST guard" else CYAN
    sql_art += (
        f'<circle cx="20" cy="{y + 14}" r="7" fill="{BG}" stroke="{col}" stroke-width="2"/>'
        f'<text class="m" x="38" y="{y + 18}" font-size="11.5" fill="{INK}">{name}</text>'
    )
sql_art += f"""
<text class="m rej" x="110" y="90" font-size="10" fill="{RED}">✗ DROP</text>
<circle cx="20" cy="14" r="4" fill="{GREEN}"><animateMotion dur="3.2s" repeatCount="indefinite" path="M0 0 V108"/></circle>
<text class="m" x="0" y="148" font-size="10" fill="{DIM}">read-only · allowlist</text>
"""
sql_css = """
.rej{animation:rej 3.2s steps(1) infinite;}
@keyframes rej{0%,50%{opacity:0}55%,75%{opacity:1}80%,100%{opacity:0}}
"""

cities = [(18, 104), (52, 60), (92, 92), (128, 38), (150, 112), (70, 128)]
tour_art = f'<path d="M18 104 L52 60 L92 92 L128 38" fill="none" stroke="{AMBER}" stroke-width="2" stroke-dasharray="5 5" class="route"/>'
for i, (x, y) in enumerate(cities):
    tour_art += (
        f'<circle cx="{x}" cy="{y}" r="11" fill="{VIOLET}" opacity=".18" class="pulse" style="animation-delay:{i * .45:.2f}s"/>'
        f'<circle cx="{x}" cy="{y}" r="4" fill="{VIOLET}"/>'
    )
tour_art += f'<text class="m" x="0" y="150" font-size="10" fill="{DIM}">unserved demand → stops</text>'
tour_css = """
.route{animation:dash 1.6s linear infinite;}
@keyframes dash{to{stroke-dashoffset:-20}}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2.7s ease-out infinite;}
@keyframes pulse{0%{transform:scale(.4);opacity:.5}100%{transform:scale(1.8);opacity:0}}
"""

vg_nodes = {"inet": (10, 20), "web": (70, 40), "api": (40, 96), "db": (130, 110), "cve": (140, 30)}
vg_art = ""
for a, b in [("inet", "web"), ("web", "api"), ("api", "db"), ("web", "cve"), ("cve", "db")]:
    (x1, y1), (x2, y2) = vg_nodes[a], vg_nodes[b]
    vg_art += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{BORDER}" stroke-width="2"/>'
vg_art += f'<path d="M10 20 L70 40 L40 96 L130 110" fill="none" stroke="{RED}" stroke-width="2.5" stroke-dasharray="6 6" class="atk"/>'
for name, (x, y) in vg_nodes.items():
    col = RED if name == "db" else (DIM if name == "cve" else CYAN)
    vg_art += (
        f'<circle cx="{x}" cy="{y}" r="7" fill="{BG}" stroke="{col}" stroke-width="2"/>'
        f'<text class="m" x="{x + 10}" y="{y - 8}" font-size="10" fill="{MUTED}">{name}</text>'
    )
vg_art += f'<text class="m" x="0" y="148" font-size="10" fill="{RED}">5.3 reaches db → patch #1</text>'
vg_css = """
.atk{animation:dash 1.2s linear infinite;}
@keyframes dash{to{stroke-dashoffset:-24}}
"""

# ---------- cards ----------

card("fastframe", "PYPI PACKAGE · DEV TOOLING", "FastFrame",
     ["Finds slow pandas/NumPy code, rewrites", "only the patterns it can prove are safe,",
      "then checks the output still matches."],
     [("332×", "best speedup"), ("94%", "test coverage"), ("pip", "fastframe-pandas")],
     "LibCST · pandas · NumPy · Docker · GitHub Actions", CYAN, fastframe_art, fastframe_css)

card("churnguard", "END-TO-END ML · DATA ENGINEERING", "ChurnGuard",
     ["Churn prediction + expected-value retention", "on KKBox: point-in-time features, calibrated",
      "model, API, consoles and monitoring."],
     [("410M", "rows ingested"), ("0.896", "out-of-time AUC"), ("1M / 19s", "members scored")],
     "DuckDB · LightGBM · MLflow · FastAPI · React · Docker", VIOLET, churn_art, churn_css)

card("satpred", "ANOMALY DETECTION · TIME SERIES", "SatPred",
     ["Explainable anomaly detection on NASA", "SMAP/MSL telemetry. Every alert names the",
      "channel and when it started."],
     [("80", "channels"), ("331", "tests passing"), ("97%", "coverage")],
     "PyTorch · scikit-learn · FastAPI · uv · mypy strict", AMBER, sat_art, sat_css)

card("sqlyapper", "LLM AGENT · GUARDRAILS", "SQLYapper",
     ["Ask your data questions in plain English.", "LLM-drafted SQL never hits the database:",
      "an AST guard rebuilds it from a safe tree."],
     [("AST", "SQL guard"), ("CI", "red-team evals"), ("OTel", "traced per step")],
     "LangGraph · Groq · SQLite · FastAPI · Prometheus", GREEN, sql_art, sql_css)

card("tourscout", "AI AGENT · MCP", "TourScout",
     ["Tour-planning agent for indie musicians,", "grounded in Qloo taste data: finds cities",
      "with fans who've never seen them live."],
     [("7", "MCP tools"), ("Live", "web demo"), ("HITL", "pick your cities")],
     "LangGraph · MCP · Gemini · FastAPI · React · Neon", VIOLET, tour_art, tour_css)

card("vulngraph", "GRAPH AGENT · SECURITY", "VulnGraph",
     ["Ranks CVEs by attack paths that actually", "reach your assets, so a quiet 5.3 can",
      "outrank a 9.8 that goes nowhere."],
     [("61", "tests"), ("Live", "web demo"), ("Graph", "attack paths")],
     "LangGraph · FalkorDB · FastMCP · Groq", RED, vg_art, vg_css)

print("wrote", sorted(p.name for p in OUT.glob("*.svg")))
