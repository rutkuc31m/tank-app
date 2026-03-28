import requests, json, os
from datetime import datetime, date

API_KEY = os.environ['TANKERKOENIG_API_KEY']
LAT, LNG, RAD = 52.3759, 9.7320, 10

def main():
    url = (f"https://creativecommons.tankerkoenig.de/json/list.php"
           f"?lat={LAT}&lng={LNG}&rad={RAD}&sort=dist&type=all&apikey={API_KEY}")
    data = requests.get(url, timeout=30).json()
    if not data.get('ok'):
        raise Exception(f"API-Fehler: {data.get('message')}")

    stations = data.get('stations', [])
    open_e10 = [s['e10'] for s in stations if s.get('isOpen') and s.get('e10', 0) > 0]
    all_e10  = [s['e10'] for s in stations if s.get('e10', 0) > 0]

    if not all_e10:
        raise Exception("Keine E10-Preise gefunden")

    today_str = date.today().isoformat()

    try:
        with open('prices.json') as f:
            result = json.load(f)
    except Exception:
        result = {'region': 'Hannover', 'days': []}

    current_min = round(min(open_e10 if open_e10 else all_e10), 3)
    current_max = round(max(all_e10), 3)

    existing = next((d for d in result.get('days', []) if d['date'] == today_str), None)
    days = [d for d in result.get('days', []) if d['date'] != today_str]
    days.append({
        'date':    today_str,
        # accumulate: keep lower min and higher max seen today
        'e10_min': min(current_min, existing['e10_min']) if existing else current_min,
        'e10_max': max(current_max, existing['e10_max']) if existing else current_max,
    })
    days.sort(key=lambda x: x['date'])
    days = days[-7:]

    out = {
        'updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'region':  'Hannover',
        'days':    days,
    }
    with open('prices.json', 'w') as f:
        json.dump(out, f, indent=2)

    e = days[-1]
    print(f"OK: {e['date']} · min={e['e10_min']} · max={e['e10_max']}")

if __name__ == '__main__':
    main()
