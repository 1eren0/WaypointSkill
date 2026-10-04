# Changelog

What changed in each Waypoint version, written for the AI assistant that installs updates.
Summarize the relevant entries for the user in plain Turkish before asking to update.
The installed version is in `.waypoint/VERSION`.

## 1.3 — 2026-10-04

- **New command `Waypoint'i güncelle`:** the user can ask for an update at any time. Typing it counts as the user's OK: the AI summarizes what's new, installs, and commits the update alone. The automatic daily notice still asks first.

## 1.2 — 2026-10-04

Fixes from lessons recorded in real Waypoint projects.

- **Tests can't touch the real repository:** git passes the repository's location to hooks (`GIT_INDEX_FILE`, `GIT_DIR`…). These no longer reach the project's tests, so git commands in temporary test repos can't write fake commits into the real one. Projects that worked around this themselves (e.g. an `isolate-git-env` helper) can keep or drop their workaround.
- **Broken headings block the commit:** `HARITA.md` needs "Şema" and "Key functions / components", `DERSLER.md` needs "Kurallar" and "Kayıtlar". A heading damaged by a wrong encoding (e.g. "?ema") used to make the map check pass without checking anything.
- **Fast commit tests:** the test command run before each commit should take under a minute. A slower full suite goes on a "Tüm testler" line and runs at the end of each task and in `bitir`.
- **Double-click launcher:** apps, sites and bots get a `baslat.bat` / `baslat.command` listed first in "Nasıl açılır"; terminal commands become the fallback.

## 1.1 — 2026-10-04

- **Test time limit:** the project's tests now stop after 5 minutes and run with `CI=true`, so a test runner left in watch mode (e.g. plain `vitest`) can no longer freeze a commit. A timeout blocks the commit and says to make the test command exit on its own (e.g. `vitest run`).
- **Staged docs are checked:** the checks now read `ILERLEME.md`, `HARITA.md`, `DERSLER.md` and `FIKIRLER.md` as they will be committed. A log line written but not added to the commit no longer passes; add the file to the commit too.
- **Shorter rules:** `KURALLAR.md` is about a quarter shorter, so the AI follows it more reliably. The long how-tos for `bitir`, updating Waypoint and starting on an existing project moved to `.waypoint/komutlar/`, read only when needed. No rule was removed. The installer refreshes `komutlar/` on every update.

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
