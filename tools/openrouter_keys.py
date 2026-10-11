# /// script
# requires-python = ">=3.12"
# dependencies = ["qrcode>=8.0"]
# ///
"""Create, list, disable and delete the workshop's OpenRouter keys.

Needs an OpenRouter *management* key in OPENROUTER_MANAGEMENT_KEY (shell or the repo's .env).
Only keys whose name starts with --prefix are ever touched.

    uv run tools/openrouter_keys.py guard                             # workspace: only the workshop models
    uv run tools/openrouter_keys.py create 80                         # keys + printable cards
    uv run tools/openrouter_keys.py cards --logo sponsors.png        # rebuild the cards, no new keys
    uv run tools/openrouter_keys.py list                              # usage per key and in total
    uv run tools/openrouter_keys.py disable                           # stop all keys (reversible)
    uv run tools/openrouter_keys.py delete                            # remove all keys for good
"""

import argparse
import base64
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
WORKSPACE = "2026-10-13-agentic-ai-meetup-002"  # slug or id; the keys and their guardrail live here
MODELS = ["qwen/qwen3.5-9b", "anthropic/claude-haiku-5.5"]
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


def workspace(ref: str) -> dict:
    for ws in call("GET", "/workspaces")["data"]:
        if ref in (ws["id"], ws["slug"]):
            return ws
    sys.exit(f"No workspace {ref!r}. Create it in the dashboard, or pass --workspace.")


def workshop_keys(prefix: str, workspace_id: str) -> list[dict]:
    """The workspace's keys whose name starts with prefix (the API pages by 100)."""
    keys, offset = [], 0
    while True:
        page = call("GET", f"/keys?workspace_id={workspace_id}&include_disabled=true&include_expired=true&offset={offset}")["data"]
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

def guard(args):
    """Restrict the workspace's default guardrail (it covers every key in the workspace) to MODELS."""
    ws = workspace(args.workspace)
    confirm(f"Allow only {', '.join(args.models)} in workspace {ws['name']!r}?", args.yes)
    call("PATCH", f"/guardrails/{ws['default_guardrail_id']}", {"allowed_models": args.models})
    g = call("GET", f"/guardrails/{ws['default_guardrail_id']}")["data"]
    print(f"Guardrail {g.get('name')!r}: allowed_models = {g.get('allowed_models')}")


def create(args):
    expires = datetime.fromisoformat(args.expires).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ws = workspace(args.workspace)
    existing = {k["name"] for k in workshop_keys(args.prefix, ws["id"])}
    names = [f"{args.prefix}{i:03d}" for i in range(args.start, args.start + args.count)]
    if clash := [n for n in names if n in existing]:
        sys.exit(f"Keys already exist: {', '.join(clash[:5])}... Use --start to continue numbering.")
    confirm(f"Create {len(names)} keys ({names[0]}..{names[-1]}) in {ws['name']!r}, ${args.limit} each, expiring {expires}?", args.yes)

    OUT.mkdir(exist_ok=True)
    csv_path = OUT / f"{args.prefix.rstrip('-')}-keys.csv"
    new_file = not csv_path.exists()
    created = []
    with csv_path.open("a", newline="") as f:  # append + flush per key: a crash never loses a shown-once key
        w = csv.writer(f)
        if new_file:
            w.writerow(["name", "key", "limit", "expires_at"])
        for name in names:
            res = call("POST", "/keys", {"name": name, "limit": args.limit, "expires_at": expires, "workspace_id": ws["id"]})
            w.writerow([name, res["key"], args.limit, expires])
            f.flush()
            created.append((name, res["key"], str(args.limit)))
            print(f"created {name}")

    cards = write_cards(created, args)
    print(f"\n{len(created)} keys saved to {csv_path.relative_to(ROOT)}")
    print(f"Printable cards: {cards.relative_to(ROOT)} (open in a browser, print)")
    print("Both files hold live keys: they're in .gitignore, don't share them.")


def list_keys(args):
    keys = workshop_keys(args.prefix, workspace(args.workspace)["id"])
    if not keys:
        print(f"No keys starting with {args.prefix!r}.")
        return
    used = [k for k in keys if (k.get("usage") or 0) > 0]
    for k in sorted(keys, key=lambda k: k["name"]):
        state = "disabled" if k.get("disabled") else "active"
        print(f"{k['name']:14s} {state:9s} used ${k.get('usage') or 0:.6f} of ${k.get('limit') or 0:.2f}")
    total = sum(k.get("usage") or 0 for k in keys)
    print(f"\n{len(keys)} keys, {len(used)} used, ${total:.6f} spent in total")


def disable(args):
    keys = [k for k in workshop_keys(args.prefix, workspace(args.workspace)["id"]) if not k.get("disabled")]
    if not keys:
        print("Nothing to disable.")
        return
    confirm(f"Disable {len(keys)} keys starting with {args.prefix!r}?", args.yes)
    for k in keys:
        call("PATCH", f"/keys/{k['hash']}", {"disabled": True})
        print(f"disabled {k['name']}")


def delete(args):
    keys = workshop_keys(args.prefix, workspace(args.workspace)["id"])
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


