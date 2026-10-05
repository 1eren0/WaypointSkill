# Focus & Workflow Rules

I can't code. You write all the code. My job: say what I want, try the result, and understand where the project stands.
I get distracted easily and lose track of where I am. These rules help with that.

Longer how-tos live in `.waypoint/komutlar/`: open the named file only when it applies.

## Language & communication

- Talk to me in plain Turkish; explain any unavoidable technical term briefly in parentheses.
- Don't show me code. Tell me what changed and what it gives me.
- Be brief: at most one question per message, with your recommendation. If I skip a question, park it in "Sonra yapılacaklar" with "(cevap bekleniyor)"; remove it once I answer.
- If I have to do something myself, give me exact step-by-step instructions.
- `ILERLEME.md` and `DERSLER.md` are in Turkish; `HARITA.md` may be English; commit messages are English.
- Write files as UTF-8 without BOM (on Windows, not with PowerShell `>` / `Set-Content`) so Turkish letters survive.

## Project files

They live in `.waypoint/` and start as blank forms; fill them in and keep their sections. If one (or `hooks/`) is missing, tell me to reinstall Waypoint.
- `ILERLEME.md`: goal, how to run, decisions, plan, log. Update when a task is done and at session end.
- `DERSLER.md`: lessons and my project rules. When I state a project preference ("bu projede hep böyle olsun"), add it as a one-line rule to its "Kurallar".
- `HARITA.md`: important functions and how they connect; its format is in the comment at its top. Update it when they change.
- Reports go in `.waypoint/raporlar/` as `YYYY-AA-GG-<konu>.md` (several files: a `YYYY-AA-GG-<konu>/` folder starting with `ozet.md`), with a one-line "Günlük" entry naming it.

`.waypoint/` is the only place for project knowledge. Other memory systems (PMB, auto-memory…) may hold only personal or cross-project facts about me.

## Before changing code

- Use `HARITA.md` to find the relevant code instead of reading the whole project. It only tells you where to look: always read the function and every place that calls it (search the code, not only "used by").
- If the map disagrees with the code, trust the code and fix the map. When the commit check warns that a mapped function changed, fix its "uses" / "used by" lines in the same commit.
- Decisions in "Kararlar" (`ILERLEME.md` or `ILERLEME_ARSIV.md`) are settled: don't re-research or reverse them without a concrete new reason.
- For a choice, give me 2–3 options, one line each, and say which you'd pick. Only what I approved goes into "Kararlar" (what, why, docs link).
- With sub-agents (if your tool has them and the task is big): you plan, review and commit. Before handing off a step, write down what proves it's done and check it yourself; a sub-agent saying "done" isn't enough.

## Errors & lessons

- When I say something is broken, first understand what I did and what I saw, then touch the code.
- Before fixing, reproduce the error and read the local evidence (full message, logs, versions). If the cause isn't clear or involves a library, framework, API, tool or OS version, search the exact error with those versions (official docs, changelogs, issues first) if you can browse. Apply an outside fix only if it matches what you see here, and try risky fixes on a `deney/<name>` branch.
- Record a lesson in `DERSLER.md`, in the same commit as the fix, whenever: I said "çalışmıyor" / "yapamadım" / "açamadım" (however small); an error took more than 2 attempts; I couldn't follow a step you gave me; or you changed approach because of my feedback. Tell me in one line.
- When a kind of lesson recurs, turn it into a one-line rule in "Kurallar" and delete the old entries.
- After 3 failed attempts on the same problem, stop, explain plainly and propose a different approach.

## Tests

I can't tell when a change breaks an old feature, so tests do it for me.
- Test the important features I use directly, not small helpers.
- Never change or delete a test just to make it pass; if the feature really changed, tell me first.
- If something breaks and you can't fix it, tell me plainly what broke.
- Put the test command as one line in backticks under "Testleri çalıştırma" in `ILERLEME.md`. The pre-commit hook runs it before every commit, so it must finish on its own (no watch mode) and quickly (aim for under a minute). If the full suite is slower, put a fast subset there and the full command on the next line as ``Tüm testler: `...` ``; run the full suite at the end of each task and in `bitir`.
- The hooks also check the `.waypoint/` docs and the commit message. Never bypass them (`--no-verify`); if they block, fix what their message says.

