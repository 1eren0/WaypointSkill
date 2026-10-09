# Before changing code

Read this before a change that can affect behavior, an interface/API, data flow or a symbol's name (function, class, method, variable). Not needed for changes only to docs, user-visible text/labels or comments.

1. Use `HARITA.md` to find the relevant code instead of reading the whole project. It only tells you where to look: read the relevant code and every place that uses it (search the code, not only "used by").
2. When the commit check warns that a mapped function changed, fix its "uses" / "used by" lines in the same commit. Add important new functions to the map; small helpers don't need it.
3. With sub-agents (if your tool has them and the task is big): you plan, review and commit. Before handing off a step, write down what proves it's done and check it yourself; a sub-agent saying "done" isn't enough. A sub-agent that researched something writes a report and hands you its summary and path, not the whole text.
