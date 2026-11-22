# LeadBot

A small Python bot that finds freelance and contract work for Moses, using only
free public feeds, and emails the ones that published a contact address.

It reads posts from places where people are already **looking to hire**, scores
each one against the skills in `config.json`, then writes a short, tailored
message to whoever posted the work. Nothing is drafted for review: the daily run
sends.

| File | What it is |
| --- | --- |
| `output/digest.html` | A ranked page of this run's finds, with links |
| `output/leads.csv` | The same list as a spreadsheet |
| `output/seen.db` | Remembers what it has shown, so nothing repeats |
| `state/sent.db` | Who has been emailed (addresses stored as hashes) |
| `docs/leads.json` | The public feed the phone page reads (addresses masked) |

---

## 1. Run it

Python 3.8+, standard library only.

```bash
cd leadbot
python3 leadbot.py            # find leads, write the report
python3 leadbot.py --dry-run  # show exactly who would be emailed, send nothing
python3 leadbot.py --send     # send, up to the daily cap
```

Useful options: `--days 3`, `--min-score 15`, `--source reddit,openstreetmap`,
`--all`, `--cap 8`, `--no-notify`.

---

## 2. How the email decides what to say

* **Service track.** The post is read for the service it actually needs:
  writing, design, video, data/statistics, agriculture, or web.
* **Greeting.** The stored poster name first, then an HR-style greeting, then the
  company or brand, then a plain "hello". Never "Dear Sir".
* **Engagement.**
  * `full-time` / `part-time` in the advert, or an advert with employment detail
    (salary, leave, probation, interviews) gets an application letter with a CV
    offer and no "freelance" in the signature.
  * contract, freelance, retainer, as needed, on call, ad hoc, seasonal and
    project work gets the short pitch letter.
  * A vacancy that never says how the work is engaged is read on its evidence,
    not assumed to be staff work: without employment detail it keeps the pitch.
* **Subject** names the service and the company, or the role for a vacancy, and
  never repeats the body's first line.
* **Voice.** Wording is chosen deterministically from a hash of the address, URL
  and title, so one lead always gets the same letter and two leads do not get the
  same one. No em dashes, no clip-ons, no "I hope this finds you well", no
  service list, no exclamation marks.

Before anything leaves, `spam_issues()` checks the copy. A message with a spam
phrase, a dash, more than one link, shouting caps, AI tics or over 170 words is
**held**, not sent, and the reason is logged.

---

## 3. Sending

`config.json` → `sending`:

```json
"sending": {
  "enabled": true,
  "provider": "smtp",
  "from_name": "Moses Ojeleye",
  "from_email": "ojeleyemoses698@gmail.com",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_starttls": true,
  "smtp_user": "ojeleyemoses698@gmail.com",
  "smtp_password": "",
  "daily_cap": 5,
  "min_seconds_between": 60
}
```

The password is never stored here: the workflow passes `SMTP_PASSWORD` from the
repository secrets, and the code falls back to that variable.

**Why five a day.** The cap protects the Gmail address. Cold mail from a personal
account is judged on complaint rate, and a burst gets limited or suspended;
five a day, one address at a time, a minute apart, keeps the record clean while
the queue carries the overflow to the next morning. It is a setting, not a
limit: raise `daily_cap`, or set the repository variable `LEADBOT_DAILY_CAP`,
while the sending record stays healthy. Warm up slowly (5 to 8 to 12).

Guardrails: one message per address ever, a suppression file
(`output/suppress.txt`), a `List-Unsubscribe` header, plain text only, and a
daily queue in `sent.db` so leads over the cap roll over instead of being lost.

Cold-email rules differ by country (CAN-SPAM, UK PECR, CASL, Australian Spam
Act). The opt-out line and the suppression file are the minimum everywhere.

---

## 4. Where the leads come from

| Source | What it is | Notes |
| --- | --- | --- |
| Reddit (`r/forhire`, `r/hireareddit`, `r/DesignJobs`, `r/freelance_forhire`) | People posting "hiring" with a budget | Needs a free Reddit app, see below |
| Hacker News | "SEEKING FREELANCER" posts and the monthly thread | Often the best clients |
| OpenStreetMap | Businesses that published their own address in the map | Prospect outreach, Lagos / Abuja / Accra / Nairobi |
| Freelancer.com | New public projects | About 20 at a time |
| Remotive, We Work Remotely, Jobicy, Himalayas, Working Nomads, Remote OK, Jobspresso, Arbeitnow, NoDesk, Dribbble | Remote job boards | Contract and freelance posts; staff roles get the application letter |
| ReliefWeb, World Bank | Consultancy and tender notices | Home-based and international only |
| Mastodon, Bluesky | Public posts asking for a freelancer | Handle becomes the greeting |
| Telegram | Public channels via `t.me/s/<channel>` | Off by default |

### Reddit, free

Reddit refuses anonymous `.json` and `.rss` reads from cloud addresses (403/429),
which is why the source used to contribute nothing from GitHub. The fix is free
and takes two minutes:

1. Sign in to Reddit, open <https://www.reddit.com/prefs/apps>, click
   **create another app**.
2. Name it anything, choose **script**, put `http://localhost:8080` in the
   redirect field. Create it.
3. The string under the app name (next to "personal use script") is the client
   id; the **secret** is the longer string.
4. Repository, Settings, Secrets and variables, Actions, **New repository
   secret**: `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`.

The bot then reads `oauth.reddit.com` with an app-only token. Without the
secrets it falls back to the public feed and logs that it did.

### OpenStreetMap

Free and keyless (Overpass API). Only records where the business put an email
into public map data are kept, and the query is sent as a POST with a real
User-Agent, which is what Overpass accepts. Four cities take a few minutes; add
cities in `sources.openstreetmap.cities`.

---

## 5. Run it every day, free (GitHub Actions)

`.github/workflows/leads.yml` runs at 06:13 and 09:43 UTC, downloads the current
`leadbot.py` and `config.json` from the published page, runs `--send`, merges the
feed and commits `docs/` and `state/`.

Secrets: `SMTP_PASSWORD`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`.
Optional variable: `LEADBOT_DAILY_CAP`.

Every run also keeps `digest.html` and `leads.csv` as a downloadable artifact for
30 days.

---

## 6. Privacy of the published feed

`docs/leads.json` is public: the phone page reads it straight from the repo.
`merge_feed.py` therefore masks every address (`m***@domain`), and `sent.db`
keeps a SHA-256 hash and a masked address instead of the real one. The queue is
the only place an unreached address is stored in the clear, and it is trimmed to
300 rows and emptied as messages go out.

---

## 7. What it will not do

* It does not DM, auto-apply or scrape LinkedIn, Upwork, Fiverr or Craigslist.
  Those platforms ban automated outreach and have no free API for it.
* It does not invent leads; a dead feed shows as skipped in the log.
* It does not send to an address the poster did not publish themselves.
