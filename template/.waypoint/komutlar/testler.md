# Tests

I can't tell when a change breaks an old feature, so tests do it for me. Read this when you add or change tests or set the test command.

1. Test the important features I use directly, not small helpers.
2. Put the test command as one line in backticks under "Testleri çalıştırma" in `ILERLEME.md`. The pre-commit hook runs it before every commit, so it must finish on its own (no watch mode) and quickly (aim for under a minute).
3. If the full suite is slower, put a fast subset there and the full command on the next line as ``Tüm testler: `...` ``; run the full suite at the end of each task and in `bitir`.
