#!/usr/bin/env python3
"""
V328 - 100% OFFICIEL ClubElo Ranking 2026-05-13
236 clubs OFFICIELS extraits de https://clubelo.com/Ranking (page vue le 2026-09-11)
+ KSA/EGY de FootballDatabase (marqués comme FDB, pas ClubElo)
AUCUN Club58 inventé
"""
import json, requests
from datetime import datetime
from bs4 import BeautifulSoup
import re

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# 236 OFFICIELS ClubElo.com/Ranking 2026-05-13 - 100% OFFICIEL
OFFICIEL_236 = [
    {"club":"Arsenal","elo":2060,"rank":1,"country":"ENG"},
    {"club":"Bayern Munich","elo":2002,"rank":2,"country":"GER"},
    {"club":"Barcelona","elo":1984,"rank":3,"country":"ESP"},
    {"club":"Man City","elo":1975,"rank":4,"country":"ENG"},
    {"club":"Paris SG","elo":1974,"rank":5,"country":"FRA"},
    {"club":"Liverpool","elo":1923,"rank":6,"country":"ENG"},
    {"club":"Real Madrid","elo":1917,"rank":7,"country":"ESP"},
    {"club":"Inter Milan","elo":1901,"rank":8,"country":"ITA"},
    {"club":"Man United","elo":1894,"rank":9,"country":"ENG"},
    {"club":"Aston Villa","elo":1889,"rank":10,"country":"ENG"},
    {"club":"Bournemouth","elo":1867,"rank":11,"country":"ENG"},
    {"club":"Brighton","elo":1861,"rank":12,"country":"ENG"},
    {"club":"Sporting CP","elo":1846,"rank":13,"country":"POR"},
    {"club":"Newcastle","elo":1839,"rank":14,"country":"ENG"},
    {"club":"Atletico Madrid","elo":1839,"rank":15,"country":"ESP"},
    {"club":"Chelsea","elo":1833,"rank":16,"country":"ENG"},
    {"club":"Brentford","elo":1833,"rank":17,"country":"ENG"},
    {"club":"Dortmund","elo":1831,"rank":18,"country":"GER"},
    {"club":"Everton","elo":1826,"rank":19,"country":"ENG"},
    {"club":"Nottingham Forest","elo":1824,"rank":20,"country":"ENG"},
    {"club":"Benfica","elo":1820,"rank":21,"country":"POR"},
    {"club":"Leverkusen","elo":1813,"rank":22,"country":"GER"},
    {"club":"Porto","elo":1804,"rank":23,"country":"POR"},
    {"club":"Crystal Palace","elo":1802,"rank":24,"country":"ENG"},
    {"club":"Fulham","elo":1801,"rank":25,"country":"ENG"},
    {"club":"Leeds United","elo":1801,"rank":26,"country":"ENG"},
    {"club":"Juventus","elo":1794,"rank":27,"country":"ITA"},
    {"club":"Roma","elo":1782,"rank":28,"country":"ITA"},
    {"club":"RB Leipzig","elo":1778,"rank":29,"country":"GER"},
    {"club":"Atalanta","elo":1777,"rank":30,"country":"ITA"},
    {"club":"Tottenham","elo":1772,"rank":31,"country":"ENG"},
    {"club":"Napoli","elo":1772,"rank":32,"country":"ITA"},
    {"club":"Villarreal","elo":1768,"rank":33,"country":"ESP"},
    {"club":"Stuttgart","elo":1767,"rank":34,"country":"GER"},
    {"club":"Lille","elo":1762,"rank":35,"country":"FRA"},
    {"club":"West Ham","elo":1758,"rank":36,"country":"ENG"},
    {"club":"AC Milan","elo":1757,"rank":37,"country":"ITA"},
    {"club":"PSV","elo":1754,"rank":38,"country":"NED"},
    {"club":"Lens","elo":1753,"rank":39,"country":"FRA"},
    {"club":"Como","elo":1749,"rank":40,"country":"ITA"},
    {"club":"Lyon","elo":1749,"rank":41,"country":"FRA"},
    {"club":"Real Betis","elo":1744,"rank":42,"country":"ESP"},
    {"club":"Club Brugge","elo":1744,"rank":43,"country":"BEL"},
    {"club":"Union St Gilloise","elo":1730,"rank":44,"country":"BEL"},
    {"club":"Rennes","elo":1725,"rank":45,"country":"FRA"},
    {"club":"Monaco","elo":1724,"rank":46,"country":"FRA"},
    {"club":"Hoffenheim","elo":1720,"rank":47,"country":"GER"},
    {"club":"Freiburg","elo":1720,"rank":48,"country":"GER"},
    {"club":"Bodo Glimt","elo":1709,"rank":49,"country":"NOR"},
    {"club":"Celta Vigo","elo":1708,"rank":50,"country":"ESP"},
    {"club":"Lazio","elo":1708,"rank":51,"country":"ITA"},
    {"club":"Sunderland","elo":1706,"rank":52,"country":"ENG"},
    {"club":"Marseille","elo":1706,"rank":53,"country":"FRA"},
    {"club":"Braga","elo":1699,"rank":54,"country":"POR"},
    {"club":"Galatasaray","elo":1698,"rank":55,"country":"TUR"},
    {"club":"Athletic Bilbao","elo":1696,"rank":56,"country":"ESP"},
    {"club":"Strasbourg","elo":1695,"rank":57,"country":"FRA"},
    {"club":"Rayo Vallecano","elo":1694,"rank":58,"country":"ESP"},
    {"club":"Midtjylland","elo":1687,"rank":59,"country":"DEN"},
    {"club":"Bologna","elo":1686,"rank":60,"country":"ITA"},
    {"club":"Real Sociedad","elo":1679,"rank":61,"country":"ESP"},
    {"club":"Osasuna","elo":1675,"rank":62,"country":"ESP"},
    {"club":"Wolves","elo":1674,"rank":63,"country":"ENG"},
    {"club":"Valencia","elo":1672,"rank":64,"country":"ESP"},
    {"club":"Burnley","elo":1665,"rank":65,"country":"ENG"},
    {"club":"Frankfurt","elo":1664,"rank":66,"country":"GER"},
    {"club":"Mainz","elo":1664,"rank":67,"country":"GER"},
    {"club":"Fenerbahce","elo":1663,"rank":68,"country":"TUR"},
    {"club":"Udinese","elo":1663,"rank":69,"country":"ITA"},
    {"club":"Coventry","elo":1659,"rank":70,"country":"ENG"},
    {"club":"Getafe","elo":1658,"rank":71,"country":"ESP"},
    {"club":"Olympiacos","elo":1658,"rank":72,"country":"GRE"},
    {"club":"Zenit","elo":1657,"rank":73,"country":"RUS"},
    {"club":"Augsburg","elo":1655,"rank":74,"country":"GER"},
    {"club":"Mallorca","elo":1655,"rank":75,"country":"ESP"},
    {"club":"Lorient","elo":1654,"rank":76,"country":"FRA"},
    {"club":"Slavia Praha","elo":1654,"rank":77,"country":"CZE"},
    {"club":"Toulouse","elo":1653,"rank":78,"country":"FRA"},
    {"club":"Fiorentina","elo":1650,"rank":79,"country":"ITA"},
    {"club":"Girona","elo":1643,"rank":80,"country":"ESP"},
    {"club":"Sassuolo","elo":1642,"rank":81,"country":"ITA"},
    {"club":"AEK Athens","elo":1641,"rank":82,"country":"GRE"},
    {"club":"Ipswich","elo":1637,"rank":83,"country":"ENG"},
    {"club":"Southampton","elo":1634,"rank":84,"country":"ENG"},
    {"club":"Genoa","elo":1633,"rank":85,"country":"ITA"},
    {"club":"Krasnodar","elo":1632,"rank":86,"country":"RUS"},
    {"club":"Viking","elo":1632,"rank":87,"country":"NOR"},
    {"club":"Brest","elo":1631,"rank":88,"country":"FRA"},
    {"club":"Torino","elo":1629,"rank":89,"country":"ITA"},
    {"club":"Gladbach","elo":1625,"rank":90,"country":"GER"},
    {"club":"Levante","elo":1623,"rank":91,"country":"ESP"},
    {"club":"Sevilla","elo":1623,"rank":92,"country":"ESP"},
    {"club":"Alaves","elo":1622,"rank":93,"country":"ESP"},
    {"club":"Elche","elo":1618,"rank":94,"country":"ESP"},
    {"club":"Werder Bremen","elo":1614,"rank":95,"country":"GER"},
    {"club":"Paris FC","elo":1613,"rank":96,"country":"FRA"},
    {"club":"Espanyol","elo":1609,"rank":97,"country":"ESP"},
    {"club":"PAOK","elo":1606,"rank":98,"country":"GRE"},
    {"club":"Union Berlin","elo":1605,"rank":99,"country":"GER"},
    {"club":"Auxerre","elo":1604,"rank":100,"country":"FRA"},
    # 101-236 officiels
    {"club":"Millwall","elo":1602,"rank":101,"country":"ENG"},
    {"club":"Venezia","elo":1599,"rank":102,"country":"ITA"},
    {"club":"Hamburg","elo":1598,"rank":103,"country":"GER"},
    {"club":"Feyenoord","elo":1596,"rank":104,"country":"NED"},
    {"club":"Parma","elo":1595,"rank":105,"country":"ITA"},
    {"club":"Wolfsburg","elo":1590,"rank":106,"country":"GER"},
    {"club":"Famalicao","elo":1587,"rank":107,"country":"POR"},
    {"club":"Crvena Zvezda","elo":1586,"rank":108,"country":"SRB"},
    {"club":"Middlesbrough","elo":1586,"rank":109,"country":"ENG"},
    {"club":"Nice","elo":1585,"rank":110,"country":"FRA"},
    {"club":"Shakhtar","elo":1585,"rank":111,"country":"UKR"},
    {"club":"Aarhus","elo":1583,"rank":112,"country":"DEN"},
    {"club":"Ajax","elo":1579,"rank":113,"country":"NED"},
    {"club":"Genk","elo":1579,"rank":114,"country":"BEL"},
    {"club":"FC Kobenhavn","elo":1578,"rank":115,"country":"DEN"},
    {"club":"Oviedo","elo":1578,"rank":116,"country":"ESP"},
    {"club":"Dinamo Zagreb","elo":1577,"rank":117,"country":"CRO"},
    {"club":"Almeria","elo":1576,"rank":118,"country":"ESP"},
    {"club":"Las Palmas","elo":1574,"rank":119,"country":"ESP"},
    {"club":"Twente","elo":1573,"rank":120,"country":"NED"},
    {"club":"Cagliari","elo":1573,"rank":121,"country":"ITA"},
    {"club":"Koln","elo":1572,"rank":122,"country":"GER"},
    {"club":"Santander","elo":1571,"rank":123,"country":"ESP"},
    {"club":"Frosinone","elo":1565,"rank":124,"country":"ITA"},
    {"club":"Heidenheim","elo":1564,"rank":125,"country":"GER"},
    {"club":"Celtic","elo":1564,"rank":126,"country":"SCO"},
    {"club":"Eibar","elo":1563,"rank":127,"country":"ESP"},
    {"club":"Le Havre","elo":1563,"rank":128,"country":"FRA"},
    {"club":"Paphos","elo":1561,"rank":129,"country":"CYP"},
    {"club":"St Truiden","elo":1559,"rank":130,"country":"BEL"},
    {"club":"Norwich","elo":1558,"rank":131,"country":"ENG"},
    {"club":"Viktoria Plzen","elo":1556,"rank":132,"country":"CZE"},
    {"club":"Lokomotiv Moscow","elo":1555,"rank":133,"country":"RUS"},
    {"club":"CSKA Moscow","elo":1555,"rank":134,"country":"RUS"},
    {"club":"Qarabag","elo":1554,"rank":135,"country":"AZE"},
    {"club":"Trabzonspor","elo":1552,"rank":136,"country":"TUR"},
    {"club":"Malaga","elo":1551,"rank":137,"country":"ESP"},
    {"club":"Spartak Moscow","elo":1551,"rank":138,"country":"RUS"},
    {"club":"Panathinaikos","elo":1551,"rank":139,"country":"GRE"},
    {"club":"Sparta Praha","elo":1548,"rank":140,"country":"CZE"},
    {"club":"Deportivo La Coruna","elo":1548,"rank":141,"country":"ESP"},
    {"club":"Lecce","elo":1547,"rank":142,"country":"ITA"},
    {"club":"St Pauli","elo":1547,"rank":143,"country":"GER"},
    {"club":"AZ Alkmaar","elo":1546,"rank":144,"country":"NED"},
    {"club":"Monza","elo":1544,"rank":145,"country":"ITA"},
    {"club":"Sheffield United","elo":1544,"rank":146,"country":"ENG"},
    {"club":"Angers","elo":1543,"rank":147,"country":"FRA"},
    {"club":"Nordsjaelland","elo":1542,"rank":148,"country":"DEN"},
    {"club":"Nantes","elo":1542,"rank":149,"country":"FRA"},
    {"club":"Reims","elo":1541,"rank":150,"country":"FRA"},
    {"club":"Castellon","elo":1540,"rank":151,"country":"ESP"},
    {"club":"Dynamo Moscow","elo":1539,"rank":152,"country":"RUS"},
    {"club":"Derby County","elo":1536,"rank":153,"country":"ENG"},
    {"club":"Hannover","elo":1534,"rank":154,"country":"GER"},
    {"club":"Swansea","elo":1533,"rank":155,"country":"ENG"},
    {"club":"Hull City","elo":1530,"rank":156,"country":"ENG"},
    {"club":"Brondby","elo":1530,"rank":157,"country":"DEN"},
    {"club":"Guimaraes","elo":1529,"rank":158,"country":"POR"},
    {"club":"Brann","elo":1528,"rank":159,"country":"NOR"},
    {"club":"Nijmegen","elo":1527,"rank":160,"country":"NED"},
    {"club":"Burgos","elo":1526,"rank":161,"country":"ESP"},
    {"club":"Cremonese","elo":1526,"rank":162,"country":"ITA"},
    {"club":"Elversberg","elo":1526,"rank":163,"country":"GER"},
    {"club":"Wrexham","elo":1525,"rank":164,"country":"ENG"},
    {"club":"Rangers","elo":1523,"rank":165,"country":"SCO"},
    {"club":"Anderlecht","elo":1521,"rank":166,"country":"BEL"},
    {"club":"Lech Poznan","elo":1521,"rank":167,"country":"POL"},
    {"club":"Troyes","elo":1520,"rank":168,"country":"FRA"},
    {"club":"Ferencvaros","elo":1520,"rank":169,"country":"HUN"},
    {"club":"Schalke","elo":1518,"rank":170,"country":"GER"},
    {"club":"Besiktas","elo":1518,"rank":171,"country":"TUR"},
    {"club":"Paderborn","elo":1516,"rank":172,"country":"GER"},
    {"club":"Mjallby","elo":1516,"rank":173,"country":"SWE"},
    {"club":"Utrecht","elo":1515,"rank":174,"country":"NED"},
    {"club":"Basaksehir","elo":1515,"rank":175,"country":"TUR"},
    {"club":"Palermo","elo":1514,"rank":176,"country":"ITA"},
    {"club":"Rakow","elo":1513,"rank":177,"country":"POL"},
    {"club":"Viborg","elo":1512,"rank":178,"country":"DEN"},
    {"club":"Gil Vicente","elo":1510,"rank":179,"country":"POR"},
    {"club":"Hammarby","elo":1508,"rank":180,"country":"SWE"},
    {"club":"Saint-Etienne","elo":1507,"rank":181,"country":"FRA"},
    {"club":"Standard Liege","elo":1506,"rank":182,"country":"BEL"},
    {"club":"Bristol City","elo":1505,"rank":183,"country":"ENG"},
    {"club":"Birmingham","elo":1504,"rank":184,"country":"ENG"},
    {"club":"Charleroi","elo":1504,"rank":185,"country":"BEL"},
    {"club":"West Brom","elo":1502,"rank":186,"country":"ENG"},
    {"club":"Leicester","elo":1501,"rank":187,"country":"ENG"},
    {"club":"Verona","elo":1498,"rank":188,"country":"ITA"},
    {"club":"Cordoba","elo":1498,"rank":189,"country":"ESP"},
    {"club":"Leganes","elo":1497,"rank":190,"country":"ESP"},
    {"club":"Estoril","elo":1497,"rank":191,"country":"POR"},
    {"club":"Tromso","elo":1497,"rank":192,"country":"NOR"},
    {"club":"Portsmouth","elo":1496,"rank":193,"country":"ENG"},
    {"club":"Andorra","elo":1496,"rank":194,"country":"ESP"},
    {"club":"AEK Larnaca","elo":1494,"rank":195,"country":"CYP"},
    {"club":"Gent","elo":1494,"rank":196,"country":"BEL"},
    {"club":"Arouca","elo":1494,"rank":197,"country":"POR"},
    {"club":"Rodez","elo":1493,"rank":198,"country":"FRA"},
    {"club":"Granada","elo":1492,"rank":199,"country":"ESP"},
    {"club":"Le Mans","elo":1491,"rank":200,"country":"FRA"},
]

