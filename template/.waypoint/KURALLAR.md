# Focus & Workflow Rules

I can't code. You write all the code. My job: say what I want, try the result, and understand where the project stands.
I get distracted easily and lose track of where I am. These rules exist to prevent that and override your defaults.

## Language & communication

- **Always talk to me in Turkish.** Plain, non-technical language. If a technical term is unavoidable, explain it in one sentence in parentheses.
- User-facing files (`ILERLEME.md`, `DERSLER.md`) and commit messages are written in **Turkish**. `HARITA.md` may be in English.
- Don't show me code or explain it line by line. Tell me **what changed** and **what it gives me**.
- Be brief. At most one question per message, always with your recommendation.
- If I must do something (run a command, change a setting, install something), give **step-by-step** instructions with the exact text to type or click.

## Project files

All live in `.waypoint/`. They start as blank forms; fill them in, keeping their section structure.

| File | For | Contents | Update when |
|---|---|---|---|
| `ILERLEME.md` | both | goal, how to run, decisions, plan, log | task done, session end |
| `DERSLER.md` | AI | errors, fixes, rules | a lesson emerges |
| `HARITA.md` | AI | important functions and their links | a function is added/removed or its links change |

If a file is missing, tell me to reinstall Waypoint (see its README); don't invent a different structure.

**`.waypoint/` is the only place for project knowledge.** Goals, decisions, plans, progress, lessons and the map go into these files — not into any other memory system (PMB, auto-memory, etc.). Those may hold only personal or cross-project facts about me.

## Context gathering

Before any work, gather context instead of guessing, in this order:
1. `ILERLEME.md` — where we are, current task
2. `DERSLER.md` — the "Kurallar" section first, then past errors related to this work
3. `HARITA.md` — which files/functions this touches and who uses them
4. **Only** the relevant code files

- Don't read the whole project; use `HARITA.md` to find what to open.
- If `HARITA.md` disagrees with the code, trust the code and fix the map.
- If something is unclear, don't guess: ask me one question with your recommendation.

## Research

Research **only when needed**:
- Choosing technology at project start
- Adding something new to the project (payments, maps, auth, an API…)
- An error not in `DERSLER.md` that 2 attempts didn't fix (check official docs)

Don't re-research anything already in the "Kararlar" section of `ILERLEME.md`. Don't reverse a decision without a concrete new reason.

- Official docs first, then recent sources. Distrust old blog posts and old versions.
- Goal: not the best option, but the **simplest one that's good enough** for a non-coder — easy setup, good docs, widely used, free or cheap.
- Present 2–3 options in Turkish, one sentence each (pro and con), mark your pick with ⭐, ask "Bununla devam edelim mi?".
- Once chosen, add one line to "Kararlar": what, why, docs link.
- **Only decisions I approved go into "Kararlar".** Your suggestion is not a decision until I say yes; never record it as one, and never treat an old note or your own earlier proposal as my approval.

## Errors & lessons

If I say something like "çalışmıyor" / "bozuldu", don't touch code yet. Ask in a single message only what's missing:
1. Ne yapmaya çalıştın?
2. Ne olmasını bekliyordun?
3. Ne oldu? (ekran görüntüsü / hata yazısı)

Then check `DERSLER.md` for similar errors, then fix.

Write to `DERSLER.md` when: an error took more than 2 attempts; I say "don't do it like this / do it like that"; something unexpected is learned. Entry = problem, cause, fix, one-line rule. Then tell me: `📝 Ders kaydedildi: <başlık>`

When the same kind of lesson recurs, promote it to a one-line rule in the "Kurallar" section at the top and delete the old entries. Keep "Kurallar" ≤ 20 lines.

## Tests

I can't tell when a new change breaks an old feature, so tests do it for me.

- Write small automated tests for **important features** only (things I use directly: login, saving, payment, home page…). No tests for small helpers.
- Use the most common, simplest test tool for the stack; record the choice in "Kararlar".
- Write tests in the same atomic step as the feature.
- **Run all tests before every commit.** Run them quietly — only show failures, not full output.
  - All pass → commit.
  - Any fail → don't commit; fix first. If you can't, tell me plainly: "Yeni değişiklik şunu bozdu: <özellik>" and propose a way forward.
- Never edit or delete a test just to make it pass. If the feature genuinely changed, tell me first.
- Put the test command in the "Testleri çalıştırma" section of `ILERLEME.md`, as one line in backticks (e.g. `` `npm test` ``). The pre-commit hook reads it from there.
- **The pre-commit hook enforces this.** `.waypoint/hooks/pre-commit` runs that command before every commit and blocks the commit if tests fail. Never bypass it (`--no-verify`). If it blocks a commit, treat it like any failing test.
- **The hooks also enforce the docs rules** (in every AI tool, since they run on `git commit`): `.waypoint/` files keep their structure, a commit that changes code needs today's line in "Günlük", every new function must appear in `HARITA.md` (in the list + diagram, or in "Not mapped"), and a fix commit prints a reminder to record a lesson. Read the ❌ messages and fix exactly what they say.

## Atomicity

Every change is **small, single-purpose, and reversible**.

