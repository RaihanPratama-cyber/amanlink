"""Evaluasi AmanLink pada dataset sintetis (stratified 80/20, seed 42).

Tiga mode dinilai pada test split yang sama (prediksi scam = label
"Berbahaya", yaitu skor gabungan >= 0.6):
- rule-only: skor rule layer saja
- model-only: probabilitas TF-IDF + Logistic Regression saja
- combined: max(rule, model) — yang dipakai Checker.check()
  (bukan rata-rata: rata-rata terbukti menarik skor model yang kuat
  ke bawah ambang, lihat catatan di checker.py)

Jalankan: python evaluate.py   (butuh scikit-learn)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_seed import CATEGORIES, EXAMPLES
from checker import _rule_score

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
except ImportError:
    print("scikit-learn tidak tersedia — evaluasi model tidak bisa jalan.")
    sys.exit(1)


def metrics(y_true, y_pred):
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 3),
        "precision_scam": round(precision_score(y_true, y_pred, zero_division=0), 3),
        "recall_scam": round(recall_score(y_true, y_pred, zero_division=0), 3),
        "f1_scam": round(f1_score(y_true, y_pred, zero_division=0), 3),
        "tp": int(sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)),
        "fn": int(sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)),
        "fp": int(sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)),
        "tn": int(sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)),
    }


def main():
    texts = [t for t, _ in EXAMPLES]
    labels = [y for _, y in EXAMPLES]
    print(f"Dataset: {len(EXAMPLES)} contoh "
          f"(scam {sum(labels)}, legit {len(labels) - sum(labels)})")
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels)
    print(f"Train {len(X_train)} / test {len(X_test)} "
          f"(test: scam {sum(y_test)}, legit {len(y_test) - sum(y_test)})\n")

    vec = TfidfVectorizer(max_features=500)
    Xtr = vec.fit_transform(X_train)
    model = LogisticRegression(max_iter=1000)
    model.fit(Xtr, y_train)
    classes = list(model.classes_)

    rows = []
    for text, y in zip(X_test, y_test):
        rule, _ = _rule_score(text)
        proba = model.predict_proba(vec.transform([text]))[0]
        m = float(proba[classes.index(1)]) if 1 in classes else 0.0
        rows.append((text, y, rule, m, max(rule, m)))

    for name, get_score in [
        ("rule-only", lambda r: r[2]),
        ("model-only", lambda r: r[3]),
        ("combined", lambda r: r[4]),
    ]:
        pred = [1 if get_score(r) >= 0.6 else 0 for r in rows]
        m = metrics(y_test, pred)
        print(f"{name:10s} acc {m['accuracy']}  prec {m['precision_scam']}  "
              f"rec {m['recall_scam']}  f1 {m['f1_scam']}  "
              f"[[TN {m['tn']}, FP {m['fp']}], [FN {m['fn']}, TP {m['tp']}]]")

    # Per-kategori pada SELURUH dataset (model dilatih ulang di semua data).
    vec_full = TfidfVectorizer(max_features=500)
    model_full = LogisticRegression(max_iter=1000)
    model_full.fit(vec_full.fit_transform(texts), labels)
    print("\nAkurasi per kategori (seluruh dataset, model full-fit):")
    for cat, items in CATEGORIES.items():
        ok = 0
        for text, y in items:
            rule, _ = _rule_score(text)
            proba = model_full.predict_proba(vec_full.transform([text]))[0]
            m = float(proba[classes.index(1)]) if 1 in classes else 0.0
            pred = 1 if max(rule, m) >= 0.6 else 0
            ok += (pred == y)
        print(f"  {cat:22s} {ok}/{len(items)} = {ok / len(items):.2f}")

    print("\nSalah klasifikasi (combined, test split):")
    n_miss = 0
    for text, y, rule, m, comb in rows:
        pred = 1 if comb >= 0.6 else 0
        if pred != y:
            n_miss += 1
            print(f"  [{'scam' if y else 'legit'} -> {'scam' if pred else 'legit'}] "
                  f"rule {rule:.2f} model {m:.2f} comb {comb:.2f} :: {text[:90]}")
    if not n_miss:
        print("  (tidak ada)")


if __name__ == "__main__":
    main()
