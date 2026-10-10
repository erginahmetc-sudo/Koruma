"""Açıkta kalmış hassas dosya ve dizin tespiti.

Yanlış alarmı önlemek için iki katmanlı doğrulama yapılır:
  1. Catch-all parmak izi: sunucunun "olmayan adres" cevabına benzeyen her şey
     (SPA ana sayfası, özel 404 sayfası, WAF engel sayfası) "yok" sayılır.
  2. İçerik doğrulama: dosya türüne özgü gerçek biçim aranır (ör. .env için satır
     başında ANAHTAR=değer, .git/HEAD için "ref: refs/"). HTML dönen cevaplar,
     HTML beklenen birkaç yol dışında baştan reddedilir.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin

from koruma import baseline
from koruma import secrets as secrets_scanner
from koruma.models import Finding, Severity

NAME = "files"

C, H, M, L, I = (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO)


def _magic(*sigs: bytes) -> str:
    return "magic:" + "|".join(s.hex() for s in sigs)


LOG_RE = (r"re:(?i)(\[\d{4}-\d{2}-\d{2}[ T]\d{2}:|\[[A-Z][a-z]{2} [A-Z][a-z]{2} +\d{1,2} "
          r"|PHP (Warning|Notice|Fatal error|Deprecated)|Stack trace:|Traceback \(most recent)")

# Doğrulama tanımları (spec):
#   re:<regex>        HTML olmayan içerikte satır bazında (re.M) aranır
#   json[:a|b]        geçerli JSON; verilirse anahtarlardan biri bulunmalı
#   magic:<hex|hex>   ikili dosya başlangıç imzası
#   html:<metin>      HTML beklenen yol (ör. phpinfo) - metin bulunmalı
#   any               HTML olmayan, boş olmayan herhangi bir içerik
# (yol, önem, açıklama, doğrulama)
SENSITIVE_PATHS = [
    # --- Sürüm kontrol sistemleri ---
    (".git/HEAD", C, "Git deposu herkese açık; tüm kaynak kod indirilebilir.", r"re:^(ref: refs/|[0-9a-f]{40}\s*$)"),
    (".git/config", C, "Git yapılandırması herkese açık.", r"re:^\[core\]"),
    (".svn/entries", H, "SVN meta verileri herkese açık.", r"re:\A\d{1,2}\s*\n"),
    (".hg/hgrc", H, "Mercurial deposu herkese açık.", r"re:^\[(paths|ui|extensions)\]"),
    # --- Ortam / yapılandırma dosyaları ---
    (".env", C, "Ortam dosyası açık; parolalar ve API anahtarları sızabilir.", r"re:^[A-Za-z_][A-Za-z0-9_.]*\s*="),
    (".env.local", C, "Ortam dosyası açık.", r"re:^[A-Za-z_][A-Za-z0-9_.]*\s*="),
    (".env.production", C, "Ortam dosyası açık.", r"re:^[A-Za-z_][A-Za-z0-9_.]*\s*="),
    (".env.bak", C, "Ortam dosyası yedeği açık.", r"re:^[A-Za-z_][A-Za-z0-9_.]*\s*="),
    ("config.php.bak", C, "Yapılandırma yedeği açık.", r"re:<\?php"),
    ("wp-config.php.bak", C, "WordPress yapılandırma yedeği açık.", r"re:DB_PASSWORD"),
    ("wp-config.php~", C, "WordPress yapılandırma yedeği açık.", r"re:DB_PASSWORD"),
    ("wp-config.php.save", C, "WordPress yapılandırma yedeği açık.", r"re:DB_PASSWORD"),
    ("wp-config.php.old", C, "WordPress yapılandırma yedeği açık.", r"re:DB_PASSWORD"),
    ("configuration.php.bak", C, "Joomla yapılandırma yedeği açık.", r"re:JConfig"),
    ("config.json", L, "Yapılandırma dosyası herkese açık; içinde sır olmadığından emin olun.", "json"),
    ("settings.py", H, "Django settings.py açık (SECRET_KEY içerebilir).", r"re:SECRET_KEY"),
    ("config/database.yml", C, "Rails veritabanı yapılandırması açık.", r"re:^\s*(password|adapter|database):"),
    ("config/aws.yml", C, "AWS yapılandırması açık.", r"re:(?i)(access_key|secret)"),
    ("app/etc/local.xml", C, "Magento yapılandırması (DB parolası) açık.", r"re:<config>|<resources>"),
    ("app/config/parameters.yml", C, "Symfony parametreleri açık.", r"re:^parameters:"),
    ("web.config", M, "IIS web.config açık.", r"re:<configuration"),
    ("web.config.bak", H, "IIS web.config yedeği açık.", r"re:<configuration"),
    (".htaccess", L, ".htaccess dosyası okunabiliyor.",
     r"re:(?i)^\s*(RewriteEngine|RewriteRule|RewriteCond|Options|AuthType|Require|Order|Deny from|Allow from|SetEnv|Header|php_value|AddType|<IfModule)"),
    (".htpasswd", H, "Parola özetleri içeren .htpasswd dosyası okunabiliyor.", r"re:^[^:\s]+:(\$|\{SHA\}|[A-Za-z0-9./]{13}$)"),
    # --- Yedekler ve veritabanı dökümleri ---
    ("backup.zip", H, "Yedek arşivi indirilebilir.", _magic(b"PK\x03\x04")),
    ("backup.sql", C, "Veritabanı dökümü indirilebilir.", r"re:(?i)^\s*(INSERT INTO|CREATE TABLE|DROP TABLE|-- MySQL dump|-- PostgreSQL database dump)"),
    ("dump.sql", C, "Veritabanı dökümü indirilebilir.", r"re:(?i)^\s*(INSERT INTO|CREATE TABLE|DROP TABLE|-- MySQL dump|-- PostgreSQL database dump)"),
    ("database.sql", C, "Veritabanı dökümü indirilebilir.", r"re:(?i)^\s*(INSERT INTO|CREATE TABLE|DROP TABLE|-- MySQL dump|-- PostgreSQL database dump)"),
    ("db.sqlite", C, "SQLite veritabanı indirilebilir.", _magic(b"SQLite format")),
    # --- SSH / kimlik bilgisi dosyaları ---
    ("id_rsa", C, "Özel SSH anahtarı açık!", r"re:PRIVATE KEY"),
    (".ssh/id_rsa", C, "Özel SSH anahtarı açık!", r"re:PRIVATE KEY"),
    (".ssh/id_ed25519", C, "Özel SSH anahtarı açık!", r"re:PRIVATE KEY"),
    (".ssh/authorized_keys", H, "SSH authorized_keys açık.", r"re:^(ssh-(rsa|ed25519|dss)|ecdsa-sha2)"),
    (".npmrc", H, ".npmrc kayıtlı token içerebilir.", r"re:_authToken|_auth\s*="),
    (".netrc", H, ".netrc kimlik bilgileri içerir.", r"re:^\s*machine\s+\S+"),
    (".ftppass", H, "FTP parola dosyası açık.", "any"),
    ("sftp-config.json", H, "SFTP yapılandırması (parola içerebilir) açık.", "json:host|user|password"),
    (".remote-sync.json", H, "Uzak senkron yapılandırması açık.", "json:host|target|transport"),
    (".bash_history", M, "Kabuk komut geçmişi açık.", "any"),
    (".mysql_history", M, "MySQL komut geçmişi açık.", "any"),
    # --- Bilgi ifşa eden sayfalar ---
    ("phpinfo.php", M, "phpinfo() sunucu yapılandırmasını ifşa ediyor.", "html:PHP Version"),
    ("info.php", M, "phpinfo() sunucu yapılandırmasını ifşa ediyor.", "html:PHP Version"),
    ("server-status", M, "Apache server-status sayfası açık.", "html:Apache Server Status"),
    ("server-info", M, "Apache server-info sayfası açık.", "html:Apache Server Information"),
    ("phpmyadmin/", M, "phpMyAdmin paneli herkese açık.", "html:phpMyAdmin"),
    ("adminer.php", H, "Adminer veritabanı paneli herkese açık.", "html:Adminer"),
    (".DS_Store", L, "macOS dizin meta dosyası dosya adlarını ifşa eder.", _magic(b"\x00\x00\x00\x01Bud1")),
    # --- Projeler / CI / konteyner ---
    ("composer.lock", L, "Bağımlılık sürümleri ifşa oluyor.", "json:packages|packages-dev"),
    ("package.json", L, "Bağımlılık listesi ifşa oluyor.", "json:dependencies|devDependencies"),
    ("docker-compose.yml", M, "Docker yapılandırması açık.", r"re:^services:"),
    ("docker-compose.yaml", M, "Docker yapılandırması açık.", r"re:^services:"),
    ("Dockerfile", L, "Dockerfile açık.", r"re:^FROM\s+\S+"),
    (".gitlab-ci.yml", L, "CI/CD yapılandırması açık (sır içerebilir).", r"re:^(stages|script|image|before_script|variables|include|build|test|deploy):"),
    (".travis.yml", L, "CI yapılandırması açık.", r"re:^(language|script|before_install|install|node_js|python|dist):"),
    # --- Günlükler ---
    ("error_log", M, "Hata günlüğü açık.", LOG_RE),
    ("debug.log", M, "Hata ayıklama günlüğü açık.", LOG_RE),
    ("wp-content/debug.log", M, "WordPress hata günlüğü açık.", LOG_RE),
    ("storage/logs/laravel.log", H, "Laravel günlüğü açık.", LOG_RE),
    # --- Spring Boot / JMX ---
    ("actuator/env", H, "Spring Boot actuator ortam değişkenlerini ifşa ediyor.", "json:propertySources|activeProfiles"),
    ("actuator/heapdump", C, "Spring Boot bellek dökümü indirilebilir.", _magic(b"JAVA PROFILE", b"\x1f\x8b")),
    ("actuator/threaddump", M, "Spring Boot thread dökümü açık.", "json:threads"),
    ("actuator/configprops", M, "Spring Boot yapılandırma özellikleri açık.", "json:contexts|beans"),
    ("actuator/mappings", L, "Spring Boot endpoint eşlemeleri açık.", "json:contexts"),
    ("jolokia", H, "Jolokia JMX arayüzü açık.", "json:request|status|agent"),
    # --- API dokümantasyonu ---
    ("swagger.json", I, "API dokümantasyonu herkese açık.", "json:swagger|openapi"),
    ("openapi.json", I, "API dokümantasyonu herkese açık.", "json:swagger|openapi"),
]

LISTING_MARKERS = ("Index of /", "<title>Directory listing", "Parent Directory</a>", "[To Parent Directory]")


def _validate(spec: str, raw: bytes, text: str, ctype: str) -> bool:
    kind, _, arg = spec.partition(":")
    if kind == "html":                       # HTML beklenen yol
        return arg in text
    if baseline.looks_html(text, ctype):     # diğerleri için HTML = kabuk/hata sayfası
        return False
    if kind == "re":
        return re.search(arg, text, re.M) is not None
    if kind == "json":
        try:
            obj = json.loads(text)
        except ValueError:
            return False
        if not isinstance(obj, (dict, list)):
            return False
        if not arg:
            return True
        return isinstance(obj, dict) and any(k in obj for k in arg.split("|"))
    if kind == "magic":
        return any(raw.startswith(bytes.fromhex(h)) for h in arg.split("|"))
    if kind == "any":
        return len(raw) > 0
    return False


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    root = urljoin(ctx.base_url, "/")
    bl = baseline.get(ctx)

    if bl.catchall:
        findings.append(Finding(NAME, "Sunucu bilinmeyen tüm adreslere 200 döndürüyor (SPA / catch-all)", Severity.INFO,
            ctx.base_url,
            "Var olmayan adresler bile 200 OK ve aynı sayfayla cevaplanıyor (tek sayfa uygulaması veya özel "
            "yönlendirme). Bu yüzden dosya/uç nokta kontrolleri HTTP koduna değil, içeriğin gerçekten beklenen "
            "dosya biçiminde olmasına göre değerlendirildi; ana sayfa dönen adresler 'yok' sayıldı.",
            "Önlem gerekmez. İsterseniz var olmayan adresler için gerçek bir 404 döndürün; bu hem taramayı hem "
            "arama motoru sıralamasını iyileştirir.",
            f"{len(bl.sigs)} rastgele adres sorgulandı"))

    for path, sev, desc, spec in SENSITIVE_PATHS:
        url = urljoin(root, path)
        r = ctx.client.get(url, allow_redirects=False, stream=True)
        if r is None or r.status_code != 200:
            continue
        # Büyük dosyaları tamamen indirmeyelim
        raw = next(r.iter_content(65536), b"")
        r.close()
        ctype = r.headers.get("Content-Type", "")
        text = raw.decode("utf-8", errors="replace")

        if bl.matches(200, ctype, text):      # sunucunun "yok" cevabına benziyor
            continue
        if not _validate(spec, raw, text, ctype):
            continue

        # Dosyanın içinde gerçek sır varsa önemi yükselt; değerleri rapora yazma
        found = secrets_scanner.scan(text)
        evidence = f"HTTP 200, {len(raw)} bayt, {ctype or 'tür belirtilmemiş'}"
        if found:
            sev = max(sev, max(s for _, _, s in found))
            evidence += "; içinde sır türleri: " + ", ".join(sorted({n for n, _, _ in found})[:4])
        findings.append(Finding(NAME, f"Hassas dosya erişilebilir: /{path}", sev, url, desc,
                                "Dosyayı web kök dizininden kaldırın veya sunucu yapılandırmasıyla erişimi engelleyin.",
                                evidence))

    # Dizin listeleme
    dirs = {root}
    for p in ctx.crawl.pages:
        dirs.add(p.url.rsplit("/", 1)[0] + "/")
    for d in list(dirs)[:30]:
        if not ctx.client.in_scope(d):
            continue
        r = ctx.client.get(d)
        if r is not None and r.status_code == 200 and any(m in r.text for m in LISTING_MARKERS):
            findings.append(Finding(NAME, "Dizin listeleme açık", Severity.MEDIUM, d,
                                    "Dizindeki tüm dosyalar listelenebiliyor.",
                                    "Apache: 'Options -Indexes', Nginx: 'autoindex off;' ayarlayın."))

    sec = ctx.client.get(urljoin(root, ".well-known/security.txt"))
    if sec is None or sec.status_code != 200 or "Contact:" not in sec.text:
        findings.append(Finding(NAME, "security.txt bulunamadı", Severity.INFO, urljoin(root, ".well-known/security.txt"),
                                "Güvenlik araştırmacılarının size nasıl ulaşacağını belirten standart dosya (RFC 9116).",
                                "/.well-known/security.txt dosyası oluşturun (Contact: ve Expires: alanlarıyla)."))
    return findings
