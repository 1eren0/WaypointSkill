# Changelog

What changed in each Waypoint version, written for the AI assistant that installs updates.
Summarize the relevant entries for the user in plain Turkish before asking to update.
The installed version is in `.waypoint/VERSION`.

## 1.0 — 2026-10-04

First numbered version. Everything below is new compared with an unversioned install.

- **Version and update notice:** `.waypoint/VERSION` records the installed version. Once a day, a commit checks GitHub for a newer version and asks the AI to tell the user; nothing installs without the user's OK.
- **Auto push:** if the project has an `origin` remote, every commit is pushed by the post-commit hook. Failures are reported and retried on the next commit. Experiments go on `deney/<name>`, parallel jobs on `is/<name>` branches.
- **Automatic log:** hooks write every commit, block and warning to `.waypoint/oto-kayit.log` (local only, not committed).
- **Session log:** `bitir` asks one question about friction and writes `.waypoint/WAYPOINT_GUNLUGU.md`; at 10 entries the AI offers a review report.
- **Reports:** reports go in `.waypoint/raporlar/` as `YYYY-AA-GG-<konu>.md` or a dated folder with `ozet.md`. Stray files in `.waypoint/` block the commit.
- **Parked ideas:** each "Sonra yapılacaklar" item is one line; long ideas keep details in `.waypoint/FIKIRLER.md`, and the check keeps both in sync.
- **Map hardening:** each map entry must still exist in its file; new functions must be mapped with their own file, listed as helpers, or have their file under `## Not mapped files`; a changed mapped function triggers a warning to re-check its links; more Mermaid node shapes are accepted; an unreadable diff blocks the commit.
- **Workflow:** before a big task the AI explains its approach in 2–3 lines and waits for OK; before changing code it reads that code and its callers.
- **New commands:** `sos` (answer only), `nep` (what we just did), `snv` (next step), `parket <fikir>` (park an idea), `liste` (done and remaining tasks).
