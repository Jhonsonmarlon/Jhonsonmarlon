"""Gera assets/contributions.svg com a grelha de contribuições do GitHub.

Quadrados vazios a azul, dias com contribuições em tons de verde.
Corre todos os dias através de .github/workflows/contributions.yml.
"""
import datetime as dt
import os
import re
import sys
import urllib.request

USER = os.environ.get("GH_USER", "Jhonsonmarlon")
OUT = os.environ.get("OUT", "assets/contributions.svg")

EMPTY = "#1e3a8a"  # azul (dias sem contribuições)
LEVELS = ["#9be9a8", "#40c463", "#30a14e", "#216e39"]  # verde, nível 1 → 4
LABEL = "#8b949e"

CELL, GAP = 11, 3
STEP = CELL + GAP
LEFT, TOP = 34, 22
MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def fetch(user: str) -> str:
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse(html: str):
    days = {}
    for td in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
        d = re.search(r'data-date="(\d{4}-\d\d-\d\d)"', td)
        lv = re.search(r'data-level="(\d)"', td)
        if d and lv:
            days[dt.date.fromisoformat(d.group(1))] = int(lv.group(1))
    m = re.search(r"([\d,.]+)\s+contributions?\s+in the last year", html)
    total = m.group(1).replace(",", "").replace(".", "") if m else None
    return days, total


def render(days, total) -> str:
    if not days:
        raise SystemExit("Sem dados de contribuições")
    first, last = min(days), max(days)
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # domingo
    weeks = (last - start).days // 7 + 1
    width = LEFT + weeks * STEP + 4
    height = TOP + 7 * STEP + 26

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Segoe UI, Helvetica, Arial, sans-serif">'
    ]
    # meses
    last_month = None
    for w in range(weeks):
        d = start + dt.timedelta(weeks=w)
        if d.month != last_month and w < weeks - 1:
            out.append(f'<text x="{LEFT + w * STEP}" y="{TOP - 8}" font-size="10" fill="{LABEL}">{MONTHS[d.month - 1]}</text>')
            last_month = d.month
    # dias da semana
    for row, name in ((1, "Seg"), (3, "Qua"), (5, "Sex")):
        out.append(f'<text x="0" y="{TOP + row * STEP + CELL - 2}" font-size="9" fill="{LABEL}">{name}</text>')
    # quadrados
    d = start
    while d <= last:
        if d >= first:
            w, row = (d - start).days // 7, (d - start).days % 7
            lv = days.get(d, 0)
            color = EMPTY if lv == 0 else LEVELS[min(lv, 4) - 1]
            out.append(
                f'<rect x="{LEFT + w * STEP}" y="{TOP + row * STEP}" width="{CELL}" height="{CELL}" '
                f'rx="2" fill="{color}"><title>{d.isoformat()}</title></rect>'
            )
        d += dt.timedelta(days=1)
    # legenda
    y = TOP + 7 * STEP + 12
    if total:
        out.append(f'<text x="{LEFT}" y="{y + 9}" font-size="10" fill="{LABEL}">{total} contribuições no último ano</text>')
    lx = width - (5 * STEP) - 72
    out.append(f'<text x="{lx}" y="{y + 9}" font-size="10" fill="{LABEL}">Menos</text>')
    for i, c in enumerate([EMPTY] + LEVELS):
        out.append(f'<rect x="{lx + 34 + i * STEP}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>')
    out.append(f'<text x="{lx + 38 + 5 * STEP}" y="{y + 9}" font-size="10" fill="{LABEL}">Mais</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    html = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else fetch(USER)
    days, total = parse(html)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(days, total))
    print(f"{OUT}: {len(days)} dias, total={total}")
