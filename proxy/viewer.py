"""Live viewer for model calls: a small web page that shows every /v1/messages
call as readable blocks (system, tools, messages, response, usage).

Load it BEFORE sse_clean.py, so it sees the original stream:

    uv run mitmweb ... -s viewer.py -s sse_clean.py

Then open http://127.0.0.1:8082 (change with --set viewer_port=...).
"""

import json
import queue
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mitmproxy import ctx, http

PAGE = Path(__file__).with_name("viewer.html")
MAX_CALLS = 300
MAX_TEXT = 500_000  # fallback text shown for bodies that aren't JSON
# Never keep x-api-key / authorization: the page must be safe to project.
SAFE_HEADERS = {"anthropic-version", "anthropic-beta", "user-agent", "content-type"}


def _parse_sse(text: str):
    """Rebuild a Messages API response from its Server-Sent Events."""
    message = None
    partial = {}
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        try:
            event = json.loads(line[5:].strip())
        except ValueError:
            continue
        kind = event.get("type")
        if kind == "message_start":
            message = event.get("message", {})
            message.setdefault("content", [])
        elif message is None:
            continue
        elif kind == "content_block_start":
            message["content"].append(dict(event.get("content_block", {})))
        elif kind == "content_block_delta":
            index, delta = event.get("index", len(message["content"]) - 1), event.get("delta", {})
            if not 0 <= index < len(message["content"]):
                continue
            block = message["content"][index]
            if delta.get("type") == "text_delta":
                block["text"] = block.get("text", "") + delta.get("text", "")
            elif delta.get("type") == "thinking_delta":
                block["thinking"] = block.get("thinking", "") + delta.get("thinking", "")
            elif delta.get("type") == "input_json_delta":
                partial[index] = partial.get(index, "") + delta.get("partial_json", "")
        elif kind == "content_block_stop":
            index = event.get("index")
            if index in partial and 0 <= index < len(message["content"]):
                try:
                    message["content"][index]["input"] = json.loads(partial.pop(index) or "{}")
                except ValueError:
                    message["content"][index]["input"] = {"_unparsed": partial.get(index)}
        elif kind == "message_delta":
            message.update({k: v for k, v in event.get("delta", {}).items() if v is not None})
            message["usage"] = {**message.get("usage", {}), **event.get("usage", {})}
    return message


def _body(message: http.Message):
    """(parsed JSON, None) or (None, text) for anything that isn't JSON."""
    text = message.get_text(strict=False) or ""
    if not text:
        return None, None
    try:
        return json.loads(text), None
    except ValueError:
        return None, text[:MAX_TEXT]


class Viewer:
    def __init__(self):
        self.calls = deque(maxlen=MAX_CALLS)
        self.by_id = {}
        self.subscribers = []
        self.lock = threading.Lock()
        self.server = None

    def load(self, loader):
        loader.add_option("viewer_port", int, 8082, "Port for the live call viewer.")

    def running(self):
        viewer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, code, body, content_type):
                self.send_response(code)
                self.send_header("content-type", content_type)
                self.send_header("cache-control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/":
                    self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
                elif self.path == "/api/calls":
                    with viewer.lock:
                        data = json.dumps(list(viewer.calls))
                    self._send(200, data.encode(), "application/json")
                elif self.path == "/events":
                    self.send_response(200)
                    self.send_header("content-type", "text/event-stream")
                    self.send_header("cache-control", "no-store")
                    self.end_headers()
                    q = queue.Queue()
                    with viewer.lock:
                        viewer.subscribers.append(q)
                    try:
                        while True:
                            try:
                                payload = q.get(timeout=15)
                            except queue.Empty:
                                payload = ": keep-alive"  # comment line, ignored by the browser
                            self.wfile.write(f"{payload}\n\n".encode())
                            self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    finally:
                        with viewer.lock:
                            viewer.subscribers.remove(q)
                else:
                    self._send(404, b"not found", "text/plain")

            def do_POST(self):
                if self.path == "/api/clear":
                    with viewer.lock:
                        viewer.calls.clear()
                        viewer.by_id.clear()
                    viewer._publish("clear", {})
                    self._send(200, b"{}", "application/json")
                else:
                    self._send(404, b"not found", "text/plain")

        port = ctx.options.viewer_port
        self.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        ctx.log.info(f"Call viewer on http://127.0.0.1:{port}")

    def done(self):
        if self.server:
            self.server.shutdown()

    def _publish(self, event, data):
        line = f"event: {event}\ndata: {json.dumps(data)}"
        with self.lock:
            for q in self.subscribers:
                q.put(line)

    def _upsert(self, call):
        with self.lock:
            if call["id"] not in self.by_id:
                if len(self.calls) == self.calls.maxlen:
                    self.by_id.pop(self.calls[0]["id"], None)
                self.calls.append(call)
                self.by_id[call["id"]] = call
        self._publish("call", call)

    # --- mitmproxy hooks ---

    def requestheaders(self, flow: http.HTTPFlow):
        if "/v1/" not in flow.request.path:
            return
        self._upsert({
            "id": flow.id,
            "started": time.time(),
            "method": flow.request.method,
            "path": flow.request.path,
            "host": flow.request.pretty_host,
            "headers": {k: v for k, v in flow.request.headers.items() if k.lower() in SAFE_HEADERS},
            "state": "pending",
        })

    def request(self, flow: http.HTTPFlow):
        self._fill_request(flow)

    def _fill_request(self, flow):
        call = self.by_id.get(flow.id)
        if call is None or "request" in call or "request_text" in call:
            return
        parsed, text = _body(flow.request)
        if parsed is not None:
            call["request"] = parsed
        elif text is not None:
            call["request_text"] = text
        else:
            return
        self._upsert(call)

    def response(self, flow: http.HTTPFlow):
        call = self.by_id.get(flow.id)
        if call is None:
            return
        self._fill_request(flow)  # with streamed bodies, the request may only be complete now
        call["status"] = flow.response.status_code
        call["duration"] = round(time.time() - call["started"], 3)
        content_type = flow.response.headers.get("content-type", "")
        text = flow.response.get_text(strict=False) or ""
        if "text/event-stream" in content_type:
            call["streamed"] = True
            message = _parse_sse(text)
            if message is not None:
                call["response"] = message
            else:
                call["response_text"] = text[:MAX_TEXT]
        else:
            parsed, raw = _body(flow.response)
            if parsed is not None:
                call["response"] = parsed
            elif raw is not None:
                call["response_text"] = raw
        call["state"] = "done"
        self._upsert(call)

    def error(self, flow: http.HTTPFlow):
        call = self.by_id.get(flow.id)
        if call is None:
            return
        call["state"] = "error"
        call["error"] = str(flow.error)
        self._upsert(call)


addons = [Viewer()]
