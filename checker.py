"""AmanLink checker: skor risiko tautan/pesan penipuan berbahasa Indonesia.

Dua lapis:
1. Rule layer (selalu jalan, tanpa dependensi): frasa urgensi, OTP/biaya,
   tautan pemendek, TLD berisiko. Menghasilkan skor 0-1 + kata pemicu.
2. Model TF-IDF + Logistic Regression (bila scikit-learn tersedia):
   dilatih dari data_seed.EXAMPLES; skor digabung dengan rule layer
   memakai max (lapisan yang paling yakin yang menang). Alasannya
   terukur: pada evaluasi 25 Nov 2026, rata-rata (rule+model)/2 memberi
   akurasi 0,435 / recall 0,000 di test split karena rule layer yang
   lemah menarik skor model yang kuat (model-only: akurasi 0,913 /
   recall 0,846) ke bawah ambang 0,6 — lihat evaluate.py.
   Bila sklearn tidak ada, hanya rule layer yang dipakai (ditandai di hasil).
"""
import re

SCAM_PHRASES = {
    "klik link ini": 0.25, "segera": 0.10, "sebelum hangus": 0.15,
    "biaya admin": 0.25, "bayar": 0.15, "otp": 0.30, "password": 0.20,
    "terpilih mendapat hadiah": 0.25, "menang undian": 0.25,
    "tanpa pengalaman": 0.15, "gaji 15 juta": 0.15, "profit 200%": 0.25,
    "dijamin aman": 0.10, "klaim hadiah": 0.20, "verifikasi": 0.10,
    "akun anda akan diblokir": 0.25, "kirim ktp": 0.20, "tanpa jaminan": 0.15,
    "kirim uang": 0.25, "kirim pulsa": 0.20, "ditahan polisi": 0.25,
    "uang jaminan": 0.20, "biaya operasi": 0.15, "transfer sekarang": 0.15,
    "transfer ke rekening ini": 0.25,
    "apk": 0.25, "unduh aplikasi": 0.15, "memenangkan": 0.15,
    "cair": 0.10, "biaya obat": 0.15,
}
SHORTENERS = ("bit.ly", "tinyurl", "s.id", "t.co", "goo.gl", "cutt.ly", "shorturl")
RISKY_TLDS = (".xyz", ".top", ".click", ".buzz", ".online", ".site")

# Frasa peringatan anti-scam (pesan legit yang memperingatkan soal penipuan).
# Pesan seperti ini mengandung kata "otp"/"password" tapi justru MELAWAN scam,
# jadi skor rule dikurangi — pelajaran yang sama dari PesanAman (GenHacks).
WARNING_PHRASES = (
    "jangan pernah", "jangan berikan", "jangan bagikan", "jangan klik",
    "waspada", "hati-hati", "peringatan", "kenali ciri penipuan",
    "tidak pernah meminta", "jangan kirim",
)

URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)


def _rule_score(text):
    low = text.lower()
    score = 0.0
    triggers = []
    for phrase, w in SCAM_PHRASES.items():
        if phrase in low:
            score += w
            triggers.append(phrase)
    if any(p in low for p in WARNING_PHRASES):
        score -= 0.20
        triggers.append("frasa peringatan anti-scam (-0.20)")
    for url in URL_RE.findall(text):
        u = url.lower()
        if any(s in u for s in SHORTENERS):
            score += 0.20
            triggers.append(f"tautan pemendek: {url}")
        if any(u.endswith(t) or (t + "/") in u or (t + "?") in u for t in RISKY_TLDS):
            score += 0.15
            triggers.append(f"TLD berisiko: {url}")
    return max(min(score, 1.0), 0.0), triggers


class Checker:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from data_seed import EXAMPLES
            texts = [t for t, _ in EXAMPLES]
            labels = [y for _, y in EXAMPLES]
            self.vectorizer = TfidfVectorizer(max_features=500)
            X = self.vectorizer.fit_transform(texts)
            self.model = LogisticRegression(max_iter=1000)
            self.model.fit(X, labels)
        except Exception:
            self.model = None  # fallback: rule layer saja

    def check(self, text):
        rule_score, triggers = _rule_score(text)
        model_score = None
        if self.model is not None:
            proba = self.model.predict_proba(
                self.vectorizer.transform([text]))[0]
            classes = list(self.model.classes_)
            model_score = float(proba[classes.index(1)]) if 1 in classes else 0.0
            score = round(max(rule_score, model_score), 3)
        else:
            score = round(rule_score, 3)
        label = "Berbahaya" if score >= 0.6 else ("Waspada" if score >= 0.35 else "Aman")
        advice = (
            "Jangan klik tautan, jangan kirim OTP/password/data pribadi, blokir dan laporkan pengirim."
            if label == "Berbahaya" else
            "Periksa sumber resmi sebelum mengikuti instruksi di pesan ini."
            if label == "Waspada" else
            "Tidak ada tanda penipuan yang terdeteksi, tetap waspada terhadap tautan asing."
        )
        return {"score": score, "label": label, "triggers": triggers,
                "model_score": model_score, "advice": advice}


def check(text):
    return Checker().check(text)