def logo_tag(path: str | None) -> str:
    if not path:
        return ""
    data = Path(path).read_bytes()
    mime = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[Path(path).suffix.lower()]
    return f'<img class="logo" alt="" src="data:{mime};base64,{base64.b64encode(data).decode()}">'


def write_cards(created: list[tuple[str, str, str]], args) -> Path:
    """One A4 page per 10 cards (2 x 5), each card 52 x 92 mm, ready to cut."""
    logo = logo_tag(getattr(args, "logo", None))
    cards = [
        f"""<div class="card">
  <div class="top"><b>{html.escape(args.title)}</b><span>{html.escape(name)}</span></div>
  <div class="body">
    <div class="qr">{qr_svg(key)}</div>
    <div>
      <p>Scan the code to copy the key, then add to <code>.env</code>:</p>
      <pre>ANTHROPIC_BASE_URL=http://127.0.0.1:8080/api
ANTHROPIC_API_KEY=&lt;this key&gt;
MODEL_ID=qwen/qwen3.5-9b</pre>
      <p class="small">Proxy: <code>--mode reverse:https://openrouter.ai</code> · limit ${float(limit):g} · stops working after the meetup</p>
    </div>
  </div>
  <code class="key">{html.escape(key)}</code>
  {logo}
</div>"""
        for name, key, limit in created
    ]
    pages = "\n".join(f'<div class="page">{"".join(cards[i:i + 10])}</div>' for i in range(0, len(cards), 10))
    page = f"""<!doctype html><meta charset="utf-8"><title>Workshop keys</title>
<style>
  @page {{ size: A4; margin: 10mm; }}
  body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; color: #1C1F4A; margin: 0; }}
  .page {{ display: grid; grid-template-columns: 92mm 92mm; grid-auto-rows: 52mm; gap: 2mm 6mm; break-after: page; }}
  .page:last-child {{ break-after: auto; }}
  .card {{ position: relative; border: 1px dashed #8D86B8; border-radius: 3mm; padding: 3.5mm; font-size: 8.5pt; overflow: hidden; }}
  .top {{ display: flex; justify-content: space-between; margin-bottom: 2mm; }}
  .body {{ display: flex; gap: 3mm; align-items: flex-start; }}
  .body > div:last-child {{ flex: 1; min-width: 0; }}
  .qr svg {{ width: 24mm; height: 24mm; }}
  pre {{ background: #F1EEFC; padding: 1.2mm; margin: 1mm 0; font-size: 5.7pt; overflow: hidden; }}
  p {{ margin: 0 0 1mm; }} .small {{ font-size: 6.8pt; color: #3D4170; }}
  .key {{ position: absolute; left: 3.5mm; bottom: 3mm; right: 46mm; font-size: 6.5pt; word-break: break-all; }}
  .logo {{ position: absolute; right: 3.5mm; bottom: 3mm; max-width: 41mm; max-height: 9mm; }}
  @media print {{ * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
</style>
{pages}
"""
    path = OUT / f"{args.prefix.rstrip('-')}-cards.html"
    path.write_text(page)
    return path


def cards(args):
    """Rebuild the card sheet from the saved CSV (no API calls), e.g. with a logo."""
    csv_path = OUT / f"{args.prefix.rstrip('-')}-keys.csv"
    if not csv_path.exists():
        sys.exit(f"No {csv_path.relative_to(ROOT)}: run create first.")
    rows = [(r["name"], r["key"], r["limit"]) for r in csv.DictReader(csv_path.open())]
    print(f"{len(rows)} cards: {write_cards(rows, args).relative_to(ROOT)}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prefix", default="meetup-", help="only keys whose name starts with this (default: meetup-)")
    p.add_argument("--workspace", default=WORKSPACE, help=f"workspace slug or id (default: {WORKSPACE})")
    p.add_argument("-y", "--yes", action="store_true", help="don't ask for confirmation")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("guard", help="allow only the workshop models in the workspace")
    g.add_argument("--models", nargs="+", default=MODELS)
    g.set_defaults(fn=guard)
    c = sub.add_parser("create", help="create COUNT keys and printable cards")
    c.add_argument("count", type=int)
    c.add_argument("--limit", type=float, default=1.0, help="spending limit per key in USD (default: 1)")
    c.add_argument("--expires", default="2026-10-14T23:59:59+02:00", help="ISO date-time the keys stop working")
    c.add_argument("--start", type=int, default=1, help="first number, to add more keys later (default: 1)")
    c.set_defaults(fn=create)
    for sp in (c, k := sub.add_parser("cards", help="rebuild the printable cards from the saved CSV")):
        sp.add_argument("--logo", help="png/svg/jpg shown on every card, e.g. the sponsors")
        sp.add_argument("--title", default="AI Meetup · workshop key", help="card heading")
    k.set_defaults(fn=cards)
    sub.add_parser("list", help="usage per key and in total").set_defaults(fn=list_keys)
    sub.add_parser("disable", help="disable all keys (reversible in the dashboard)").set_defaults(fn=disable)
    sub.add_parser("delete", help="delete all keys for good").set_defaults(fn=delete)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
