# Before changing code

Read this before a change that can affect behavior, an interface/API, data flow or a symbol's name (function, class, method, variable). Not needed for changes only to docs, user-visible text/labels or comments.

1. Use `HARITA.md` to find the relevant code instead of reading the whole project. It only tells you where to look: read the relevant code and every place that uses it (search the code, not only "used by").
2. When the commit check warns that a mapped function changed, fix its "uses" / "used by" lines in the same commit. Add important new functions to the map; small helpers don't need it.
3. Error handling: never swallow an error (an empty `except` / `catch`, or returning a safe-looking value that hides a failure). When something fails, show me a short plain message: what happened and what I can do ("İnternete bağlanılamadı. Bağlantını kontrol edip tekrar dene."), with no codes or blame. Write the details (time, the full error, which step) to one fixed log file, e.g. `logs/hata.log`, without passwords or keys. When you create it, add its path to the project's `.gitignore` right away (it can hold user data; the commit check refuses `.log` files) and name it under "Nasıl açılır" in `ILERLEME.md`.
4. A fallback (quietly doing something else when the normal way fails) is a product decision: add one only with my OK, mark it with a comment, and log every time it's used.
5. With sub-agents (if your tool has them and the task is big): you plan, review and commit. Before handing off a step, write down what proves it's done and check it yourself; a sub-agent saying "done" isn't enough.
