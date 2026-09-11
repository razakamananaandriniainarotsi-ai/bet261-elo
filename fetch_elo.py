#!/usr/bin/env python3
"""
Bet261 Elo Fetcher - V321
Fetch 3 Elo sources daily, no API key, bypass 403 via direct Python requests (no CORS)
Outputs elo.json with all exploitable fields
"""
import requests
import json
import csv
import re
from datetime import datetime
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Bet261-Elo-Bot/1.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def fetch_clubelo():
    """ClubElo - Europe ~600 clubs, daily, free, no key - CSV"""
    result = []
    try:
        # Today's ranking
        url = f"http://api.clubelo.com/{datetime.now().strftime('%Y-%m-%d')}"
        print(f"Fetching ClubElo: {url}")
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200 and 'Rank' in r.text:
            reader = csv.DictReader(r.text.splitlines())
            for row in reader:
                result.append({
                    'club': row.get('Club','').strip(),
                    'country': row.get('Country','').strip(),
                    'level': int(row.get('Level','1') or 1),
                    'elo': int(float(row.get('Elo','1500') or 1500)),
                    'rank': int(row.get('Rank','9999') or 9999),
                    'from': row.get('From',''),
                    'to': row.get('To',''),
                    'source': 'clubelo'
                })
            print(f"ClubElo OK: {len(result)} clubs")
        else:
            # Fallback to Ranking endpoint
            url2 = "http://api.clubelo.com/Ranking"
            r2 = requests.get(url2, headers=HEADERS, timeout=30)
            if r2.status_code == 200:
                reader = csv.DictReader(r2.text.splitlines())
                for row in reader:
                    result.append({
                        'club': row.get('Club','').strip(),
                        'country': row.get('Country','').strip(),
                        'level': int(row.get('Level','1') or 1),
                        'elo': int(float(row.get('Elo','1500') or 1500)),
                        'rank': int(row.get('Rank','9999') or 9999),
                        'from': row.get('From',''),
                        'to': row.get('To',''),
                        'source': 'clubelo'
                    })
    except Exception as e:
        print(f"ClubElo error: {e}")
    return result

def fetch_footballdatabase():
    """FootballDatabase - Worldwide, free, no key - HTML scrape"""
    result = []
    urls = [
        "https://footballdatabase.com/ranking/world",
        "https://footballdatabase.com/ranking/afc",
        "https://footballdatabase.com/ranking/uefa",
        "https://footballdatabase.com/ranking/conmebol",
        "https://footballdatabase.com/ranking/caf",
        "https://footballdatabase.com/ranking/concacaf",
    ]
    try:
        for url in urls:
            print(f"Fetching FootballDatabase: {url}")
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, 'html.parser')
            # Find tables with Club Country Points
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # skip header
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        try:
                            rank = cols[0].get_text(strip=True)
                            club = cols[1].get_text(strip=True)
                            country = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                            points = cols[3].get_text(strip=True) if len(cols) > 3 else cols[2].get_text(strip=True)
                            # Clean points
                            pts_match = re.search(r'(\d{3,4})', points)
                            if pts_match and club:
                                result.append({
                                    'club': club,
                                    'country': country,
                                    'points': int(pts_match.group(1)),
                                    'rank': int(re.search(r'\d+', rank).group()) if re.search(r'\d+', rank) else 9999,
                                    'source': 'footballdatabase',
                                    'confederation': url.split('/')[-1]
                                })
                        except:
                            continue
            # Avoid hammering
            if len(result) > 100:
                break
        print(f"FootballDatabase OK: {len(result)} clubs")
    except Exception as e:
        print(f"FootballDatabase error: {e}")
    return result

def fetch_eloratings():
    """Eloratings.net - 244 national teams, daily, free TSV, no key"""
    result = []
    try:
        url = "https://www.eloratings.net/World.tsv"
        print(f"Fetching Eloratings: {url}")
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            lines = r.text.splitlines()
            for line in lines:
                if not line.strip() or line.startswith('Rank'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 4:
                    try:
                        result.append({
                            'rank': int(re.search(r'\d+', parts[0]).group()) if re.search(r'\d+', parts[0]) else 9999,
                            'country': parts[1].strip(),
                            'code': parts[2].strip() if len(parts) > 2 else '',
                            'elo': int(re.search(r'\d+', parts[3]).group()) if re.search(r'\d+', parts[3]) else 1500,
                            'source': 'eloratings'
                        })
                    except:
                        continue
        print(f"Eloratings OK: {len(result)} national teams")
    except Exception as e:
        print(f"Eloratings error: {e}")
    return result

def main():
    clubelo = fetch_clubelo()
    fdb = fetch_footballdatabase()
    elor = fetch_eloratings()
    
    # Build unified index
    elo_index = {}
    for entry in clubelo:
        key = entry['club'].lower()
        elo_index[key] = entry
    
    for entry in fdb:
        key = entry['club'].lower()
        if key not in elo_index:  # keep ClubElo priority for Europe
            elo_index[key] = entry
        else:
            # Merge points if ClubElo exists
            elo_index[key]['fdb_points'] = entry.get('points')
    
    output = {
        'updated': datetime.now().isoformat(),
        'sources': {
            'clubelo': {
                'count': len(clubelo),
                'coverage': 'Europe ~600 clubs, daily, free no key',
                'format': 'Rank,Club,Country,Level,Elo,From,To',
                'url': 'http://api.clubelo.com/YYYY-MM-DD',
                'exploitable': ['elo', 'level', 'rank', 'country']
            },
            'footballdatabase': {
                'count': len(fdb),
                'coverage': 'Worldwide UEFA/CONMEBOL/CONCACAF/AFC/CAF - Al Hilal 1747, Al Nassr 1667, Pyramids 1669, Bayern 2097',
                'format': 'HTML table Club Country Points',
                'url': 'https://footballdatabase.com/ranking/world',
                'exploitable': ['points', 'rank', 'country', 'confederation']
            },
            'eloratings': {
                'count': len(elor),
                'coverage': '244 national teams, daily, free TSV no key',
                'format': 'TSV Rank Country Code Elo',
                'url': 'https://www.eloratings.net/World.tsv',
                'exploitable': ['elo', 'rank', 'code']
            }
        },
        'clubs': clubelo,
        'world_clubs': fdb,
        'national_teams': elor,
        'index': elo_index  # quick lookup by club name lowercased
    }
    
    with open('elo.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ elo.json generated: {len(clubelo)} ClubElo + {len(fdb)} FDB + {len(elor)} Eloratings")
    print(f"Total unique clubs in index: {len(elo_index)}")

if __name__ == "__main__":
    main()
