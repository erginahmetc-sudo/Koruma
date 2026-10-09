"""Girdi işleme kontrolleri: yansıtma (reflection), veritabanı hata
mesajları, şablon değerlendirmesi, dosya yolu işleme ve CSRF token'ı.

Bu modül yalnızca sunucunun girdiyi nasıl işlediğini GÖZLEMLER. Gönderilen
değerler zararsızdır: hiçbir kaydı değiştirmez, silmez veya oluşturmaz;
yalnızca yanıtı okur. Amaç, kendi sitenizdeki kusurları siz kapatabilesiniz
diye raporlamaktır.
"""
from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from koruma.models import Finding, Form, Severity

NAME = "injection"

# Veritabanı motorlarının sızdırdığı hata imzaları (yalnızca eşleştirme için).
DB_ERRORS = [
    ("MySQL", re.compile(r"You have an error in your SQL syntax|mysql_fetch|mysqli_|MySqlException|corresponds to your (?:MySQL|MariaDB) server version", re.I)),
    ("PostgreSQL", re.compile(r"PG::SyntaxError|pg_query\(\)|PSQLException|unterminated quoted string at or near|syntax error at or near", re.I)),
    ("MSSQL", re.compile(r"Unclosed quotation mark after the character string|Microsoft OLE DB Provider for SQL Server|SqlException|\[SQL Server\]", re.I)),
    ("Oracle", re.compile(r"\bORA-\d{5}\b|quoted string not properly terminated", re.I)),
    ("SQLite", re.compile(r"SQLite3?::|sqlite3\.OperationalError|SQLITE_ERROR|unrecognized token:", re.I)),
    ("Genel", re.compile(r"SQLSTATE\[|Dynamic SQL Error|ODBC Driver", re.I)),
]

PATH_PARAM_HINTS = ("file", "path", "page", "include", "template", "doc", "document", "folder", "dir", "load", "view")
PATH_PROBES = ["../../../../../../../../etc/passwd", "....//....//....//....//....//etc/passwd",
               "..\\..\\..\\..\\..\\..\\windows\\win.ini"]
PATH_MARKERS = (re.compile(r"root:[x*]?:0:0:"), re.compile(r"\[(?:fonts|extensions)\]", re.I))

CSRF_HINTS = ("csrf", "xsrf", "token", "authenticity", "nonce", "__requestverification", "_token")


@dataclass
class Target:
    """Test edilecek bir giriş noktası: bir URL'nin parametreleri ya da bir form."""
    url: str
    method: str
    params: dict[str, str]
    source: str

    def send(self, client, param: str, value: str):
        data = dict(self.params)
        data[param] = value
        if self.method == "post":
            return client.request("POST", self.url, data=data)
        p = urlparse(self.url)
        return client.get(urlunparse(p._replace(query=urlencode(data))))


def collect_targets(ctx) -> list[Target]:
    targets: list[Target] = []
    for url in ctx.crawl.param_urls:
        p = urlparse(url)
        params = dict(parse_qsl(p.query, keep_blank_values=True))
        if params:
            targets.append(Target(urlunparse(p._replace(query="")), "get", params, url))
    for form in ctx.crawl.forms:
        if not form.inputs:
            continue
        if form.method == "post" and not ctx.test_post_forms:
            continue
        params = {k: (v or "test") for k, v in form.inputs.items()}
        targets.append(Target(form.action, form.method, params, f"form @ {form.page_url}"))
    return targets


def _baseline(ctx, t: Target, param: str) -> str:
    r = t.send(ctx.client, param, t.params.get(param) or "koruma")
    return r.text if r is not None else ""


def _check_reflection(ctx, t: Target, param: str):
    """Girdinin HTML'e kodlanmadan geri yansıtılıp yansıtılmadığını kontrol eder."""
    tok = "kz" + secrets.token_hex(4)
    probe = f"{tok}<kzx>"
    r = t.send(ctx.client, param, probe)
    if r is None or "html" not in r.headers.get("Content-Type", ""):
        return None
    if probe in r.text:
        return Finding(NAME, f"Yansıtılan girdi HTML olarak işleniyor (XSS): '{param}'", Severity.HIGH, t.url,
                       "Girdideki '<' karakteri kodlanmadan yanıta geçiyor; bu, sayfaya script enjekte edilebileceği "
                       "anlamına gelir (reflected XSS).",
                       "Çıktıyı bağlama göre encode edin (HTML entity), şablon motorunun otomatik kaçışını açık tutun ve "
                       "Content-Security-Policy ekleyin.",
                       f"{t.method.upper()} {param}={probe} -> yanıtta aynen bulundu ({t.source})")
    if tok in r.text and probe not in r.text:
        return None  # yansıyor ama '<' kaçırılmış: güvenli
    return None


