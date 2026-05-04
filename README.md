# storeng.photo

Personlig fotonettside som bygges automatisk fra mappestrukturen i `photos/`. Hver undermappe blir et eget galleri.

Live: <https://photo.storeng.eu>

```
photos/
├── favorites/
│   ├── _meta.txt           ← (valgfritt) tittel, beskrivelse, cover
│   ├── IMG_0001.jpeg
│   └── ...
├── architecture/
└── nature/
```

Bilder legges i undermapper, scriptet leser EXIF for årstall og lager thumbnails. GitHub Actions bygger og publiserer ved hver push.

---

## Legge til et nytt galleri

1. Lag en ny undermappe under `photos/`, f.eks. `photos/winter/`.
2. Slipp bildene inn.
3. *Valgfritt:* lag `_meta.txt` i mappa:
   ```
   title: Winter
   description: Lys og kulde fra januar.
   cover: img-04.jpg
   ```
   Alle linjer er valgfrie. Uten `cover` brukes første bilde alfabetisk.
4. Commit og push. GitHub Actions bygger og publiserer på ca. ett minutt.

### Årstall

Hentes automatisk fra `DateTimeOriginal` i EXIF-data:

| Bildene tatt | Vises som    |
|--------------|--------------|
| 2025         | `2025`       |
| 2024–2026    | `2024–2026`  |
| 2024 og 2026 | `2024, 2026` |

Overstyring i `_meta.txt`: `year: 2026` eller `years: 2024, 2026`.

### Bildetekster (vises i lightbox når man klikker et bilde)

Kamera, brennvidde, blender og lukkertid hentes automatisk fra EXIF. Kommentarteksten
kan legges til på to måter – velg den som passer arbeidsflyten:

**Metode 1 – Lightroom Caption (anbefalt for digitale bilder)**

1. Merk bildet i Lightroom.
2. Gå til **Metadata**-panelet (trykk `D` for Develop, deretter `Library`, eller bruk
   menyen View → Library).
3. Finn **Caption**-feltet og skriv inn teksten.
4. Eksporter som vanlig (`Fil → Eksporter` / `⇧⌘E`). Sørg for at
   **Metadata → Alle metadata** er valgt i eksportdialogen.

Teksten embeddes i JPEG-filen og leses automatisk ved neste bygg.

**Metode 2 – Sidecar-fil (for analoge bilder eller rask redigering)**

Lag en `.txt`-fil med nøyaktig samme navn som bildet, i samme mappe:

```
photos/nature/IMG_0474.jpg   ← bildet
photos/nature/IMG_0474.txt   ← kommentaren
```

Innholdet i `.txt`-filen brukes som bildetekst og overstyrer eventuell EXIF-caption.
Nyttig for analoge bilder som ikke har EXIF, eller når du vil endre teksten
uten å re-eksportere fra Lightroom.

### Skjul et galleri midlertidig

Gi mappa et `_`-prefiks: `_draft-winter/` blir hoppet over av build-en.

### Endre rekkefølge

Mapper sorteres alfabetisk. Bruk prefikser hvis du vil styre rekkefølgen: `01-favorites/`, `02-architecture/`.

---

## Prosjektstruktur

| Sti                       | Hva det er                                                       |
|---------------------------|------------------------------------------------------------------|
| `photos/`                 | Bildene. Hver undermappe = ett galleri.                           |
| `site_template/assets/`   | CSS og JavaScript.                                                |
| `site_template/pages/`    | Statiske sider (`/about/`, `/contact/`).                          |
| `scripts/build.py`        | Genererer `dist/` fra kilden (Python 3 + Pillow).                 |
| `.github/workflows/`      | GitHub Actions: bygg og publiser ved hver push.                    |
| `CNAME`                   | Custom domain for GitHub Pages.                                    |
| `requirements.txt`        | Python-avhengigheter.                                              |
| `dist/`                   | Bygget output (gitignored, genereres av Actions).                  |

---

## Tilpasninger

- **Tittel, taglinje, navigasjon:** `SITE`-blokka øverst i `scripts/build.py`.
- **Tema (farger, font, bakgrunn):** `site_template/assets/style.css`. CSS-variablene øverst (`--bg-base`, `--accent` osv.) styrer mørkhet og toning.
- **About- og contact-tekst:** rediger HTML-fragmentene i `site_template/pages/`.

---

## Lokal utvikling

```bash
pip install -r requirements.txt
python3 scripts/build.py
python3 -m http.server -d dist 8000
```

Åpne <http://localhost:8000>.

Build-scriptet velger automatisk URL-prefiks: tomt for custom domain (CNAME tilstede), `/<repo-navn>` for GitHub Pages uten custom domain. Kan overstyres med miljøvariabel `SITE_BASE_URL`.

---

## Lisens

Bildene er © Einar Storeng. Koden er fri å bruke som inspirasjon.
