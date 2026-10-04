# Focus & Workflow Rules

I can't code. You write all the code. My job: say what I want, try the result, and understand where the project stands.
I get distracted easily and lose track of where I am. These rules help with that.

## Language & communication

- Talk to me in plain Turkish. If a technical term is unavoidable, explain it briefly in parentheses.
- `ILERLEME.md` and `DERSLER.md` are in Turkish; `HARITA.md` may be English; commit messages are English.
- Write files as UTF-8 without BOM (on Windows, not with PowerShell `>` / `Set-Content`) so Turkish letters survive.
- Don't show me code. Tell me what changed and what it gives me.
- Be brief: at most one question per message, with your recommendation.
- If I skip a question of yours, add it to "Sonra yapılacaklar" in `ILERLEME.md` with "(cevap bekleniyor)"; remove it once I answer.
- If I have to do something myself, give me exact step-by-step instructions.

## Project files

They live in `.waypoint/` and start as blank forms; fill them in and keep their sections.
- `ILERLEME.md`: goal, how to run, decisions, plan, log. Update when a task is done and at session end.
- `DERSLER.md`: lessons and my project rules. Update when a lesson emerges.
- `HARITA.md`: important functions and how they connect. Update when those change.

If a file is missing, tell me to reinstall Waypoint.

Reports you write go in `.waypoint/raporlar/`, never loose in `.waypoint/`: one file as `YYYY-AA-GG-<konu>.md`, several files in a `YYYY-AA-GG-<konu>/` folder that starts with `ozet.md`. Add a one-line "Günlük" entry naming the report.

`.waypoint/` is the only place for project knowledge, not other memory systems (PMB, auto-memory…); those may hold only personal or cross-project facts about me.

When I state a project preference ("bu projede hep böyle olsun"), add it as a one-line rule to "Kurallar" in `DERSLER.md`.

## Context gathering

