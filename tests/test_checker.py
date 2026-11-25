"""Tes lokal AmanLink checker (stdlib saja; model sklearn opsional)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from checker import Checker

def test_scam_message_scores_high():
    r = Checker().check("Selamat! Anda terpilih mendapat hadiah Rp5.000.000, klik link ini segera sebelum hangus")
    assert r["score"] >= 0.6 and r["label"] == "Berbahaya", r

def test_legit_message_scores_low():
    r = Checker().check("Jadwal kuliah besok: Pemrograman Jaringan jam 08.00 di lab 3, bawa laptop")
    assert r["score"] < 0.35 and r["label"] == "Aman", r

def test_otp_phishing_flagged():
    r = Checker().check("Akun Anda akan diblokir hari ini, verifikasi OTP Anda di link berikut segera")
    assert r["score"] >= 0.6, r
    assert any("otp" in t for t in r["triggers"])

def test_shortened_url_adds_risk():
    r = Checker().check("Info resmi kampus di https://bit.ly/contoh-palsu segera")
    assert r["score"] > 0.2, r

def test_result_has_advice():
    r = Checker().check("Halo, apa kabar?")
    assert r["advice"] and r["label"] in ("Aman", "Waspada", "Berbahaya")

def test_dataset_has_100_plus_examples():
    from data_seed import EXAMPLES, CATEGORIES
    assert len(EXAMPLES) >= 100, len(EXAMPLES)
    assert len(set(t for t, _ in EXAMPLES)) == len(EXAMPLES), "ada contoh duplikat"
    scam = sum(1 for _, y in EXAMPLES if y == 1)
    legit = sum(1 for _, y in EXAMPLES if y == 0)
    assert scam >= 50 and legit >= 40, (scam, legit)
    assert len(CATEGORIES) >= 10, len(CATEGORIES)

def test_bank_warning_not_flagged_as_scam():
    r = Checker().check("Peringatan dari Bank: jangan pernah berikan kode OTP atau password kepada siapa pun, termasuk yang mengaku petugas bank")
    assert r["label"] != "Berbahaya" and r["score"] < 0.6, r

def test_family_emergency_scam_flagged():
    # Kategori keluarga-darurat tanpa tautan/OTP mengandalkan model:
    # rule layer menaikannya dari Aman ke Waspada, model yang menangkapnya.
    r = Checker().check("Nak, mama di rumah sakit, kirim uang 2 juta untuk biaya obat, cepat ya")
    assert r["score"] >= 0.35 and r["label"] in ("Waspada", "Berbahaya"), r
    if r["model_score"] is not None:
        assert r["model_score"] >= 0.6, r

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"{len(tests)}/{len(tests)} tes lolos")
