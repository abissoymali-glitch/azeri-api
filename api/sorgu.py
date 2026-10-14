from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os

# azeri.txt yolu (repo kökünde)
TXT_PATH = os.path.join(os.path.dirname(__file__), "..", "azeri.txt")
_CACHE = None

# ==================== API KEY ====================
ADMIN_KEY = "YxceBerkk-Azeri-Gizli-2026"


def txt_yukle():
    """azeri.txt dosyasını okur, kayıt listesi döner."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    kayitlar = []
    try:
        with open(TXT_PATH, "r", encoding="utf-8", errors="replace") as f:
            for satir in f:
                satir = satir.strip()
                if not satir:
                    continue
                parcalar = satir.split(":")
                if len(parcalar) < 5:
                    continue

                kayit = {
                    "telefon": parcalar[0].strip(),
                    "tc": parcalar[1].strip(),
                    "ad": parcalar[2].strip(),
                    "soyad": parcalar[3].strip(),
                    "cinsiyet": parcalar[4].strip() if len(parcalar) > 4 else "",
                    "dogum_yeri": parcalar[5].strip() if len(parcalar) > 5 else "",
                    "medeni": parcalar[7].strip() if len(parcalar) > 7 else "",
                    "dogum_tarihi": parcalar[8].strip() if len(parcalar) > 8 else "",
                }
                kayitlar.append(kayit)
    except Exception as e:
        print(f"TXT okuma hatası: {e}")

    _CACHE = kayitlar
    return kayitlar


def db_sorgula(tc=None, numara=None, ad=None, soyad=None, limit=100):
    kayitlar = txt_yukle()
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
            if len(sonuclar) >= limit:
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

        # İSTATİSTİK (ADMIN)
        if yol == "/istatistik":
            key = p("key") or self.headers.get("X-API-Key", "")
            if key != ADMIN_KEY:
                js({"_imza": "YxceBerkkAzeriApi", "hata": "Yetkisiz"}, 403)
                return
            kayitlar = txt_yukle()
            js({
                "_imza": "YxceBerkkAzeriApi",
                "toplam_kayit": len(kayitlar),
                "admin": True
            })
            return

        # ADMIN: TÜM VERİ
        if yol == "/admin/tum":
            key = p("key") or self.headers.get("X-API-Key", "")
            if key != ADMIN_KEY:
                js({"_imza": "YxceBerkkAzeriApi", "hata": "Yetkisiz"}, 403)
                return
            kayitlar = txt_yukle()
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

        # PUBLIC SORGU
        if yol in ("/", "/api/sorgu", "/sorgu"):
            tc = p("tc")
            numara = p("numara")
            ad = p("ad")
            soyad = p("soyad")

            if not any([tc, numara, ad, soyad]):
                kayitlar = txt_yukle()
                js({
                    "_imza": "YxceBerkkAzeriApi",
                    "mesaj": "Azeri Sorgu API calisiyor",
                    "toplam_kayit": len(kayitlar),
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

        js({"_imza": "YxceBerkkAzeriApi", "hata": "Endpoint yok"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