- **One atomic step does one thing.** "Add login button" and "change colors" are separate steps.
- **A step is either fully done or not done at all.** No half-finished work; if it can't be finished, revert that step's changes.
- **If a step looks big** (many files, or can't be described in one sentence), split it first.
- **Commit after every atomic step without asking — this is my standing permission.**
  - Order: tests pass → update `HARITA.md` / `DERSLER.md` if needed → everything in the same commit.
  - Commit message: Turkish, short, one line. Example: `Giriş butonu eklendi`
  - If there's no git repo, run `git init` before the first commit and tell me in one sentence: "Kayıt noktası alabilmek için git kurdum." Right after `git init`, run `git config core.hooksPath .waypoint/hooks` to turn on the checks. If `.waypoint/hooks/` is missing, tell me to reinstall Waypoint.
  - Local commits only. Never push, rewrite history, or run irreversible commands like `reset --hard` without asking.
  - Never commit secrets (passwords, API keys, `.env`); add them to `.gitignore`. Also keep `.obsidian/` in `.gitignore` (Obsidian's settings folder).
- After committing, report in one line: `✅ Kaydedildi: <commit mesajı>`
- If something breaks, revert only the offending step (`git revert`) — but tell me which step first and get my OK.

## Project map

- **`HARITA.md` (for you):** see the project's structure without reading all the code, and know what a change will affect. Check the "kullanan / used by" lines before changing anything.
  - **Important functions only:** core parts of a feature, used from multiple places, or talking to the outside (DB, API). Small helpers go on the one-line "Not mapped (small helpers)" list instead.
  - Short and structured, no prose. Format is in the comment at the top of `HARITA.md`.
  - The "Şema" section is a Mermaid diagram of the same functions, so I can see the map in Obsidian. **Update the diagram and the list together, in the same step.**
  - Max 15 boxes per diagram. When the project outgrows that, switch to one overview diagram (files only) plus one small diagram per file.

## Workflow

Every project goes through these stages; the current stage is recorded in `ILERLEME.md`.

1. **Idea → Goal:** For a new project ask me: what will it do, who uses it, what must work to call it "done". Turn my answers into a 2–3 sentence goal in `ILERLEME.md`. Then research the tech choice and present options.
2. **Plan:** Split the goal into 3–8 **tasks**, each ending with something I can try ("giriş sayfası açılıyor"). Each task = one or more atomic steps. Simplest working version first, polish last. Show me the plan; don't start without approval.
3. **Build in atomic steps:** One task at a time; say in 1–2 sentences what you'll do. If the task needs something new, research and get approval first. Each step: write code → write/update tests → run all tests → update `HARITA.md` if needed → commit. If how to start the project changes (new command, new setup step), update **"Nasıl açılır"** in `ILERLEME.md` immediately, with exact copy-pasteable commands.
4. **Let me test:** When a task is done, tell me step by step how to try it (what to open, click, and expect), using "Nasıl açılır". Not done until I say "çalışıyor". Before handing a task to me, try it yourself and fix what you find. Every bug — whether I report it or you spot it — is fixed as its own atomic step and commit.
5. **Close the task:** Update `ILERLEME.md` and commit. Name the next task, ask "Buna geçelim mi?", and remind me that I can start a fresh session now to save context (tell me the exact command for the tool you're running in, e.g. `/clear` in Claude Code): "Görev bitti, istersen `<komut>` yazıp temiz başlayabilirsin."

## Focus rules

- If I ask for something off-topic (new feature, new idea, "bir de şunu ekleyelim"), don't do it. Ask:
  **"Bu yeni bir konu. 'Sonra yapılacaklar' listesine ekleyeyim mi, yoksa şimdiki görevi bırakıp buna mı geçelim?"**
- Fixing a bug in the current task is not off-topic; just do it.
- After 3 failed attempts on the same problem, stop, explain plainly, and propose a different approach. Once solved, record it in `DERSLER.md`.

## Commands I may type

- **Session start (automatic):** do Context gathering steps 1–3; if `ILERLEME.md` is still a blank form, start at stage 1. Then give me 3 lines: what we did last, current stage and task, next concrete step.
- **`neredeyiz` / `kayboldum` / `özet` / `ne yapıyorduk`:** stop and summarize — **Hedef** (1 sentence), **Plan** (tasks, ✅ done, 👉 current), **Şu an** (what and why), **Sıradaki adım** (one concrete step).
- **`nasıl açarım`:** show the "Nasıl açılır" steps from `ILERLEME.md` verbatim.
- **`haritayı göster`:** read `HARITA.md` and draw it for me in the chat as a diagram (boxes = important functions, grouped by file, with a ≤5-word plain-Turkish caption each; arrows = "uses"). Never create a file for it. If your tool can't draw in chat, explain the map in plain Turkish instead.
- **`bitir` / `bugünlük bu kadar`:**
  - Finish or revert any half-done atomic step.
  - Record any unrecorded lesson in `DERSLER.md`.
  - Update `ILERLEME.md` (check "Nasıl açılır" is current). If "Günlük" has more than 10 entries, move the older ones to `.waypoint/GUNLUK_ARSIV.md`.
  - Run tests and commit.
  - Give me a 3-bullet "bugün ne yaptık" summary in plain Turkish.
