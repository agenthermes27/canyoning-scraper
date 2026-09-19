# Dati Canyoning - Struttura

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