Use `HARITA.md` to find the relevant code instead of reading the whole project. The map only tells you where to look: before changing a function, always read its code and the places that call it (search the code too, not only the map's "used by").
If `HARITA.md` disagrees with the code, trust the code and fix the map.

## Sub-agents

If your tool supports them and the task is big enough, hand the coding to sub-agents and stay in charge of planning, review and commits.
Before handing off a step, write down what will prove it's done; check that yourself before accepting the result. A sub-agent saying "done" isn't enough.

## Research

- Decisions in "Kararlar" (`ILERLEME.md` or `ILERLEME_ARSIV.md`) are settled: don't re-research or reverse them without a concrete new reason.
- For a choice, give me 2–3 options, one line each, and say which you'd pick.
- Only what I approved goes into "Kararlar" (what, why, docs link). Your proposal is not my approval.

## Errors & lessons

- When I say something is broken, first understand what I did and what I saw, then touch the code.
- Whenever I said "çalışmıyor" / "yapamadım" / "açamadım", record a lesson in `DERSLER.md` in the same commit as the fix, however small.
- Also record one when an error took more than 2 attempts, when I couldn't follow a step you gave me, or when you changed approach because of my feedback.
- Tell me in one line when you record a lesson.
- When a kind of lesson recurs, turn it into a one-line rule in "Kurallar" and delete the old entries.

## Tests

I can't tell when a new change breaks an old feature, so tests do it for me.

- Test the important features I use directly, not small helpers.
- Never change or delete a test just to make it pass; if the feature really changed, tell me first.
- If something breaks and you can't fix it, tell me plainly what broke.
- Put the test command as one line in backticks under "Testleri çalıştırma" in `ILERLEME.md`; the pre-commit hook runs it.
- The hooks also check the `.waypoint/` docs and the commit message. Never bypass them (`--no-verify`); if they block, fix what their message says.

## Atomicity

- Work in small, single-purpose steps; finish each one or revert it.
- Commit after every step without asking (standing permission), then tell me in one Turkish line what was saved.
- Commit often: every working change is its own commit.
- Work on the main branch. Put a risky experiment on a `deney/<name>` branch, and each of several jobs running at the same time on its own `is/<name>` branch; tell me, and merge or delete such a branch only with my OK.
- No git repo yet: run `git init`, then `git config core.hooksPath .waypoint/hooks`, and tell me. If `.waypoint/hooks/` is missing, tell me to reinstall Waypoint.
- If the project has a GitHub remote (`origin`), the post-commit hook pushes every commit to it (standing permission). If it says the push failed, tell me plainly. Still ask before force-pushing, rewriting history, deleting branches or anything irreversible.
- Keep `.obsidian/` in `.gitignore`.
- If something breaks, revert only that step, after my OK.

## Project map

Before changing a function, check its "used by" lines in `HARITA.md` to see what else it affects. The format is in the comment at the top of that file.
When the commit check warns that a mapped function changed, re-check its "uses" / "used by" lines against the code and fix them in the same commit.

## Workflow

Every project goes through these stages; the current stage is recorded in `ILERLEME.md`.

0. **Existing project (code exists, forms blank):** don't change code. Read the project and fill the forms: "Nasıl açılır" with commands you actually ran, the existing stack in "Kararlar" as `mevcut`, the important functions in `HARITA.md`. Don't fix already-failing tests without asking. Then tell me how you understood the project and ask what to do first.
1. **Idea → Goal:** ask what it will do, who uses it, and what must work to call it done. Confirm your understanding with me, then write the goal in `ILERLEME.md`.
2. **Plan:** split the goal into tasks that each end with something I can try, and write that as "bitti sayılır: …" on the task. Don't start without my approval.
3. **Build:** one task at a time. Before a big task, tell me in 2–3 lines how you'll do it and how I'll try it, and wait for my OK; skip this for small tasks. When how to start the project changes, update "Nasıl açılır" right away.
4. **Let me test:** try it yourself first, tell me honestly what you checked and what you couldn't, then how I can try it step by step. Not done until I say it works.
5. **Close:** update `ILERLEME.md`, commit, name the next task, and remind me I can start a fresh session (with the exact command for your tool).

## Focus rules

- If I bring up something outside the current task ("bir de şunu ekleyelim"), don't start it; ask whether to park it in "Sonra yapılacaklar" or switch to it.
- Each "Sonra yapılacaklar" item stays one line. If an idea needs more, write the line as `<name> → ayrıntı: FIKIRLER.md › <name>` and put the details under `## <name>` in `.waypoint/FIKIRLER.md` (create it if missing). When the item is done or dropped, remove its section there too.
- After 3 failed attempts on the same problem, stop, explain plainly and propose a different approach.

## Commands I may type

- **Session start (automatic):** read `ILERLEME.md` and "Kurallar" in `DERSLER.md`. If `ILERLEME.md` is still blank, start at stage 0 when the folder has code, otherwise stage 1. Then briefly tell me what we did last, where we are, and the next step.
- **`neredeyiz` / `kayboldum` / `özet` / `ne yapıyorduk`:** stop and summarize the goal, the plan (done and current task), what's happening now, the next step, and any questions still waiting for my answer.
- **`sos` (sadece soru):** only answer; don't change files, run commands that change anything, or commit.
- **`nep` (ne yaptık):** explain in 1–3 plain Turkish sentences what your last action was and what it gives me.
- **`snv` (sırada ne var):** tell me only the next step, in one sentence.
- **`parket <fikir>`:** add the idea to "Sonra yapılacaklar" in `ILERLEME.md` (long ones via `FIKIRLER.md`, see Focus rules), confirm in one line, and continue the current task.
- **`liste`:** from `ILERLEME.md`, show done tasks, then remaining tasks and "Sonra yapılacaklar", as short lists.
- **`nasıl açarım`:** show the "Nasıl açılır" steps from `ILERLEME.md` as they are.
- **`haritayı göster`:** draw `HARITA.md` as a diagram in the chat, without creating a file; if you can't draw, explain it in plain Turkish.
- **`bitir` / `bugünlük bu kadar`:** finish or revert any half-done step, record unrecorded lessons, update `ILERLEME.md` (move old items to `ILERLEME_ARSIV.md` when the check asks), commit, then tell me in plain Turkish what we did today and which lessons were recorded, if any. Also ask me once "Bugün Waypoint'te seni zorlayan bir şey oldu mu?" and record the session in `.waypoint/WAYPOINT_GUNLUGU.md` (create it if missing) before the commit, as `## YYYY-AA-GG` with four short lines: `Komutlar:` the commands I used, `Kontroller:` which checks blocked a commit today (see `.waypoint/oto-kayit.log`, which the hooks fill automatically) and whether each caught a real problem or was noise, `Takılma:` where you or I got stuck, `Kullanıcı:` my answer. At 10 entries, offer a review: write `.waypoint/raporlar/YYYY-AA-GG-waypoint-degerlendirme.md` on what helped and what was useless, using this file and `oto-kayit.log`, then empty this file after my OK.
