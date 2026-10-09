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
        <a href="/hesap?token=gizli123">Hesap</a>
        <a href="/profil?id=1">Profil</a>
        <a href="/login">Giriş</a>
        <!-- Kasıtlı olarak savunmasız/eski kütüphaneler ve SRI eksikliği -->
        <script src="https://cdn.example.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
        <script src="https://cdn.example.com/lodash/4.17.10/lodash.min.js"></script>
        <script src="/static/bootstrap-4.1.0.min.js"></script>
        <meta name="generator" content="WordPress 5.8.1">
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

    if path == "/":  # Host başlığını mutlak bağlantıya yansıtır (host header injection)
        fhost = environ.get("HTTP_X_FORWARDED_HOST") or environ.get("HTTP_HOST", "localhost")
        body = PAGES["/"].replace("</body>",
                 f'<link rel="canonical" href="http://{escape(fhost)}/"></body>')
        return _resp(start_response, "200 OK", body)

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

    if path == "/go":  # açık yönlendirme + CRLF enjeksiyonu taklidi
        raw_qs = environ.get("QUERY_STRING", "")
        nxt = qs.get("next", ["/"])[0]
        extra = []
        # Kasıtlı CRLF: 'next' değerindeki ham satır sonlarını başlığa yansıt
        if "next=" in raw_qs:
            from urllib.parse import unquote
            val = unquote(raw_qs.split("next=", 1)[1].split("&", 1)[0])
            nxt = val.split("\r\n")[0]  # Location yalnızca ilk satır (wsgiref CRLF'i reddeder)
            for line in val.split("\r\n")[1:]:
                if ":" in line:
                    k, _, v = line.partition(":")
                    extra.append((k.strip(), v.strip()))
        start_response("302 Found", [("Location", nxt), ("Content-Type", "text/html")] + extra)
        return [b""]

    if path == "/profil":  # IDOR: id değişince başka kullanıcının profili döner
        uid = qs.get("id", ["1"])[0]
        return _resp(start_response, "200 OK",
                     f"<html><body><h1>Kullanıcı Profili #{escape(uid)}</h1>"
                     f"<p>Ad: Kullanıcı {escape(uid)}</p><p>E-posta: user{escape(uid)}@ornek.com</p>"
                     f"<p>Telefon: 0555-000-{escape(uid).zfill(4)}</p></body></html>")

    if path == "/admin" or path == "/admin/":  # korunmasız yönetim paneli
        return _resp(start_response, "200 OK",
                     "<html><body><h1>Yönetim Paneli</h1><p>Hoş geldiniz yönetici. "
                     "Kullanıcıları ve ayarları buradan yönetebilirsiniz.</p></body></html>")

    if path == "/graphql":  # introspection açık
        import json as _json
        return _resp(start_response, "200 OK",
                     _json.dumps({"data": {"__schema": {"queryType": {"name": "Query"}}}}),
                     ctype="application/json")

    if path == "/crossdomain.xml":  # gevşek çapraz alan politikası
        return _resp(start_response, "200 OK",
                     '<?xml version="1.0"?><cross-domain-policy><allow-access-from domain="*"/></cross-domain-policy>',
                     ctype="text/x-cross-domain-policy")

    if path == "/wp-json/wp/v2/users":  # WordPress kullanıcı sayımı
        import json as _json
        return _resp(start_response, "200 OK",
                     _json.dumps([{"id": 1, "name": "Yönetici", "slug": "admin"}]),
                     ctype="application/json")

    if path == "/hesap":  # oturum çerezi + önbellek kısıtı yok (hassas sayfa)
        return _resp(start_response, "200 OK",
                     '<html><body>Hesabım<input type="password" name="p"></body></html>',
                     headers=[("Set-Cookie", "sessionid=abc123; Path=/")])

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
