import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")
matplotlib.rcParams["font.family"] = "AppleGothic"
matplotlib.rcParams["axes.unicode_minus"] = False
plt.style.use("seaborn-v0_8-whitegrid")

# ── 경로 설정 ──────────────────────────────────────────────────────────────────
FILES = {
    "sovereign_kr": "final_dataset_for_tft_sovereign_kr.csv",
    "sovereign_us": "final_dataset_for_tft_sovereign_us.csv",
    "real_assets":  "final_dataset_for_tft_realassets.csv",
}
OUT_DIR = "eda_output"
DPI = 150

os.makedirs(OUT_DIR, exist_ok=True)

# ── 데이터 로드 ────────────────────────────────────────────────────────────────
datasets: dict[str, pd.DataFrame] = {}
for sector, path in FILES.items():
    df = pd.read_csv(path, parse_dates=["date"])
    datasets[sector] = df

# ══════════════════════════════════════════════════════════════════════════════
# 1. Sanity Check
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("1. SANITY CHECK")
print("=" * 60)

for sector, df in datasets.items():
    print(f"\n[{sector}]")
    print(f"  shape        : {df.shape}")
    print(f"  date range   : {df['date'].min().date()} ~ {df['date'].max().date()}")

    print("  ticker rows  :")
    for t, cnt in df["ticker"].value_counts().items():
        name = df.loc[df["ticker"] == t, "name"].iloc[0]
        print(f"    {t} ({name}): {cnt}")

    print("  NaN 비율 (%) :")
    nan_pct = df.isna().mean() * 100
    for col, pct in nan_pct[nan_pct > 0].items():
        print(f"    {col}: {pct:.1f}%")

    t = df["target_5d"].dropna()
    print("  target_5d 기초통계:")
    print(f"    mean={t.mean():.6f}  std={t.std():.6f}  "
          f"min={t.min():.6f}  max={t.max():.6f}  skew={t.skew():.3f}")

# ══════════════════════════════════════════════════════════════════════════════
# 2. NaN 히트맵
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("2. NaN HEATMAP")
print("=" * 60)

NAN_COLS = [
    "end", "AUM", "target_5d",
    "domestic_mean", "domestic_std", "domestic_count",
    "global_mean", "global_std", "global_count",
]

for sector, df in datasets.items():
    # ticker별로 첫 번째 row만 남겨 날짜 x 컬럼 피벗
    # date 기준으로 집계(ticker 여러 개면 OR 사용)
    pivot = df.groupby("date")[NAN_COLS].first()
    nan_mask = pivot.isna().astype(int)  # 1=NaN, 0=값있음

    fig, ax = plt.subplots(figsize=(12, max(4, len(pivot) // 50)))
    sns.heatmap(
        nan_mask.T,
        ax=ax,
        cmap=["#2196F3", "white"],  # 값있음=파랑, NaN=흰색
        cbar=False,
        xticklabels=False,
        yticklabels=True,
        linewidths=0,
    )
    ax.set_title(f"NaN 히트맵 — {sector}", fontsize=13, pad=10)
    ax.set_xlabel("날짜 (오래된 순 →)", fontsize=10)
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=9)

    # x축에 연도 눈금
    dates = pivot.index
    year_idx = [i for i, d in enumerate(dates) if d.month == 1 and d.day <= 7]
    ax.set_xticks(year_idx)
    ax.set_xticklabels([str(dates[i].year) for i in year_idx], fontsize=8, rotation=0)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, f"nan_heatmap_{sector}.png")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  saved: {out}")

# ══════════════════════════════════════════════════════════════════════════════
# 3. 감성 시계열
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("3. SENTIMENT TREND")
print("=" * 60)

for sector, df in datasets.items():
    sent = df.groupby("date")[["domestic_mean", "global_mean"]].mean().reset_index()
    sent = sent.sort_values("date")
    sent["domestic_ma7"] = sent["domestic_mean"].rolling(7, min_periods=1).mean()
    sent["global_ma7"]   = sent["global_mean"].rolling(7, min_periods=1).mean()

    fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
    for ax, col, ma_col, label, color in [
        (axes[0], "domestic_mean", "domestic_ma7", "국내 감성 (MK)", "#1976D2"),
        (axes[1], "global_mean",   "global_ma7",   "해외 감성 (NYT)", "#E64A19"),
    ]:
        ax.plot(sent["date"], sent[col], alpha=0.3, color=color, linewidth=0.8)
        ax.plot(sent["date"], sent[ma_col], color=color, linewidth=1.8, label="7일 MA")
        ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
        ax.set_ylabel("sentiment_score", fontsize=10)
        ax.set_title(label, fontsize=11)
        ax.legend(fontsize=9)

    axes[1].set_xlabel("날짜", fontsize=10)
    fig.suptitle(f"감성 시계열 — {sector}", fontsize=13, y=1.01)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, f"sentiment_trend_{sector}.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: {out}")

