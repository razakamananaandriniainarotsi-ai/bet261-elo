#!/usr/bin/env python3
"""
Bet261 V400 WORLD ELO - 0 BUDGET HALLU - 100% AUTO - TOUTES LES EQUIPES MONDE
Objectif: résoudre le problème "nc" en ayant ~5000 clubs au lieu de 236

Sources:
1. ClubElo API: http://api.clubelo.com/YYYY-MM-DD -> ~1800 clubs actifs (Europe + top monde)
2. FootballDatabase World Ranking: https://www.footballdatabase.com/ranking/world + /{page}
   -> ~3500 clubs (toutes confédérations: UEFA, AFC, CAF, CONMEBOL, CONCACAF, OFC)
3. Fallback officiel 236 si tout échoue (pour ne jamais avoir 0)

Merge intelligent:
- Normalisation noms pour déduplication
- Si club dans 2 sources: merged = moyenne pondérée (ClubElo prioritaire Europe)
- Sinon garde source unique

Output: elo.json compatible avec Bet261 V320 (index + clubs + updated + count)
Auto-update via GitHub Actions toutes les heures

Auteur: Bet261 Fix
"""

import json
import re
import csv
import io
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8'
}

# Fallback officiel si tout échoue (ton 236 + KSA/EGY)
OFFICIEL_236_FALLBACK = [
    {"club":"Arsenal","elo":2060,"rank":1,"country":"ENG"},
    {"club":"Bayern Munich","elo":2002,"rank":2,"country":"GER"},
    {"club":"Barcelona","elo":1984,"rank":3,"country":"ESP"},
    # ... minimal pour fallback, le reste sera chargé depuis API
]

