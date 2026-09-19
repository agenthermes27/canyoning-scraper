#!/usr/bin/env python3
"""
Organizza i dati estratti in una struttura di cartelle pulita:
- data/
  ├── canyoning_data.json          # File principale completo
  ├── by_country/                  # Un file per nazione
  ├── by_region/                   # Un file per regione (solo Italia per ora)
  ├── geojson/                     # GeoJSON per mapping
  ├── summary.json                 # Statistiche riepilogative
  └── README.md                    # Documentazione struttura dati
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def main():
    base = Path("/home/pi/progetti/canyoning-scraper")
    data_dir = base / "data"
    
    # Carica dati principali
    with open(base / "canyoning_data.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    canyons = data['canyons']
    
    # 1. Sposta file principale in data/
    (data_dir / "canyoning_data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    (base / "canyoning_data.json").unlink(missing_ok=True)
    
    # 2. Split per nazione
    by_country_dir = data_dir / "by_country"
    countries = defaultdict(list)
    for c in canyons:
        countries[c['nazione']].append(c)
    
    for country, items in countries.items():
        safe_name = country.replace(' ', '_').replace('/', '_')
        out = by_country_dir / f"{safe_name}.json"
        out.write_text(
            json.dumps({
                "metadata": {
                    "country": country,
                    "count": len(items),
                    "source": "www.cicarudeclan.com"
                },
                "canyons": items
            }, ensure_ascii=False, indent=2), encoding='utf-8'
        )
    
    # 3. Split per regione (solo Italia)
    by_region_dir = data_dir / "by_region"
    italy_canyons = [c for c in canyons if c['nazione'] == 'italia']
    regions = defaultdict(list)
    for c in italy_canyons:
        regions[c['regione']].append(c)
    
    for region, items in regions.items():
        safe_name = region.replace(' ', '_').replace('/', '_').replace("'", "")
        out = by_region_dir / f"italia_{safe_name}.json"
        out.write_text(
            json.dumps({
                "metadata": {
                    "country": "italia",
                    "region": region,
                    "count": len(items)
                },
                "canyons": items
            }, ensure_ascii=False, indent=2), encoding='utf-8'
        )
    
    # 4. Crea GeoJSON per mapping
    geojson_dir = data_dir / "geojson"
    features = []
    for c in canyons:
        # Estrai coordinate se disponibili (da KMZ URL o altro)
        props = {
            "nome": c['nome'],
            "nazione": c['nazione'],
            "regione": c['regione'],
            "difficolta": c.get('difficolta'),
            "calate": c.get('calate'),
            "calata_max": c.get('calata_max'),
            "lunghezza": c.get('lunghezza'),
            "dislivello": c.get('dislivello'),
            "tempi": c.get('tempi'),
            "navetta": c.get('navetta'),
            "materiale": c.get('materiale'),
            "kmz_url": c.get('kmz_url'),
            "foto_count": len(c.get('foto_urls', [])),
            "url": c['url']
        }
        
        # Non abbiamo coordinate GPS dirette, ma link KMZ
        # Creiamo feature con proprietà, geometria null (da popolare dopo parsing KMZ)
        features.append({
            "type": "Feature",
            "geometry": None,
            "properties": props
        })
    
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total": len(features),
            "source": "www.cicarudeclan.com",
            "note": "Geometrie null - coordinate disponibili nei file KMZ linkati"
        }
    }
    
    (geojson_dir / "canyons.geojson").write_text(
        json.dumps(geojson, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    
    # 5. Summary statistics
    from collections import Counter
    
    summary = {
        "overview": {
            "total_canyons": len(canyons),
            "countries": len(countries),
            "with_kmz": sum(1 for c in canyons if c.get('kmz_url')),
            "with_foto": sum(1 for c in canyons if c.get('foto_urls')),
            "with_calata_max": sum(1 for c in canyons if c.get('calata_max')),
            "with_accesso": sum(1 for c in canyons if c.get('accesso')),
        },
        "by_country": {c: len(v) for c, v in sorted(countries.items(), key=lambda x: -len(x[1]))},
        "by_region_italia": {r: len(v) for r, v in sorted(regions.items(), key=lambda x: -len(x[1]))},
        "difficolta_distribution": dict(Counter(c.get('difficolta', 'N/D') for c in canyons)),
    }
    
    (data_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    
    # 6. README per la cartella data
    readme_content = """# Dati Canyoning - Struttura

## File principali
- `canyoning_data.json` — Dataset completo (329 canyon, 19 nazioni)
- `summary.json` — Statistiche riepilogative

## Suddivisioni
### `by_country/`
Un file JSON per nazione (es. `italia.json`, `francia.json`, `spagna.json`...)

### `by_region/`
Solo per Italia: un file per regione (es. `italia_Liguria.json`, `italia_Piemonte.json`...)

### `geojson/`
- `canyons.geojson` — FeatureCollection con proprietà di tutti i canyon (geometrie null, coordinate nei KMZ)

### `kmz/` (vuoto - da popolare scaricando i file KMZ)
### `images/` (vuoto - da popolare scaricando le foto)

## Schema Canyon
```json
{
  "nome": "Rio Barbaira",
  "url": "https://www.cicarudeclan.com/ita/a5_barbaira.htm",
  "nazione": "italia",
  "regione": "Liguria",
  "difficolta": "v2 a3 II",
  "periodo": "da aprile a ottobre",
  "lunghezza": "circa 1,3 km da quello basso",
  "dislivello": "140 metri (430-290)",
  "calate": "8, alcune evitabili con tuffi, calata più alta 12 metri",
  "calata_max": "12 metri",
  "ancoraggi": "ottimi - 2009",
  "tempi": "45' avvicinamento + 3h 30' discesa + 10' rientro",
  "navetta": "0 km",
  "materiale": "1 corda da 60 metri",
  "descrizione": "...",
  "accesso": "...",
  "avvicinamento": "...",
  "rientro": "...",
  "note": "...",
  "foto_urls": ["https://.../barbaira01.jpg", ...],
  "kmz_url": "https://.../Rio Barbaira.kmz",
  "scraped_at": "2026-09-19 23:07:32"
}
```

## Statistiche rapide
- **329 canyon** totali
- **19 nazioni** 
- **16 regioni italiane**
- **34 file KMZ** (10.3%) per tracce GPS
- **217 canyon con foto** (66%)
- **259 con calata_max** (78.7%)
"""
    
    (data_dir / "README.md").write_text(readme_content, encoding='utf-8')
    
    print(f"✅ Organizzazione completata in {data_dir}")
    print(f"   - canyoning_data.json ({len(canyons)} canyon)")
    print(f"   - by_country/: {len(countries)} file")
    print(f"   - by_region/: {len(regions)} file (Italia)")
    print(f"   - geojson/: 1 file")
    print(f"   - summary.json")
    print(f"   - README.md")

if __name__ == "__main__":
    main()