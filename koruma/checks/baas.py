"""Backend-as-a-Service ve bulut yanlış yapılandırmaları.

Modern uygulamalarda en yüksek etkili açıkların bulunduğu yer: Supabase,
Firebase ve açık bulut depolama. Site içeriğinden keşfedilen backend uç
noktaları (yani sizin kendi backend'iniz) salt-okunur isteklerle test edilir.

- Supabase: istemciye sızmış service_role anahtarı (KRİTİK), RLS kapalı
  tablolardan veri okunabilmesi (anon anahtarıyla).
- Firebase: herkese açık Realtime Database (.json okunabiliyor).
- Bulut depolama: herkese listelenebilen S3/GCS bucket'ları.

Not: Bu kontrol, sitenizin JS/HTML'inde REFERANS VERİLEN backend'leri test
eder; rastgele hedeflere istek atmaz.
"""
from __future__ import annotations

import base64
import json
import re

from koruma.models import Finding, Severity
from koruma.sitedata import collect

NAME = "baas"

SUPABASE_URL = re.compile(r"https://([a-z0-9]{20})\.supabase\.(?:co|in)")
JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
SB_SECRET = re.compile(r"\bsb_secret_[A-Za-z0-9_-]{20,}\b")
FIREBASE_DB = re.compile(r"https://([a-z0-9-]+(?:-default-rtdb)?)\.(?:firebaseio\.com|[a-z0-9-]+\.firebasedatabase\.app)")
S3_BUCKET = re.compile(r"https?://([a-z0-9][a-z0-9.-]{1,61})\.s3[.-][a-z0-9-]*\.?amazonaws\.com|https?://s3[.-][a-z0-9-]*\.amazonaws\.com/([a-z0-9][a-z0-9.-]{1,61})")
GCS_BUCKET = re.compile(r"https?://storage\.googleapis\.com/([a-z0-9][a-z0-9._-]{1,61})")


def _requests():
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = "Koruma güvenlik tarayıcısı"
    return s


def _jwt_role(token: str):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("role")
    except Exception:
        return None


def _check_supabase(text, sess, timeout) -> list[Finding]:
    findings = []
    projects = set(SUPABASE_URL.findall(text))
    if not projects:
        return findings

    # service_role / sb_secret anahtarı sızıntısı (her zaman kritik)
    anon_keys = []
    for tok in set(JWT.findall(text)):
        role = _jwt_role(tok)
        if role == "service_role":
            findings.append(Finding(NAME, "Supabase service_role anahtarı istemciye sızmış", Severity.CRITICAL,
                "frontend", "service_role anahtarı RLS'i tamamen atlar ve TÜM verilere tam erişim verir. "
                "İstemci koduna gömülmüş olması, herkesin veritabanınızı okuyup yazabileceği anlamına gelir.",
                "Anahtarı DERHAL Supabase panelinden iptal edip döndürün; service_role'u asla istemcide kullanmayın.",
                tok[:12] + "…(role=service_role)"))
        elif role == "anon":
            anon_keys.append(tok)
    for sec in set(SB_SECRET.findall(text)):
        findings.append(Finding(NAME, "Supabase gizli anahtarı (sb_secret) istemciye sızmış", Severity.CRITICAL,
            "frontend", "sb_secret anahtarı yönetici düzeyinde erişim verir ve istemcide asla bulunmamalıdır.",
            "Anahtarı derhal döndürün.", sec[:16] + "…"))

    anon = anon_keys[0] if anon_keys else None
    for ref in projects:
        base = f"https://{ref}.supabase.co"
        if not anon:
            findings.append(Finding(NAME, "Supabase projesi tespit edildi (anon anahtarı görülmedi)", Severity.INFO,
                base, "Site bir Supabase backend'i kullanıyor. RLS politikalarının tüm tablolarda etkin "
                "olduğundan emin olun.", "Supabase panelinde Security Advisor uyarılarını gözden geçirin."))
            continue
        headers = {"apikey": anon, "Authorization": f"Bearer {anon}"}
        # OpenAPI kökünden tabloları listele
        tables = []
        try:
            r = sess.get(f"{base}/rest/v1/", headers=headers, timeout=timeout)
            if r.status_code == 200:
                spec = r.json()
                tables = list((spec.get("definitions") or spec.get("components", {}).get("schemas") or {}).keys())
        except Exception:
            pass
        exposed = []
        for tbl in tables[:8]:
            try:
                rr = sess.get(f"{base}/rest/v1/{tbl}", headers=headers,
                              params={"select": "*", "limit": "1"}, timeout=timeout)
                if rr.status_code == 200 and isinstance(rr.json(), list) and rr.json():
                    exposed.append(tbl)
            except Exception:
                continue
        if exposed:
            findings.append(Finding(NAME, "Supabase: RLS kapalı tablolardan veri okunabiliyor", Severity.CRITICAL,
                f"{base}/rest/v1/", "Yalnızca herkese açık anon anahtarı kullanılarak şu tablolardan satır "
                f"okunabildi: {', '.join(exposed)}. Bu, Row Level Security'nin kapalı olduğunu ve verilerin "
                "herkese açık olduğunu gösterir (Supabase 'rls_disabled_in_public' uyarısı).",
                "İlgili tablolarda RLS'i etkinleştirin ve uygun politikalar (policy) tanımlayın; "
                "'USING (true)' gibi izin veren politikalardan kaçının.",
                f"anon ile {len(exposed)} tablo okundu: {', '.join(exposed[:5])}"))
        elif tables:
            findings.append(Finding(NAME, "Supabase REST API tablo adlarını listeliyor", Severity.LOW,
                f"{base}/rest/v1/", f"anon anahtarıyla şema okunabiliyor ({len(tables)} tablo adı). Satır "
                "okunamadı (RLS muhtemelen etkin) ama tablo adları ifşa oluyor.",
                "Gerekmiyorsa şema ifşasını kısıtlayın; RLS politikalarını doğrulayın.",
                f"tablolar: {', '.join(tables[:8])}"))
    return findings


