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
