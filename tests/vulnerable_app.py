"""Testler için kasıtlı olarak güvenlik açığı içeren küçük bir WSGI uygulaması.

SADECE Koruma'nın bulgularını doğrulamak için kullanılır; gerçek bir sunucuda
ASLA çalıştırmayın. Dışarıya hiçbir şey açmaz, hiçbir dosyayı okumaz; tüm
"açıklar" sabit kodlanmış taklitlerdir.
"""
from __future__ import annotations

from html import escape
from urllib.parse import parse_qs

PAGES = {
    "/": """<html><head><title>Zafiyetli Test</title></head><body>
        <h1>Ana Sayfa</h1>
        <!-- TODO: admin password is hunter2, remove before launch -->
        <a href="/search?q=merhaba">Arama</a>
        <a href="/item?id=1">Ürün</a>
        <a href="/go?next=/profil">Profil</a>
        <a href="/read?file=notlar.txt">Dosya</a>
        <a href="/login">Giriş</a>
        <form action="/comment" method="post">
          <input name="yorum" type="text"><input type="submit">
        </form>
        </body></html>""",
    "/login": """<html><body><form action="/login" method="post">
        <input name="kullanici"><input name="parola" type="password">
        <input type="submit"></form></body></html>""",
}


def _resp(start, status, body, headers=None, ctype="text/html; charset=utf-8"):
    h = [("Content-Type", ctype)]
    if headers:
        h.extend(headers)
    start(status, h)
    return [body.encode("utf-8")]


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    qs = parse_qs(environ.get("QUERY_STRING", ""))

    if path == "/search":  # yansıtılan XSS (kodlanmamış)
        q = qs.get("q", [""])[0]
        return _resp(start_response, "200 OK", f"<html><body>Sonuç: {q}</body></html>")

    if path == "/item":  # SQL hata sızıntısı
        id_ = qs.get("id", [""])[0]
        if "'" in id_ or '"' in id_:
            body = "<html><body>You have an error in your SQL syntax; check the manual</body></html>"
        else:
            body = f"<html><body>Ürün #{escape(id_)}</body></html>"
        return _resp(start_response, "200 OK", body)

    if path == "/read":  # dizin geçişi taklidi
        f = qs.get("file", [""])[0]
        if "etc/passwd" in f:
            return _resp(start_response, "200 OK", "root:x:0:0:root:/root:/bin/bash\n", ctype="text/plain")
        return _resp(start_response, "200 OK", f"<html><body>Dosya: {escape(f)}</body></html>")

    if path == "/go":  # açık yönlendirme
        nxt = qs.get("next", ["/"])[0]
        start_response("302 Found", [("Location", nxt), ("Content-Type", "text/html")])
        return [b""]

    if path in PAGES:
        return _resp(start_response, "200 OK", PAGES[path])

    return _resp(start_response, "404 Not Found", "<html><body>Bulunamadı</body></html>")


def serve(host="127.0.0.1", port=0):
    """Test için bir thread içinde başlatılabilen WSGI sunucusu döndürür."""
    from wsgiref.simple_server import WSGIServer, make_server

    class QuietServer(WSGIServer):
        def handle_error(self, request, client_address):
            pass

    httpd = make_server(host, port, app, server_class=QuietServer)
    return httpd


if __name__ == "__main__":
    srv = serve(port=8000)
    print(f"http://127.0.0.1:{srv.server_port} üzerinde çalışıyor (Ctrl+C ile durdurun)")
    srv.serve_forever()
