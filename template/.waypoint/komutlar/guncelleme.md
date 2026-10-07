# Waypoint update

Read this when I type `Waypoint'i güncelle` or a commit prints "Waypoint güncellemesi var". `.waypoint/VERSION` is the installed version.

1. Read what changed: `gh api repos/erenuzman/WaypointSkill/contents/CHANGELOG.md -H "Accept: application/vnd.github.raw"`
2. Summarize the versions newer than mine for me in plain Turkish. If the commit message started this, ask whether to install and never update without my OK. If I typed `Waypoint'i güncelle`, that is my OK: go on.
3. On OK, never run the installer yourself (not even part by part): it runs code downloaded from the internet, safety checks rightly block that, and the choice is mine. Tell me to double-click `.waypoint/guncelle.bat` (macOS: `.waypoint/guncelle.command`) and to write "güncelledim" when it says it's done. If that file is missing (installed before 1.9), give me one line to paste into a terminal opened in the project folder: Windows PowerShell `gh api repos/erenuzman/WaypointSkill/contents/install.ps1 -H "Accept: application/vnd.github.raw" | Out-String | iex`, macOS/Linux `gh api repos/erenuzman/WaypointSkill/contents/install.sh -H "Accept: application/vnd.github.raw" | sh`. Then check that `.waypoint/VERSION` shows the new version.
4. Commit the result alone as `chore: update Waypoint to <version>`.
5. Tidy `.waypoint/` once: Waypoint's own entries are `KURALLAR.md`, `VERSION`, `ILERLEME*.md`, `DERS*.md`, `HARITA.md`, `FIKIRLER.md`, `WAYPOINT_GUNLUGU.md`, `oto-kayit.log`, `.son-surum`, `guncelle.bat`, `guncelle.command`, `.gitignore`, `.gitattributes`, `hooks/`, `komutlar/`, `raporlar/`. With `git mv`, move every other report into `raporlar/` as `YYYY-AA-GG-<konu>.md` (date of its last commit: `git log -1 --format=%as -- <file>`). Move anything that isn't a report (code, patches, themes…) to a fitting place in the project and tell me where. Commit this alone as `chore: move old reports into raporlar`.
6. If new checks then block commits, fix what they say before other work.
