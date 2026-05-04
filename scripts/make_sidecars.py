#!/usr/bin/env python3
"""
Lager tomme .txt-sidecar-filer for alle bilder som ikke allerede har en.
Kjør én gang, og igjen når du legger til nye bilder:

    python3 scripts/make_sidecars.py

En tom .txt-fil viser ingen bildetekst på siden.
Skriv én linje i filen for å vise den som bildetekst i lightbox.
"""

from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
PHOTOS_DIR = ROOT / "photos"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

created = 0
skipped = 0

for img in sorted(PHOTOS_DIR.rglob("*")):
    if img.suffix.lower() not in IMAGE_EXTS:
        continue
    if img.name.startswith("_") or img.name.startswith("."):
        continue

    sidecar = img.with_suffix(".txt")
    if sidecar.exists():
        skipped += 1
    else:
        sidecar.write_text("", encoding="utf-8")
        print(f"  + {sidecar.relative_to(ROOT)}")
        created += 1

print(f"\n✓ {created} nye sidecar-filer opprettet, {skipped} eksisterte allerede.")
