# AmanLink — Indonesian Scam Link & Message Checker

Paste a link or a message, get a risk score in seconds. Built for **SLAY HACKS 2026** (Devpost).

## Why

Indonesian students get fake job/internship offers, fake scholarships, and fake prizes over WhatsApp/Telegram every day. The signs repeat (time pressure, URL shorteners, requests for data/OTP/admin fees, informal language), but there is no fast checker in Bahasa Indonesia.

## What it does

- Risk score 0–1 + label (Aman / Waspada / Berbahaya)
- Trigger words/phrases that explain the score (explainability)
- Link analysis: suspicious domains, URL shorteners, risky TLDs
- Action advice: don't click, block, where to report

## How it works

- **Model:** TF-IDF + Logistic Regression (scikit-learn), trained on 114 synthetic Indonesian examples (62 scam across 8 scam categories, 52 legit including 8 official-bank anti-scam warnings as hard negatives).
- **Rule layer:** keyword lists per scam category + URL heuristics (shortener, suspicious TLD, `.apk` files).
- **Evaluation (stratified 80/20, seed 42, test 23):** Accuracy 0.957, Precision 1.000, Recall 0.923, F1 0.960, 0 false positives. All data is synthetic — a real-world test is planned before the final submission.
- **UI:** Streamlit, free deploy on Streamlit Community Cloud.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run the tests

```bash
python -m pytest tests/ -q
```

## License

MIT — see `LICENSE`.
