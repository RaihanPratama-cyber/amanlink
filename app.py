"""AmanLink — Streamlit app skeleton (jalankan: streamlit run app.py)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import streamlit as st
except ImportError:
    st = None

from checker import Checker

def main():
    if st is None:
        print("Streamlit belum terinstal. Jalankan: pip install -r requirements.txt")
        return
    st.set_page_config(page_title="AmanLink — Cek Penipuan", page_icon="🛡️")
    st.title("🛡️ AmanLink")
    st.write("Tempel tautan atau isi pesan berbahasa Indonesia untuk memeriksa risiko penipuan.")
    checker = Checker()
    text = st.text_area("Tautan / isi pesan", height=150,
                        placeholder="Contoh: Selamat! Anda terpilih mendapat hadiah, klik link ini segera")
    if st.button("Cek Sekarang"):
        if not text.strip():
            st.warning("Masukkan tautan atau pesan dulu.")
        else:
            r = checker.check(text)
            st.metric("Skor Risiko", f"{r['score']:.2f}", r["label"])
            if r["triggers"]:
                st.write("**Kata pemicu:** " + ", ".join(r["triggers"]))
            st.info(r["advice"])

if __name__ == "__main__":
    main()
