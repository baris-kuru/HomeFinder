# HomeFinder

Watches the Berlin state-owned housing portal
[inberlinwohnen.de/wohnungsfinder](https://www.inberlinwohnen.de/wohnungsfinder/),
filters new listings to the ones that fit you, and **pre-fills the application
form** on the housing company's own site so all you have to do is review and click
submit. It emails you the moment a match appears.

It aggregates all 7 companies (berlinovo, degewo, GESOBAU, Gewobag, HOWOGE,
STADT UND LAND, WBM). Auto-fill adapters currently exist for **gewobag, degewo,
howoge, stadtundland**. Other companies still get scraped, filtered, and emailed,
so you can apply to those manually via the link in the email.

## How it works

Every few minutes it scrapes the newest listings, drops anything already seen or
that fails your filters, and for each new match:

1. If the company has an enabled adapter, it opens the application form in a real
   (visible) browser and fills in your details. It never clicks submit.
2. It emails you a summary plus a link, so you can review the open tab and send it
   yourself.

The final submit is always yours. The forms use invisible captchas
(reCAPTCHA v3, Friendly Captcha) that solve themselves, so there is nothing to
click there, but keeping you on the submit button is deliberate.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
cp config.example.toml config.toml
```

Then edit `config.toml`:

- **`[filters]`**: rooms, size, max rent, districts, and `require_no_wbs`
  (keep it `true` if your income is too high to qualify for a WBS).
- **`[applicant]`**: your real name, email, phone, and address. These go into the
  application forms.
- **`[email]`**: a Gmail App Password, not your normal password. Create one at
  [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
  (requires 2-Step Verification) and paste it into `app_password`.

`config.toml` and `homefinder.db` are gitignored, since they hold your personal data.

## Usage

First, baseline the current listings so you don't get flooded by the existing
backlog. You'll only be notified about listings that appear after this:

```bash
.venv/bin/python -m homefinder.main --seed
```

Then run it:

```bash
.venv/bin/python -m homefinder.main
```

Leave it running. When a match appears, a browser tab opens with the form
pre-filled and you get an email. Review the tab and click the submit button
(*Anfrage versenden*, *Absenden*, or *Kontakt aufnehmen*).

### Options

- `--once`: run a single cycle and exit (good for testing).
- `--no-apply`: scrape and email only, never open the apply browser.
- `--seed`: mark all current listings as seen without applying (run this first).

## Notes

- **HOWOGE** uses a 4-step wizard (WBS, income, and credit acknowledgements, then
  the contact form). The adapter opens it and pre-ticks the acknowledgements; you
  step through with *Weiter* and submit. The other three adapters fill the whole
  form on one page.
- Poll interval is `[poll].interval_seconds` (default 300s). Keep it reasonable.
- To reset and start fresh, delete `homefinder.db`.
- The apply browser uses a persistent profile in `browser_profile/` (kept out of
  git) so cookie consent and the reCAPTCHA-v3 reputation stay stable between runs.
