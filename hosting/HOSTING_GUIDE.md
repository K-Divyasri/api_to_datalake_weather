# Hosting Guide — put this on GitHub and run it hourly for free

The whole point of this project is a data lake that *fills itself*. You don't pay
for a server; GitHub Actions runs your collector on a schedule and commits the new
data back to the repo. This guide takes you from a folder on your laptop to a
live, self-updating pipeline with a green checkmark recruiters can see.

Everything here is free. No credit card, no cloud bill.

## The shape of the plan

1. Put the project on GitHub.
2. Add the scheduled workflow (the YAML in `github_actions/`).
3. Let the `data/` folder be committed (it's normally git-ignored).
4. Watch it run, hourly, building your lake in public.

That's it. Let's do each step.

---

## Step 1 — Get the project on GitHub

If you've never used Git, read `knowledge/READING_LIST.md` (Git section) first —
ten minutes is enough. Then, from the project root:

```bash
# from the repo root
git init
git add .
git commit -m "Weather data-lake pipeline"
```

Make a new empty repo on github.com (no README, no .gitignore — you have those),
then:

```bash
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

Your code is now on GitHub. The schedule won't run yet — we add it next.

> Note on repo layout: the workflow file assumes this project is the repo root,
> so it has no `working-directory:` and the `git add` path is just `data`. If you
> instead nest this project in a subfolder of a bigger repo, add that subfolder as
> a `working-directory:` and prefix the `git add` path with it.

---

## Step 2 — Add the scheduled workflow

GitHub only runs workflows that live in `.github/workflows/` on your **default
branch** (`main`). Copy the provided file there:

```bash
mkdir -p .github/workflows
cp hosting/github_actions/collect_weather.yml .github/workflows/
git add .github/workflows/collect_weather.yml
git commit -m "Add hourly weather collection workflow"
git push
```

Open the **Actions** tab on your repo. You'll see the "Collect weather" workflow.

### Test it immediately (don't wait an hour)

The workflow has `workflow_dispatch:`, which adds a **Run workflow** button.
Click it (Actions → Collect weather → Run workflow). Watch the logs: it installs
deps, runs the collector, and commits the data. If it goes green, you're done —
the hourly schedule uses the exact same steps.

---

## Step 3 — Let `data/` be committed

There's a catch. `.gitignore` ignores `data/`, sensible on
your laptop, where you don't want to commit gigabytes of local runs. But for the
*hosted* version, committing the data IS the storage mechanism. So for the repo
you host, remove the lake from the ignore list.

Open `.gitignore` and delete (or comment out) the `data/`
line. Commit that change. Now the workflow's `git add ... data` actually stages
the new files.

If you'd rather keep big data out of Git entirely, see "Where else can the data
go?" below — but committing it is the simplest free option and looks great on a
portfolio (reviewers can browse the actual Parquet partitions).

---

## Step 4 — Understand the schedule (and its quirks)

The workflow runs on:

```yaml
on:
  schedule:
    - cron: "7 * * * *"      # 7 minutes past every hour
```

Cron is five fields: `minute hour day-of-month month day-of-week`. `7 * * * *`
means "minute 7 of every hour". A few things that trip everyone up:

- **It's UTC.** GitHub schedules always run in UTC, never your local time. Our
  pipeline stores everything in UTC too, which keeps the whole thing consistent.
- **It can be late.** Scheduled runs are best-effort. Under load — especially at
  the top of the hour — they can be delayed 5–15 minutes, or occasionally
  skipped. That's why we use minute `7`, not `0`. Don't build anything that needs
  exact timing on the free tier.
- **Default branch only.** The schedule runs from `main`. A workflow sitting on a
  feature branch won't fire on a timer.
- **It sleeps if the repo goes quiet.** GitHub disables scheduled workflows after
  **60 days** with no commits to the repo. Since this workflow commits data every
  hour, that clock keeps resetting itself — it stays alive as long as it's
  collecting. Good to know anyway.

The free tier gives you ~2,000 Actions minutes/month on a private repo, and
**unlimited** minutes on a **public** repo. This job takes well under a minute, so
even hourly you're nowhere near any limit. Make the repo public — it's a portfolio
piece meant to be seen.

---

## Is this really "free"? Yes — and why

- **Open-Meteo**: free, no API key, generous limits. Ten cities once an hour is
  240 calls a day, a rounding error against their allowance.
- **GitHub Actions**: free minutes cover this comfortably; public repos are
  unlimited.
- **Storage**: the Parquet is tiny (a few KB per hour) and lives in your repo.

No step in this pipeline costs money.

---

## Where else can the data go? (optional upgrades)

Committing to the repo is the simplest path, but you have options as you grow:

- **Upload as build artifacts** — replace the commit step with
  `actions/upload-artifact`. Good if you don't want data in Git history, but
  artifacts expire (default 90 days) and aren't browsable as a lake.
- **Push to cloud object storage** — write to an S3 bucket (AWS), a GCS bucket
  (Google), or Cloudflare R2 (no egress fees) using credentials stored as GitHub
  **Secrets**. This is the realistic production target and a natural lead-in to
  Project 12 (AWS data lake). Your local `year=/month=/day=` layout uploads to S3
  unchanged — that's the whole point of the folder convention.
- **Load into a warehouse** — have the workflow append to BigQuery or Snowflake
  instead of (or as well as) files. That's Project 7's territory.

Start by committing to the repo. It works, it's free, and it's visible. Upgrade
the destination later when a project calls for it.

---

## What to put in your README so it counts

A recruiter spends 60 seconds. Make them count:

- One line on what it does and the green Actions badge (see `deploy_checklist.md`).
- The architecture in one breath: *Open-Meteo API → raw JSON (bronze) → flatten →
  partitioned Parquet (silver) → DuckDB SQL, scheduled hourly on GitHub Actions.*
- A screenshot of the Actions run history (all those green hourly checkmarks are
  the proof it's real and automated).
- A couple of example DuckDB queries and their output.

Then rehearse the 60-second pitch from `knowledge/11_interview_prep.md`. A live,
self-updating pipeline you can explain beats ten dead repos.
