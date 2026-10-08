# Changelog

What changed in each Waypoint version, written for the AI assistant that installs updates.
Summarize the relevant entries for the user in plain Turkish before asking to update.
The installed version is in `.waypoint/VERSION`.

## 1.13 — 2026-10-08

- **English short forms:** `where` (where are we), `ask` (just a question), `recap` (what did we do), `next` (what's next), `run` (how do I run it), `map` (show the map). A one-word short form, Turkish or English, counts as a command only when it is the user's whole message, so a normal sentence containing "next" isn't mistaken for one.

## 1.12 — 2026-10-08

- **English commands and replies:** every command also works in English (`where are we`, `just a question`, `what did we do`, `what's next`, `park <idea>`, `list`, `how do I run it`, `show the map`, `clarify`, `finish`, `update Waypoint`). If the user writes in English, the AI answers in plain English; project notes stay in Turkish.

## 1.11 — 2026-10-08

- **Commands anyone can guess:** the short commands now have plain Turkish long forms that work the same way: `sadece soru` (= `sos`), `ne yaptık` (= `nep`), `sırada ne var` (= `snv`), `sonraya ekle <fikir>` (= `parket <fikir>`). The short forms keep working.

## 1.10 — 2026-10-08

- **No GitHub CLI needed anymore:** the Waypoint repo is public now. Installing, `guncelle.bat` / `guncelle.command` and the daily new-version check download straight from GitHub, so `gh` and `gh auth login` are no longer required. Projects on 1.9 still update with their old `guncelle.bat` if `gh` is set up; after that, the new launcher works without it.

## 1.9 — 2026-10-07

- **The user starts the update, not the AI:** Claude Code's auto mode blocked the AI from running the installer ("Code from External"), and rightly so: it runs code downloaded from the internet. The AI still summarizes what's new, then asks the user to double-click the new `.waypoint/guncelle.bat` (macOS: `.waypoint/guncelle.command`) and write "güncelledim"; then it commits and tidies as before. It never runs the installer itself.
- **This one update is by hand:** projects on 1.8 or older don't have `guncelle.bat` yet. The AI gives the user one line to paste into a terminal in the project folder; from 1.9 on, double-clicking is enough.

## 1.8 — 2026-10-07

- **Reading callers only where it matters:** the code and every place that uses it must be read for changes that can affect behavior, an interface/API, data flow or a symbol's name. Changes only to docs, user-visible text/labels or comments no longer require it.
- **No second OK after the plan:** before a big task the AI still says in 2–3 lines what it will do and how the user will try it, but then goes on. It stops only for a new product decision, work growing clearly beyond the approved plan, or a risky, irreversible or shared-system step.

## 1.7 — 2026-10-07

- **`sorgula` no longer skips the plan step:** at stage 1 its summary only fills "Proje hedefi"; the plan is still made and approved in stage 2.
- **"Bilmiyorum" is a temporary assumption:** the AI's recommendation is used for now but is not a decision and never goes into "Kararlar"; the question is parked in "Sonra yapılacaklar" with "(cevap bekleniyor)" to confirm later.
- Fixed duplicate step number in the update recipe.

## 1.6 — 2026-10-07

- **New `sorgula` step (inspired by the `grill-me` skill):** at stage 1 and before a big new feature, the AI questions the idea before building: product questions only, one per message with a recommended answer, basics first, about 10 at most. It then confirms a 3–5 line summary and records it in the goal, plan or the task's "bitti sayılır" line. Skipped for small fixes; the user can start it any time by typing `sorgula`.
  It looks facts up in the code and files instead of asking, never answers a decision for the user (but always recommends), accepts "bilmiyorum" (uses the recommendation and marks it for later), offers a throwaway mock-up for look-and-feel questions, and doesn't start building before the summary is confirmed.

## 1.5 — 2026-10-05

Fixes from the `oto-kayit.log` files of two real projects.

- **Ignored warnings now block:** a size warning (Günlük, Plan, Kararlar, Sonra yapılacaklar, DERSLER Kayıtlar) that was already shown on an earlier day within the last week blocks the commit until it's fixed. In the logs these warnings repeated for two days and were never acted on.
- **One line for changed map functions:** instead of one warning per changed function (often 5–12 per commit), a single line lists them.
- **Only top-level functions must be mapped:** inner functions and indented methods (e.g. `schedule()` / `cancel()` inside a returned object) no longer block the commit; map the outer function or class. Names added to "Not mapped (small helpers)" only for this reason can be removed.
- **Session log without `bitir`:** at each task close, if `WAYPOINT_GUNLUGU.md` has no entry for today, the AI asks the friction question and writes the entry. No project had used `bitir` yet.
- **One-time tidy on update:** after installing an update, the AI moves old loose files in `.waypoint/` (reports from before 1.0) into `raporlar/` with dated names, and anything that isn't a report into the project.

## 1.4 — 2026-10-05

- **Error diagnosis:** before fixing, the AI reproduces the error and reads the local evidence (full message, logs, versions). For unclear or version-related errors it searches the exact message (official docs, changelogs, issues first) when it can browse, applies an outside fix only if it matches the project's evidence, and tries risky fixes on a `deney/<name>` branch.

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
