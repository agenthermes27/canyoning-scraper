# Canyoning Scraper - Cica Rude Clan

Scraper per estrarre tutte le schede tecniche di canyoning da www.cicarudeclan.com

## Struttura del sito
Il sito usa **frames** (vecchia scuola anni '90):
- `left.htm` - Menu laterale (non usato per contenuto)
- `middle.htm` - Contenuto principale 
- `bottom_1.htm` - Footer/navigazione
- `ita/schede.htm` - Indice schede per nazione (menu laterale dentro frame)
- `ita/a5_*.htm` - Pagine elenco canyon per regione
- `ita/a5_*.htm` - Schede singole canyon (es. `a5_barbaira.htm`)

## Installazione
```bash
cd /home/pi/progetti/canyoning-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso
```bash
# Scraping completo (tutte le nazioni, tutte le schede)
python scraper.py --all

# Solo Italia
python scraper.py --country italia

# Solo una scheda specifica
python scraper.py --url https://www.cicarudeclan.com/ita/a5_barbaira.htm

# Export JSON
python scraper.py --all --output canyoning_data.json
```