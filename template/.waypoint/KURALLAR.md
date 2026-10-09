# Focus & Workflow Rules

I can't code. You write all the code. My job: say what I want, try the result, and understand where the project stands.
I get distracted easily and lose track of where I am. These rules help with that.

The rules below always apply. When a situation below names a file in `.waypoint/komutlar/`, open it then and follow it.

## Language & communication

- Talk to me in plain Turkish (in plain English if I write in English); explain any unavoidable technical term briefly in parentheses.
- Don't show me code. Tell me what changed and what it gives me.
- Be brief: at most one question per message, with your recommendation. If I skip a question, park it in "Sonra yapılacaklar" with "(cevap bekleniyor)"; remove it once I answer.
- If I have to do something myself, give me exact step-by-step instructions.
- `ILERLEME.md` and `DERSLER.md` are in Turkish; `HARITA.md` may be English; commit messages are English.
- Write files as UTF-8 without BOM (on Windows, not with PowerShell `>` / `Set-Content`) so Turkish letters survive.

## Project files

In `.waypoint/`, the only place for project knowledge (other memory systems may hold only personal or cross-project facts about me). Fill the forms and keep their sections; if one (or `hooks/`) is missing, tell me to reinstall Waypoint.
- `ILERLEME.md`: goal, how to run, decisions, plan, log. Update when a task is done.
- `DERSLER.md`: lessons and my project rules. When I state a project preference ("bu projede hep böyle olsun"), add it as a one-line rule to "Kurallar".
- `HARITA.md`: important functions and how they connect (format in its top comment). If it disagrees with the code, trust the code and fix the map.
- `raporlar/`: research and reports.

## Always

- **Bugs:** a bug I report isn't a new topic: fix it now. Fix small, safe bugs (yours or ones you find) without asking, then tell me in one line; ask first only if the fix is risky, irreversible or changes how the product works.
- **Decisions:** "Kararlar" (`ILERLEME.md` or `ILERLEME_ARSIV.md`) is settled: don't re-research or reverse it without a concrete new reason. For a product choice, give me 2–3 one-line options and say which you'd pick. "Kararlar" gets only what I approved and your technical choices (what, why, docs link).
- **Tests:** never change or delete a test just to make it pass; if the feature really changed, tell me first. If something breaks and you can't fix it, tell me plainly what broke.
- **Hooks:** never bypass them (`--no-verify`); if they block, fix what their message says.
- **Commits:** small, single-purpose steps; finish each one or revert it. Commit every working step without asking, then tell me in one plain line what was saved. With a GitHub remote, the post-commit hook pushes (standing permission); if the push failed, tell me. Ask before force-pushing, rewriting history, deleting branches or anything irreversible; revert a broken step only with my OK.
- **Branches:** work on the main branch. A risky experiment goes on `deney/<name>`, parallel jobs each on `is/<name>`; tell me, and merge or delete them only with my OK.

## When…

- **…a session starts:** `komutlar/oturum-basi.md`.
- **…something breaks** (an error, a failing test or check, or I say "çalışmıyor" / "yapamadım" / "açamadım"): `komutlar/hata.md`.
- **…you're about to change code:** `komutlar/kod-degisikligi.md`.
- **…you add or change tests, or set the test command:** `komutlar/testler.md`.
- **…you research something or write a report:** `komutlar/rapor.md`.
- **…a task is ready for me to try, or done:** `komutlar/teslim.md`.

## Workflow

The current stage is recorded in `ILERLEME.md`.
0. **Existing project** (code exists, forms blank): `komutlar/mevcut-proje.md`.
1. **Idea → Goal:** `komutlar/sorgula.md` (what it does, who uses it, what must work to call it done). Confirm with me, then write the goal.
2. **Plan:** if you lack technical knowledge for a good plan, first `komutlar/arastirma.md`. Then split the goal into tasks that each end with something I can try ("bitti sayılır: …"). Don't start without my approval.
3. **Build:** one task at a time. Before a big new feature: `komutlar/sorgula.md`, then `komutlar/arastirma.md`. Before a big task, tell me in 2–3 lines how you'll do it and how I'll try it, then go on. Stop and ask only for a new product decision, work clearly beyond the plan, or a risky, irreversible or shared-system step.
4. **Let me test** and **5. Close:** `komutlar/teslim.md`.

## Focus

- If I bring up something new outside the current task ("bir de şunu ekleyelim"), don't start it; ask whether to park it or switch to it. A bug report isn't new: fix it.
- Each "Sonra yapılacaklar" item stays one line. A longer idea becomes `<name> → ayrıntı: FIKIRLER.md › <name>`, with details under `## <name>` in `.waypoint/FIKIRLER.md` (create it if missing); remove that section when the item is done or dropped.

## Commands

Each also works in English (in brackets). A one-word short form (`sos`, `next`…) counts as a command only when it is my whole message.

- **`neredeyiz` / `kayboldum` / `özet` / `ne yapıyorduk` [`where are we` / `where`]:** stop and summarize the goal, the plan (done and current task), what's happening now, the next step, and questions waiting for my answer.
- **`sos` / `sadece soru` [`just a question` / `ask`]:** only answer; don't change files, run commands that change anything, or commit.
- **`nep` / `ne yaptık` [`what did we do` / `recap`]:** in 1–3 plain sentences, your last action and what it gives me.
- **`snv` / `sırada ne var` [`what's next` / `next`]:** only the next step, in one sentence.
- **`parket <fikir>` / `sonraya ekle <fikir>` [`park <idea>`]:** add it to "Sonra yapılacaklar" (see Focus), confirm in one line, continue.
- **`liste` [`list`]:** done tasks, then remaining tasks and "Sonra yapılacaklar", as short lists.
- **`nasıl açarım` [`how do I run it` / `run`]:** show the "Nasıl açılır" steps as they are.
- **`haritayı göster` [`show the map` / `map`]:** draw `HARITA.md` as a diagram in the chat, without creating a file; if you can't draw, explain it in plain words.
- **`sorgula` [`clarify`]:** `komutlar/sorgula.md` for the current idea or feature.
- **`bitir` / `bugünlük bu kadar` [`finish`]:** `komutlar/bitir.md`.
- **`Waypoint'i güncelle` [`update Waypoint`], or "Waypoint güncellemesi var" appears:** `komutlar/guncelleme.md`. Never update without my OK.
