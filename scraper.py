#!/usr/bin/env python3
"""
Cica Rude Clan Canyoning Scraper

Estrae tutte le schede tecniche da www.cicarudeclan.com
Output: JSON strutturato con tutte le informazioni.
"""

import re
import json
import time
import argparse
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


BASE_URL = "https://www.cicarudeclan.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CanyoningScraper/1.0; +https://github.com/your-repo)"
}


@dataclass
class Canyon:
    """Schema per una scheda canyon."""
    # Identificativi
    nome: str
    url: str
    nazione: str
    regione: str
    
    # Scheda tecnica
    difficolta: Optional[str] = None
    periodo: Optional[str] = None
    lunghezza: Optional[str] = None
    dislivello: Optional[str] = None
    calate: Optional[str] = None
    calata_max: Optional[str] = None
    ancoraggi: Optional[str] = None
    tempi: Optional[str] = None
    navetta: Optional[str] = None
    materiale: Optional[str] = None
    
    # Descrizioni
    descrizione: Optional[str] = None
    accesso: Optional[str] = None
    avvicinamento: Optional[str] = None
    rientro: Optional[str] = None
    note: Optional[str] = None
    
    # Media
    foto_urls: List[str] = field(default_factory=list)
    kmz_url: Optional[str] = None
    
    # Metadata
    scraped_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class CicaRudeScraper:
    def __init__(self, delay: float = 1.0):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay
        self.canyons: List[Canyon] = []
        self.visited_urls = set()
        
    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        if url in self.visited_urls:
            return None
        self.visited_urls.add(url)
        
        time.sleep(self.delay)
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            # Il sito usa iso-8859-1
            resp.encoding = 'iso-8859-1'
            return BeautifulSoup(resp.text, 'lxml')
        except Exception as e:
            print(f"[ERROR] Fetch {url}: {e}")
            return None
    
    def get_country_pages(self) -> Dict[str, str]:
        """Estrae le pagine elenco per nazione da ita/schede.htm"""
        url = urljoin(BASE_URL, "/ita/schede.htm")
        soup = self.fetch(url)
        if not soup:
            return {}
        
        countries = {}
        # Link nel menu laterale: a5_ita.htm, a5_fra.htm, etc.
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('a5_') and href.endswith('.htm'):
                # Nome nazione dal testo del link o dall'immagine
                name = link.get_text(strip=True)
                if not name:
                    img = link.find('img')
                    if img:
                        name = img.get('name', '') or img.get('alt', '')
                name = name.lower().replace(' ', '_')
                countries[name] = urljoin(BASE_URL, f"/ita/{href}")
        
        return countries
    
    def get_canyon_links_from_country_soup(self, soup: BeautifulSoup, country_url: str) -> List[tuple]:
        """Estrae tutti i link alle schede canyon da una soup già parsata."""
        links = []
        seen_urls = set()
        # Pattern: <img src="../img/p-green.gif"> <a href="a5_barbaira.htm">Rio Barbaira</a>
        for img in soup.find_all('img', src=True):
            if 'p-green.gif' in img['src'] or 'p-yellow.gif' in img['src'] or 'p-red.gif' in img['src']:
                # Il link è il prossimo sibling <a>
                parent = img.parent
                if parent and parent.name == 'a':
                    href = parent.get('href', '')
                    name = parent.get_text(strip=True)
                else:
                    # Cerca il link successivo
                    next_a = img.find_next('a')
                    if next_a:
                        href = next_a.get('href', '')
                        name = next_a.get_text(strip=True)
                    else:
                        continue
                
                if href and href.endswith('.htm'):
                    full_url = urljoin(country_url, href)
                    # Deduplica: lo stesso canyon appare in 4 tabelle identiche
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        links.append((name, full_url))
        
        return links
    
    def get_canyon_links_from_country(self, country_url: str) -> List[tuple]:
        """Estrae tutti i link alle schede canyon da una pagina nazione."""
        soup = self.fetch(country_url)
        if not soup:
            return []
        return self.get_canyon_links_from_country_soup(soup, country_url)
    
    def parse_canyon_page(self, url: str, nazione: str, regione: str) -> Optional[Canyon]:
        """Parsa una singola scheda canyon."""
        soup = self.fetch(url)
        if not soup:
            return None
        
        # Titolo
        title_tag = soup.find('title')
        nome = title_tag.get_text(strip=True) if title_tag else ""
        nome = nome.replace("CICA RUDE CLAN - ", "").strip()
        
        # Descrizione principale (primo paragrafo sotto il titolo)
        descrizione = ""
        first_table = soup.find('table', width="600")
        if first_table:
            desc_cell = first_table.find('td', width="345")
            if desc_cell:
                descrizione = desc_cell.get_text(strip=True)
        
        # Tabella dati tecnici (quella con border=1)
        tech_data = {}
        tech_table = soup.find('table', border="1")
        if tech_table:
            for row in tech_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).rstrip(':')
                    value = cells[1].get_text(strip=True)
                    tech_data[key] = value
        
        # Mappa campi
        field_map = {
            'Difficoltà': 'difficolta',
            'Difficoltà:': 'difficolta',
            'Periodo': 'periodo',
            'Periodo:': 'periodo',
            'Lunghezza': 'lunghezza',
            'Lunghezza:': 'lunghezza',
            'Dislivello': 'dislivello',
            'Dislivello:': 'dislivello',
            'Calate': 'calate',
            'Calate:': 'calate',
            'Ancoraggi': 'ancoraggi',
            'Ancoraggi:': 'ancoraggi',
            'Tempi': 'tempi',
            'Tempi:': 'tempi',
            'Navetta': 'navetta',
            'Navetta:': 'navetta',
            'Materiale': 'materiale',
            'Materiale:': 'materiale',
        }
        
        canyon = Canyon(
            nome=nome,
            url=url,
            nazione=nazione,
            regione=regione,
            descrizione=descrizione,
        )
        
        for key, value in tech_data.items():
            field_name = field_map.get(key)
            if field_name:
                setattr(canyon, field_name, value)
        
        # Estrai calata_max da calate se presente
        if canyon.calate:
            # Cerca pattern come "calata più alta 12 metri" o "calata piu' alta 13 metri"
            # Il carattere ù (U+00F9) è in iso-8859-1, usiamo regex flessibile
            match = re.search(r'calata pi[ùu].?alta (\d+)', canyon.calate, re.IGNORECASE)
            if match:
                canyon.calata_max = f"{match.group(1)} metri"
        
        # Foto (thumbnail nella prima tabella)
        if first_table:
            for img in first_table.find_all('img'):
                src = img.get('src', '')
                if src and 'galleria' in src:
                    full_url = urljoin(url, src.replace('_', ''))  # _barbaira01.jpg -> barbaira01.jpg
                    canyon.foto_urls.append(full_url)
        
        # KMZ
        for link in soup.find_all('a', href=True):
            if '.kmz' in link['href']:
                canyon.kmz_url = urljoin(url, link['href'])
                break
        
        # Accesso, Avvicinamento, Rientro, Note (tabella finale)
        final_tables = soup.find_all('table', width="600")
        for table in final_tables:
            for row in table.find_all('tr'):
                cell = row.find('td')
                if cell:
                    text = cell.get_text(strip=True)
                    if text.startswith('Accesso'):
                        canyon.accesso = text.replace('Accesso:', '').strip()
                    elif text.startswith('Avvicinamento'):
                        canyon.avvicinamento = text.replace('Avvicinamento:', '').strip()
                    elif text.startswith('Rientro'):
                        canyon.rientro = text.replace('Rientro:', '').strip()
                    elif text.startswith('Nota:'):
                        canyon.note = text.replace('Nota:', '').strip()
        
        return canyon
    
    def scrape_country(self, country_name: str, country_url: str) -> List[Canyon]:
        """Scrapa tutti i canyon di una nazione."""
        print(f"\n📍 Scraping {country_name} da {country_url}")
        
        # Fetch la pagina una sola volta
        soup = self.fetch(country_url)
        if not soup:
            return []
        
        # Estrai link canyon dalla soup già fetchata
        links = self.get_canyon_links_from_country_soup(soup, country_url)
        print(f"   Trovati {len(links)} canyon")
        
        # Parsia la pagina paese per estrarre regione per ogni link canyon
        # La pagina ha la stessa tabella ripetuta 4 volte - usiamo solo la PRIMA che ha region headers
        # Colori header regione variano per paese: Italia=#3C7878, Francia=#143278, Spagna=#C8A014, etc.
        regione_per_link = {}
        target_table = None
        
        # Trova la prima tabella che contiene region headers (td con bgcolor e testo in grassetto)
        for table in soup.find_all('table'):
            for cell in table.find_all('td', bgcolor=True):
                # Controlla se è un header regione: ha bgcolor e contiene testo in <b> o <font><b>
                if cell.find(['b', 'strong']) or (cell.find('font') and cell.find('font').find('b')):
                    target_table = table
                    break
            if target_table:
                break
        
        # Fallback: se non trova con grassetto, cerca td con bgcolor che non siano link
        if not target_table:
            for table in soup.find_all('table'):
                for cell in table.find_all('td', bgcolor=True):
                    text = cell.get_text(strip=True)
                    if text and len(text) > 1 and not cell.find('a'):
                        target_table = table
                        break
                if target_table:
                    break
        
        if target_table:
            # Gestisci layout multi-riga multi-colonna (es. Francia, Spagna): 
            # Header regioni in righe con valign="middle" definiscono regioni per colonna
            # Data rows hanno valign="top" e seguono i header
            
            # Mappa colonna -> regione corrente
            col_region_map = {}
            
            for row_idx, row in enumerate(target_table.find_all('tr')):
                # Detecta se è una riga di header (valign="middle" o contiene <b> in td con bgcolor)
                is_header_row = (
                    row.get('valign') == 'middle' or
                    any(cell.find(['b', 'strong']) for cell in row.find_all('td', bgcolor=True))
                )
                
                cells = row.find_all(['td', 'th'])
                
                if is_header_row:
                    # Aggiorna mappa colonna -> regione
                    for col_idx, cell in enumerate(cells):
                        if cell.get('bgcolor'):
                            text = cell.get_text(strip=True)
                            if text:
                                col_region_map[col_idx] = text
                else:
                    # Riga dati: usa mappa colonna -> regione
                    for col_idx, cell in enumerate(cells):
                        # Header regione inline (per layout singolo come Italia)
                        if cell.get('bgcolor'):
                            current_regione = cell.get_text(strip=True)
                        # Link canyon nella cella
                        for link in cell.find_all('a', href=True):
                            href = link['href']
                            if href.startswith('a5_') and href.endswith('.htm'):
                                link_name = link.get_text(strip=True)
                                link_href = urljoin(country_url, href)
                                # Usa regione dalla mappa colonna se disponibile
                                regione = col_region_map.get(col_idx, current_regione if 'current_regione' in locals() else "")
                                if link_name and regione:
                                    regione_per_link[link_href] = regione
        
        canyons = []
        for name, link_url in tqdm(links, desc=f"  {country_name}", leave=False):
            regione = regione_per_link.get(link_url, "Sconosciuta")
            canyon = self.parse_canyon_page(link_url, country_name, regione)
            if canyon:
                canyons.append(canyon)
        
        return canyons
    
    def scrape_all(self) -> List[Canyon]:
        """Scrapa tutto il sito."""
        countries = self.get_country_pages()
        print(f"Trovate {len(countries)} nazioni: {list(countries.keys())}")
        
        all_canyons = []
        for country_name, country_url in countries.items():
            canyons = self.scrape_country(country_name, country_url)
            all_canyons.extend(canyons)
        
        self.canyons = all_canyons
        return all_canyons
    
    def to_json(self, output_path: str):
        """Salva su file JSON."""
        data = {
            "metadata": {
                "source": "www.cicarudeclan.com",
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_canyons": len(self.canyons),
                "countries": list(set(c.nazione for c in self.canyons))
            },
            "canyons": [asdict(c) for c in self.canyons]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Salvato {len(self.canyons)} canyon in {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Cica Rude Clan Canyoning Scraper")
    parser.add_argument('--all', action='store_true', help='Scrapa tutto il sito')
    parser.add_argument('--country', type=str, help='Scrapa solo una nazione (es. italia)')
    parser.add_argument('--url', type=str, help='Scrapa una singola scheda')
    parser.add_argument('--output', type=str, default='canyoning_data.json', help='File output JSON')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay tra richieste (secondi)')
    args = parser.parse_args()
    
    scraper = CicaRudeScraper(delay=args.delay)
    
    if args.url:
        # Singola scheda
        canyon = scraper.parse_canyon_page(args.url, "unknown", "unknown")
        if canyon:
            print(json.dumps(asdict(canyon), ensure_ascii=False, indent=2))
    elif args.country:
        countries = scraper.get_country_pages()
        if args.country in countries:
            canyons = scraper.scrape_country(args.country, countries[args.country])
            scraper.canyons = canyons
            scraper.to_json(args.output)
        else:
            print(f"Nazione '{args.country}' non trovata. Disponibili: {list(countries.keys())}")
    elif args.all:
        scraper.scrape_all()
        scraper.to_json(args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()