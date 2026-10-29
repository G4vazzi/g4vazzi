
import os
import json
import math
import urllib.request
from pathlib import Path
from collections import defaultdict
from html import escape

USERNAME = "g4vazzi"
TOKEN = os.getenv("GITHUB_TOKEN", "")

OUTPUT = Path("assets/languages.svg")
COLORS = [
    "#3B82F6", "#60A5FA", "#1D4ED8",
    "#93C5FD", "#2563EB", "#38BDF8",
    "#64748B"
]


def github_get(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "PG-Reality-Stats"
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers=headers
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def get_repositories():
    repos = []
    page = 1

    while True:
        batch = github_get(
            f"/users/{USERNAME}/repos"
            f"?type=owner&per_page=100&page={page}"
        )

        if not batch:
            break

        repos.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return [
        repo for repo in repos
        if not repo["fork"]
        and not repo["archived"]
        and repo["name"].lower() != USERNAME.lower()
    ]


def collect_languages():
    totals = defaultdict(int)

    for repo in get_repositories():
        name = repo["name"]

        languages = github_get(
            f"/repos/{USERNAME}/{name}/languages"
        )

        print(f"Analisando: {name}")

        for language, size in languages.items():
            totals[language] += size

    return totals


def polar(cx, cy, radius, angle):
    radians = math.radians(angle - 90)

    return (
        cx + radius * math.cos(radians),
        cy + radius * math.sin(radians)
    )


def sector_path(cx, cy, radius, start, end):
    x1, y1 = polar(cx, cy, radius, start)
    x2, y2 = polar(cx, cy, radius, end)

    large_arc = 1 if end - start > 180 else 0

    return (
        f"M {cx} {cy} "
        f"L {x1:.3f} {y1:.3f} "
        f"A {radius} {radius} 0 {large_arc} 1 "
        f"{x2:.3f} {y2:.3f} Z"
    )


def generate_svg(totals):
    total = sum(totals.values())

    if total <= 0:
        raise RuntimeError(
            "Nenhuma linguagem encontrada nos repositórios."
        )

    languages = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True
    )

    # Exibe as seis maiores e agrupa o restante.
    displayed = languages[:6]
    others = sum(value for _, value in languages[6:])

    if others:
        displayed.append(("Outras", others))

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="820" height="340" viewBox="0 0 820 340">',
        '<rect width="820" height="340" rx="18" '
        'fill="#071429"/>',
        '<rect x="1" y="1" width="818" height="338" '
        'rx="17" fill="none" stroke="#29496A"/>',
        '<text x="35" y="46" fill="#60A5FA" '
        'font-family="Arial,sans-serif" font-size="14" '
        'font-weight="bold">PG REALITY // LANGUAGE ANALYTICS</text>',
        '<text x="35" y="75" fill="#CBD5E1" '
        'font-family="Arial,sans-serif" font-size="12">'
        'Distribuição por volume de código</text>'
    ]

    start = 0
    cx, cy, radius = 225, 195, 113

    for index, (name, value) in enumerate(displayed):
        percent = value / total * 100
        angle = value / total * 360
        color = COLORS[index % len(COLORS)]

        # Um círculo completo precisa de tratamento especial.
        if len(displayed) == 1:
            svg.append(
                f'<circle cx="{cx}" cy="{cy}" '
                f'r="{radius}" fill="{color}"/>'
            )
        else:
            path = sector_path(
                cx, cy, radius, start, start + angle
            )
            svg.append(
                f'<path d="{path}" fill="{color}" '
                'stroke="#071429" stroke-width="2"/>'
            )

        y = 108 + index * 31

        svg.extend([
            f'<circle cx="453" cy="{y}" r="6" '
            f'fill="{color}"/>',
            f'<text x="470" y="{y+5}" '
            'font-family="Arial,sans-serif" '
            'font-size="14" fill="#DBEAFE">'
            f'{escape(name)}</text>',
            f'<text x="775" y="{y+5}" '
            'font-family="Arial,sans-serif" '
            'font-size="14" text-anchor="end" '
            f'fill="#FFFFFF">{percent:.1f}%</text>'
        ])

        start += angle

    svg.extend([
        f'<circle cx="{cx}" cy="{cy}" r="69" '
        'fill="#071429"/>',
        f'<text x="{cx}" y="{cy-5}" '
        'font-family="Arial,sans-serif" font-size="21" '
        'font-weight="bold" text-anchor="middle" '
        'fill="#FFFFFF">LANG</text>',
        f'<text x="{cx}" y="{cy+20}" '
        'font-family="Arial,sans-serif" font-size="13" '
        'text-anchor="middle" fill="#60A5FA">STATS</text>',
        '<text x="35" y="323" font-family="Arial,sans-serif" '
        'font-size="11" fill="#64748B">'
        'AUTO GENERATED · GITHUB API · PUBLIC REPOSITORIES'
        '</text>',
        '</svg>'
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")

    print(f"Gráfico criado: {OUTPUT}")


if __name__ == "__main__":
    languages = collect_languages()
    generate_svg(languages)
