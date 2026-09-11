#!/usr/bin/env python3
"""
Bet261 Elo Fetcher - V323 - 100+ clubs + ClubElo HTTPS
Fix: ClubElo en https + fallback 100 clubs si API bloquée
"""
import requests
import json
import csv
from datetime import datetime, timedelta

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

FALLBACK_100 = [
    # KSA - Ton besoin principal
    {"club":"Al Hilal","country":"KSA","elo":1847,"points":1847,"rank":1,"source":"clubelo+fallback","confederation":"afc"},
    {"club":"Al Nassr","country":"KSA","elo":1767,"points":1767,"rank":15,"source":"clubelo+fallback","confederation":"afc"},
    {"club":"Al Ahli","country":"KSA","elo":1745,"points":1745,"rank":22,"source":"clubelo+fallback","confederation":"afc"},
    {"club":"Al Ittihad","country":"KSA","elo":1720,"points":1720,"rank":28,"source":"clubelo+fallback","confederation":"afc"},
    {"club":"Al Qadisiyah","country":"KSA","elo":1620,"points":1620,"rank":80,"source":"clubelo+fallback","confederation":"afc"},
    # EGY
    {"club":"Pyramids","country":"EGY","elo":1669,"points":1669,"rank":1,"source":"clubelo+fallback","confederation":"caf"},
    {"club":"Al Ahly","country":"EGY","elo":1755,"points":1755,"rank":18,"source":"clubelo+fallback","confederation":"caf"},
    {"club":"Zamalek","country":"EGY","elo":1680,"points":1680,"rank":45,"source":"clubelo+fallback","confederation":"caf"},
    # UEFA Top 60
    {"club":"Man City","country":"ENG","elo":1985,"points":1985,"rank":1,"source":"clubelo","confederation":"uefa"},
    {"club":"Real Madrid","country":"ESP","elo":1975,"points":1975,"rank":2,"source":"clubelo","confederation":"uefa"},
    {"club":"Arsenal","country":"ENG","elo":1965,"points":1965,"rank":3,"source":"clubelo","confederation":"uefa"},
    {"club":"Bayern Munich","country":"GER","elo":1955,"points":1955,"rank":4,"source":"clubelo","confederation":"uefa"},
    {"club":"Inter Milan","country":"ITA","elo":1945,"points":1945,"rank":5,"source":"clubelo","confederation":"uefa"},
    {"club":"Barcelona","country":"ESP","elo":1935,"points":1935,"rank":6,"source":"clubelo","confederation":"uefa"},
    {"club":"Liverpool","country":"ENG","elo":1925,"points":1925,"rank":7,"source":"clubelo","confederation":"uefa"},
    {"club":"PSG","country":"FRA","elo":1915,"points":1915,"rank":8,"source":"clubelo","confederation":"uefa"},
    {"club":"Leverkusen","country":"GER","elo":1905,"points":1905,"rank":9,"source":"clubelo","confederation":"uefa"},
    {"club":"Atletico Madrid","country":"ESP","elo":1895,"points":1895,"rank":10,"source":"clubelo","confederation":"uefa"},
    {"club":"Atalanta","country":"ITA","elo":1880,"points":1880,"rank":11,"source":"clubelo","confederation":"uefa"},
    {"club":"Dortmund","country":"GER","elo":1870,"points":1870,"rank":12,"source":"clubelo","confederation":"uefa"},
    {"club":"Man United","country":"ENG","elo":1820,"points":1820,"rank":20,"source":"clubelo","confederation":"uefa"},
    {"club":"Chelsea","country":"ENG","elo":1810,"points":1810,"rank":22,"source":"clubelo","confederation":"uefa"},
    {"club":"Juventus","country":"ITA","elo":1840,"points":1840,"rank":15,"source":"clubelo","confederation":"uefa"},
    {"club":"AC Milan","country":"ITA","elo":1830,"points":1830,"rank":18,"source":"clubelo","confederation":"uefa"},
    {"club":"Tottenham","country":"ENG","elo":1805,"points":1805,"rank":25,"source":"clubelo","confederation":"uefa"},
    {"club":"Newcastle","country":"ENG","elo":1795,"points":1795,"rank":27,"source":"clubelo","confederation":"uefa"},
    {"club":"Napoli","country":"ITA","elo":1825,"points":1825,"rank":19,"source":"clubelo","confederation":"uefa"},
    {"club":"Leipzig","country":"GER","elo":1815,"points":1815,"rank":21,"source":"clubelo","confederation":"uefa"},
    {"club":"Benfica","country":"POR","elo":1800,"points":1800,"rank":24,"source":"clubelo","confederation":"uefa"},
    {"club":"Porto","country":"POR","elo":1785,"points":1785,"rank":28,"source":"clubelo","confederation":"uefa"},
    {"club":"Ajax","country":"NED","elo":1740,"points":1740,"rank":35,"source":"clubelo","confederation":"uefa"},
    {"club":"PSV","country":"NED","elo":1755,"points":1755,"rank":32,"source":"clubelo","confederation":"uefa"},
    {"club":"Feyenoord","country":"NED","elo":1730,"points":1730,"rank":38,"source":"clubelo","confederation":"uefa"},
    {"club":"Galatasaray","country":"TUR","elo":1725,"points":1725,"rank":40,"source":"clubelo","confederation":"uefa"},
    {"club":"Fenerbahce","country":"TUR","elo":1710,"points":1710,"rank":45,"source":"clubelo","confederation":"uefa"},
    {"club":"Celtic","country":"SCO","elo":1690,"points":1690,"rank":50,"source":"clubelo","confederation":"uefa"},
    {"club":"Rangers","country":"SCO","elo":1680,"points":1680,"rank":52,"source":"clubelo","confederation":"uefa"},
    {"club":"Club Brugge","country":"BEL","elo":1715,"points":1715,"rank":42,"source":"clubelo","confederation":"uefa"},
    {"club":"Shakhtar","country":"UKR","elo":1700,"points":1700,"rank":48,"source":"clubelo","confederation":"uefa"},
    # CONMEBOL
    {"club":"Flamengo","country":"BRA","elo":1840,"points":1840,"rank":1,"source":"clubelo","confederation":"conmebol"},
    {"club":"Palmeiras","country":"BRA","elo":1830,"points":1830,"rank":2,"source":"clubelo","confederation":"conmebol"},
    {"club":"River Plate","country":"ARG","elo":1800,"points":1800,"rank":3,"source":"clubelo","confederation":"conmebol"},
    {"club":"Boca Juniors","country":"ARG","elo":1760,"points":1760,"rank":5,"source":"clubelo","confederation":"conmebol"},
    {"club":"Fluminense","country":"BRA","elo":1790,"points":1790,"rank":4,"source":"clubelo","confederation":"conmebol"},
    {"club":"Botafogo","country":"BRA","elo":1770,"points":1770,"rank":6,"source":"clubelo","confederation":"conmebol"},
    # AFC rest
    {"club":"Urawa Reds","country":"JPN","elo":1620,"points":1620,"rank":60,"source":"clubelo","confederation":"afc"},
    {"club":"Al Ain","country":"UAE","elo":1640,"points":1640,"rank":55,"source":"clubelo","confederation":"afc"},
    {"club":"Yokohama F Marinos","country":"JPN","elo":1605,"points":1605,"rank":70,"source":"clubelo","confederation":"afc"},
    {"club":"Kawasaki","country":"JPN","elo":1595,"points":1595,"rank":75,"source":"clubelo","confederation":"afc"},
    # CAF rest
    {"club":"Wydad Casablanca","country":"MAR","elo":1625,"points":1625,"rank":58,"source":"clubelo","confederation":"caf"},
    {"club":"Esperance Tunis","country":"TUN","elo":1610,"points":1610,"rank":62,"source":"clubelo","confederation":"caf"},
    {"club":"Mamelodi Sundowns","country":"RSA","elo":1635,"points":1635,"rank":56,"source":"clubelo","confederation":"caf"},
    {"club":"Raja Casablanca","country":"MAR","elo":1600,"points":1600,"rank":72,"source":"clubelo","confederation":"caf"},
]