def _check_firebase(text, sess, timeout) -> list[Finding]:
    findings = []
    seen = set()
    for m in FIREBASE_DB.finditer(text):
        dburl = m.group(0)
        if dburl in seen:
            continue
        seen.add(dburl)
        try:
            r = sess.get(dburl.rstrip("/") + "/.json", params={"shallow": "true"}, timeout=timeout)
        except Exception:
            continue
        body = (r.text or "").strip()
        if r.status_code == 200 and "permission denied" not in body.lower():
            sev = Severity.CRITICAL if body not in ("null", "") else Severity.HIGH
            detail = "veri döndü" if body not in ("null", "") else "boş ama erişime açık"
            findings.append(Finding(NAME, "Firebase Realtime Database herkese açık (okunabilir)", sev, dburl,
                f"Veritabanı kök dizini kimlik doğrulaması olmadan okunabiliyor ({detail}). Firebase güvenlik "
                "kuralları yetkisiz okumaya izin veriyor.",
                "Firebase güvenlik kurallarını '.read'/'.write' için kimlik doğrulaması gerektirecek şekilde "
                "sıkılaştırın (varsayılan: auth != null).",
                f"GET {dburl}/.json?shallow=true -> HTTP {r.status_code}"))
    return findings


def _check_storage(text, sess, timeout) -> list[Finding]:
    findings = []
    buckets = set()
    for m in S3_BUCKET.finditer(text):
        name = m.group(1) or m.group(2)
        if name:
            buckets.add(("s3", name, f"https://{name}.s3.amazonaws.com/"))
    for name in set(GCS_BUCKET.findall(text)):
        buckets.add(("gcs", name, f"https://storage.googleapis.com/{name}"))

    for kind, name, url in list(buckets)[:8]:
        try:
            if kind == "s3":
                r = sess.get(f"https://{name}.s3.amazonaws.com/", params={"list-type": "2", "max-keys": "1"}, timeout=timeout)
            else:
                r = sess.get(f"https://storage.googleapis.com/{name}", params={"max-keys": "1"}, timeout=timeout)
        except Exception:
            continue
        if r.status_code == 200 and ("<ListBucketResult" in r.text or "<Contents>" in r.text or "<Key>" in r.text):
            findings.append(Finding(NAME, f"Herkese açık/listelenebilir bulut bucket: {name}", Severity.HIGH, url,
                f"{kind.upper()} bucket'ı kimlik doğrulaması olmadan listelenebiliyor; içindeki dosyalar "
                "herkese açık olabilir.",
                "Bucket'ı özel yapın; genel listelemeyi kapatın ve yalnızca gereken nesnelere erişim verin.",
                f"liste isteği HTTP 200 (ListBucketResult)"))
    return findings


def run(ctx) -> list[Finding]:
    data = collect(ctx)
    text = data.combined
    sess = _requests()
    timeout = ctx.client.timeout
    findings = []
    findings += _check_supabase(text, sess, timeout)
    findings += _check_firebase(text, sess, timeout)
    findings += _check_storage(text, sess, timeout)
    return findings
