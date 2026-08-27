#!/usr/bin/env python3
"""
Assembleur statique dentist237 v2.

Trente pages partagent le meme en-tete et le meme pied de page : les
dupliquer a la main est ingerable. Chaque page vit dans src/pages/ sous
la forme d'un fragment precede d'un bloc <!--meta {...} -->, et ce script
l'insere dans src/layout.html.

    python build.py            # genere tout le site a la racine
    python build.py --clean    # supprime d'abord les pages generees

Genere aussi, sans intervention manuelle :
  - le fil d'Ariane (visuel + JSON-LD BreadcrumbList) depuis l'URL
  - les 10 pages de quartier depuis src/data/quartiers.json
  - sitemap.xml et robots.txt
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
SITE = "https://dentist237.com"

META_RE = re.compile(r"<!--meta\s*(\{.*?\})\s*-->", re.S)
JSONLD_RE = re.compile(r"<!--jsonld\s*(\[.*?\]|\{.*?\})\s*-->", re.S)

# Libelles du fil d'Ariane par segment d'URL. Un segment absent d'ici
# retombe sur le titre court de la page elle-meme.
SEGMENTS = {
    "soins": "Soins",
    "tarifs": "Tarifs",
    "urgences": "Urgences",
    "cabinets": "Cabinets",
    "contact": "Contact",
    "rendez-vous": "Rendez-vous",
    "a-propos": "À propos",
    "equipe": "Notre équipe",
    "yaounde": "Yaoundé",
    "mentions-legales": "Mentions légales",
}


def out_path(url: str) -> Path:
    """/soins/detartrage/ -> soins/detartrage/index.html"""
    if url == "/":
        return ROOT / "index.html"
    return ROOT / url.strip("/") / "index.html"


def breadcrumb(url: str, short: str) -> tuple[str, dict]:
    """Retourne (html, JSON-LD BreadcrumbList) pour une URL donnee."""
    if url == "/":
        return "", {}

    parts = [p for p in url.strip("/").split("/") if p]
    crumbs = [("Accueil", "/")]
    acc = ""
    for i, part in enumerate(parts):
        acc += "/" + part
        last = i == len(parts) - 1
        label = short if last else SEGMENTS.get(part, part.replace("-", " ").capitalize())
        crumbs.append((label, acc + "/"))

    items = []
    for i, (label, href) in enumerate(crumbs, start=1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "name": label,
            "item": SITE + href,
        })

    links = []
    for label, href in crumbs[:-1]:
        links.append(f'<a href="{href}">{label}</a>')
    links.append(f'<span aria-current="page">{crumbs[-1][0]}</span>')

    html = (
        '<nav class="crumbs" aria-label="Fil d\'Ariane"><div class="wrap">'
        + "".join(links)
        + "</div></nav>"
    )
    return html, {"@type": "BreadcrumbList", "itemListElement": items}


def parse_page(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")

    m = META_RE.search(raw)
    if not m:
        sys.exit(f"[erreur] {path.name} : bloc <!--meta {{...}} --> manquant")
    meta = json.loads(m.group(1))
    body = raw[m.end():]

    graph = []
    j = JSONLD_RE.search(body)
    if j:
        parsed = json.loads(j.group(1))
        graph = parsed if isinstance(parsed, list) else [parsed]
        body = body[: j.start()] + body[j.end():]

    meta["body"] = body.strip()
    meta["graph"] = graph
    return meta


def render(meta: dict, layout: str, sprite: str, footer: str) -> str:
    url = meta["url"]
    short = meta.get("short", meta["title"].split("—")[0].strip())

    crumb_html, crumb_ld = breadcrumb(url, short)
    graph = ([crumb_ld] if crumb_ld else []) + meta["graph"]
    jsonld = json.dumps(
        {"@context": "https://schema.org", "@graph": graph},
        ensure_ascii=False,
        indent=1,
    ) if graph else "{}"

    html = layout
    html = html.replace("{{SPRITE}}", sprite)
    html = html.replace("{{FOOTER}}", footer)
    html = html.replace("{{CONTENT}}", crumb_html + "\n" + meta["body"])
    html = html.replace("{{JSONLD}}", jsonld)
    html = html.replace("{{TITLE}}", meta["title"])
    html = html.replace("{{DESC}}", meta["desc"])
    html = html.replace("{{URL}}", url)
    html = html.replace("{{OGTYPE}}", meta.get("ogtype", "website"))
    html = html.replace(
        "{{ROBOTS}}",
        '<meta name="robots" content="noindex,follow">' if meta.get("noindex") else "",
    )

    active = meta.get("nav", "")
    for key in ("cabinets", "soins", "tarifs", "urgences", "apropos", "contact"):
        html = html.replace(
            "{{NAV_" + key + "}}",
            ' aria-current="page" class="is-active"' if key == active else "",
        )
    return html


def build_quartiers() -> list[dict]:
    """Les 10 pages de quartier : meme gabarit, contenu propre a chacune.

    Elles sont generees plutot qu'ecrites a la main parce qu'elles
    partagent 80 % de leur structure. Ce qui les differencie (acces,
    reperes, distance) vient de quartiers.json : sans ces champs on
    produirait 10 pages quasi identiques, ce que Google traite comme
    du contenu mince.
    """
    data = json.loads((SRC / "data" / "quartiers.json").read_text(encoding="utf-8"))
    tpl = (SRC / "templates" / "quartier.html").read_text(encoding="utf-8")
    pages = []

    for q in data:
        body = tpl
        for key, val in q.items():
            if isinstance(val, list):
                continue
            body = body.replace("{{" + key + "}}", str(val))

        reperes = "".join(f"<li>{r}</li>" for r in q["reperes"])
        body = body.replace("{{REPERES}}", reperes)

        pages.append({
            "url": f"/yaounde/dentiste-{q['slug']}/",
            "title": f"Dentiste à {q['nom']} (Yaoundé) — Cabinet dentist237",
            "short": f"Dentiste {q['nom']}",
            "desc": q["meta"],
            "nav": "",
            "body": body,
            "graph": [{
                "@type": "Dentist",
                "name": f"dentist237 — dentiste pour {q['nom']}",
                "url": f"{SITE}/yaounde/dentiste-{q['slug']}/",
                "telephone": "+237694885836",
                "areaServed": {"@type": "Place", "name": f"{q['nom']}, Yaoundé"},
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "Avenue Charles de Gaulle, face Omnisport-Mfandena",
                    "addressLocality": "Yaoundé",
                    "addressCountry": "CM",
                },
            }],
        })
    return pages


def sitemap(urls: list[str]) -> str:
    body = "".join(
        f"\n  <url><loc>{SITE}{u}</loc><changefreq>monthly</changefreq></url>"
        for u in sorted(urls)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{body}\n</urlset>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true", help="supprime les dossiers generes")
    args = ap.parse_args()

    generated_dirs = ["soins", "tarifs", "urgences", "cabinets", "contact",
                      "rendez-vous", "a-propos", "yaounde", "mentions-legales"]
    if args.clean:
        for d in generated_dirs:
            shutil.rmtree(ROOT / d, ignore_errors=True)
        print("[clean] dossiers generes supprimes")

    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    sprite = (SRC / "_sprite.html").read_text(encoding="utf-8")
    footer = (SRC / "footer.html").read_text(encoding="utf-8")

    pages = [parse_page(p) for p in sorted((SRC / "pages").glob("*.html"))]
    pages += build_quartiers()

    indexable = []
    for meta in pages:
        target = out_path(meta["url"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(meta, layout, sprite, footer), encoding="utf-8")
        if not meta.get("noindex"):
            indexable.append(meta["url"])
        print(f"  {meta['url']:<42} -> {target.relative_to(ROOT)}")

    # La plupart des hebergeurs (Apache ErrorDocument, Netlify, Vercel)
    # attendent /404.html a la racine, pas /404/index.html.
    src404 = ROOT / "404" / "index.html"
    if src404.exists():
        (ROOT / "404.html").write_text(src404.read_text(encoding="utf-8"), encoding="utf-8")

    (ROOT / "sitemap.xml").write_text(sitemap(indexable), encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8"
    )

    print(f"\n{len(pages)} pages generees, {len(indexable)} indexables.")


if __name__ == "__main__":
    main()
