#%%
import pandas as pd

# ── 설정 ──────────────────────────────────────────────────────────────────────
FILES = {
    "mk":  "../news_clean_ver/mk_news_geonho_filtered_sentiment.csv",
    "nyt": "../news_clean_ver/nyt_news_geonho_sentiment.csv",
}
OUTPUT_DIR = "../news_clean_ver"
# ─────────────────────────────────────────────────────────────────────────────

for name, path in FILES.items():
    df = pd.read_csv(path)

    # sentiment_score = pos - neg  (범위: [-1, 1])
    df["sentiment_score"] = (df["pos"] - df["neg"]).round(6)

    out_path = f"{OUTPUT_DIR}/{name}_sentiment_scored.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"[{name.upper()}] {len(df):,}건 → {out_path}")
    print(df["sentiment_score"].describe().round(4))
    print()