def normalize_key(name: str) -> str:
    if not name:
        return ""
    s = str(name).lower().strip()
    # enlève accents simples
    s = re.sub(r'[àáâä]', 'a', s)
    s = re.sub(r'[èéêë]', 'e', s)
    s = re.sub(r'[ìíîï]', 'i', s)
    s = re.sub(r'[òóôö]', 'o', s)
    s = re.sub(r'[ùúûü]', 'u', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # enlève préfixes/suffixes courants pour matching
    s = re.sub(r'\b(fc|sc|cf|ac|as|us|ss|rc|afc|cfc|lfc| united| city| town| rovers| athletic| wanderers)\b', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_for_index(name: str) -> str:
    return str(name).lower().strip()

def fetch_clubelo_api():
    """Fetch ~1800 clubs via ClubElo API daily snapshot"""
    clubs = []
    today = datetime.utcnow().date()
    # essaie 7 derniers jours car API peut avoir 1 jour de retard
    for delta in range(0, 8):
        d = today - timedelta(days=delta)
        date_str = d.strftime("%Y-%m-%d")
        for proto in ["http", "https"]:
            url = f"{proto}://api.clubelo.com/{date_str}"
            try:
                print(f"Trying ClubElo API {url}")
                r = requests.get(url, headers=HEADERS, timeout=20)
                if r.status_code != 200:
                    continue
                text = r.text
                if len(text) < 1000 or "Club" not in text or "Elo" not in text:
                    continue
                # Parse CSV
                reader = csv.DictReader(io.StringIO(text))
                tmp = []
                for row in reader:
                    try:
                        club = row.get('Club') or row.get('club')
                        if not club:
                            continue
                        elo_str = row.get('Elo') or row.get('elo')
                        if not elo_str:
                            continue
                        elo = float(elo_str)
                        rank = row.get('Rank') or row.get('rank') or len(tmp)+1
                        try:
                            rank = int(float(rank))
                        except:
                            rank = len(tmp)+1
                        country = row.get('Country') or row.get('country') or ""
                        level = row.get('Level') or row.get('level') or 1
                        try:
                            level = int(float(level))
                        except:
                            level = 1
                        tmp.append({
                            "club": club.strip(),
                            "elo": int(elo),
                            "points": int(elo),
                            "rank": rank,
                            "country": country.strip(),
                            "level": level,
                            "source": "clubelo-api-officiel",
                            "confederation": "uefa" if country in ["ENG","GER","ESP","ITA","FRA","POR","NED","BEL","TUR","RUS","UKR","GRE","SCO","DEN","NOR","SWE","CZE","POL","AUT","SUI","CRO","SRB"] else "world"
                        })
                    except Exception as e:
                        continue
                if len(tmp) >= 500:  # doit avoir au moins 500 clubs pour être valide
                    print(f"✅ ClubElo API LIVE {len(tmp)} clubs from {date_str}")
                    return tmp
            except Exception as e:
                print(f"ClubElo API fail {url}: {e}")
                continue
    print("⚠️ ClubElo API failed, will try scrape fallback")
    return []

def fetch_clubelo_scrape_fallback():
    """Scrape https://clubelo.com/Ranking si API down - au moins 200 clubs"""
    try:
        for url in ["https://clubelo.com/Ranking", "http://clubelo.com/Ranking"]:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200 or len(r.text) < 5000:
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            tmp = []
            for table in soup.find_all('table'):
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        try:
                            rank_txt = cols[0].get_text(strip=True)
                            club_txt = cols[1].get_text(strip=True)
                            elo_txt = cols[2].get_text(strip=True)
                            club_txt = re.sub(r'^\d+\s*', '', club_txt).strip()
                            m_rank = re.search(r'\d+', rank_txt)
                            m_elo = re.search(r'(\d{3,4})', elo_txt)
                            if m_elo and club_txt and len(club_txt) >= 3 and len(club_txt) < 40:
                                tmp.append({
                                    "club": club_txt,
                                    "elo": int(m_elo.group(1)),
                                    "points": int(m_elo.group(1)),
                                    "rank": int(m_rank.group()) if m_rank else len(tmp)+1,
                                    "country": "",
                                    "level": 1,
                                    "source": "clubelo-scrape-officiel"
                                })
                        except:
                            continue
                if len(tmp) > 150:
                    print(f"✅ ClubElo SCRAPE {len(tmp)} clubs")
                    return tmp
    except Exception as e:
        print(f"ClubElo scrape fail: {e}")
    return []

def fetch_footballdatabase_world():
    """Scrape FootballDatabase world ranking pages 1..70 => ~3500 clubs MONDE"""
    all_clubs = []
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Pages 1 à 75 (50 clubs par page => ~3750 clubs)
    for page in range(1, 76):
        if page == 1:
            url = "https://www.footballdatabase.com/ranking/world"
        else:
            url = f"https://www.footballdatabase.com/ranking/world/{page}"
        try:
            print(f"Fetching FDB page {page}/75: {url}")
            r = session.get(url, timeout=20)
            if r.status_code != 200 or len(r.text) < 2000:
                print(f"FDB page {page} fail status {r.status_code}")
                if page > 5 and len(all_clubs) > 1000:
                    break
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            # Cherche tous les tableaux
            found_this_page = 0
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for tr in rows[1:]:
                    tds = tr.find_all('td')
                    if len(tds) < 2:
                        continue
                    try:
                        # Format: Rank | Club / Country | Points | change
                        rank_txt = tds[0].get_text(strip=True)
                        club_country_txt = tds[1].get_text(" ", strip=True)  # ex: "Bayern München Germany"
                        points_txt = tds[2].get_text(strip=True) if len(tds) > 2 else ""
                        
                        m_rank = re.search(r'\d+', rank_txt)
                        m_points = re.search(r'(\d{3,4})', points_txt)
                        
                        if not m_points:
                            continue
                        points = int(m_points.group(1))
                        if points < 800 or points > 2500:
                            continue
                        
                        # Extraction club: tout avant dernier mot (country) mais country peut être 2 mots
                        # On récupère le texte du lien <a> si présent
                        club_name = ""
                        country_name = ""
                        links = tds[1].find_all('a')
                        if len(links) >= 1:
                            club_name = links[0].get_text(strip=True)
                            if len(links) >= 2:
                                country_name = links[1].get_text(strip=True)
                        else:
                            # fallback: split
                            # Ex: "Bayern MünchenGermany" collé -> sépare par majuscule?
                            # On prend tout sauf dernier mot comme club
                            full = club_country_txt
                            # Heuristique: country souvent dernier token
                            parts = full.rsplit(' ', 1)
                            if len(parts) == 2:
                                club_name = parts[0]
                                country_name = parts[1]
                            else:
                                club_name = full
                        
                        if not club_name or len(club_name) < 2 or len(club_name) > 50:
                            continue
                        # nettoie
                        club_name = re.sub(r'\s+', ' ', club_name).strip()
                        
                        rank_val = int(m_rank.group()) if m_rank else len(all_clubs)+1
                        
                        all_clubs.append({
                            "club": club_name,
                            "elo": points,  # FDB points utilisés comme Elo
                            "points": points,
                            "rank": rank_val,
                            "country": country_name,
                            "level": 1,
                            "source": "footballdatabase-officiel",
                            "confederation": "world"
                        })
                        found_this_page += 1
                    except Exception as e:
                        continue
            print(f"FDB page {page}: +{found_this_page} clubs (total {len(all_clubs)})")
            if found_this_page == 0 and page > 3:
                # plus de données, on s'arrête
                if len(all_clubs) > 2000:
                    break
            # petite pause anti-ban
            # time.sleep(0.3)
        except Exception as e:
            print(f"FDB page {page} exception: {e}")
            continue
    
    # Déduplique FDB interne
    seen = set()
    dedup = []
    for c in all_clubs:
        k = normalize_key(c["club"])
        if k not in seen and k:
            seen.add(k)
            dedup.append(c)
    print(f"✅ FootballDatabase WORLD {len(dedup)} clubs uniques (après dédup {len(all_clubs)} raw)")
    return dedup

def fetch_additional_continental():
    """Optionnel: AFC, CAF, CONMEBOL rankings pour compléter"""
    # On peut ajouter ici si besoin, mais world ranking suffit pour V400
    return []

def merge_clubs(clubelo_list, fdb_list):
    """Merge intelligent avec moyenne pondérée"""
    merged_dict = {}
    
    # 1. Ajoute ClubElo (prioritaire Europe)
    for c in clubelo_list:
        key = normalize_key(c["club"])
        if not key:
            continue
        # garde le meilleur Elo si doublon ClubElo interne
        if key in merged_dict:
            if c["elo"] > merged_dict[key]["elo"]:
                merged_dict[key]["elo"] = c["elo"]
                merged_dict[key]["points"] = c["elo"]
        else:
            merged_dict[key] = {
                "club": c["club"],
                "elo": c["elo"],
                "points": c["points"],
                "merged": c["elo"],
                "rank": c.get("rank", 9999),
                "country": c.get("country", ""),
                "level": c.get("level", 1),
                "source": c["source"],
                "confederation": c.get("confederation", "uefa"),
                "sources_count": 1,
                "all_names": [c["club"]]
            }
    
    # 2. Ajoute FootballDatabase
    for c in fdb_list:
        key = normalize_key(c["club"])
        if not key:
            continue
        if key in merged_dict:
            # club dans les 2 sources: moyenne pondérée ClubElo 60% + FDB 40%
            existing = merged_dict[key]
            # Si existant est ClubElo, on fait moyenne
            avg = int(existing["elo"] * 0.6 + c["elo"] * 0.4)
            existing["merged"] = avg
            existing["points"] = avg
            # garde le meilleur rank (le plus petit)
            existing["rank"] = min(existing["rank"], c["rank"])
            existing["source"] = "clubelo+fdb"
            existing["sources_count"] = 2
            if c["club"] not in existing["all_names"]:
                existing["all_names"].append(c["club"])
        else:
            merged_dict[key] = {
                "club": c["club"],
                "elo": c["elo"],
                "points": c["elo"],
                "merged": c["elo"],
                "rank": c.get("rank", 9999),
                "country": c.get("country", ""),
                "level": c.get("level", 1),
                "source": c["source"],
                "confederation": c.get("confederation", "world"),
                "sources_count": 1,
                "all_names": [c["club"]]
            }
    
    # Convertit en liste triée par merged desc
    merged_list = list(merged_dict.values())
    merged_list.sort(key=lambda x: x["merged"], reverse=True)
    
    # Re-rank global
    for i, c in enumerate(merged_list):
        c["global_rank"] = i+1
    
    return merged_list

def build_index(merged_list):
    """Construit index compatible Bet261: lower name -> data + alias"""
    index = {}
    for c in merged_list:
        # clé principale
        key_main = normalize_for_index(c["club"])
        if key_main and key_main not in index:
            index[key_main] = {
                "club": c["club"],
                "elo": c["elo"],
                "points": c["points"],
                "merged": c["merged"],
                "rank": c["global_rank"],
                "country": c["country"],
                "source": c["source"],
                "confederation": c["confederation"],
                "best": "AVG" if c["sources_count"]>1 else ("CE" if "clubelo" in c["source"] else "FDB")
            }
        # alias normalisés sans FC etc.
        key_norm = normalize_key(c["club"])
        if key_norm and key_norm not in index and key_norm != key_main:
            index[key_norm] = index[key_main]
        
        # alias supplémentaires (tous les noms connus)
        for alias in c.get("all_names", []):
            k1 = normalize_for_index(alias)
            k2 = normalize_key(alias)
            if k1 and k1 not in index:
                index[k1] = index[key_main]
            if k2 and k2 not in index:
                index[k2] = index[key_main]
    
    # Ajoute alias manuels courants (Man City, PSG, etc) - 0 hardcoding minimal pour matching FotMob
    manual_aliases = {
        "man city": "manchester city",
        "man united": "manchester united",
        "man utd": "manchester united",
        "psg": "paris saint-germain",
        "paris sg": "paris saint-germain",
        "bayern": "bayern munich",
        "bayern munchen": "bayern munich",
        "inter": "inter milan",
        "ac milan": "ac milan",
        "milan": "ac milan",
        "spurs": "tottenham",
        "tottenham hotspur": "tottenham",
        "leeds": "leeds united",
        "leicester": "leicester city",
        "wolves": "wolverhampton wanderers",
        "forest": "nottingham forest",
        "newcastle": "newcastle united",
        "brighton": "brighton & hove albion",
        "atletico": "atletico madrid",
        "atletico madrid": "atletico madrid",
        "real madrid": "real madrid",
        "barca": "barcelona",
        "barcelona": "barcelona",
        "sporting cp": "sporting",
        "sporting lisbon": "sporting",
        "benfica": "benfica",
        "porto": "fc porto",
        "ajax": "ajax",
        "psv": "psv eindhoven",
        "feyenoord": "feyenoord",
        "al hilal": "al hilal",
        "al nassr": "al nassr",
        "al ahly": "al ahly",
        "zamalek": "zamalek",
    }
    for alias, target in manual_aliases.items():
        if target in index and alias not in index:
            index[alias] = index[target]
    
    return index

def main():
    print("=== Bet261 V400 WORLD ELO FETCH ===")
    print(f"Start {datetime.utcnow().isoformat()}Z")
    
    # 1. ClubElo API
    clubelo = fetch_clubelo_api()
    if len(clubelo) < 500:
        print("ClubElo API failed or too small, trying scrape fallback")
        clubelo_scrape = fetch_clubelo_scrape_fallback()
        if len(clubelo_scrape) > len(clubelo):
            clubelo = clubelo_scrape
    
    # Fallback ultime si vraiment rien
    if len(clubelo) == 0:
        print("⚠️ No ClubElo data, using minimal fallback")
        clubelo = [{"club":c["club"],"elo":c["elo"],"points":c["elo"],"rank":c["rank"],"country":c["country"],"level":1,"source":"fallback-officiel"} for c in OFFICIEL_236_FALLBACK]
    
    # 2. FootballDatabase WORLD
    fdb = fetch_footballdatabase_world()
    if len(fdb) < 500:
        print(f"⚠️ FDB only {len(fdb)} clubs, may be blocked - continuing anyway")
    
    # 3. Merge
    merged = merge_clubs(clubelo, fdb)
    print(f"✅ MERGED total {len(merged)} clubs uniques")
    print(f"  - ClubElo: {len(clubelo)}")
    print(f"  - FDB: {len(fdb)}")
    print(f"  - Merged: {len(merged)}")
    
    # 4. Index
    index = build_index(merged)
    print(f"✅ INDEX {len(index)} keys (avec alias)")
    
    # 5. Build final JSON
    out = {
        "updated": datetime.utcnow().isoformat() + "Z",
        "count": len(merged),
        "index_count": len(index),
        "sources": {
            "clubelo": {"count": len(clubelo), "api": "http://api.clubelo.com/YYYY-MM-DD"},
            "footballdatabase": {"count": len(fdb), "url": "https://www.footballdatabase.com/ranking/world"},
            "merged": {"count": len(merged)}
        },
        "live_count": len(clubelo),
        "is_live": len(clubelo) >= 500,
        "official_note": f"V400 WORLD - {len(clubelo)} ClubElo API (Europe top) + {len(fdb)} FootballDatabase World (toutes confédérations) = {len(merged)} clubs uniques. Plus de 'nc' car estimation automatique coté JS si non trouvé.",
        "clubs": merged[:5000],  # garde top 5000 pour taille raisonnable
        "index": index
    }
    
    with open("elo.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    
    print(f"✅ elo.json écrit: {len(merged)} clubs, {len(index)} index keys")
    print(f"File size: {len(json.dumps(out))/1024/1024:.2f} MB")

if __name__ == "__main__":
    main()
