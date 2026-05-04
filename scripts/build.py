#!/usr/bin/env python3
"""
Bygger den statiske fotosiden fra mappestrukturen i photos/.

Hver undermappe i photos/ blir et galleri. Eksempel:

    photos/
      autumn/
        _meta.txt        (valgfritt: tittel, år, beskrivelse)
        cover.jpg        (valgfritt: forside-bilde. Hvis ikke, brukes første bilde alfabetisk)
        IMG_001.jpg
        IMG_002.jpg
      moments/
        ...

Output havner i dist/ og er klar for GitHub Pages.

Krever Pillow:  pip install Pillow
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageOps

# ---------- Konfigurasjon ----------
ROOT = Path(__file__).resolve().parent.parent
PHOTOS_DIR = ROOT / "photos"
TEMPLATE_DIR = ROOT / "site_template"
DIST_DIR = ROOT / "dist"


def detect_base_url() -> str:
    """Bestem URL-prefiks for alle absolutte lenker:

    - Custom domene (CNAME-fil i repo-rota): tomt prefiks (siden serveres fra rot).
    - GitHub Pages uten custom domene: '/<repo-navn>' (siden serveres i undermappe).
    - Lokalt (python -m http.server -d dist): tomt prefiks.
    Kan overstyres med miljøvariabel SITE_BASE_URL.
    """
    override = os.environ.get("SITE_BASE_URL")
    if override is not None:
        return override.rstrip("/")
    if (ROOT / "CNAME").exists():
        return ""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo and "/" in repo:
        return "/" + repo.split("/", 1)[1]
    return ""


BASE_URL = detect_base_url()

THUMB_MAX = 1400          # bredeste/høyeste side på grid-thumbnails
FULL_MAX = 2400           # bredeste/høyeste side på lightbox-bilder
JPEG_QUALITY = 85

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Site-tekst (kan endres her uten å rote i HTML)
SITE = {
    "title": "Einar Storeng",
    "tagline": "Arkitektur, byliv og naturmotiver — Architecture, city life, and nature",
    "footer": "© Einar Storeng",
    "nav": [
        ("Photos", "/"),
        ("Om meg", "/about/"),
        ("Contact", "/contact/"),
    ],
    "goatcounter": "storeng-photo",   # ← bytt ut med din GoatCounter site-kode
}


# ---------- Datamodell ----------
@dataclass
class Photo:
    src: Path           # original-fil
    rel: str            # "autumn/IMG_001.jpg" (relativt til photos/)
    width: int = 0
    height: int = 0
    year: int | None = None
    camera: str = ""
    focal_length: str = ""
    aperture: str = ""
    shutter: str = ""
    comment: str = ""


@dataclass
class Gallery:
    slug: str
    title: str
    year: str = ""        # ferdig formatert årstall-tekst, f.eks. "2024–2026"
    description: str = ""
    photos: list[Photo] = field(default_factory=list)
    cover: Photo | None = None


# ---------- Hjelpere ----------
def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "gallery"


def read_exif(src: Path) -> dict:
    """Les EXIF: år, kamera, brennvidde, blender, lukkertid og kommentar."""
    result: dict = {}
    try:
        with Image.open(src) as im:
            exif = im.getexif()
            ifd  = exif.get_ifd(0x8769)  # ExifIFD

            # År
            date_str = ifd.get(36867) or ifd.get(36868) or exif.get(306)
            if date_str and len(date_str) >= 4:
                try:
                    y = int(date_str[:4])
                    if 1900 <= y <= 2100:
                        result["year"] = y
                except ValueError:
                    pass

            def rat(val):
                try:
                    if hasattr(val, "numerator"):
                        d = float(val.denominator)
                        return float(val.numerator) / d if d else None
                    if isinstance(val, tuple):
                        return float(val[0]) / float(val[1]) if val[1] else None
                    return float(val)
                except Exception:
                    return None

            # Kameramodell (tag 272)
            model = exif.get(272) or ""
            if isinstance(model, bytes):
                model = model.decode("utf-8", errors="ignore")
            model = model.strip()
            if model:
                result["camera"] = model

            # Brennvidde (tag 37386)
            fl = rat(ifd.get(37386))
            if fl and fl > 0:
                result["focal_length"] = f"{round(fl)} mm"

            # Blenderåpning / f-tall (tag 33437)
            fn = rat(ifd.get(33437))
            if fn and fn > 0:
                result["aperture"] = f"f/{fn:g}"

            # Lukkertid (tag 33434)
            et = rat(ifd.get(33434))
            if et and et > 0:
                result["shutter"] = f"1/{round(1/et)}s" if et < 1 else f"{et:g}s"

            # Kommentar: ImageDescription (270) → UserComment (37510)
            desc = exif.get(270) or ""
            if isinstance(desc, bytes):
                desc = desc.decode("utf-8", errors="ignore")
            desc = desc.strip()
            if not desc:
                uc = ifd.get(37510) or b""
                if isinstance(uc, bytes) and len(uc) > 8:
                    desc = uc[8:].decode("utf-8", errors="ignore").strip("\x00").strip()
            if desc:
                result["comment"] = desc

    except Exception:
        pass
    return result


def format_years(years: list[int]) -> str:
    """[2024, 2025, 2026] -> '2024–2026'. [2024, 2026] -> '2024, 2026'."""
    if not years:
        return ""
    years = sorted(set(years))
    if len(years) == 1:
        return str(years[0])
    if years == list(range(years[0], years[-1] + 1)):
        return f"{years[0]}–{years[-1]}"  # en-dash
    return ", ".join(str(y) for y in years)


def parse_meta(path: Path) -> dict:
    """Les enkel KEY: value-format i _meta.txt."""
    meta: dict = {}
    if not path.exists():
        return meta
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip().lower()] = value.strip()
    return meta


def collect_galleries() -> list[Gallery]:
    galleries: list[Gallery] = []
    if not PHOTOS_DIR.exists():
        return galleries

    for folder in sorted(p for p in PHOTOS_DIR.iterdir() if p.is_dir()):
        if folder.name.startswith("_") or folder.name.startswith("."):
            continue

        meta = parse_meta(folder / "_meta.txt")
        title = meta.get("title") or folder.name.replace("-", " ").replace("_", " ").title()
        description = meta.get("description", "")
        custom_cover = meta.get("cover", "")

        photos: list[Photo] = []
        for f in sorted(folder.iterdir()):
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS and not f.name.startswith("_"):
                photos.append(Photo(src=f, rel=f"{folder.name}/{f.name}"))
        if not photos:
            continue

        # Les EXIF for alle bilder (år + visnings-metadata)
        for p in photos:
            data = read_exif(p.src)
            p.camera       = data.get("camera", "")
            p.focal_length = data.get("focal_length", "")
            p.aperture     = data.get("aperture", "")
            p.shutter      = data.get("shutter", "")
            p.comment      = data.get("comment", "")
            p.year         = data.get("year")
            # Sidecar-fil (.txt med samme navn) overstyrer EXIF-kommentar
            sidecar = p.src.with_suffix(".txt")
            if sidecar.exists():
                text = sidecar.read_text(encoding="utf-8").strip()
                if text:
                    p.comment = text

        # Årstall: _meta.txt vinner over EXIF
        year_str = ""
        if meta.get("year"):
            year_str = meta["year"]
        elif meta.get("years"):
            try:
                ys = [int(y.strip()) for y in re.split(r"[,\s]+", meta["years"]) if y.strip()]
                year_str = format_years(ys)
            except ValueError:
                year_str = meta["years"]
        else:
            ys = [p.year for p in photos if p.year]
            year_str = format_years(ys)

        # Cover-bilde: 1) navngitt i _meta.txt, 2) cover.jpg, 3) første bilde
        cover: Photo | None = None
        if custom_cover:
            for p in photos:
                if p.src.name.lower() == custom_cover.lower():
                    cover = p
                    break
        if cover is None:
            for p in photos:
                if p.src.stem.lower() == "cover":
                    cover = p
                    break
        if cover is None:
            cover = photos[0]

        galleries.append(
            Gallery(
                slug=slugify(folder.name),
                title=title,
                year=year_str,
                description=description,
                photos=photos,
                cover=cover,
            )
        )
    return galleries


def write_resized(src: Path, dst: Path, max_dim: int) -> tuple[int, int]:
    """Lag forminsket variant av et bilde. Returnerer (width, height)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        with Image.open(dst) as im:
            return im.size

    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)  # respekter rotasjons-EXIF
        im.thumbnail((max_dim, max_dim), Image.LANCZOS)
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        im.save(dst, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        return im.size


# ---------- HTML-rendering ----------
def render_layout(title: str, body: str, *, active: str = "/") -> str:
    nav_items = "".join(
        f'<a class="{"active" if href == active else ""}" href="{BASE_URL}{href}">{html.escape(label)}</a>'
        for label, href in SITE["nav"]
    )
    return f"""<!doctype html>
<html lang="no">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — {html.escape(SITE["title"])}</title>
<link rel="stylesheet" href="{BASE_URL}/assets/style.css">
<meta name="description" content="{html.escape(SITE["tagline"])}">
</head>
<body>
<header class="site-header">
  <a class="brand" href="{BASE_URL}/">{html.escape(SITE["title"])}</a>
  <nav class="site-nav">{nav_items}</nav>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <span>{html.escape(SITE["footer"])}</span>
</footer>
<script src="{BASE_URL}/assets/lightbox.js" defer></script>
{f'<script data-goatcounter="https://{SITE["goatcounter"]}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>' if SITE.get("goatcounter") else ''}
</body>
</html>
"""


def render_index(galleries: list[Gallery]) -> str:
    cards = []
    for g in galleries:
        cover_thumb = f"{BASE_URL}/photos/{g.slug}/_thumb_{g.cover.src.stem}.jpg"
        cards.append(f"""
<a class="card" href="{BASE_URL}/{g.slug}/">
  <div class="card-image">
    <img loading="lazy" src="{cover_thumb}" alt="{html.escape(g.title)}">
  </div>
  <div class="card-meta">
    <h2>{html.escape(g.title)}</h2>
    {f'<span class="year">{html.escape(g.year)}</span>' if g.year else ''}
  </div>
</a>""")

    body = f"""
<section class="hero">
  <h1>{html.escape(SITE["tagline"])}</h1>
</section>
<section class="grid">
{''.join(cards)}
</section>
"""
    return render_layout(SITE["title"], body, active="/")


def render_gallery(g: Gallery) -> str:
    items = []
    for i, p in enumerate(g.photos):
        thumb = f"{BASE_URL}/photos/{g.slug}/_thumb_{p.src.stem}.jpg"
        full = f"{BASE_URL}/photos/{g.slug}/_full_{p.src.stem}.jpg"
        attrs = ""
        if p.camera:        attrs += f' data-camera="{html.escape(p.camera)}"'
        if p.focal_length:  attrs += f' data-focal="{html.escape(p.focal_length)}"'
        if p.aperture:      attrs += f' data-aperture="{html.escape(p.aperture)}"'
        if p.shutter:       attrs += f' data-shutter="{html.escape(p.shutter)}"'
        if p.comment:       attrs += f' data-comment="{html.escape(p.comment)}"'
        items.append(
            f'<figure class="photo" data-index="{i}"{attrs}>'
            f'<img loading="lazy" src="{thumb}" data-full="{full}" '
            f'width="{p.width}" height="{p.height}" alt="{html.escape(p.src.stem)}">'
            f'</figure>'
        )

    body = f"""
<section class="gallery-header">
  <a class="back" href="{BASE_URL}/">← Tilbake</a>
  <h1>{html.escape(g.title)}</h1>
  {f'<p class="year">{html.escape(g.year)}</p>' if g.year else ''}
  {f'<p class="description">{html.escape(g.description)}</p>' if g.description else ''}
</section>
<section class="masonry">
{''.join(items)}
</section>
<div id="lightbox" hidden>
  <button class="lightbox-close" aria-label="Lukk">×</button>
  <button class="lightbox-prev" aria-label="Forrige">‹</button>
  <button class="lightbox-next" aria-label="Neste">›</button>
  <img alt="">
  <div class="lightbox-info" hidden></div>
</div>
"""
    return render_layout(g.title, body, active="/")


def render_static_page(slug: str, title: str, body_html: str) -> str:
    return render_layout(title, body_html, active=f"/{slug}/")


def print_config() -> None:
    if BASE_URL:
        print(f"  BASE_URL = '{BASE_URL}'  (siden serveres i undermappe)")
    else:
        print("  BASE_URL = ''  (siden serveres fra rot)")


# ---------- Hovedflyt ----------
def build():
    print(f"→ Bygger fra {PHOTOS_DIR}")
    print_config()
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    # Kopier statiske assets
    assets_src = TEMPLATE_DIR / "assets"
    if assets_src.exists():
        shutil.copytree(assets_src, DIST_DIR / "assets")

    # Statiske sider (about, contact) som markdown- eller html-fragmenter
    pages_src = TEMPLATE_DIR / "pages"
    if pages_src.exists():
        for page_file in pages_src.glob("*.html"):
            slug = page_file.stem
            content = page_file.read_text(encoding="utf-8")
            # Tittel hentes fra første <h1> hvis mulig
            m = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.IGNORECASE | re.DOTALL)
            title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else slug.title()
            out = DIST_DIR / slug / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render_static_page(slug, title, content), encoding="utf-8")
            print(f"  ✓ side: /{slug}/")

    # Bygg gallerier
    galleries = collect_galleries()
    print(f"  Fant {len(galleries)} gallerier")

    for g in galleries:
        out_dir = DIST_DIR / "photos" / g.slug
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in g.photos:
            thumb_path = out_dir / f"_thumb_{p.src.stem}.jpg"
            full_path = out_dir / f"_full_{p.src.stem}.jpg"
            write_resized(p.src, thumb_path, THUMB_MAX)
            w, h = write_resized(p.src, full_path, FULL_MAX)
            p.width, p.height = w, h

        gallery_html = render_gallery(g)
        gallery_index = DIST_DIR / g.slug / "index.html"
        gallery_index.parent.mkdir(parents=True, exist_ok=True)
        gallery_index.write_text(gallery_html, encoding="utf-8")
        print(f"  ✓ galleri: /{g.slug}/  ({len(g.photos)} bilder)")

    # Forside
    (DIST_DIR / "index.html").write_text(render_index(galleries), encoding="utf-8")

    # Sitemap (enkel)
    sm = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
          f"<url><loc>{BASE_URL}/</loc></url>"]
    for g in galleries:
        sm.append(f"<url><loc>{BASE_URL}/{g.slug}/</loc></url>")
    sm.append("</urlset>")
    (DIST_DIR / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # CNAME-fil for tilpasset domene legges av deploy-stega via repo-rota.
    print(f"\n✓ Ferdig. Output i {DIST_DIR}")


if __name__ == "__main__":
    build()
