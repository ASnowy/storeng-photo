"""Lager pene plassholderbilder for demo (slettes når du legger inn ekte foto)."""
from __future__ import annotations
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent / "photos"

PALETTES = {
    "autumn":       [("#8b3a1d", "#e8b04a"), ("#d97a3a", "#3b2410"), ("#a64427", "#f3d07a"),
                     ("#5e2a14", "#cf6a2a"), ("#c8612b", "#fae6b3"), ("#7a3520", "#e3a45a")],
    "architecture": [("#e7e6e2", "#1a1a1c"), ("#cfd2d6", "#2c333b"), ("#ffffff", "#3a3a3a"),
                     ("#bfc5cd", "#1f2226"), ("#dadcde", "#0e1012"), ("#9aa1aa", "#202428")],
    "nature":       [("#0f3b1b", "#9bcf6a"), ("#1f5d3a", "#cfe9b3"), ("#0d2a17", "#5fa67a"),
                     ("#22442a", "#a9d28b"), ("#3a6b46", "#dfe9c5"), ("#0a3320", "#7eb88b")],
}

LABELS = {
    "autumn":       ["Park", "Skog", "Allé", "Felt", "Trær", "Lys"],
    "architecture": ["Fasade", "Vindu", "Bro", "Trappe", "Linje", "Tårn"],
    "nature":       ["Fjell", "Elv", "Stein", "Mose", "Sti", "Vann"],
}


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def make_image(out: Path, c1: str, c2: str, label: str, seed: int, year: int = 2025) -> None:
    W, H = 1800, 1200
    rng = random.Random(seed)
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    img = Image.new("RGB", (W, H), a)
    px = img.load()
    angle = rng.uniform(0, math.pi)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    diag = abs(W * cos_a) + abs(H * sin_a)
    for y in range(H):
        for x in range(W):
            t = ((x * cos_a + y * sin_a) / diag + 1) / 2
            t = max(0.0, min(1.0, t))
            px[x, y] = (
                int(a[0] + (b[0] - a[0]) * t),
                int(a[1] + (b[1] - a[1]) * t),
                int(a[2] + (b[2] - a[2]) * t),
            )
    # Litt struktur (svake "lysflekker")
    overlay = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for _ in range(60):
        cx = rng.randint(0, W)
        cy = rng.randint(0, H)
        r = rng.randint(120, 360)
        shade = rng.randint(15, 55)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(shade, shade, shade))
    overlay = overlay.filter(ImageFilter.GaussianBlur(80))
    img = Image.blend(img, Image.eval(overlay, lambda v: v), 0.18)

    # Tekst-stempel
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 70)
    except OSError:
        font = ImageFont.load_default()
    text = label
    tw, th = draw.textbbox((0, 0), text, font=font)[2:]
    draw.text(((W - tw) // 2, (H - th) // 2), text, fill=(255, 255, 255, 200), font=font)

    # Skriv inn EXIF DateTime + DateTimeOriginal slik at auto-årsdeteksjon kan testes
    exif_obj = Image.Exif()
    date_str = f"{year}:06:15 12:00:00"
    exif_obj[306] = date_str  # DateTime (top-level)
    try:
        ifd = exif_obj.get_ifd(0x8769)
        ifd[36867] = date_str  # DateTimeOriginal
        ifd[36868] = date_str  # DateTimeDigitized
    except Exception:
        pass
    img.save(out, "JPEG", quality=88, exif=exif_obj)


def main() -> None:
    # Spre årstall på bildene slik at vi kan demonstrere ulike formater:
    #   autumn       → 2024–2026 (sammenhengende intervall)
    #   architecture → 2025      (ett enkelt år)
    #   nature       → 2024, 2026 (ikke-sammenhengende)
    YEARS = {
        "autumn":       [2024, 2024, 2025, 2025, 2026, 2026],
        "architecture": [2025, 2025, 2025, 2025, 2025, 2025],
        "nature":       [2024, 2024, 2024, 2026, 2026, 2026],
    }
    for cat, palette in PALETTES.items():
        d = ROOT / cat
        d.mkdir(parents=True, exist_ok=True)
        for i, (c1, c2) in enumerate(palette, start=1):
            label = LABELS[cat][i - 1]
            year = YEARS[cat][i - 1]
            out = d / f"img-{i:02d}.jpg"
            make_image(out, c1, c2, label, seed=hash((cat, i)) & 0xFFFF, year=year)
            print(f"  {out.relative_to(ROOT.parent)}  ({year})")
    # Meta-filer (ingen year:/years: – det leses fra EXIF i demobildene)
    (ROOT / "autumn"       / "_meta.txt").write_text("title: Autumn\ndescription: Høstmotiver fra parker og skog.\n", encoding="utf-8")
    (ROOT / "architecture" / "_meta.txt").write_text("title: Architecture\ndescription: Linjer, fasader og lys i byen.\n", encoding="utf-8")
    (ROOT / "nature"       / "_meta.txt").write_text("title: Nature\ndescription: Fjell, vann og det stille i naturen.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
