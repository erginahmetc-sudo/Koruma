// Önem düzeyleri ve görsel eşlemeleri (Python motoruyla aynı etiketler).
export const SEVERITIES = [
  { key: "KRİTİK", color: "#ef4444", bg: "rgba(239,68,68,.14)", order: 4 },
  { key: "YÜKSEK", color: "#f97316", bg: "rgba(249,115,22,.14)", order: 3 },
  { key: "ORTA", color: "#eab308", bg: "rgba(234,179,8,.14)", order: 2 },
  { key: "DÜŞÜK", color: "#3b82f6", bg: "rgba(59,130,246,.14)", order: 1 },
  { key: "BİLGİ", color: "#94a3b8", bg: "rgba(148,163,184,.14)", order: 0 },
];

export const SEV_META = Object.fromEntries(SEVERITIES.map((s) => [s.key, s]));

// Kullanılabilir kontroller ve açıklamaları.
export const CHECKS = [
  { id: "headers", label: "Güvenlik Başlıkları", desc: "CSP, X-Frame-Options, HSTS ve sürüm sızıntısı" },
  { id: "tls", label: "TLS / HTTPS", desc: "Sertifika, HSTS, HTTP→HTTPS, eski protokoller" },
  { id: "cookies", label: "Çerezler", desc: "Secure, HttpOnly, SameSite bayrakları" },
  { id: "files", label: "Açık Dosyalar", desc: ".git, .env, yedekler, dizin listeleme" },
  { id: "cors", label: "CORS", desc: "Aşırı gevşek köken (origin) politikaları" },
  { id: "methods", label: "HTTP Metotları", desc: "Riskli metotlar, TRACE" },
  { id: "disclosure", label: "Bilgi Sızıntısı", desc: "API anahtarı, stack trace, iç IP, yorumlar" },
  { id: "injection", label: "Enjeksiyon", desc: "XSS, SQL, SSTI, dizin geçişi, CSRF" },
  { id: "redirect", label: "Açık Yönlendirme", desc: "Doğrulanmamış yönlendirme hedefleri" },
  { id: "fingerprint", label: "Teknoloji Tespiti", desc: "Sunucu, çerçeve, CMS ve sürüm ifşası" },
  { id: "components", label: "Savunmasız Bileşenler", desc: "Bilinen CVE'li JS kütüphaneleri + SRI (OWASP A06)" },
  { id: "endpoints", label: "Açık Uç Noktalar", desc: "GraphQL, API/yönetim panelleri, WordPress sayımı" },
  { id: "advanced", label: "Gelişmiş Enjeksiyon", desc: "CRLF, Host başlığı enjeksiyonu, önbellek" },
  { id: "dns_email", label: "DNS & E-posta", desc: "SPF, DMARC, DKIM, CAA, DNSSEC" },
  { id: "access", label: "Erişim Kontrolü", desc: "Forced browsing, IDOR, oturum karşılaştırması (OWASP A01)" },
];
