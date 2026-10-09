from __future__ import annotations

import uuid
from urllib.parse import urljoin

from koruma.models import Finding, Severity

NAME = "files"

# (yol, önem, açıklama, içerikte aranacak işaret veya None)
SENSITIVE_PATHS = [
    (".git/HEAD", Severity.CRITICAL, "Git deposu herkese açık; tüm kaynak kod indirilebilir.", "ref:"),
    (".git/config", Severity.CRITICAL, "Git yapılandırması herkese açık.", "[core]"),
    (".svn/entries", Severity.HIGH, "SVN meta verileri herkese açık.", None),
    (".hg/hgrc", Severity.HIGH, "Mercurial deposu herkese açık.", None),
    (".env", Severity.CRITICAL, "Ortam dosyası açık; parolalar ve API anahtarları sızabilir.", "="),
    (".env.local", Severity.CRITICAL, "Ortam dosyası açık.", "="),
    (".env.production", Severity.CRITICAL, "Ortam dosyası açık.", "="),
    ("config.php.bak", Severity.CRITICAL, "Yapılandırma yedeği açık.", "<?php"),
    ("wp-config.php.bak", Severity.CRITICAL, "WordPress yapılandırma yedeği açık.", "DB_PASSWORD"),
    ("wp-config.php~", Severity.CRITICAL, "WordPress yapılandırma yedeği açık.", "DB_PASSWORD"),
    ("wp-config.php.save", Severity.CRITICAL, "WordPress yapılandırma yedeği açık.", "DB_PASSWORD"),
    ("config.json", Severity.MEDIUM, "Yapılandırma dosyası açık olabilir.", "{"),
    ("backup.zip", Severity.HIGH, "Yedek arşivi indirilebilir.", None),
    ("backup.sql", Severity.CRITICAL, "Veritabanı dökümü indirilebilir.", "INSERT"),
    ("dump.sql", Severity.CRITICAL, "Veritabanı dökümü indirilebilir.", "INSERT"),
    ("database.sql", Severity.CRITICAL, "Veritabanı dökümü indirilebilir.", "INSERT"),
    ("db.sqlite", Severity.CRITICAL, "SQLite veritabanı indirilebilir.", "SQLite format"),
    ("phpinfo.php", Severity.MEDIUM, "phpinfo() sunucu yapılandırmasını ifşa ediyor.", "PHP Version"),
    ("info.php", Severity.MEDIUM, "phpinfo() sunucu yapılandırmasını ifşa ediyor.", "PHP Version"),
    ("server-status", Severity.MEDIUM, "Apache server-status sayfası açık.", "Apache Server Status"),
    ("server-info", Severity.MEDIUM, "Apache server-info sayfası açık.", "Apache Server Information"),
    (".DS_Store", Severity.LOW, "macOS dizin meta dosyası dosya adlarını ifşa eder.", None),
    (".htaccess", Severity.LOW, ".htaccess dosyası okunabiliyor.", None),
    (".htpasswd", Severity.HIGH, "Parola özetleri içeren .htpasswd dosyası okunabiliyor.", ":"),
    ("composer.lock", Severity.LOW, "Bağımlılık sürümleri ifşa oluyor.", "packages"),
    ("package.json", Severity.LOW, "Bağımlılık listesi ifşa oluyor.", "dependencies"),
    ("docker-compose.yml", Severity.MEDIUM, "Docker yapılandırması açık.", "services"),
    ("Dockerfile", Severity.LOW, "Dockerfile açık.", "FROM"),
    ("id_rsa", Severity.CRITICAL, "Özel SSH anahtarı açık!", "PRIVATE KEY"),
    ("error_log", Severity.MEDIUM, "Hata günlüğü açık.", None),
    ("debug.log", Severity.MEDIUM, "Hata ayıklama günlüğü açık.", None),
    ("wp-content/debug.log", Severity.MEDIUM, "WordPress hata günlüğü açık.", None),
    ("storage/logs/laravel.log", Severity.HIGH, "Laravel günlüğü açık.", None),
    ("actuator/env", Severity.HIGH, "Spring Boot actuator ortam değişkenlerini ifşa ediyor.", "propertySources"),
    ("actuator/heapdump", Severity.CRITICAL, "Spring Boot bellek dökümü indirilebilir.", None),
    ("swagger.json", Severity.INFO, "API dokümantasyonu herkese açık.", "swagger"),
    ("openapi.json", Severity.INFO, "API dokümantasyonu herkese açık.", "openapi"),
    ("phpmyadmin/", Severity.MEDIUM, "phpMyAdmin paneli herkese açık.", "phpMyAdmin"),
    ("adminer.php", Severity.HIGH, "Adminer veritabanı paneli herkese açık.", "Adminer"),
    # SecLists (danielmiessler) quickhits'ten türetilmiş yüksek-sinyalli yollar
    (".ssh/id_rsa", Severity.CRITICAL, "Özel SSH anahtarı açık!", "PRIVATE KEY"),
    (".ssh/id_ed25519", Severity.CRITICAL, "Özel SSH anahtarı açık!", "PRIVATE KEY"),
    (".ssh/authorized_keys", Severity.HIGH, "SSH authorized_keys açık.", "ssh-"),
    (".npmrc", Severity.HIGH, ".npmrc kayıtlı token içerebilir.", "_authToken"),
    (".netrc", Severity.HIGH, ".netrc kimlik bilgileri içerir.", "machine"),
    (".ftppass", Severity.HIGH, "FTP parola dosyası açık.", None),
    ("sftp-config.json", Severity.HIGH, "SFTP yapılandırması (parola içerebilir) açık.", "host"),
    (".remote-sync.json", Severity.HIGH, "Uzak senkron yapılandırması açık.", "host"),
    (".bash_history", Severity.MEDIUM, "Kabuk komut geçmişi açık.", None),
    (".mysql_history", Severity.MEDIUM, "MySQL komut geçmişi açık.", None),
    (".gitlab-ci.yml", Severity.LOW, "CI/CD yapılandırması açık (sır içerebilir).", None),
    (".travis.yml", Severity.LOW, "CI yapılandırması açık.", None),
    ("web.config", Severity.MEDIUM, "IIS web.config açık.", "<configuration"),
    ("web.config.bak", Severity.HIGH, "IIS web.config yedeği açık.", "<configuration"),
    ("settings.py", Severity.HIGH, "Django settings.py açık (SECRET_KEY içerebilir).", "SECRET_KEY"),
    ("config/database.yml", Severity.CRITICAL, "Rails veritabanı yapılandırması açık.", "password"),
    ("config/aws.yml", Severity.CRITICAL, "AWS yapılandırması açık.", None),
    ("app/etc/local.xml", Severity.CRITICAL, "Magento yapılandırması (DB parolası) açık.", "<config"),
    ("app/config/parameters.yml", Severity.CRITICAL, "Symfony parametreleri açık.", "parameters"),
    ("configuration.php.bak", Severity.CRITICAL, "Joomla yapılandırma yedeği açık.", "JConfig"),
    ("wp-config.php.old", Severity.CRITICAL, "WordPress yapılandırma yedeği açık.", "DB_PASSWORD"),
    ("actuator/heapdump", Severity.CRITICAL, "Spring Boot bellek dökümü indirilebilir.", None),
    ("actuator/threaddump", Severity.MEDIUM, "Spring Boot thread dökümü açık.", "threads"),
    ("actuator/configprops", Severity.MEDIUM, "Spring Boot yapılandırma özellikleri açık.", None),
    ("actuator/mappings", Severity.LOW, "Spring Boot endpoint eşlemeleri açık.", None),
    ("jolokia", Severity.HIGH, "Jolokia JMX arayüzü açık.", None),
    (".DS_Store", Severity.LOW, "macOS dizin meta dosyası dosya adlarını ifşa eder.", None),
]

