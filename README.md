# Sleeper league sync — 1367558309900468224

A **read-only** hourly snapshot of your Sleeper fantasy football league, hosted free using GitHub Actions and GitHub Pages. Uses only Python standard library.

## Setup (about 10 minutes)

1. Create a **public** GitHub repository named `sleeper-sync` (or any name). **Note: your league's rosters, manager display names, transactions, and team names will be public**. Do not use this method if that is unacceptable.
2. Upload `sync.py`, `README.md`, and `.github/workflows/sleeper.yml` preserving the folders. GitHub web uploads sometimes skip hidden `.github` folders; you can create `.github/workflows/sleeper.yml` using **Add file → Create new file**, typing the complete path.
3. Go to **Actions → Update Sleeper league → Run workflow**. The workflow generates `docs/league.json`.
4. Go to **Settings → Pages → Build and deployment → Deploy from a branch**, select `main` and `/docs`, then Save. Wait a few minutes for Pages to publish.
5. Your JSON URL will be `https://YOUR-GITHUB-USERNAME.github.io/sleeper-sync/league.json` (adjust if repo has another name). Test it in a browser.
6. Give ChatGPT that URL and ask it to fetch the latest snapshot before evaluating trades. You can also upload the JSON file directly if ChatGPT's browser cannot access the Pages URL.

## How it works

- Runs hourly at minute 17 UTC; GitHub schedules can be delayed or skipped under load. GitHub may disable schedules on inactive public repositories after 60 days; reactivate in Actions if needed.
- Reads league info, users, rosters, NFL week, transactions through the current week, and Sleeper's NFL player directory.
- Converts roster player IDs to names in `player_directory` and includes scoring settings.
- Outputs `docs/league.json` with `last_updated_utc`; use that timestamp to check freshness.
- Sleeper's full player dictionary is downloaded **at most once daily per local runner**, but GitHub's ephemeral runner has no cache in this basic setup, so this workflow would otherwise fetch it hourly. To respect Sleeper's recommendation, the workflow instead should cache the file using `actions/cache`, as described below.

### Important: player directory caching

To keep the NFL player directory request to about once per day, add the following step between `setup-python` and `Fetch Sleeper data` in the workflow:

```yaml
      - uses: actions/cache@v4
        with:
          path: players-cache.json
          key: sleeper-players-${{ github.run_id }}
          restore-keys: |
            sleeper-players-
```

The cache restore reuses the most recent saved dictionary; `sync.py` refreshes only after 24 hours. `players-cache.json` is **not** committed to the repository.

## Limits

- Not a persistent ChatGPT connector: you must share the URL and request a fresh fetch, and some ChatGPT sessions cannot read arbitrary URLs.
- It does **not** calculate player projections or trade values; pair it with current fantasy rankings and injury news.
- Does not submit trades or access private Sleeper account data.
- In a 3-for-2 trade, the receiving manager may need a roster cut; check roster constraints before offering.
