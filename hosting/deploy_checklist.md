# Deploy checklist

Tick these off the first time you ship it. The full explanation for each is in
`HOSTING_GUIDE.md`; this is the quick version.

## Before you push

- [ ] It runs locally: `python run_pipeline.py` writes a
      Parquet file with no errors.
- [ ] Tests pass: `pytest` is green.
- [ ] No secrets in the code. (This project has none — Open-Meteo needs no key —
      but check anyway. `.env` is git-ignored.)
- [ ] You have a GitHub account and Git works (`git --version`).

## Push the project

- [ ] `git init && git add . && git commit -m "Weather data-lake pipeline"`
- [ ] Created an empty repo on github.com (make it **public** — unlimited Actions
      minutes, and it's a portfolio piece).
- [ ] `git remote add origin ...` then `git push -u origin main`.

## Turn on the schedule

- [ ] Copied `hosting/github_actions/collect_weather.yml` to
      `.github/workflows/collect_weather.yml` at the repo root.
- [ ] Checked the `working-directory:` and `git add` paths in the workflow match
      where the project actually sits in your repo.
- [ ] Removed (or commented out) the `data/` line in
      `.gitignore` so collected data can be committed.
- [ ] Committed and pushed both changes.

## Verify it works

- [ ] Actions tab → "Collect weather" → **Run workflow** (manual trigger).
- [ ] The run is green.
- [ ] A new commit appeared from `github-actions[bot]` adding a Parquet file under
      `.../data/lake/weather/year=.../`.
- [ ] Wait for the next `:07` and confirm the *scheduled* run fires on its own
      (it may be a few minutes late — that's normal).

## Make it look good

- [ ] README has a one-line description and an architecture line.
- [ ] Added the Actions status badge to the README:

      ```markdown
      ![Collect weather](https://github.com/<you>/<repo>/actions/workflows/collect_weather.yml/badge.svg)
      ```

- [ ] Screenshot of the green hourly run history in the README.
- [ ] An example DuckDB query + its output in the README.
- [ ] Rehearsed the 60-second walkthrough (`knowledge/11_interview_prep.md`).

## A week later

- [ ] The lake has real history — dozens of partitions across several days.
- [ ] `duckdb` + `.read sql/analysis.sql` shows trends per city.
- [ ] You can explain, out loud, why the data is Parquet, why it's partitioned by
      date, and why re-running an hour doesn't duplicate anything.
