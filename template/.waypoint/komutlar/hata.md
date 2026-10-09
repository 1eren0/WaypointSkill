# When something breaks

Read this when there's an error, a failing test or check, or I say "çalışmıyor" / "yapamadım" / "açamadım". Fix it now (see "Always" in `KURALLAR.md`).

1. If I reported it, ask me only what you can't see yourself (what I did, what I saw).
2. Reproduce the error and read the local evidence: the full message, logs, versions.
3. If the cause isn't clear or involves a library, framework, API, tool or OS version, check `raporlar/` first (`rapor.md`), then search the exact error with those versions (official docs, changelogs, issues first) if you can browse. Apply an outside fix only if it matches what you see here. Try risky fixes on a `deney/<name>` branch.
4. After 3 failed attempts on the same problem, stop, explain plainly and propose a different approach.
5. Record a lesson in `DERSLER.md`, in the same commit as the fix, whenever: I said "çalışmıyor" / "yapamadım" / "açamadım" (however small); it took more than 2 attempts; I couldn't follow a step you gave me; or you changed approach because of my feedback. Tell me in one line.
6. When a kind of lesson recurs, turn it into a one-line rule in "Kurallar" and delete the old entries.
