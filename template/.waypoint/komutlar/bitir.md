# `bitir` / `bugünlük bu kadar`

Do these in order:

1. Finish or revert any half-done step.
2. Record unrecorded lessons in `DERSLER.md`.
3. Update `ILERLEME.md`. When the commit check asks, move old items to `ILERLEME_ARSIV.md`.
4. Ask me once: "Bugün Waypoint'te seni zorlayan bir şey oldu mu?"
5. Record the session in `.waypoint/WAYPOINT_GUNLUGU.md` (create it if missing) as `## YYYY-AA-GG` with four short lines:
   - `Komutlar:` the commands I used today.
   - `Kontroller:` which checks blocked a commit today (see `.waypoint/oto-kayit.log`, which the hooks fill automatically) and whether each caught a real problem or was noise.
   - `Takılma:` where you or I got stuck.
   - `Kullanıcı:` my answer to the question.
6. Commit.
7. Tell me in plain Turkish what we did today and which lessons were recorded, if any.

When `WAYPOINT_GUNLUGU.md` reaches 10 entries, offer a review: write `.waypoint/raporlar/YYYY-AA-GG-waypoint-degerlendirme.md` on what helped and what was useless, using that file and `oto-kayit.log`. Empty `WAYPOINT_GUNLUGU.md` only after my OK.
