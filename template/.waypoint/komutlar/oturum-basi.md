# Session start

Do this at the start of every session, before anything else.

1. Read `ILERLEME.md` and "Kurallar" in `DERSLER.md`.
2. Glance at git: uncommitted changes, the last few commits, open `deney/` / `is/` branches. If they don't match `ILERLEME.md` (a session cut off midway, work done in another tool), tell me in one line.
3. No git repo yet: run `git init`, then `git config core.hooksPath .waypoint/hooks`, and tell me. Keep `.obsidian/` in `.gitignore`.
4. Blank `ILERLEME.md`: stage 0 if the folder has code (`mevcut-proje.md`), otherwise stage 1 (`sorgula.md`).
5. Briefly tell me what we did last, where we are, and the next step.
6. If `.waypoint/.son-surum` names a newer version than `.waypoint/VERSION`, add one line saying so and ask whether to update (`guncelleme.md`).
