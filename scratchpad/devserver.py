"""No-cache static server for local development.

`python -m http.server` sends Last-Modified and no Cache-Control, so the browser
(and then the service worker, which caches whatever it was handed at install
time) happily serves a stale js/app.js for the rest of the session - edits look
like they did nothing. See CLAUDE.md, "Cache gotcha". This sends no-store on
everything instead.

    python scratchpad/devserver.py [port]      # default 8081

The service worker still installs; if you have an old one registered from the
plain server, unregister it once in DevTools (Application > Service workers).

Two other things this fixes, both of which present as "the app is broken" rather
than as a network problem, because a truncated js/app.js parses to nothing and
every global in it silently disappears:

  * HTTP/1.1 instead of 1.0, so the body is framed by Content-Length rather than
    by closing the socket.
  * gzip for text responses. js/app.js is ~210KB and was arriving short every few
    loads even over 1.1; compressed it's ~45KB and stops tripping whatever size
    limit sits between here and the browser. Also just faster to iterate on.
"""
import gzip, io, os, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Worth compressing: text that gets big. Images and fonts are already compressed.
GZIP_TYPES = (".js", ".css", ".html", ".json", ".webmanifest", ".svg", ".map")


class DevHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def do_GET(self):
        path = self.translate_path(self.path)
        if not (os.path.isfile(path)
                and path.lower().endswith(GZIP_TYPES)
                and "gzip" in self.headers.get("Accept-Encoding", "")):
            return super().do_GET()
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError:
            return super().do_GET()
        buf = io.BytesIO()
        # mtime=0 keeps the output byte-identical between runs of the same file.
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6, mtime=0) as gz:
            gz.write(raw)
        body = buf.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    print(f"serving http://localhost:{port} (no-store, HTTP/1.1, gzip)")
    ThreadingHTTPServer(("", port), DevHandler).serve_forever()
