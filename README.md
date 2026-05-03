# storeng.photo — fotosida

Automatisk fotonettside som bygges fra mappestrukturen i `photos/`.
Hver undermappe blir et eget galleri på sida.

```
photos/
├── autumn/
│   ├── _meta.txt          ← (valgfritt) tittel, år, beskrivelse
│   ├── img-01.jpg
│   ├── img-02.jpg
│   └── ...
├── architecture/
└── nature/
```

Når du dytter (`git push`) nye bilder til GitHub, bygges sida om og publiseres til `photo.storeng.eu` automatisk via GitHub Actions. Du trenger aldri å skrive HTML.

---

## Slik tar du det i bruk – steg for steg

### 1. Engangsoppsett (gjør én gang)

1. **Lag en GitHub-konto** på [github.com](https://github.com) hvis du ikke har en.
2. **Last ned [GitHub Desktop](https://desktop.github.com/)** – det er en gratis app som lar deg dra-og-slippe filer uten å bruke kommandolinje.
3. **Lag et nytt repository** (klikk «New repository» på github.com). Kall det for eksempel `storeng-photo`. Sett det til *Public* (kreves for gratis GitHub Pages).
4. **Last opp denne mappa** til repoet:
   - Åpne GitHub Desktop → *File* → *Add Local Repository* → velg denne mappa
   - Klikk *Publish repository*
5. **Skru på GitHub Pages**:
   - Gå til repoet på github.com → *Settings* → *Pages*
   - Under «Build and deployment»: *Source* = **GitHub Actions**
   - Vent et par minutter, så ligger sida på `https://<brukernavn>.github.io/storeng-photo/`
6. **Koble til ditt eget domene** (`photo.storeng.eu`):
   - I `CNAME`-fila i denne mappa står allerede `photo.storeng.eu`. Bra.
   - Gå til DNS-leverandøren din for `storeng.eu` og legg til en **CNAME-record**:
     - Name: `photo`
     - Value: `<ditt-brukernavn>.github.io`
   - Tilbake i *Settings → Pages*: skriv inn `photo.storeng.eu` under «Custom domain» og kryss av «Enforce HTTPS» (kan ta noen timer før det blir tilgjengelig).

### 2. Hverdagsbruk – legg til nye bilder

Den enkleste flyten:

1. **Lag en ny mappe** under `photos/` på maskinen din, f.eks. `photos/winter/`.
2. **Slipp bildene dine inn** i mappa.
3. *Valgfritt:* lag en fil `_meta.txt` i mappa med:
   ```
   title: Winter
   description: Lys og kulde fra Bergen i januar.
   cover: img-04.jpg
   ```
   (Alle linjer er valgfrie. Hvis du dropper `cover`, brukes første bilde alfabetisk.)
   **Årstall trenger du som regel ikke skrive** – det leses automatisk fra EXIF i bildene
   og vises som «2025», «2024–2026» (sammenhengende) eller «2024, 2026» (med hopp).
   Vil du overstyre, skriv `year: 2026` eller `years: 2024, 2026` i `_meta.txt`.
4. **Åpne GitHub Desktop**, skriv en kort melding (f.eks. «Lagt til Winter»), klikk *Commit* → *Push origin*.
5. **Vent ca. 1–2 minutter**. GitHub Actions bygger og publiserer sida på `photo.storeng.eu`.

Det er alt. Du trenger aldri å forstå HTML, CSS eller PHP.

---

## Hva er hva i denne mappa

| Fil/mappe                 | Hva det er                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `photos/`                 | **Bildene dine.** Hver undermappe = ett galleri på sida.                    |
| `site_template/assets/`   | CSS og JavaScript. Endre `style.css` hvis du vil pusle med design.          |
| `site_template/pages/`    | Tekstene på `/about/` og `/contact/`. Rediger fritt – det er bare HTML.     |
| `scripts/build.py`        | Byggescriptet. Du trenger ikke å røre dette.                                |
| `.github/workflows/`      | Automatikk. Kjører ved hver push.                                            |
| `CNAME`                   | Forteller GitHub hvilket domene som skal brukes.                             |
| `dist/`                   | Bygget output (genereres automatisk – ligger ikke i Git).                    |
| `preview.html`            | Selvstendig forhåndsvisning du kan dobbeltklikke for å se designet.          |

---

## Kjøre lokalt (valgfritt – bra for å teste før du pusher)

Krever Python 3 og `Pillow`:

```bash
pip install Pillow
python3 scripts/build.py
python3 -m http.server -d dist 8000
```

Åpne deretter <http://localhost:8000> i nettleseren.

---

## Tilpasninger

- **Endre tittelen, taglinjen eller menyen**: rediger `SITE`-blokka øverst i `scripts/build.py`.
- **Endre fonten eller fargene**: `site_template/assets/style.css` (alt ligger i `:root`-variablene øverst).
- **Endre rekkefølgen på galleriene**: legg til prefiks i mappenavnet, f.eks. `01-autumn/`, `02-architecture/`. Mapper sorteres alfabetisk.
- **Skjul et galleri midlertidig**: gi mappa et prefiks `_`, f.eks. `_draft-winter/`.

---

## Bytte fra de gamle sidene

- **storeng.eu** (WordPress på InfinityFree): du kan la den ligge til alt fungerer på `photo.storeng.eu`, og deretter sette opp en `redirect` fra rot-domenet til `photo.storeng.eu/` om du vil.
- **storeng.photo** (Adobe Portfolio): når den nye sida er på plass kan du laste ned originalbildene fra Adobe og legge dem inn i `photos/<galleri-navn>/` her.

---

## Spørsmål eller småfiks

Det er bare HTML, CSS, litt Python og en YAML-fil. Spør gjerne om hjelp til endringer – det krever ikke at du blir webutvikler.
