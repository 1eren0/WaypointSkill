# Waypoint — developer notes

This repo IS the Waypoint product (not a project using it).

- `template/` = exactly what gets installed into a user's project. Its `.waypoint/*.md` files are blank forms: never fill them in here.
- `install.ps1` / `install.sh` = one-command installers. `tests/` = all tests: `python -m unittest discover -s tests -p "test_*.py"` (run before every commit). Lint: `ruff check .` (config in `ruff.toml`); CI (`.github/workflows/`) also runs ShellCheck on `install.sh` and the hooks.
- `README.md` is the product page (Turkish); `README.en.md` is its English translation. Keep both in sync.
- Keep `template/.waypoint/KURALLAR.md` small: it is loaded on every message. Only always-on rules and one-line command triggers go there; a longer or situational how-to goes in its own `template/.waypoint/komutlar/<name>.md`, referenced from KURALLAR by name.
- Versioning: for every user-facing change, bump `template/.waypoint/VERSION` (1.0 → 1.1; major only for breaking changes) and add an English entry to `CHANGELOG.md`. Installed projects compare their `.waypoint/VERSION` with the one on GitHub once a day.
- Talk to the user in plain Turkish, follow the "Language & communication", "Atomicity" and "Focus rules" sections of `template/.waypoint/KURALLAR.md`.
