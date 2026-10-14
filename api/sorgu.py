from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "kayitlar.json")
_CACHE = None

# ==================== API KEY ====================
ADMIN_KEY = "YxceBerkk-Azeri-Gizli-2026"

# İstatistik ve admin endpoint'leri için gerekli


def db_yukle():
    global _CACHE
    if _CACHE is None:
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                _CACHE = json.load(f)
        except Exception:
            _CACHE = []
    return _CACHE


def db_sorgula(tc=None, numara=None, ad=None, soyad=None):
    kayitlar = db_yukle()
    sonuclar = []
    for k in kayitlar:
        eslesme = True
        if tc and str(k.get("tc", "")).strip() != str(tc).strip():
            eslesme = False
        if numara and eslesme:
            kt = str(k.get("telefon", "")).replace(" ", "").replace("-", "").replace("+", "")
            ar = str(numara).replace(" ", "").replace("-", "").replace("+", "")
            if ar.startswith("90"):
                ar = ar[2:]
            if ar.startswith("0"):
                ar = ar[1:]
            if not kt.endswith(ar):
                eslesme = False
        if ad and eslesme:
            if str(ad).lower().strip() not in str(k.get("ad", "")).lower():
                eslesme = False
        if soyad and eslesme:
            if str(soyad).lower().strip() not in str(k.get("soyad", "")).lower():
                eslesme = False
        if eslesme:
            sonuclar.append(k)
            if len(sonuclar) >= 100:
                break
    return sonuclar


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        yol = parsed.path
        params = parse_qs(parsed.query)

        def p(k):
            v = params.get(k, [None])[0]
            return v.strip() if v else None

        def js(veri, kod=200):
            body = json.dumps(veri, ensure_ascii=False).encode("utf-8")
            self.send_response(kod)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # ==================== İSTATİSTİK (ADMIN) ====================
        if yol == "/istatistik":
            key = p("key") or self.headers.get("X-API-Key", "")
            if key != ADMIN_KEY:
                js({
                    "_imza": "YxceBerkkAzeriApi",
                    "hata": "Yetkisiz erişim",
                    "kod": 403
                }, 403)
                return

            kayitlar = db_yukle()
            js({
                "_imza": "YxceBerkkAzeriApi",
                "toplam_kayit": len(kayitlar),
                "admin": True
            })
            return

        # ==================== ADMIN: TÜM VERİ ====================
        if yol == "/admin/tum":
            key = p("key") or self.headers.get("X-API-Key", "")
            if key != ADMIN_KEY:
                js({"_imza": "YxceBerkkAzeriApi", "hata": "Yetkisiz"}, 403)
                return

            kayitlar = db_yukle()
            limit = p("limit")
            try:
                limit_int = int(limit) if limit else 100
            except:
                limit_int = 100

            js({
                "_imza": "YxceBerkkAzeriApi",
                "toplam": len(kayitlar),
                "gosterilen": min(limit_int, len(kayitlar)),
                "kayitlar": kayitlar[:limit_int]
            })
            return

        # ==================== İSTATİSTİK DETAY ====================
        if yol == "/admin/istatistik":
            key = p("key") or self.headers.get("X-API-Key", "")
            if key != ADMIN_KEY:
                js({"_imza": "YxceBerkkAzeriApi", "hata": "Yetkisiz"}, 403)
                return

            kayitlar = db_yukle()

            # Cinsiyet dağılımı
            cinsiyet = {}
            medeni = {}
            dogum_yeri = {}

            for k in kayitlar:
                c = k.get("cinsiyet", "bilinmiyor") or "bilinmiyor"
                cinsiyet[c] = cinsiyet.get(c, 0) + 1

                m = k.get("medeni", "bilinmiyor") or "bilinmiyor"
                medeni[m] = medeni.get(m, 0) + 1

                dy = k.get("dogum_yeri", "bilinmiyor") or "bilinmiyor"
                dogum_yeri[dy] = dogum_yeri.get(dy, 0) + 1

            js({
                "_imza": "YxceBerkkAzeriApi",
                "toplam_kayit": len(kayitlar),
                "cinsiyet": cinsiyet,
                "medeni": medeni,
                "dogum_yeri_top10": sorted(dogum_yeri.items(), key=lambda x: -x[1])[:10]
            })
            return

        # ==================== PUBLIC SORGU ====================
        if yol in ("/", "/api/sorgu", "/sorgu"):
            tc = p("tc")
            numara = p("numara")
            ad = p("ad")
            soyad = p("soyad")

            # Sorgu yoksa → bilgi ver, ama sadece public endpoint'i söyle
            if not any([tc, numara, ad, soyad]):
                js({
                    "_imza": "YxceBerkkAzeriApi",
                    "mesaj": "Azeri Sorgu API calisiyor",
                    "toplam_kayit": len(db_yukle()),
                    "kullanim": {
                        "tc": "/api/sorgu?tc=100028349722094",
                        "numara": "/api/sorgu?numara=994552014875",
                        "adsoyad": "/api/sorgu?ad=Milosh&soyad=Forman",
                        "ad": "/api/sorgu?ad=Gunel"
                    }
                })
                return

            sonuclar = db_sorgula(tc=tc, numara=numara, ad=ad, soyad=soyad)
            js({
                "_imza": "YxceBerkkAzeriApi",
                "toplam": len(sonuclar),
                "sonuclar": sonuclar
            })
            return

        # ==================== 404 ====================
        js({
            "_imza": "YxceBerkkAzeriApi",
            "hata": "Endpoint bulunamadi",
            "public_endpointler": ["/api/sorgu?tc=...", "/api/sorgu?ad=...", "/api/sorgu?numara=..."]
        }, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
