import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
from tqdm import tqdm

# ── 설정 ──────────────────────────────────────────────────────────────────────
DATA_PATH   = "../news_clean_ver/nyt_news_geonho_clean.csv"
OUTPUT_PATH = "../news_clean_ver/nyt_news_geonho_sentiment.csv"
MODEL_NAME  = "ProsusAI/finbert"
BATCH_SIZE  = 64
# ─────────────────────────────────────────────────────────────────────────────

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# 모델 로드
print(f"Loading model: {MODEL_NAME}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.to(device)
model.eval()

# ProsusAI/finbert 레이블 순서: positive(0), negative(1), neutral(2)
# → pos/neu/neg 컬럼으로 매핑
LABEL_MAP = {0: "pos", 1: "neg", 2: "neu"}


def predict_batch(texts: list[str]) -> list[dict]:
    """텍스트 배치를 받아 pos/neu/neg 확률 딕셔너리 리스트 반환"""
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        logits = model(**encoded).logits
    probs = softmax(logits, dim=-1).cpu().numpy()

    results = []
    for prob in probs:
        results.append({
            "pos": round(float(prob[0]), 6),
            "neg": round(float(prob[1]), 6),
            "neu": round(float(prob[2]), 6),
        })
    return results


# 데이터 로드
print(f"Loading data: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"  rows: {len(df):,}")

titles = df["title"].fillna("").tolist()

# 배치 추론
all_results = []
for i in tqdm(range(0, len(titles), BATCH_SIZE), desc="Sentiment inference"):
    batch = titles[i : i + BATCH_SIZE]
    all_results.extend(predict_batch(batch))

# 결과 컬럼 추가
df["pos"] = [r["pos"] for r in all_results]
df["neu"] = [r["neu"] for r in all_results]
df["neg"] = [r["neg"] for r in all_results]

# 저장
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print(f"\nSaved → {OUTPUT_PATH}")
print(df[["title", "pos", "neu", "neg"]].head(10))
