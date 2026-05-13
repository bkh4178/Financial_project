"""
FinBERT 감성 스코어링
- MK  (한국어): snunlp/KR-FinBERT-SC   label: negative(0), neutral(1), positive(2)
- NYT (영어):   ProsusAI/finbert        label: positive(0), negative(1), neutral(2)
sentiment_score = P(positive) - P(negative)  →  [-1, 1]

입력:
  data/processed/mk/mk_news_preprocessed.csv
  data/processed/nyt/nyt_news_preprocessed.csv
출력:
  data/sentiment/mk_news_scored.csv
  data/sentiment/nyt_news_scored.csv
"""
from pathlib import Path
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

BASE_DIR   = Path(__file__).resolve().parent.parent
BATCH_SIZE = 64
MAX_LEN    = 128

CONFIGS = {
    "MK": {
        "input":   BASE_DIR / "data/processed/mk/mk_news_preprocessed.csv",
        "output":  BASE_DIR / "data/sentiment/mk_news_scored.csv",
        "model":   "snunlp/KR-FinBERT-SC",
        "pos_idx": 2,
        "neg_idx": 0,
    },
    "NYT": {
        "input":   BASE_DIR / "data/processed/nyt/nyt_news_preprocessed.csv",
        "output":  BASE_DIR / "data/sentiment/nyt_news_scored.csv",
        "model":   "ProsusAI/finbert",
        "pos_idx": 0,
        "neg_idx": 1,
    },
}


def score_texts(texts, tokenizer, model, pos_idx, neg_idx, device):
    scores = []
    model.eval()
    with torch.no_grad():
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            enc = tokenizer(batch, padding=True, truncation=True,
                            max_length=MAX_LEN, return_tensors="pt").to(device)
            probs = F.softmax(model(**enc).logits, dim=-1).cpu()
            scores.extend((probs[:, pos_idx] - probs[:, neg_idx]).tolist())
            if (i // BATCH_SIZE) % 20 == 0:
                print(f"  {i + len(batch):,}/{len(texts):,} 완료")
    return scores


def run(source: str) -> None:
    cfg = CONFIGS[source]
    print(f"\n=== {source} 스코어링 ({cfg['model']}) ===")

    df = pd.read_csv(cfg["input"], encoding="utf-8-sig")
    print(f"입력: {len(df):,}건")

    device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(cfg["model"])
    model     = AutoModelForSequenceClassification.from_pretrained(cfg["model"]).to(device)
    print(f"모델 로드 완료 | 디바이스: {device}")

    df["sentiment_score"] = score_texts(
        df["title"].fillna("").tolist(),
        tokenizer, model, cfg["pos_idx"], cfg["neg_idx"], device,
    )

    cfg["output"].parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg["output"], index=False, encoding="utf-8-sig")
    print(f"저장: {cfg['output']}")
    print(df["sentiment_score"].describe().round(4))


if __name__ == "__main__":
    run("MK")
    run("NYT")
