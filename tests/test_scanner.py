from __future__ import annotations

import threading

import pytest

from koruma.crawler import parse_forms
from koruma.models import Severity
from koruma.report import to_html, to_json, to_text
from koruma.scanner import scan
from tests.vulnerable_app import serve


@pytest.fixture(scope="module")
def server():
    httpd = serve(port=0)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


@pytest.fixture(scope="module")
def result(server):
    return scan(server, delay=0.0, timeout=5, max_pages=30,
                test_post_forms=True, log=lambda *a, **k: None)


def titles(result):
    return [f.title for f in result.findings]


def test_crawl_finds_pages_and_forms(result):
    assert result.pages_crawled >= 4
    assert result.forms_found >= 2


def test_detects_reflected_xss(result):
    assert any("XSS" in t for t in titles(result))


def test_detects_sql_error(result):
    assert any("SQL" in t for t in titles(result))


def test_detects_path_traversal(result):
    assert any("yol parametresi" in t or "traversal" in t.lower() or "dosya" in t.lower()
               for t in titles(result))


def test_detects_open_redirect(result):
    assert any("yönlendirme" in t.lower() for t in titles(result))


def test_detects_missing_security_headers(result):
    assert any("Content-Security-Policy" in t for t in titles(result))


def test_detects_html_comment_secret(result):
    assert any("yorum" in t.lower() for t in titles(result))


def test_findings_sorted_by_severity(result):
    sev = [int(f.severity) for f in result.findings]
    assert sev == sorted(sev, reverse=True)


def test_report_formats_render(result):
    assert "Koruma" in to_text(result, color=False)
    assert '"findings"' in to_json(result)
    assert "<html" in to_html(result)


def test_parse_forms():
    html = '<form action="/x" method="post"><input name="a"><input type="submit"></form>'
    forms = parse_forms("http://h/", html)
    assert len(forms) == 1 and forms[0].method == "post" and "a" in forms[0].inputs


def test_scope_enforced(server):
    from koruma.http import Client
    c = Client(server)
    assert c.in_scope(server + "/x")
    assert not c.in_scope("https://baska-site.example/x")
    with pytest.raises(ValueError):
        c.get("https://baska-site.example/")


def test_severity_labels():
    assert Severity.CRITICAL.label == "KRİTİK"
    assert Severity.HIGH > Severity.LOW


def test_detects_vulnerable_js_library(result):
    ts = titles(result)
    assert any("jquery" in t.lower() for t in ts), "savunmasız jQuery tespit edilmeli"
    # CVE kanıtı bulunmalı
    comp = [f for f in result.findings if f.check == "components" and "jquery" in f.title.lower()]
    assert comp and "CVE-2020-11022" in comp[0].evidence


def test_detects_missing_sri(result):
    assert any("SRI" in t for t in titles(result))


def test_detects_cms_version(result):
    assert any("WordPress 5.8" in t or "CMS sürümü" in t for t in titles(result))


def test_fingerprint_reports_tech(result):
    assert any(f.check == "fingerprint" for f in result.findings)


def test_semver_compare():
    from koruma import semver
    assert semver.lt("3.4.1", "3.5.0")
    assert semver.lt("3.0.0-rc.1", "3.0.0")
    assert semver.in_range("4.1.0", "4.0.0", "4.3.1", None)
    assert not semver.in_range("4.17.21", None, "4.17.21", None)


def test_detects_graphql_introspection(result):
    assert any("GraphQL" in t for t in titles(result))


def test_detects_wordpress_user_enum(result):
    assert any("kullanıcı sayımı" in t.lower() for t in titles(result))


def test_detects_crossdomain_policy(result):
    assert any("çapraz alan" in t.lower() for t in titles(result))


def test_detects_crlf_injection(result):
    assert any("CRLF" in t for t in titles(result))


def test_detects_host_header_injection(result):
    assert any("Host başlığı" in t for t in titles(result))


def test_detects_secret_in_url(result):
    assert any("hassas parametre" in t.lower() for t in titles(result))


def test_detects_cache_on_sensitive_page(result):
    assert any("önbellekleme" in t.lower() for t in titles(result))