def _check_db_errors(ctx, t: Target, param: str, baseline: str):
    """Özel karakterlerin veritabanı hata mesajı tetikleyip tetiklemediğine bakar."""
    for suffix in ("'", "\"", "')"):
        r = t.send(ctx.client, param, (t.params.get(param) or "1") + suffix)
        if r is None:
            continue
        for db, rx in DB_ERRORS:
            m = rx.search(r.text)
            if m and not rx.search(baseline):
                return Finding(NAME, f"Girdi doğrudan SQL sorgusuna giriyor ({db}): '{param}'", Severity.CRITICAL, t.url,
                               "Tek tırnak eklendiğinde ham veritabanı hatası dönüyor; bu, girdinin sorguya string "
                               "birleştirme ile eklendiğini gösterir (SQL injection).",
                               "Parametreli sorgular (prepared statements) veya bir ORM kullanın; girdiyi asla sorgu "
                               "metnine eklemeyin. Üretimde ham hata mesajlarını gizleyin.",
                               f"{param}=…{suffix} -> '{m.group(0)[:80]}' ({t.source})")
    return None


def _check_template_eval(ctx, t: Target, param: str, baseline: str):
    """Girdinin şablon motorunca değerlendirilip değerlendirilmediğine bakar (SSTI)."""
    a, b = 1337, 7331
    expected = str(a * b)
    if expected in baseline:
        return None
    for probe in (f"{{{{{a}*{b}}}}}", f"${{{a}*{b}}}", f"<%= {a}*{b} %>", f"#{{{a}*{b}}}"):
        r = t.send(ctx.client, param, probe)
        if r is not None and expected in r.text:
            return Finding(NAME, f"Girdi şablon olarak değerlendiriliyor (SSTI): '{param}'", Severity.CRITICAL, t.url,
                           "Sayfa, gönderilen aritmetik ifadeyi hesaplayıp sonucu döndürdü; girdi şablon motorunca kod "
                           "gibi çalıştırılıyor. Bu genellikle sunucuda kod çalıştırmaya kadar gider.",
                           "Kullanıcı girdisini şablon kaynağına eklemeyin; yalnızca bir veri değişkeni olarak geçirin.",
                           f"{param}={probe} -> yanıtta {expected} ({t.source})")
    return None


def _check_path_handling(ctx, t: Target, param: str, baseline: str):
    """Yol benzeri parametrelerde dosya içeriğinin geri dönüp dönmediğine bakar."""
    if not any(h in param.lower() for h in PATH_PARAM_HINTS):
        return None
    for probe in PATH_PROBES:
        r = t.send(ctx.client, param, probe)
        if r is None:
            continue
        for rx in PATH_MARKERS:
            if rx.search(r.text) and not rx.search(baseline):
                return Finding(NAME, f"Dosya yolu parametresi sunucudaki dosyaları açığa çıkarıyor: '{param}'",
                               Severity.CRITICAL, t.url,
                               "Göreli yol gönderildiğinde web kökü dışındaki bir sistem dosyasının içeriği döndü "
                               "(path traversal / local file inclusion).",
                               "Dosya adlarını kesin bir beyaz liste ile doğrulayın; '..' ve mutlak yolları reddedin.",
                               f"{param}={probe} ({t.source})")
    return None


def _check_csrf(form: Form):
    if form.method != "post" or not form.inputs:
        return None
    if any(any(h in n.lower() for h in CSRF_HINTS) for n in form.inputs):
        return None
    return Finding(NAME, "POST formunda CSRF token alanı görünmüyor", Severity.LOW, form.page_url,
                   "Form alanları arasında bir anti-CSRF token'ı yok; SameSite çerezleri de yoksa başka bir site "
                   "kullanıcı adına bu formu gönderebilir.",
                   "Her duruma etki eden forma oturuma bağlı, tahmin edilemez bir CSRF token'ı ekleyin ve sunucuda doğrulayın.",
                   f"action={form.action} alanlar={', '.join(form.inputs)}")


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    reported: set = set()

    def add(f):
        if f is None:
            return
        if f.key() not in reported:
            reported.add(f.key())
            findings.append(f)

    for form in ctx.crawl.forms:
        add(_check_csrf(form))

    for t in collect_targets(ctx):
        for param in t.params:
            baseline = _baseline(ctx, t, param)
            add(_check_reflection(ctx, t, param))
            add(_check_db_errors(ctx, t, param, baseline))
            add(_check_template_eval(ctx, t, param, baseline))
            add(_check_path_handling(ctx, t, param, baseline))
    return findings
