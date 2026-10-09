from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

from koruma import __version__
from koruma.checks import ALL_CHECKS
from koruma.models import Severity
from koruma.report import to_html, to_json, to_text
from koruma.scanner import scan

BANNER = r"""
  _  __
 | |/ /___  _ __ _   _ _ __ ___   __ _
 | ' // _ \| '__| | | | '_ ` _ \ / _` |
 | . \ (_) | |  | |_| | | | | | | (_| |
 |_|\_\___/|_|   \__,_|_| |_| |_|\__,_|
     Kendi sitenizi tarayın · v%s
""" % __version__

SEV_BY_NAME = {s.name.lower(): s for s in Severity}


def _parse_kv(pairs: list[str]) -> dict[str, str]:
    out = {}
    for p in pairs or []:
        k, _, v = p.partition(":" if ":" in p else "=")
        out[k.strip()] = v.strip()
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="koruma",
        description="Koruma — KENDİ web sitenizdeki yaygın güvenlik açıklarını bulan, yıkıcı olmayan bir tarayıcı.",
        epilog="Yalnızca sahibi olduğunuz veya test etmek için açık izniniz olan siteleri tarayın.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("url", nargs="?", help="Hedef site, örn: https://ornek.com")
    p.add_argument("--checks", help="Virgülle ayrılmış kontrol listesi (vars.: hepsi). Seçenekler: "
                   + ", ".join(ALL_CHECKS))
    p.add_argument("--max-pages", type=int, default=50, help="Taranacak azami sayfa sayısı (vars. 50)")
    p.add_argument("--delay", type=float, default=0.2, help="İstekler arası bekleme, saniye (vars. 0.2)")
    p.add_argument("--timeout", type=float, default=10.0, help="İstek zaman aşımı, saniye (vars. 10)")
    p.add_argument("--insecure", action="store_true", help="TLS sertifika doğrulamasını atla")
    p.add_argument("--test-post-forms", action="store_true",
                   help="POST formlarını da test et (yan etkisi olabilir; dikkatli kullanın)")
    p.add_argument("--header", action="append", metavar="Ad: Değer",
                   help="Ek istek başlığı (ör. kimlik doğrulama için). Birden çok kez verilebilir.")
    p.add_argument("--cookie", action="append", metavar="ad=değer",
                   help="Oturum çerezi (giriş yapılmış alanları taramak için). Birden çok kez verilebilir.")
    p.add_argument("--format", choices=["text", "json", "html"], default="text", help="Çıktı biçimi")
    p.add_argument("-o", "--output", help="Raporu bu dosyaya yaz (vars. ekrana)")
    p.add_argument("--no-color", action="store_true", help="Renkli çıktıyı kapat")
    p.add_argument("--fail-on", choices=[s.name.lower() for s in Severity], default=None,
                   help="Bu önem düzeyi veya üstünde bulgu varsa çıkış kodu 2 döndür (CI için)")
    p.add_argument("-q", "--quiet", action="store_true", help="Tarama ilerleme çıktısını gösterme")
    p.add_argument("-y", "--yes", action="store_true", help="Yetki onayını otomatik kabul et")
    p.add_argument("--progress-json", action="store_true",
                   help="İlerlemeyi stderr'e '@@KORUMA@@{json}' satırları olarak yaz (arayüz için)")
    p.add_argument("--version", action="version", version=f"Koruma {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.url:
        print(BANNER)
        parser.print_help()
        return 0

    url = args.url if "://" in args.url else "https://" + args.url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        print(f"Geçersiz URL: {args.url}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(BANNER, file=sys.stderr)

    # Yetki onayı: aracın yalnızca kendi sitenizde kullanılması içindir.
    if not args.yes:
        print(f"Hedef: {url}")
        print("Bu aracı yalnızca SAHİBİ OLDUĞUNUZ veya test izniniz olan sitelerde kullanın.")
        try:
            ans = input("Bu siteyi taramaya yetkiniz var mı? [e/H] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nİptal edildi.")
            return 1
        if ans not in ("e", "evet", "y", "yes"):
            print("Onay verilmedi; çıkılıyor.")
            return 1

    checks = None
    if args.checks:
        checks = [c.strip() for c in args.checks.split(",") if c.strip()]
        unknown = [c for c in checks if c not in ALL_CHECKS]
        if unknown:
            print(f"Bilinmeyen kontrol(ler): {', '.join(unknown)}", file=sys.stderr)
            print(f"Geçerli kontroller: {', '.join(ALL_CHECKS)}", file=sys.stderr)
            return 1

    # İlerleme bilgisi her zaman stderr'e gider; stdout yalnızca rapor içindir
    # (böylece JSON/HTML çıktısı bozulmaz ve Electron temiz ayrıştırabilir).
    if args.quiet:
        log = lambda *a, **k: None
    elif args.progress_json:
        def log(*a, **k):
            import json as _json
            print("@@KORUMA@@" + _json.dumps({"msg": " ".join(str(x) for x in a)},
                                             ensure_ascii=False), file=sys.stderr, flush=True)
    else:
        def log(*a, **k):
            print(*a, **{**k, "file": sys.stderr, "flush": True})

    try:
        result = scan(
            url, checks=checks, delay=args.delay, timeout=args.timeout,
            max_pages=args.max_pages, verify_tls=not args.insecure,
            test_post_forms=args.test_post_forms,
            headers=_parse_kv(args.header), cookies=_parse_kv(args.cookie), log=log,
        )
    except KeyboardInterrupt:
        print("\nTarama kullanıcı tarafından durduruldu.", file=sys.stderr)
        return 1

    renderer = {"text": lambda r: to_text(r, color=not args.no_color and not args.output),
                "json": to_json, "html": to_html}[args.format]
    report = renderer(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
        if not args.quiet:
            print(f"\nRapor yazıldı: {args.output} ({len(result.findings)} bulgu)")
    else:
        print(report)

    if args.fail_on:
        threshold = SEV_BY_NAME[args.fail_on]
        if any(f.severity >= threshold for f in result.findings):
            return 2
    return 0