def test_detects_more_js_libraries():
    from koruma.checks import components
    db = components._load_db()
    assert len(db) >= 15
    # Vue sürüm tespiti
    v = components._detect_version("https://cdn/vue@2.5.0/dist/vue.min.js", db["vue"])
    assert v == "2.5.0" and components._match_vulns(v, db["vue"])


def test_detects_forced_browsing(result):
    assert any("kimlik doğrulamasız erişilebilir" in t.lower() for t in titles(result))


def test_detects_idor(result):
    assert any("IDOR" in t for t in titles(result))


def test_pdf_report_generation(result, tmp_path):
    from koruma.pdfreport import build_pdf
    import json as _json
    from koruma.report import to_json
    out = tmp_path / "rapor.pdf"
    build_pdf(_json.loads(to_json(result)), str(out))
    assert out.exists() and out.stat().st_size > 1000
    assert out.read_bytes().startswith(b"%PDF")


def test_update_db_converter():
    # Retire.js biçimindeki bir girdiyi doğru dönüştürür
    from koruma.update import _convert_entry
    entry = {
        "extractors": {"uri": ["/(§§version§§)/testlib(\\.min)?\\.js"], "func": ["x"]},
        "vulnerabilities": [
            {"ranges": [{"atOrAbove": "1.0.0", "below": "2.0.0"}],
             "severity": "high", "summary": "örnek açık",
             "identifiers": {"CVE": ["CVE-2024-0001"]}},
        ],
    }
    conv = _convert_entry(entry)
    assert conv and conv["vulns"][0]["ids"] == ["CVE-2024-0001"]
    assert conv["vulns"][0]["below"] == "2.0.0" and conv["vulns"][0]["severity"] == "HIGH"


def test_access_auth_diff_requires_user_auth(server):
    # Kullanıcı kimlik bilgisi vermediyse auth-diff çalışmaz (yanlış pozitif önleme)
    from koruma.checks import access, Context
    from koruma.http import Client
    from koruma.crawler import CrawlResult
    ctx = Context(client=Client(server), base_url=server, crawl=CrawlResult(), authenticated=False)
    assert access._check_auth_diff(ctx) == []


def test_detects_supabase_service_role_leak(result):
    assert any("service_role" in t for t in titles(result))


def test_detects_secret_in_js_file(result):
    comp = [f for f in result.findings if f.check == "jsrecon" and "AWS" in f.title]
    assert comp, "JS dosyasındaki AWS anahtarı tespit edilmeli"


def test_detects_source_map_exposure(result):
    assert any("Kaynak haritası" in t for t in titles(result))


def test_detects_risky_endpoint_in_js(result):
    assert any("riskli uç nokta" in t.lower() for t in titles(result))


def test_secret_scanner_breadth():
    from koruma import secrets
    # Not: sahte token'lar parça parça birleştirilir; depoda gerçek sır deseni
    # oluşmasın (GitHub gizli tarama koruması) diye.
    cases = [
        "AKIA" + "A" * 16,
        "ghp_" + "a" * 36,
        "sk_live_" + "b" * 30,
        "xoxb-" + "1" * 11 + "-" + "2" * 11 + "-" + "x" * 16,
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "sk-ant-api03-" + "c" * 93 + "AA",
    ]
    for c in cases:
        assert secrets.scan(c), f"tespit edilmeli: {c[:12]}"
    assert len(secrets._rules()) >= 25


def test_seclists_paths_present():
    from koruma.checks.files import SENSITIVE_PATHS
    paths = {p[0] for p in SENSITIVE_PATHS}
    for expected in (".ssh/id_rsa", ".npmrc", "actuator/heapdump", "config/database.yml"):
        assert expected in paths


def test_jwt_role_decode():
    from koruma.checks.baas import _jwt_role
    import base64, json as _json
    def b64(d): return base64.urlsafe_b64encode(_json.dumps(d).encode()).rstrip(b"=").decode()
    tok = f"{b64({'alg':'HS256'})}.{b64({'role':'service_role'})}.sig"
    assert _jwt_role(tok) == "service_role"