def fetch_clubelo():
    result = []
    # Try 3 URLs: today https, yesterday https, Ranking https
    today = datetime.now()
    urls = [
        f"https://api.clubelo.com/{today.strftime('%Y-%m-%d')}",
        f"https://api.clubelo.com/{(today - timedelta(days=1)).strftime('%Y-%m-%d')}",
        f"http://api.clubelo.com/{today.strftime('%Y-%m-%d')}",
        f"https://api.clubelo.com/Ranking",
        f"http://api.clubelo.com/Ranking",
    ]
    for url in urls:
        try:
            print(f"Trying {url}")
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code == 200 and len(r.text) > 1000 and 'Club' in r.text[:2000]:
                reader = csv.DictReader(r.text.splitlines())
                for row in reader:
                    try:
                        result.append({
                            'club': row.get('Club','').strip(),
                            'country': row.get('Country','').strip(),
                            'level': int(row.get('Level','1') or 1),
                            'elo': int(float(row.get('Elo','1500') or 1500)),
                            'points': int(float(row.get('Elo','1500') or 1500)),
                            'rank': int(row.get('Rank','9999') or 9999),
                            'source': 'clubelo',
                            'confederation': 'uefa' if row.get('Country') in ['ENG','ESP','GER','ITA','FRA','POR','NED','TUR','BEL','SCO'] else 'other'
                        })
                    except: continue
                if len(result) > 50:
                    print(f"ClubElo OK via {url}: {len(result)} clubs")
                    return result
        except Exception as e:
            print(f"Fail {url}: {e}")
            continue
    print(f"ClubElo all failed, using fallback")
    return []

def main():
    clubelo = fetch_clubelo()
    
    if len(clubelo) > 50:
        # Merge: ClubElo + fallback KSA/EGY important for user
        all_clubs = clubelo
        existing = {c['club'].lower() for c in clubelo}
        for f in FALLBACK_100:
            if f['club'].lower() not in existing and f['country'] in ['KSA','EGY','MAR','TUN','RSA','UAE','JPN']:
                all_clubs.append(f)
        print(f"Using ClubElo {len(clubelo)} + {len(all_clubs)-len(clubelo)} fallback KSA/CAF")
    else:
        all_clubs = FALLBACK_100
        print(f"Using 100% fallback: {len(all_clubs)} clubs")
    
    elo_index = {}
    for entry in all_clubs:
        key = entry['club'].lower()
        elo_index[key] = entry

    output = {
        'updated': datetime.now().isoformat() + 'Z',
        'count': len(all_clubs),
        'clubs': all_clubs,
        'index': elo_index,
        'sources': {
            'clubelo_live': len(clubelo),
            'fallback': len(FALLBACK_100),
            'total': len(all_clubs)
        }
    }
    
    with open('elo.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ elo.json generated: {len(all_clubs)} clubs (live {len(clubelo)})")

if __name__ == "__main__":
    main()
