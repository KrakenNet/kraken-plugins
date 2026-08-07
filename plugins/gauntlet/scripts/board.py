#!/usr/bin/env python3
"""Render the live Gauntlet Loop progress board from the ledger.

Rule 6 of the loop: watch it without interrupting it. This writes a
self-refreshing page you can open from a phone while the run continues.

  board.py render          write .gauntlet/board.html
  board.py serve --port N  serve .gauntlet/ over http (foreground)
"""
from __future__ import annotations

import argparse
import html
import json
import os
import time
from pathlib import Path


def root() -> Path:
    return Path(os.environ.get("GAUNTLET_ROOT", ".gauntlet")).resolve()


def load_rows() -> list[dict]:
    led = root() / "ledger.jsonl"
    if not led.is_file():
        return []
    return [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]


def collect(rows: list[dict]) -> dict:
    staged = {r["trial"]: r for r in rows if r.get("event") == "staged"}
    resolved = {r["trial"]: r for r in rows if r.get("event") == "resolved"}
    pieces: dict[str, dict] = {}
    for trial, s in staged.items():
        p = pieces.setdefault(s["piece"], {"rounds": 0, "wins": 0, "trials": []})
        res = resolved.get(trial)
        p["rounds"] = max(p["rounds"], s.get("round", 0))
        if res and res["outcome"] == "WIN":
            p["wins"] += 1
        p["trials"].append({
            "trial": trial,
            "round": s.get("round", 0),
            "outcome": res["outcome"] if res else "JUDGING",
            "gap": res["gap"] if res else "",
            "ts": s.get("ts", 0),
        })
    for p in pieces.values():
        p["trials"].sort(key=lambda t: t["round"])
    return pieces


CSS = """
:root{--bg:#0e1116;--fg:#e6edf3;--dim:#8b949e;--card:#161b22;--line:#30363d;
--win:#3fb950;--loss:#f85149;--tie:#d29922;--wait:#58a6ff}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--fg);
font:15px/1.55 ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif}
h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--dim);font-size:13px;margin-bottom:24px}
.piece{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:16px;margin-bottom:14px}
.ph{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.pn{font-weight:600}
.meta{color:var(--dim);font-size:12px}
.track{display:flex;gap:6px;margin:12px 0 0;flex-wrap:wrap}
.dot{width:26px;height:26px;border-radius:6px;display:grid;place-items:center;
font-size:11px;font-weight:700;color:#0e1116}
.WIN{background:var(--win)} .LOSS{background:var(--loss)}
.TIE{background:var(--tie)} .JUDGING{background:var(--wait)}
.gap{margin-top:10px;font-size:13px;color:var(--dim);border-left:2px solid var(--line);padding-left:10px}
.empty{color:var(--dim)}
.legend{margin-top:26px;font-size:12px;color:var(--dim)}
.legend span{display:inline-block;margin-right:14px}
.sw{display:inline-block;width:10px;height:10px;border-radius:3px;vertical-align:middle;margin-right:5px}
"""


def render_html(pieces: dict, charter: str, bar: str) -> str:
    total = sum(len(p["trials"]) for p in pieces.values())
    resolved = sum(1 for p in pieces.values() for t in p["trials"] if t["outcome"] != "JUDGING")
    wins = sum(1 for p in pieces.values() for t in p["trials"] if t["outcome"] == "WIN")

    body = []
    for name, p in sorted(pieces.items()):
        last_gap = ""
        for t in reversed(p["trials"]):
            if t["gap"]:
                last_gap = t["gap"]
                break
        dots = "".join(
            f'<div class="dot {t["outcome"]}" title="round {t["round"]} — {html.escape(t["outcome"])}">{t["round"]}</div>'
            for t in p["trials"]
        )
        body.append(f"""<div class="piece">
  <div class="ph"><div class="pn">{html.escape(name)}</div>
  <div class="meta">{len(p['trials'])} rounds · {p['wins']} beat the bar</div></div>
  <div class="track">{dots}</div>
  {f'<div class="gap"><b>Open gap:</b> {html.escape(last_gap)}</div>' if last_gap else ''}
</div>""")

    if not body:
        body.append('<p class="empty">No trials staged yet.</p>')

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="15">
<title>Gauntlet Loop</title><style>{CSS}</style></head><body>
<h1>Gauntlet Loop</h1>
<div class="sub">{len(pieces)} pieces · {total} trials · {resolved} judged · {wins} beat the bar
&nbsp;·&nbsp; updated {time.strftime('%H:%M:%S')} · refreshes every 15s</div>
<div class="piece"><div class="pn">Goal</div><div class="gap">{html.escape(charter[:1200]) or 'no charter'}</div></div>
<div class="piece"><div class="pn">The bar</div><div class="gap">{html.escape(bar[:1200]) or 'no bar set'}</div></div>
{''.join(body)}
<div class="legend">
<span><i class="sw WIN"></i>ours won</span>
<span><i class="sw LOSS"></i>bar won — gap open</span>
<span><i class="sw TIE"></i>indistinguishable</span>
<span><i class="sw JUDGING"></i>critic judging</span>
</div>
</body></html>"""


def read_if(p: Path) -> str:
    return p.read_text(encoding="utf-8").strip() if p.is_file() else ""


def cmd_render(_):
    r = root()
    r.mkdir(parents=True, exist_ok=True)
    out = r / "board.html"
    out.write_text(
        render_html(collect(load_rows()), read_if(r / "charter.md"), read_if(r / "bar.md")),
        encoding="utf-8",
    )
    print(out)


def cmd_serve(args):
    """Serve the board, and only the board.

    The naive version of this — SimpleHTTPRequestHandler rooted at .gauntlet/ —
    would publish keys/*.json over HTTP, handing out the sealed A/B mapping that
    the PreToolUse hook exists to protect. So: deny keys/ outright, and bind to
    localhost unless the operator explicitly asks for the network.
    """
    import functools
    import http.server
    import socketserver
    from urllib.parse import unquote, urlparse

    DENIED = ("keys",)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def _denied(self) -> bool:
            path = unquote(urlparse(self.path).path).lstrip("/")
            head = path.split("/", 1)[0]
            return head in DENIED

        def do_GET(self):
            if self._denied():
                self.send_error(403, "sealed: A/B mappings are not served")
                return
            super().do_GET()

        def do_HEAD(self):
            if self._denied():
                self.send_error(403, "sealed: A/B mappings are not served")
                return
            super().do_HEAD()

    cmd_render(args)
    handler = functools.partial(Handler, directory=str(root()))
    with socketserver.TCPServer((args.host, args.port), handler) as httpd:
        shown = "localhost" if args.host in ("127.0.0.1", "localhost") else args.host
        print(f"http://{shown}:{args.port}/board.html")
        if args.host == "0.0.0.0":
            print("bound to all interfaces — anyone on this network can read the board")
        httpd.serve_forever()


def main():
    ap = argparse.ArgumentParser(prog="board.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("render").set_defaults(func=cmd_render)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8787)
    s.add_argument("--host", default="127.0.0.1",
                   help="pass 0.0.0.0 to reach the board from your phone on the same network")
    s.set_defaults(func=cmd_serve)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
