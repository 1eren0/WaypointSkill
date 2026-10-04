# Waypoint update

Read this when I type `Waypoint'i güncelle` or a commit prints "Waypoint güncellemesi var". `.waypoint/VERSION` is the installed version.

1. Read what changed: `gh api repos/erenuzman/WaypointSkill/contents/CHANGELOG.md -H "Accept: application/vnd.github.raw"`
2. Summarize the versions newer than mine for me in plain Turkish. If the commit message started this, ask whether to install and never update without my OK. If I typed `Waypoint'i güncelle`, that is my OK: go on.
3. On OK, run the installer:
   - Windows: `gh api repos/erenuzman/WaypointSkill/contents/install.ps1 -H "Accept: application/vnd.github.raw" | Out-String | iex`
   - macOS/Linux: `gh api repos/erenuzman/WaypointSkill/contents/install.sh -H "Accept: application/vnd.github.raw" | sh`
4. Commit the result alone as `chore: update Waypoint to <version>`.
5. If new checks then block commits, fix what they say before other work.
