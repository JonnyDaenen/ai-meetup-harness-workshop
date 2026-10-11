# /// script
# requires-python = ">=3.12"
# dependencies = ["qrcode>=8.0"]
# ///
"""Create, list, disable and delete the workshop's OpenRouter keys.

Needs an OpenRouter *management* key in OPENROUTER_MANAGEMENT_KEY (shell or the repo's .env).
Only keys whose name starts with --prefix are ever touched.

    uv run tools/openrouter_keys.py create 80 --workspace-id <uuid>   # keys + printable cards
    uv run tools/openrouter_keys.py list                              # usage per key and in total
    uv run tools/openrouter_keys.py disable                           # stop all keys (reversible)
    uv run tools/openrouter_keys.py delete                            # remove all keys for good
"""

import argparse
import csv
import html
import io
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://openrouter.ai/api/v1"
ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"


# --- config ---

def management_key() -> str:
    key = os.getenv("OPENROUTER_MANAGEMENT_KEY")
    env_file = ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "OPENROUTER_MANAGEMENT_KEY" and value.strip():
                key = value.strip()
    if not key:
        sys.exit("OPENROUTER_MANAGEMENT_KEY is not set (shell or .env). Create one under Management Keys.")
    return key


def call(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {management_key()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} failed: HTTP {e.code} {e.read().decode()[:300]}")


def workshop_keys(prefix: str) -> list[dict]:
    """All keys whose name starts with prefix (the API pages by 100)."""
    keys, offset = [], 0
    while True:
        page = call("GET", f"/keys?offset={offset}")["data"]
        keys += [k for k in page if (k.get("name") or "").startswith(prefix)]
        if len(page) < 100:
            return keys
        offset += 100


def confirm(question: str, yes: bool) -> None:
    if yes:
        return
    if input(f"{question} [y/N] ").strip().lower() != "y":
        sys.exit("Cancelled.")


# --- commands ---

def create(args):
    expires = datetime.fromisoformat(args.expires).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    existing = {k["name"] for k in workshop_keys(args.prefix)}
    names = [f"{args.prefix}{i:03d}" for i in range(args.start, args.start + args.count)]
    if clash := [n for n in names if n in existing]:
        sys.exit(f"Keys already exist: {', '.join(clash[:5])}... Use --start to continue numbering.")
    confirm(f"Create {len(names)} keys ({names[0]}..{names[-1]}), ${args.limit} each, expiring {expires}?", args.yes)

    OUT.mkdir(exist_ok=True)
    csv_path = OUT / f"{args.prefix.rstrip('-')}-keys.csv"
    new_file = not csv_path.exists()
    created = []
    with csv_path.open("a", newline="") as f:  # append + flush per key: a crash never loses a shown-once key
        w = csv.writer(f)
        if new_file:
            w.writerow(["name", "key", "limit", "expires_at"])
        for name in names:
            body = {"name": name, "limit": args.limit, "expires_at": expires}
            if args.workspace_id:
                body["workspace_id"] = args.workspace_id
            res = call("POST", "/keys", body)
            w.writerow([name, res["key"], args.limit, expires])
            f.flush()
            created.append((name, res["key"]))
            print(f"created {name}")

    cards = write_cards(created, args)
    print(f"\n{len(created)} keys saved to {csv_path.relative_to(ROOT)}")
    print(f"Printable cards: {cards.relative_to(ROOT)} (open in a browser, print)")
    print("Both files hold live keys: they're in .gitignore, don't share them.")


def list_keys(args):
    keys = workshop_keys(args.prefix)
    if not keys:
        print(f"No keys starting with {args.prefix!r}.")
        return
    used = [k for k in keys if (k.get("usage") or 0) > 0]
    for k in sorted(keys, key=lambda k: k["name"]):
        state = "disabled" if k.get("disabled") else "active"
        print(f"{k['name']:14s} {state:9s} used ${k.get('usage') or 0:.4f} of ${k.get('limit') or 0:.2f}")
    total = sum(k.get("usage") or 0 for k in keys)
    print(f"\n{len(keys)} keys, {len(used)} used, ${total:.4f} spent in total")


def disable(args):
    keys = [k for k in workshop_keys(args.prefix) if not k.get("disabled")]
    if not keys:
        print("Nothing to disable.")
        return
    confirm(f"Disable {len(keys)} keys starting with {args.prefix!r}?", args.yes)
    for k in keys:
        call("PATCH", f"/keys/{k['hash']}", {"disabled": True})
        print(f"disabled {k['name']}")


def delete(args):
    keys = workshop_keys(args.prefix)
    if not keys:
        print("Nothing to delete.")
        return
    confirm(f"Permanently delete {len(keys)} keys starting with {args.prefix!r}?", args.yes)
    for k in keys:
        call("DELETE", f"/keys/{k['hash']}")
        print(f"deleted {k['name']}")


# --- printable cards ---

def qr_svg(text: str) -> str:
    import qrcode
    import qrcode.image.svg

    buf = io.BytesIO()
    qrcode.make(text, image_factory=qrcode.image.svg.SvgPathImage, box_size=6, border=1).save(buf)
    svg = buf.getvalue().decode()
    return svg[svg.index("<svg"):]


def write_cards(created: list[tuple[str, str]], args) -> Path:
    cards = "\n".join(
        f"""<div class="card">
  <div class="top"><b>AI Meetup · workshop key</b><span>{html.escape(name)}</span></div>
  <div class="body">
    <div class="qr">{qr_svg(key)}</div>
    <div>
      <p>Scan the code to copy the key, then add to <code>.env</code>:</p>
      <pre>ANTHROPIC_BASE_URL=http://127.0.0.1:8080/api
ANTHROPIC_API_KEY=&lt;this key&gt;
MODEL_ID=qwen/qwen3.5-9b</pre>
      <p class="small">Proxy: <code>--mode reverse:https://openrouter.ai</code> · limit ${args.limit:g} · stops working after the meetup</p>
    </div>
  </div>
  <code class="key">{html.escape(key)}</code>
</div>"""
        for name, key in created
    )
    page = f"""<!doctype html><meta charset="utf-8"><title>Workshop keys</title>
<style>
  body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; color: #1C1F4A; margin: 0; }}
  .sheet {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; padding: 8mm; }}
  .card {{ border: 1px dashed #8D86B8; border-radius: 3mm; padding: 4mm; break-inside: avoid; font-size: 9pt; }}
  .top {{ display: flex; justify-content: space-between; margin-bottom: 2mm; }}
  .body {{ display: flex; gap: 3mm; align-items: flex-start; }}
  .qr svg {{ width: 28mm; height: 28mm; }}
  pre {{ background: #F1EEFC; padding: 2mm; margin: 1mm 0; font-size: 7.5pt; }}
  p {{ margin: 0 0 1mm; }} .small {{ font-size: 7.5pt; color: #3D4170; }}
  .key {{ display: block; margin-top: 2mm; font-size: 7pt; word-break: break-all; }}
</style>
<div class="sheet">
{cards}
</div>
"""
    path = OUT / f"{args.prefix.rstrip('-')}-cards.html"
    path.write_text(page)
    return path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prefix", default="meetup-", help="only keys whose name starts with this (default: meetup-)")
    p.add_argument("-y", "--yes", action="store_true", help="don't ask for confirmation")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create", help="create COUNT keys and printable cards")
    c.add_argument("count", type=int)
    c.add_argument("--limit", type=float, default=1.0, help="spending limit per key in USD (default: 1)")
    c.add_argument("--expires", default="2026-10-14T23:59:59+02:00", help="ISO date-time the keys stop working")
    c.add_argument("--workspace-id", help="workspace UUID (default: your default workspace)")
    c.add_argument("--start", type=int, default=1, help="first number, to add more keys later (default: 1)")
    c.set_defaults(fn=create)
    sub.add_parser("list", help="usage per key and in total").set_defaults(fn=list_keys)
    sub.add_parser("disable", help="disable all keys (reversible in the dashboard)").set_defaults(fn=disable)
    sub.add_parser("delete", help="delete all keys for good").set_defaults(fn=delete)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
