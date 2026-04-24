# YouTube Data API Setup — 5-minute walkthrough

The `fetch_youtube_mentions.py` pipeline runs in two modes:

- **Seeded mode** (default): ships a curated set of recent frontier-tech mentions so the UI always has content. Runs every Sunday, no config needed.
- **Live mode** (when `YOUTUBE_API_KEY` is set as a repo secret): hits the YouTube Data API v3, fetches the 8 most recent videos from each of our 14 curated channels, pulls auto-captions via `youtube-transcript-api`, and NER-matches against the 868-company database.

To switch to live mode, follow the 3 steps below.

---

## Step 1: Get a YouTube Data API key

1. Go to **https://console.cloud.google.com/apis/credentials**
2. If you don't have a GCP project: click **Select a project → New Project** → name it `innovators-league-youtube`.
3. With the project selected, click **+ CREATE CREDENTIALS → API key**.
4. Copy the key (it looks like `AIza...`).
5. Optional but recommended — click **Restrict key** → under **API restrictions**, select "Restrict key" → pick **YouTube Data API v3** from the dropdown. This scope-limits the key so a leak can't incur costs elsewhere.

### Enable the API
6. In the GCP console, go to **APIs & Services → Library**.
7. Search for **YouTube Data API v3** → click it → click **Enable**.

### Cost
YouTube Data API v3 gives you **10,000 quota units per day free**. Each search request = 100 units. We fetch 8 videos from each of 14 channels once per week = ~1,120 units per run, leaving 98% of your daily quota unused. **No credit card required.** No surprises.

---

## Step 2: Add the key as a GitHub repo secret

1. Go to **https://github.com/PaleoFaire/innovators-league/settings/secrets/actions**
2. Click **New repository secret**.
3. Name: `YOUTUBE_API_KEY`
4. Secret: paste your `AIza...` key.
5. Click **Add secret**.

GitHub Actions will now pass the key to the workflow as `$YOUTUBE_API_KEY` on the next run. **Don't share the key, don't commit it, don't paste it in chat.**

---

## Step 3: Trigger the first live run

You have two options:

**Option A — wait for Sunday**: the `weekly-intelligence-sync.yml` workflow runs every Sunday at 08:00 UTC. It will automatically detect the new secret and switch to live mode.

**Option B — manual trigger**: go to the **Actions** tab → **Weekly Intelligence Sync** → **Run workflow** → pick `main` → **Run workflow**. Takes ~8 minutes. When it completes, `data/youtube_mentions_auto.json` will have `"source_status": "live"` and real mentions from the last week of videos.

---

## What the live pipeline does

For each of the 14 curated channels (NVIDIA, Tesla, SpaceX, Boston Dynamics, Figure, Anduril, Rocket Lab + 7 investor podcasts), the pipeline:

1. Lists the 8 most recent uploaded videos (YouTube Data API `search` endpoint).
2. For each video, pulls the auto-generated English captions via `youtube-transcript-api` (no API key needed for this — it uses YouTube's public caption tracks).
3. Scans every caption chunk for mentions of any of the 868 tracked companies using word-boundary regex.
4. For each hit, builds a ±3-chunk context snippet (~180 chars) and records the timestamp.
5. Emits `data/youtube_mentions_auto.json` with the newest mentions first.

The UI on `signals.html` renders each mention as a clickable card that jumps directly to the timestamp in the YouTube video.

---

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| Source status = `seeded` after setup | Check the secret name is exactly `YOUTUBE_API_KEY` (case-sensitive, underscores). |
| Source status = `seeded_fallback` | Live pipeline errored — check the workflow logs. Usually means YouTube Data API isn't enabled on the project. |
| `No captions available` errors in logs | Some videos don't have auto-captions yet (especially within first 24h of upload). The pipeline skips these gracefully. |
| Quota exceeded errors | Unlikely at our volume, but if you hit 10K units/day: wait 24h or request a quota increase in GCP console. |
| Want to add / remove channels | Edit `CURATED_CHANNELS` dict at the top of `scripts/fetch_youtube_mentions.py`. Key is the display name, value is the YouTube channel ID (the `UC...` string from the channel URL). |

---

## Regenerating channel IDs

If you want to find a channel's ID for `CURATED_CHANNELS`:

1. Visit the channel on YouTube (e.g., `https://www.youtube.com/@AcquiredFM`).
2. Right-click → View Page Source.
3. Search for `"channelId"` — the value is what you want.

Alternative: use `https://commentpicker.com/youtube-channel-id.php` — paste the channel URL, get the ID.
