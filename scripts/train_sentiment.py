"""NSMC 샘플로 리뷰 감성 분석 모델 학습

    python scripts/train_sentiment.py
"""
import argparse
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=ROOT / "data" / "nsmc_sample.csv")
    parser.add_argument("--out", default=ROOT / "models" / "sentiment.joblib")
    args = parser.parse_args()

    df = pd.read_csv(args.data).dropna()
    train, test = df[df.split == "train"], df[df.split == "test"]

    # 형태소 분석기 없이 글자 2~4gram 으로. 오타/신조어에도 덜 민감함
    model = make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=3, max_features=50_000, sublinear_tf=True),
        LogisticRegression(C=4, max_iter=1000),
    )

    t0 = time.time()
    model.fit(train.document, train.label)
    acc = model.score(test.document, test.label)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out, compress=3)
    print(f"train={len(train):,} test={len(test):,} acc={acc:.4f} ({time.time() - t0:.1f}s) -> {out}")


if __name__ == "__main__":
    main()