LISTING_MARKERS = ("Index of /", "<title>Directory listing", "Parent Directory</a>", "[To Parent Directory]")


def _soft404_signature(ctx):
    """Var olmayan bir sayfaya verilen yanıtı öğren (her şeye 200 dönen siteler için)."""
    r = ctx.client.get(urljoin(ctx.base_url, f"/{uuid.uuid4().hex}.txt"))
    if r is None or r.status_code != 200:
        return None
    return len(r.content)


def _looks_soft404(size: int, sig) -> bool:
    if sig is None:
        return False
    return abs(size - sig) <= max(50, sig * 0.05)


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    root = urljoin(ctx.base_url, "/")
    sig = _soft404_signature(ctx)

    for path, sev, desc, marker in SENSITIVE_PATHS:
        url = urljoin(root, path)
        r = ctx.client.get(url, allow_redirects=False, stream=True)
        if r is None or r.status_code != 200:
            continue
        # Büyük dosyaları tamamen indirmeyelim
        chunk = next(r.iter_content(65536), b"")
        r.close()
        text = chunk.decode("utf-8", errors="replace")
        if "html" in r.headers.get("Content-Type", "") and marker is None:
            continue
        if marker is not None and marker not in text:
            continue
        if marker is None and _looks_soft404(len(chunk), sig):
            continue
        findings.append(Finding(NAME, f"Hassas dosya erişilebilir: /{path}", sev, url, desc,
                                "Dosyayı web kök dizininden kaldırın veya sunucu yapılandırmasıyla erişimi engelleyin.",
                                text[:120].replace("\n", "\\n")))

    # Dizin listeleme
    dirs = {root}
    for p in ctx.crawl.pages:
        base = p.url.rsplit("/", 1)[0] + "/"
        dirs.add(base)
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
