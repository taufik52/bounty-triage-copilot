#!/usr/bin/env python3
"""Bounty Triage Copilot — local web app (Python standard library only).

Run:
    python3 app.py            # serves on http://127.0.0.1:8080
    python3 app.py --port 9000

Endpoints:
    GET  /                    web UI
    GET  /api/health          status + Ollama availability
    GET  /api/samples         example drafts
    POST /api/triage          instant rules-based scoring (JSON in/out)
    POST /api/triage/llm      optional local-LLM review (slow, async from UI)

No data leaves the machine: the rules engine is local and the LLM is
Ollama on localhost. Nothing is stored server-side.
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from llm import MODEL, OLLAMA_URL, llm_review, ollama_available
from samples import SAMPLES
from triage import score_draft

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json",
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    # -- helpers ------------------------------------------------------------
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str) -> None:
        ext = os.path.splitext(path)[1]
        with open(path, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    # -- routing ------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler naming
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send_file(os.path.join(STATIC_DIR, "index.html"))
            return
        if parsed.path == "/api/health":
            ok, detail = ollama_available()
            self._send_json({
                "status": "ok",
                "engine": "rules v1",
                "ollama_url": OLLAMA_URL,
                "ollama_model": MODEL,
                "ollama_available": ok,
                "ollama_detail": detail,
            })
            return
        if parsed.path == "/api/samples":
            self._send_json({"samples": SAMPLES})
            return
        if parsed.path.startswith("/static/"):
            name = os.path.basename(parsed.path)
            path = os.path.join(STATIC_DIR, name)
            if os.path.isfile(path) and os.path.dirname(path) == STATIC_DIR:
                self._send_file(path)
                return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler naming
        parsed = urlparse(self.path)
        if parsed.path == "/api/triage":
            data = self._read_json()
            title = str(data.get("title", "")).strip()
            program = str(data.get("program", "")).strip() or "Unspecified program"
            draft = str(data.get("draft", "")).strip()
            if not draft:
                self._send_json({"error": "draft is empty"}, status=400)
                return
            if len(draft) > 20000:
                self._send_json({"error": "draft too long (max 20000 chars)"}, status=400)
                return
            self._send_json(score_draft(title, program, draft))
            return
        if parsed.path == "/api/triage/llm":
            data = self._read_json()
            title = str(data.get("title", "")).strip()
            program = str(data.get("program", "")).strip() or "Unspecified program"
            draft = str(data.get("draft", "")).strip()
            if not draft:
                self._send_json({"error": "draft is empty"}, status=400)
                return
            review = llm_review(program, title, draft)
            if review is None:
                self._send_json({
                    "error": "LLM review unavailable (Ollama slow, down, "
                             "or returned unparseable output). "
                             "Rules-based score above still stands.",
                }, status=502)
                return
            self._send_json({"llm": review})
            return
        self._send_json({"error": "not found"}, status=404)

    def log_message(self, fmt: str, *args) -> None:  # quieter logging
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounty Triage Copilot")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Bounty Triage Copilot running at http://{args.host}:{args.port}")
    print(f"Ollama: {OLLAMA_URL} (model {MODEL})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