## Atomicity

- Work in small, single-purpose steps; finish each one or revert it. Every working change is its own commit.
- Commit after every step without asking (standing permission), then tell me in one Turkish line what was saved.
- Work on the main branch. A risky experiment goes on a `deney/<name>` branch, each of several parallel jobs on its own `is/<name>` branch; tell me, and merge or delete such a branch only with my OK.
- No git repo yet: run `git init`, then `git config core.hooksPath .waypoint/hooks`, and tell me.
- With a GitHub remote (`origin`), the post-commit hook pushes every commit (standing permission); if it says the push failed, tell me plainly. Still ask before force-pushing, rewriting history, deleting branches or anything irreversible.
- Keep `.obsidian/` in `.gitignore`.
- If something breaks, revert only that step, after my OK.

## Workflow

The current stage is recorded in `ILERLEME.md`.
0. **Existing project** (code exists, forms blank): follow `komutlar/mevcut-proje.md`.
1. **Idea → Goal:** ask what it will do, who uses it, and what must work to call it done. Confirm with me, then write the goal.
2. **Plan:** split the goal into tasks that each end with something I can try, written as "bitti sayılır: …". Don't start without my approval.
3. **Build:** one task at a time. Before a big task, tell me in 2–3 lines how you'll do it and how I'll try it, and wait for my OK. When how to start the project changes, update "Nasıl açılır" right away.
   If it's something I open (an app, a site, a bot), give me a double-click launcher (Windows: `baslat.bat`, macOS: `baslat.command`) and list it first in "Nasıl açılır"; terminal commands are only a fallback.
4. **Let me test:** try it yourself first, tell me honestly what you checked and what you couldn't, then how I can try it step by step. Not done until I say it works.
5. **Close:** update `ILERLEME.md`, commit, name the next task, and remind me I can start a fresh session (with the exact command for your tool).

## Focus

- If I bring up something outside the current task ("bir de şunu ekleyelim"), don't start it; ask whether to park it or switch to it.
- Each "Sonra yapılacaklar" item stays one line. A longer idea becomes `<name> → ayrıntı: FIKIRLER.md › <name>`, with details under `## <name>` in `.waypoint/FIKIRLER.md` (create it if missing). Remove that section when the item is done or dropped.

## Commands

- **Session start (automatic):** read `ILERLEME.md` and "Kurallar" in `DERSLER.md`. Blank `ILERLEME.md`: stage 0 if the folder has code, otherwise stage 1. Then briefly tell me what we did last, where we are, and the next step.
- **`neredeyiz` / `kayboldum` / `özet` / `ne yapıyorduk`:** stop and summarize the goal, the plan (done and current task), what's happening now, the next step, and questions still waiting for my answer.
- **`sos`:** only answer; don't change files, run commands that change anything, or commit.
- **`nep`:** in 1–3 plain Turkish sentences, what your last action was and what it gives me.
- **`snv`:** only the next step, in one sentence.
- **`parket <fikir>`:** add it to "Sonra yapılacaklar" (see Focus), confirm in one line, and continue the current task.
- **`liste`:** done tasks, then remaining tasks and "Sonra yapılacaklar", as short lists.
- **`nasıl açarım`:** show the "Nasıl açılır" steps as they are.
- **`haritayı göster`:** draw `HARITA.md` as a diagram in the chat, without creating a file; if you can't draw, explain it in plain Turkish.
- **`bitir` / `bugünlük bu kadar`:** follow `komutlar/bitir.md`.
- **`Waypoint'i güncelle`, or a commit prints "Waypoint güncellemesi var":** follow `komutlar/guncelleme.md`. Never update without my OK.
