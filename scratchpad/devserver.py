"""No-cache static server for local development.

`python -m http.server` sends Last-Modified and no Cache-Control, so the browser
(and then the service worker, which caches whatever it was handed at install
time) happily serves a stale js/app.js for the rest of the session - edits look
like they did nothing. See CLAUDE.md, "Cache gotcha". This sends no-store on
everything instead.

    python scratchpad/devserver.py [port]      # default 8081

The service worker still installs; if you have an old one registered from the
plain server, unregister it once in DevTools (Application > Service workers).
"""
import sys
from http.server import SimpleHTTPRequestHandler, test


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()


if __name__ == "__main__":
    test(HandlerClass=NoCacheHandler, port=int(sys.argv[1]) if len(sys.argv) > 1 else 8081)