# ══════════════════════════════════════════════════════════════════════════════
# 4. target_5d 분포
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("4. TARGET_5D DISTRIBUTION")
print("=" * 60)

for sector, df in datasets.items():
    tickers = df["ticker"].unique()
    n = len(tickers)
    ncols = min(n, 3)
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
    axes = np.array(axes).flatten()

    for i, ticker in enumerate(tickers):
        ax = axes[i]
        sub = df[df["ticker"] == ticker]["target_5d"].dropna()
        name = df.loc[df["ticker"] == ticker, "name"].iloc[0]
        ax.hist(sub, bins=40, density=True, alpha=0.5, color="#42A5F5", edgecolor="none")
        sub.plot.kde(ax=ax, color="#1565C0", linewidth=2)
        ax.axvline(sub.mean(), color="red", linewidth=1.2, linestyle="--", label=f"mean={sub.mean():.4f}")
        ax.set_title(f"{ticker}\n{name}", fontsize=9)
        ax.set_xlabel("target_5d", fontsize=9)
        ax.legend(fontsize=8)

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(f"target_5d 분포 — {sector}", fontsize=13)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, f"target_dist_{sector}.png")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  saved: {out}")

# ══════════════════════════════════════════════════════════════════════════════
# 5. 감성 vs target_5d 상관관계
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("5. SENTIMENT vs TARGET_5D CORRELATION")
print("=" * 60)

def corr_text(x: pd.Series, y: pd.Series) -> str:
    mask = x.notna() & y.notna()
    x, y = x[mask], y[mask]
    if len(x) < 5:
        return "n<5"
    r_p, _ = stats.pearsonr(x, y)
    r_s, _ = stats.spearmanr(x, y)
    return f"Pearson={r_p:.3f}\nSpearman={r_s:.3f}\nn={len(x)}"


for sector, df in datasets.items():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, xcol, xlabel, color in [
        (axes[0], "domestic_mean", "국내 감성 (MK)",  "#1976D2"),
        (axes[1], "global_mean",   "해외 감성 (NYT)", "#E64A19"),
    ]:
        mask = df[xcol].notna() & df["target_5d"].notna()
        x = df.loc[mask, xcol]
        y = df.loc[mask, "target_5d"]
        ax.scatter(x, y, alpha=0.15, s=10, color=color)

        # 회귀선
        if len(x) >= 5:
            m, b = np.polyfit(x, y, 1)
            xline = np.linspace(x.min(), x.max(), 200)
            ax.plot(xline, m * xline + b, color="black", linewidth=1.5)

        txt = corr_text(df[xcol], df["target_5d"])
        ax.text(0.05, 0.93, txt, transform=ax.transAxes,
                fontsize=9, verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel("target_5d", fontsize=10)
        ax.set_title(f"{xlabel} vs target_5d", fontsize=11)

    fig.suptitle(f"감성 vs target_5d — {sector}", fontsize=13)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, f"sentiment_corr_{sector}.png")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  saved: {out}")

# ══════════════════════════════════════════════════════════════════════════════
# 6. ticker별 정규화 종가 시계열
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("6. NORMALIZED PRICE TREND")
print("=" * 60)

COLORS = ["#1976D2", "#E64A19", "#388E3C", "#7B1FA2", "#F57C00"]

for sector, df in datasets.items():
    fig, ax = plt.subplots(figsize=(14, 5))

    for i, ticker in enumerate(df["ticker"].unique()):
        sub = df[df["ticker"] == ticker].sort_values("date")
        name = sub["name"].iloc[0]
        price = sub.set_index("date")["end"].dropna()
        if price.empty:
            continue
        normalized = price / price.iloc[0] * 100
        ax.plot(normalized.index, normalized.values,
                label=f"{ticker} {name}", color=COLORS[i % len(COLORS)], linewidth=1.5)

    ax.axhline(100, color="gray", linewidth=0.8, linestyle="--")
    ax.set_title(f"정규화 종가 시계열 (첫날=100) — {sector}", fontsize=13)
    ax.set_xlabel("날짜", fontsize=10)
    ax.set_ylabel("정규화 종가", fontsize=10)
    ax.legend(fontsize=9, loc="upper left")
    plt.tight_layout()
    out = os.path.join(OUT_DIR, f"price_trend_{sector}.png")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  saved: {out}")

print("\n완료. 모든 결과물 →", os.path.abspath(OUT_DIR))
