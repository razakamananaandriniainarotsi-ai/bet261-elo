#!/usr/bin/env python3
"""
Bet261 Elo Fetcher - V326 CORRIGE - Scrape https://clubelo.com/Ranking (vrai tableau)
Donne 500+ clubs live dynamiques
"""
import requests
import json
import csv
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def fetch_api_csv():
    """1) api.clubelo.com en http:// - CSV 600+ clubs si dispo"""
    for back in range(0, 7):
        d = (datetime.utcnow() - timedelta(days=back)).strftime('%Y-%m-%d')
        for url in [f"http://api.clubelo.com/{d}", f"http://api.clubelo.com/Ranking"]:
            try:
                print(f"TRY API {url}")
                r = requests.get(url, headers=HEADERS, timeout=20)
                if r.status_code == 200 and len(r.text) > 5000 and 'Club' in r.text[:2000]:
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
                                'source': 'clubelo-api-live',
                            })
                        except: continue
                    if len(tmp) > 200:
                        print(f"✅ API LIVE {len(tmp)} via {url}")
                        return tmp
            except Exception as e:
                print(f" API fail {e}")
    return []

def fetch_ranking_html():
    """2) https://clubelo.com/Ranking - vrai tableau Rank | Club | Elo"""
    result = []
    try:
        url = "https://clubelo.com/Ranking"
        print(f"TRY HTML {url}")
        r = requests.get(url, headers=HEADERS, timeout=20)
        print(f" -> {r.status_code} len {len(r.text)}")
        if r.status_code != 200:
            # try http
            url = "http://clubelo.com/Ranking"
            r = requests.get(url, headers=HEADERS, timeout=20)
        
        soup = BeautifulSoup(r.text, 'html.parser')
        # Trouve le tableau avec header Rank | Club | Elo
        tables = soup.find_all('table')
        for table in tables:
            header = table.get_text()[:500]
            if 'Rank' in header and 'Club' in header and 'Elo' in header:
                rows = table.find_all('tr')
                for row in rows[1:]:  # skip header
                    cols = row.find_all(['td','th'])
                    if len(cols) >= 3:
                        try:
                            rank_txt = cols[0].get_text(strip=True)
                            club_txt = cols[1].get_text(strip=True)
                            elo_txt = cols[2].get_text(strip=True)
                            
                            # Nettoie club: enlève chiffre leading et drapeau
                            # Ex: "1 Arsenal" -> "Arsenal", "2 Bayern" -> "Bayern"
                            club_clean = re.sub(r'^\d+\s*', '', club_txt)  # enlève "1 "
                            club_clean = club_clean.strip()
                            # Enlève encore chiffres si reste
                            club_clean = re.sub(r'^\d+', '', club_clean).strip()
                            
                            # Elo: nombre 1000-2500
                            m_elo = re.search(r'(\d{3,4})', elo_txt)
                            m_rank = re.search(r'(\d+)', rank_txt)
                            
                            if m_elo and club_clean and len(club_clean) >= 3 and len(club_clean) < 40:
                                # Filtre garbage: pas de % ou 🏆
                                if '%' not in club_clean and 'Champion' not in club_clean and 'Relegation' not in club_clean:
                                    result.append({
                                        'club': club_clean,
                                        'country': '',  # pas dans ce tableau, on remplira après si besoin
                                        'elo': int(m_elo.group(1)),
                                        'points': int(m_elo.group(1)),
                                        'rank': int(m_rank.group(1)) if m_rank else len(result)+1,
                                        'level': 1,
                                        'source': 'clubelo-ranking-live',
                                    })
                        except Exception as e:
                            continue
                if len(result) > 50:
                    print(f"✅ Ranking HTML LIVE {len(result)} clubs")
                    # Tri par rank
                    result.sort(key=lambda x: x['rank'])
                    return result
    except Exception as e:
        print(f"HTML scrape fail {e}")
    print(f"HTML scrape gave {len(result)}")
    return result

def main():
    live_api = fetch_api_csv()
    live_html = fetch_ranking_html() if len(live_api) < 200 else []

    all_clubs = []
    seen = set()

    # Priorité API > HTML
    for src in [live_api, live_html]:
        for c in src:
            key = c['club'].lower()
            if key not in seen and len(c['club']) > 2:
                all_clubs.append(c)
                seen.add(key)

    # Ajoute KSA/EGY si manquants (ClubElo est Europe, pas KSA)
    essentials = [
        {"club":"Al Hilal","country":"KSA","elo":1847,"rank":999,"source":"essential","level":1,"points":1847},
        {"club":"Al Nassr","country":"KSA","elo":1767,"rank":999,"source":"essential","level":1,"points":1767},
        {"club":"Al Ahli","country":"KSA","elo":1745,"rank":999,"source":"essential","level":1,"points":1745},
        {"club":"Al Ittihad","country":"KSA","elo":1720,"rank":999,"source":"essential","level":1,"points":1720},
        {"club":"Pyramids","country":"EGY","elo":1669,"rank":999,"source":"essential","level":1,"points":1669},
        {"club":"Al Ahly","country":"EGY","elo":1755,"rank":999,"source":"essential","level":1,"points":1755},
    ]
    for e in essentials:
        if e['club'].lower() not in seen:
            all_clubs.append(e)
            seen.add(e['club'].lower())

    is_live = len(live_api) >= 200 or len(live_html) >= 200

    out = {
        'updated': datetime.utcnow().isoformat() + 'Z',
        'count': len(all_clubs),
        'live_api': len(live_api),
        'live_html': len(live_html),
        'is_live': is_live,
        'clubs': all_clubs,
        'index': {c['club'].lower(): c for c in all_clubs},
    }

    with open('elo.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n✅ FINAL {len(all_clubs)} clubs | api={len(live_api)} html={len(live_html)} is_live={is_live}")

if __name__ == "__main__":
    main()
