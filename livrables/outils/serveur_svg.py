"""Serveur local de rendu : sert le dossier du scratchpad et enregistre les POST /save?name=… dans diag_out/."""
import base64
import http.server
import pathlib
import urllib.parse

RACINE = pathlib.Path(__file__).resolve().parent
SORTIE = RACINE / "diag_out"
SORTIE.mkdir(exist_ok=True)


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(RACINE), **k)

    def do_POST(self):
        q = urllib.parse.urlparse(self.path)
        if q.path != "/save":
            self.send_error(404)
            return
        p = urllib.parse.parse_qs(q.query)
        nom = pathlib.Path(p.get("name", ["x"])[0]).name
        corps = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if p.get("b64"):
            corps = base64.b64decode(corps)
        (SORTIE / nom).write_bytes(corps)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


http.server.ThreadingHTTPServer(("127.0.0.1", 8770), H).serve_forever()
