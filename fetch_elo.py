#!/usr/bin/env python3
"""
Bet261 Elo Fetcher - V325 VRAI DYNAMIQUE
ClubElo http + Scraping clubelo.com + footballdatabase.com
Objectif: 500+ clubs live, pas fallback
"""
import requests
import json
import csv
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def fetch_clubelo_http():
    """Essaie http://api.clubelo.com sur 12 jours"""
    result = []
    today = datetime.utcnow()
    for back in range(0, 12):
        d = (today - timedelta(days=back)).strftime('%Y-%m-%d')
        for url in [f"http://api.clubelo.com/{d}", f"http://api.clubelo.com/Ranking"]:
            try:
                print(f"TRY ClubElo {url}")
                r = requests.get(url, headers=HEADERS, timeout=20)
                if r.status_code == 200 and 'Club' in r.text[:2000] and len(r.text) > 5000:
                    reader = csv.DictReader(r.text.splitlines())
                    tmp = []
                    for row in reader:
                        try:
                            tmp.append({
                                'club': row.get('Club','').strip(),
                                'country': row.get('Country','').strip(),
                                'elo': int(float(row.get('Elo','1500'))),
                                'points': int(float(row.get('Elo','1500'))),
                                'rank': int(row.get('Rank','9999')),
                                'level': int(row.get('Level','1') or 1),
                                'source': 'clubelo-live',
                            })
                        except: continue
                    if len(tmp) > 200:
                        print(f"✅ ClubElo LIVE {len(tmp)} via {url}")
                        return tmp
            except Exception as e:
                print(f"  fail {e}")
                continue
    return []

def fetch_clubelo_com_scrape():
    """Scrape https://clubelo.com/ - table HTML"""
    result = []
    try:
        url = "http://clubelo.com/"
        print(f"TRY scrape {url}")
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # cherche table ranking
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        try:
                            club = cols[1].get_text(strip=True)
                            country = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                            elo_txt = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                            m = re.search(r'(\d{3,4})', elo_txt)
                            if m and club:
                                result.append({
                                    'club': club,
                                    'country': country,
                                    'elo': int(m.group(1)),
                                    'points': int(m.group(1)),
                                    'rank': len(result)+1,
                                    'source': 'clubelo-com-scrape',
                                    'level': 1
                                })
                        except: continue
            if len(result) > 50:
                print(f"✅ clubelo.com scrape {len(result)}")
                return result
    except Exception as e:
        print(f"scrape fail {e}")
    return []

def fetch_footballdatabase():
    """Scrape footballdatabase.com/ranking/world - 100+ clubs mondiaux"""
    result = []
    try:
        url = "https://footballdatabase.com/ranking/world"
        print(f"TRY {url}")
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # cherche ranking
            for table in soup.find_all('table'):
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        try:
                            rank = cols[0].get_text(strip=True)
                            club = cols[1].get_text(strip=True)
                            # country peut être drapeau + texte
                            country = cols[2].get_text(strip=True) if len(cols) > 3 else ''
                            pts = cols[3].get_text(strip=True) if len(cols) > 3 else cols[2].get_text(strip=True)
                            m = re.search(r'(\d{3,4})', pts)
                            mr = re.search(r'\d+', rank)
                            if m and club and len(club) > 2:
                                result.append({
                                    'club': club,
                                    'country': country[:3],
                                    'elo': int(m.group(1)),
                                    'points': int(m.group(1)),
                                    'rank': int(mr.group()) if mr else len(result)+1,
                                    'source': 'footballdatabase-live',
                                    'level': 1
                                })
                        except: continue
            if len(result) > 30:
                print(f"✅ FootballDatabase LIVE {len(result)}")
                return result
    except Exception as e:
        print(f"FDB fail {e}")
    return []

def main():
    print("=== FETCH DYNAMIQUE ===")
    live_clubelo = fetch_clubelo_http()
    scrape_clubelo = fetch_clubelo_com_scrape() if len(live_clubelo) < 200 else []
    fdb = fetch_footballdatabase() if len(live_clubelo) < 200 else []

    all_clubs = []
    seen = set()

    # Priorité: ClubElo live > scrape clubelo.com > FDB > fallback
    for src in [live_clubelo, scrape_clubelo, fdb]:
        for c in src:
            key = c['club'].lower()
            if key not in seen:
                all_clubs.append(c)
                seen.add(key)

    # Si toujours < 100, complète avec fallback KSA/EGY essentiels
    fallback_essentials = [
        {"club":"Al Hilal","country":"KSA","elo":1847,"rank":1,"source":"fallback","level":1,"points":1847},
        {"club":"Al Nassr","country":"KSA","elo":1767,"rank":15,"source":"fallback","level":1,"points":1767},
        {"club":"Al Ahli","country":"KSA","elo":1745,"rank":22,"source":"fallback","level":1,"points":1745},
        {"club":"Al Ittihad","country":"KSA","elo":1720,"rank":28,"source":"fallback","level":1,"points":1720},
        {"club":"Pyramids","country":"EGY","elo":1669,"rank":30,"source":"fallback","level":1,"points":1669},
        {"club":"Al Ahly","country":"EGY","elo":1755,"rank":18,"source":"fallback","level":1,"points":1755},
        {"club":"Bayern Munich","country":"GER","elo":1985,"rank":4,"source":"fallback","level":1,"points":1985},
        {"club":"Man City","country":"ENG","elo":1985,"rank":1,"source":"fallback","level":1,"points":1985},
    ]
    for f in fallback_essentials:
        if f['club'].lower() not in seen:
            all_clubs.append(f)
            seen.add(f['club'].lower())

    is_live = len(live_clubelo) >= 200 or len(scrape_clubelo) >= 100 or len(fdb) >= 50

    out = {
        'updated': datetime.utcnow().isoformat() + 'Z',
        'count': len(all_clubs),
        'live_count': len(live_clubelo),
        'scrape_count': len(scrape_clubelo),
        'fdb_count': len(fdb),
        'is_live': is_live,
        'clubs': all_clubs,
        'index': {c['club'].lower(): c for c in all_clubs},
    }

    with open('elo.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n✅ FINAL elo.json {len(all_clubs)} clubs | live={len(live_clubelo)} scrape={len(scrape_clubelo)} fdb={len(fdb)} is_live={is_live}")

if __name__ == "__main__":
    main()
