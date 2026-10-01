# Waypoint — developer notes

This repo IS the Waypoint product (not a project using it).

- `template/` = exactly what gets installed into a user's project. Its `.waypoint/*.md` files are blank forms: never fill them in here.
- `install.ps1` / `install.sh` = one-command installers. `tests/` = all tests: `python -m unittest discover -s tests -p "test_*.py"` (run before every commit).
- `README.md` is the product page (Turkish).
- Talk to the user in plain Turkish, follow the "Language & communication", "Atomicity" and "Focus rules" sections of `template/.waypoint/KURALLAR.md`.
