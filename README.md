# LeadBot

Finds freelance work for me — writing, brand and book design, motion and
explainer video, research writing, statistical analysis and agricultural
consulting — using only free public feeds. No API keys, no paid accounts.

It scores every post against the skills in `config.json` and produces a ranked
shortlist with a draft pitch under each lead.

## How it runs here

* `.github/workflows/leads.yml` runs daily at **06:00 UTC** and on demand.
* `leadbot.py` is downloaded from the published copy on every run, so the
  repository stays small. To keep the code in the repo instead, upload
  `leadbot.py` and delete the "Fetch LeadBot" step.
* Each run keeps `digest.html` and `leads.csv` as a downloadable artifact for
  30 days. Nothing is public — the repository is private.

## Run it now

1. Open the **Actions** tab.
2. Choose **LeadBot** → **Run workflow**.
3. Open the finished run and download the artifact **leads-N**.
4. Open `digest.html` on your phone.

## Phone notifications (optional)

Create a bot with **@BotFather** in Telegram, get your numeric id from
**@userinfobot**, then add repository secrets `TELEGRAM_TOKEN` and
`TELEGRAM_CHAT`. The morning run then messages the top ten leads to you.

## Sending email (off by default)

Set `sending.enabled` to `true` in `config.json` with an SMTP host, user and
from address, and add the password as the `SMTP_PASSWORD` secret so it never
lives in the repo. Brevo's free tier (~300/day) works and only needs a verified
sender address.

Use it carefully: it emails only posters who published their own address, caps
at 10 a day, never repeats an address, adds an opt-out line and honours
`suppress.txt`.

## Tuning

All in `config.json`: `keywords` (what I sell, with weights), `filters.exclude`
(instant no), `filters.penalise` (lower the score), `filters.min_score` (raise
for fewer, better leads) and `sources` (switch feeds on or off).

## Limits

* No auto-DM or auto-apply: Reddit, Freelancer, Upwork and LinkedIn ban it.
* Reddit sometimes rate-limits datacenter IPs, so that source may show as
  blocked on a cloud run. The "Sources checked" table at the bottom of each
  digest says what actually ran.
* It cannot see marketplaces without public feeds (Upwork, Fiverr,
  PeoplePerHour, LinkedIn).
