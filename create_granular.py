#!/usr/bin/env python3
"""
Crea una struttura di file ultra-granulare per fruizione ottimale nel sito 3D:
- data/canyons/<id>.json          # Un file per canyon (caricamento lazy)
- data/index.json                 # Indice minimale per ricerca/filtri
- data/by_country/<country>.json  # Già esistenti
- data/by_region/<region>.json    # Già esistenti
- data/search_index.json          # Indice full-text leggero
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

def slugify(text: str) -> str:
    """Crea uno slug sicuro per filename."""
    text = text.lower()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text[:100]

def main():
    base = Path("/home/pi/progetti/canyoning-scraper")
    data_dir = base / "data"
    
    # Carica dati principali
    with open(data_dir / "canyoning_data.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    canyons = data['canyons']
    
    # 1. Crea file individuali per canyon
    canyons_dir = data_dir / "canyons"
    canyons_dir.mkdir(exist_ok=True)
    
    index_entries = []
    search_entries = []
    
    for i, canyon in enumerate(canyons):
        # ID univoco
        canyon_id = f"{slugify(canyon['nazione'])}-{slugify(canyon['regione'])}-{slugify(canyon['nome'])}"
        if not canyon_id or canyon_id == '--':
            canyon_id = f"canyon-{i:04d}"
        
        # File individuale (dati completi)
        canyon_file = canyons_dir / f"{canyon_id}.json"
        canyon_file.write_text(
            json.dumps(canyon, ensure_ascii=False, indent=2), encoding='utf-8'
        )
        
        # Entry per index (minimale per listing/filtri)
        index_entries.append({
            "id": canyon_id,
            "nome": canyon['nome'],
            "nazione": canyon['nazione'],
            "regione": canyon['regione'],
            "difficolta": canyon.get('difficolta'),
            "calate": canyon.get('calate'),
            "calata_max": canyon.get('calata_max'),
            "lunghezza": canyon.get('lunghezza'),
            "dislivello": canyon.get('dislivello'),
            "tempi": canyon.get('tempi'),
            "has_kmz": bool(canyon.get('kmz_url')),
            "has_foto": bool(canyon.get('foto_urls')),
            "foto_count": len(canyon.get('foto_urls', [])),
            "file": f"canyons/{canyon_id}.json"
        })
        
        # Entry per search index (solo campi testuali ricercabili)
        search_text = " ".join(filter(None, [
            canyon['nome'],
            canyon['nazione'],
            canyon['regione'],
            canyon.get('descrizione', ''),
            canyon.get('accesso', ''),
            canyon.get('avvicinamento', ''),
            canyon.get('rientro', ''),
            canyon.get('note', ''),
        ])).lower()
        
        search_entries.append({
            "id": canyon_id,
            "nome": canyon['nome'],
            "nazione": canyon['nazione'],
            "regione": canyon['regione'],
            "search_text": search_text[:500],  # Tronca per leggerezza
        })
    
    # 2. Salva index principale (per listing, filtri, mappe)
    (data_dir / "index.json").write_text(
        json.dumps({
            "version": "1.0",
            "total": len(index_entries),
            "canyons": index_entries
        }, ensure_ascii=False, separators=(',', ':')), encoding='utf-8'
    )
    
    # 3. Salva search index (per autocomplete/ricerca full-text client-side)
    (data_dir / "search_index.json").write_text(
        json.dumps(search_entries, ensure_ascii=False, separators=(',', ':')), encoding='utf-8'
    )
    
    # 4. Crea anche index per nazione (già esistenti ma aggiornati con solo riferimenti)
    by_country_dir = data_dir / "by_country"
    by_country_dir.mkdir(exist_ok=True)
    
    countries = defaultdict(list)
    for entry in index_entries:
        countries[entry['nazione']].append(entry)
    
    for country, items in countries.items():
        safe_name = country.replace(' ', '_').replace('/', '_')
        out = by_country_dir / f"{safe_name}.json"
        out.write_text(
            json.dumps({
                "metadata": {"country": country, "count": len(items)},
                "canyons": items
            }, ensure_ascii=False, separators=(',', ':')), encoding='utf-8'
        )
    
    # 5. Crea index per regione (Italia)
    by_region_dir = data_dir / "by_region"
    by_region_dir.mkdir(exist_ok=True)
    
    italy_items = [e for e in index_entries if e['nazione'] == 'italia']
    regions = defaultdict(list)
    for entry in italy_items:
        regions[entry['regione']].append(entry)
    
    for region, items in regions.items():
        safe_name = region.replace(' ', '_').replace('/', '_').replace("'", "")
        out = by_region_dir / f"italia_{safe_name}.json"
        out.write_text(
            json.dumps({
                "metadata": {"country": "italia", "region": region, "count": len(items)},
                "canyons": items
            }, ensure_ascii=False, separators=(',', ':')), encoding='utf-8'
        )
    
    print(f"✅ Struttura granulare creata in {data_dir}")
    print(f"   - canyons/: {len(canyons)} file individuali")
    print(f"   - index.json ({len(index_entries)} entry minimali)")
    print(f"   - search_index.json ({len(search_entries)} entry per ricerca)")
    print(f"   - by_country/: {len(countries)} file")
    print(f"   - by_region/: {len(regions)} file")

if __name__ == "__main__":
    main()