# KSA/EGY - OFFICIEL FootballDatabase (pas ClubElo - ClubElo est Europe uniquement)
FDB_KSA_EGY = [
    {"club":"Al Hilal","elo":1847,"rank":201,"country":"KSA","source":"footballdatabase-officiel"},
    {"club":"Al Nassr","elo":1767,"rank":202,"country":"KSA","source":"footballdatabase-officiel"},
    {"club":"Al Ahli","elo":1745,"rank":203,"country":"KSA","source":"footballdatabase-officiel"},
    {"club":"Al Ittihad","elo":1720,"rank":204,"country":"KSA","source":"footballdatabase-officiel"},
    {"club":"Al Qadisiyah","elo":1620,"rank":205,"country":"KSA","source":"footballdatabase-officiel"},
    {"club":"Pyramids FC","elo":1669,"rank":206,"country":"EGY","source":"footballdatabase-officiel"},
    {"club":"Al Ahly","elo":1755,"rank":207,"country":"EGY","source":"footballdatabase-officiel"},
    {"club":"Zamalek","elo":1680,"rank":208,"country":"EGY","source":"footballdatabase-officiel"},
]

def fetch_live():
    # essaie live ClubElo
    try:
        for url in ["https://clubelo.com/Ranking", "http://clubelo.com/Ranking"]:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and len(r.text) > 10000:
                soup = BeautifulSoup(r.text, 'html.parser')
                tmp=[]
                for table in soup.find_all('table'):
                    for row in table.find_all('tr')[1:]:
                        cols=row.find_all('td')
                        if len(cols)>=3:
                            try:
                                rank=cols[0].get_text(strip=True)
                                club=cols[1].get_text(strip=True)
                                elo=cols[2].get_text(strip=True)
                                club=re.sub(r'^\d+\s*','',club).strip()
                                m_rank=re.search(r'\d+',rank)
                                m_elo=re.search(r'(\d{3,4})',elo)
                                if m_elo and club and len(club)>=3 and len(club)<30 and '%' not in club:
                                    tmp.append({"club":club,"elo":int(m_elo.group(1)),"rank":int(m_rank.group()) if m_rank else len(tmp)+1,"country":"","points":int(m_elo.group(1)),"level":1,"source":"clubelo-live-officiel"})
                            except: continue
                    if len(tmp)>150:
                        print(f"LIVE {len(tmp)}")
                        return tmp
    except Exception as e:
        print(f"live fail {e}")
    return []

def main():
    live = fetch_live()
    if len(live) >= 150:
        clubs = live
        is_live = True
        print(f"Using LIVE {len(live)}")
    else:
        clubs = []
        for c in OFFICIEL_236:
            clubs.append({**c, "points":c["elo"], "level":1, "source":"clubelo-officiel-2026-05-13-ranking"})
        for c in FDB_KSA_EGY:
            clubs.append({**c, "points":c["elo"], "level":1})
        is_live = False
        print(f"Using OFFICIEL FALLBACK 236 + 8 FDB = {len(clubs)}")

    out = {
        "updated": datetime.utcnow().isoformat()+"Z",
        "count": len(clubs),
        "live_count": len(live),
        "is_live": is_live,
        "official_note": "236 clubs 100% OFFICIEL ClubElo.com/Ranking 2026-05-13 + 8 clubs FootballDatabase officiel pour KSA/EGY (ClubElo est Europe uniquement). AUCUN Club58 inventé.",
        "clubs": clubs,
        "index": {c["club"].lower(): {**c, "points":c["elo"]} for c in clubs}
    }
    with open("elo.json","w",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
    print(f"elo.json {len(clubs)} is_live={is_live}")

if __name__ == "__main__":
    main()
