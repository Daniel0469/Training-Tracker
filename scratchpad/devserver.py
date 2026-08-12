"""No-cache static server for local development.

`python -m http.server` sends Last-Modified and no Cache-Control, so the browser
(and then the service worker, which caches whatever it was handed at install
time) happily serves a stale js/app.js for the rest of the session - edits look
like they did nothing. See CLAUDE.md, "Cache gotcha". This sends no-store on
everything instead.

    python scratchpad/devserver.py [port]      # default 8081

The service worker still installs; if you have an old one registered from the
plain server, unregister it once in DevTools (Application > Service workers).

HTTP/1.1 + threading is deliberate: on HTTP/1.0 the handler signals end-of-body
by closing the socket, and js/app.js (~195KB, by far the biggest file here) was
arriving truncated every few loads - the browser then reports ERR_CONNECTION_RESET
and every global in app.js is silently missing, which looks exactly like the app
being broken. HTTP/1.1 frames the body with Content-Length instead, and threading
stops one slow request stalling the rest of the page.
"""
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    print(f"serving http://localhost:{port} (no-store, HTTP/1.1)")
    ThreadingHTTPServer(("", port), NoCacheHandler).serve_forever()
