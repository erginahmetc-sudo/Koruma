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


def test_dns_email_skips_ip(server):
    # IP adresli hedefte DNS/e-posta kontrolü sessizce atlanır
    from koruma.checks import dns_email
    from koruma.checks import Context
    from koruma.http import Client
    from koruma.crawler import CrawlResult
    ctx = Context(client=Client(server), base_url=server, crawl=CrawlResult())
    assert dns_email.run(ctx) == []
