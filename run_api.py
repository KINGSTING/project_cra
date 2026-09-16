# run_api.py
import http.server
import socketserver
import sys
import os
import importlib
from dotenv import load_dotenv

load_dotenv(".env.local")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))

PORT = 3001

# Map URL path -> module name in api/ that exports `handler`
ROUTES = {
    "/api/send_verification": "send_verification",
    "/api/verify_email":      "verify_email",
    "/api/auth/request_link": "request_link",
}

# Import each handler lazily
_handler_cache = {}


def _load_handler(module_name):
    if module_name not in _handler_cache:
        mod = importlib.import_module(module_name)
        _handler_cache[module_name] = mod.handler
    return _handler_cache[module_name]


class Router(http.server.BaseHTTPRequestHandler):
    def _dispatch(self, method):
        path = self.path.split("?", 1)[0].rstrip("/")
        module_name = ROUTES.get(path)
        if not module_name:
            body = b'{"error":"not_found"}'
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        handler_cls = _load_handler(module_name)

        # Build a fresh handler instance bound to the same socket/stream
        self.__class__ = handler_cls  # swap class in place
        getattr(self, method)()

    def do_GET(self):     self._dispatch("do_GET")
    def do_POST(self):    self._dispatch("do_POST")
    def do_OPTIONS(self): self._dispatch("do_OPTIONS")


class LocalServer(socketserver.TCPServer):
    allow_reuse_address = True


with LocalServer(("", PORT), Router) as httpd:
    print(f"✅ Python API server running at http://localhost:{PORT}")
    print(f"   Routes:")
    for path, mod in ROUTES.items():
        print(f"     {path}  ->  api/{mod}.py")
    print("   Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")