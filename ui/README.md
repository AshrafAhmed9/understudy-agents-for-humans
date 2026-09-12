# ui/

`index.html` is the source for the four-screen dashboard (Watch, Receipts, Evidence, Inbox).
It's a static page: all data is the real `results.json` at the repo root, embedded inline
at build time. No model or Docker call happens from this page (CLAUDE.md rule 7).

Live copy: https://claude.ai/code/artifact/076c03d5-f79f-4e4a-8970-7ee4e46079e4

To rebuild after a new eval run:

```
python3 scripts/build_results.py          # regenerates results.json from runs/*.json
python3 - <<'PY'
html = open("ui/index.html").read()
# replace the JSON literal between the DATA = ... assignment and the following ;
# see scripts/build_results.py's output for the exact object to splice in
PY
```

(This splice is currently manual — the JSON was hand-injected once via a throwaway script.
If the UI needs to be rebuilt often, that step should become a real script rather than
repeating the manual splice.)