def test_dns_email_skips_ip(server):
    # IP adresli hedefte DNS/e-posta kontrolü sessizce atlanır
    from koruma.checks import dns_email
    from koruma.checks import Context
    from koruma.http import Client
    from koruma.crawler import CrawlResult
    ctx = Context(client=Client(server), base_url=server, crawl=CrawlResult())
    assert dns_email.run(ctx) == []


# --- SPA / catch-all (sahte alarm) regresyon testleri ----------------------------------

SPA_CHECKS = ["files", "endpoints", "access", "fingerprint", "jsrecon", "disclosure",
              "components", "advanced", "cors", "methods", "injection", "redirect", "cookies"]


def _run_server(wsgi):
    from tests.vulnerable_app import serve
    httpd = serve(port=0, wsgi=wsgi)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_port}"


def test_spa_catchall_produces_no_false_alarms():
    """Bilinmeyen her adrese ana sayfayı 200 ile döndüren site, sahte alarm üretmemeli."""
    from tests.vulnerable_app import spa_app
    httpd, url = _run_server(spa_app)
    try:
        res = scan(url, delay=0, checks=SPA_CHECKS, log=lambda *a, **k: None)
    finally:
        httpd.shutdown()
    bad = [f.title for f in res.findings
           if f.severity >= Severity.LOW and f.check in ("files", "endpoints", "access", "fingerprint")]
    assert bad == [], bad
    assert any("catch-all" in f.title for f in res.findings), "catch-all bilgi notu bulunmalı"


def test_real_exposure_still_found_behind_catchall():
    """SPA'nın arkasında GERÇEKTEN açık bir .env varsa, yine de bulunmalı (yanlış negatif yok)."""
    from tests.vulnerable_app import spa_app, _resp

    def spa_with_env(environ, start_response):
        if environ.get("PATH_INFO") == "/.env":
            return _resp(start_response, "200 OK", "APP_ENV=production\nDB_PASSWORD=ornek\n", ctype="text/plain")
        return spa_app(environ, start_response)

    httpd, url = _run_server(spa_with_env)
    try:
        res = scan(url, delay=0, checks=["files"], log=lambda *a, **k: None)
    finally:
        httpd.shutdown()
    exposed = [f.title for f in res.findings if f.title.startswith("Hassas dosya")]
    assert exposed == ["Hassas dosya erişilebilir: /.env"], exposed


def test_real_env_and_git_head_detected(result):
    ts = titles(result)
    assert "Hassas dosya erişilebilir: /.env" in ts
    assert "Hassas dosya erişilebilir: /.git/HEAD" in ts


def test_baseline_ignores_nonce_and_hashes():
    from koruma.baseline import Baseline, _Sig
    a = '<html><title>T</title><script nonce="aaaaaaaaaaaaaaaa">x</script></html>'
    b = '<html><title>T</title><script nonce="bbbbbbbbbbbbbbbb">x</script></html>'
    bl = Baseline([_Sig(200, "text/html", a)])
    assert bl.catchall and bl.matches(200, "text/html", b)
    assert not bl.matches(404, "text/html", b)          # farklı durum kodu = farklı cevap
    assert not bl.matches(200, "text/plain", "APP_ENV=production\nDB_PASSWORD=x\n")


def test_file_validation_rejects_html_and_accepts_real_content():
    from koruma.checks.files import _validate
    env_re = r"re:^[A-Za-z_][A-Za-z0-9_.]*\s*="
    html = "<!doctype html><html><head></head><body>a=b {x}</body></html>"
    assert not _validate(env_re, html.encode(), html, "text/html")
    env = "APP_ENV=production\nDB_PASSWORD=x\n"
    assert _validate(env_re, env.encode(), env, "text/plain")
    assert not _validate("json", b"<html>", "<html>", "application/json")
    assert _validate("json:a", b'{"a":1}', '{"a":1}', "application/json")
    assert _validate("magic:" + b"PK\x03\x04".hex(), b"PK\x03\x04rest", "PK", "application/zip")
    assert not _validate("magic:" + b"PK\x03\x04".hex(), html.encode(), html, "text/html")
