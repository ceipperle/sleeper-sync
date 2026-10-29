#!/usr/bin/env python3
"""Read-only Sleeper league snapshot for GitHub Pages. No third-party dependencies."""
import json
import os
import pathlib
import urllib.request
from datetime import datetime, timezone

LEAGUE_ID = os.environ.get('SLEEPER_LEAGUE_ID', '1367558309900468224')
BASE = 'https://api.sleeper.app/v1'
OUT = pathlib.Path('docs')
OUT.mkdir(exist_ok=True)

def fetch(path):
    req = urllib.request.Request(BASE + path, headers={'User-Agent': 'personal-sleeper-sync/1.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

league = fetch(f'/league/{LEAGUE_ID}')
if not isinstance(league, dict) or str(league.get('league_id')) != LEAGUE_ID:
    raise RuntimeError('League ID not found or Sleeper response invalid')
rosters = fetch(f'/league/{LEAGUE_ID}/rosters')
users = fetch(f'/league/{LEAGUE_ID}/users')
state = fetch('/state/nfl')
week = int(state.get('week') or 1)
# Weekly transactions can contain previous weeks' activity; include all season-to-date.
transactions = []
for n in range(1, min(week + 1, 19)):
    transactions.extend(fetch(f'/league/{LEAGUE_ID}/transactions/{n}') or [])
# The full player dictionary is large; Sleeper requests it no more than daily.
cache = pathlib.Path('players-cache.json')
refresh = not cache.exists() or (datetime.now(timezone.utc).timestamp() - cache.stat().st_mtime) > 86400
if refresh:
    players = fetch('/players/nfl')
    cache.write_text(json.dumps(players, separators=(',', ':')), encoding='utf-8')
else:
    players = json.loads(cache.read_text(encoding='utf-8'))
used = {str(pid) for r in rosters for pid in (r.get('players') or [])}
for tx in transactions:
    used.update(str(pid) for pid in (tx.get('adds') or {}))
    used.update(str(pid) for pid in (tx.get('drops') or {}))
player_names = {pid: {
    'name': (players.get(pid) or {}).get('full_name') or ' '.join(filter(None, [(players.get(pid) or {}).get('first_name'), (players.get(pid) or {}).get('last_name')])) or pid,
    'position': (players.get(pid) or {}).get('position'),
    'team': (players.get(pid) or {}).get('team'),
    'injury_status': (players.get(pid) or {}).get('injury_status')
} for pid in used}
by_user = {str(u['user_id']): u for u in users}
teams = []
for r in rosters:
    u = by_user.get(str(r.get('owner_id')), {})
    teams.append({
        'roster_id': r.get('roster_id'),
        'manager': u.get('display_name') or u.get('username') or 'Unknown',
        'team_name': (u.get('metadata') or {}).get('team_name') or u.get('display_name') or 'Unknown',
        'starters': r.get('starters') or [],
        'players': r.get('players') or [],
        'reserve': r.get('reserve') or [],
        'taxi': r.get('taxi') or [],
        'record': r.get('settings') or {}
    })
snapshot = {
    'last_updated_utc': datetime.now(timezone.utc).isoformat(),
    'source': 'Sleeper public read-only API',
    'league_id': LEAGUE_ID,
    'league_name': league.get('name'),
    'season': league.get('season'),
    'week': week,
    'roster_positions': league.get('roster_positions'),
    'scoring_settings': league.get('scoring_settings'),
    'teams': teams,
    'player_directory': player_names,
    'transactions': transactions
}
save('league.json', snapshot)
(OUT / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Sleeper League Snapshot</title><h1>Sleeper League Snapshot</h1><p><a href="league.json">View latest JSON snapshot</a></p><p>Automatically updated by GitHub Actions. Public league data only.</p>\n', encoding='utf-8')
print(f"Updated {len(teams)} rosters, {len(transactions)} transactions, week {week}")
