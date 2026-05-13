#%%
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.font_manager as fm
import numpy as np

# 한글 폰트 설정
import platform
if platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
elif platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
else:
    plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 120

# ── 공통 함수 ──────────────────────────────────────────────────────────────────
def add_label_col(df):
    """pos/neu/neg 중 최대값을 label로 부여"""
    df["label"] = df[["pos", "neu", "neg"]].idxmax(axis=1)
    return df

def print_stats(df, name):
    print(f"\n{'='*50}")
    print(f"  {name} 감성분석 기술통계")
    print(f"{'='*50}")
    print(df[["pos", "neu", "neg"]].describe().round(4))
    print("\n[label 분포]")
    vc = df["label"].value_counts()
    for lbl, cnt in vc.items():
        print(f"  {lbl:>3}: {cnt:>6,}건  ({cnt/len(df)*100:.1f}%)")

def plot_sentiment(df, name, palette):
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle(f"{name} 감성분석 결과 분포", fontsize=15, fontweight="bold")

    label_colors = {"pos": "#4C9BE8", "neu": "#A0A0A0", "neg": "#E8604C"}
    labels = ["pos", "neu", "neg"]
    counts = df["label"].value_counts().reindex(labels, fill_value=0)

    # 1) label 막대그래프
    ax = axes[0, 0]
    bars = ax.bar(labels, counts.values,
                  color=[label_colors[l] for l in labels], edgecolor="white", width=0.5)
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + len(df)*0.003,
                f"{val:,}\n({val/len(df)*100:.1f}%)", ha="center", va="bottom", fontsize=9)
    ax.set_title("Label 분포 (argmax)")
    ax.set_ylabel("건수")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    # 2) label 파이차트
    ax = axes[0, 1]
    wedge_colors = [label_colors[l] for l in labels]
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=labels, colors=wedge_colors,
        autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5}
    )
    ax.set_title("Label 비율 (파이차트)")

    # 3) pos/neu/neg 평균 막대
    ax = axes[0, 2]
    means = df[["pos", "neu", "neg"]].mean()
    bars2 = ax.bar(means.index, means.values,
                   color=[label_colors[l] for l in means.index], edgecolor="white", width=0.5)
    for bar, val in zip(bars2, means.values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.003,
                f"{val:.4f}", ha="center", va="bottom", fontsize=9)
    ax.set_title("pos / neu / neg 평균 확률")
    ax.set_ylabel("평균 확률")
    ax.set_ylim(0, means.max() * 1.2)

    # 4) pos 점수 분포 히스토그램
    ax = axes[1, 0]
    ax.hist(df["pos"], bins=50, color=label_colors["pos"], edgecolor="white", alpha=0.85)
    ax.set_title("Positive 점수 분포")
    ax.set_xlabel("확률")
    ax.set_ylabel("건수")

    # 5) neg 점수 분포 히스토그램
    ax = axes[1, 1]
    ax.hist(df["neg"], bins=50, color=label_colors["neg"], edgecolor="white", alpha=0.85)
    ax.set_title("Negative 점수 분포")
    ax.set_xlabel("확률")
    ax.set_ylabel("건수")

    # 6) 연도별 label 비율 누적 막대
    ax = axes[1, 2]
    df["year"] = pd.to_datetime(df["date"]).dt.year
    yearly = (df.groupby(["year", "label"]).size()
                .unstack(fill_value=0)
                .reindex(columns=labels, fill_value=0))
    yearly_pct = yearly.div(yearly.sum(axis=1), axis=0) * 100
    bottom = np.zeros(len(yearly_pct))
    for lbl in labels:
        ax.bar(yearly_pct.index.astype(str), yearly_pct[lbl],
               bottom=bottom, label=lbl, color=label_colors[lbl], edgecolor="white")
        bottom += yearly_pct[lbl].values
    ax.set_title("연도별 감성 비율")
    ax.set_xlabel("연도")
    ax.set_ylabel("%")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_ylim(0, 100)

    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════════════════════
# %% 매일경제 (MK)
# ══════════════════════════════════════════════════════════════════════════════
MK_PATH = "../news_clean_ver/mk_news_geonho_filtered_sentiment.csv"

mk = pd.read_csv(MK_PATH)
mk = add_label_col(mk)

print_stats(mk, "매일경제 (KR-FinBERT)")
plot_sentiment(mk, "매일경제 (KR-FinBERT)", "Blues")


# ══════════════════════════════════════════════════════════════════════════════
# %% 뉴욕타임즈 (NYT)
# ══════════════════════════════════════════════════════════════════════════════
NYT_PATH = "../news_clean_ver/nyt_news_geonho_sentiment.csv"

nyt = pd.read_csv(NYT_PATH)
nyt = add_label_col(nyt)

print_stats(nyt, "뉴욕타임즈 (FinBERT)")
plot_sentiment(nyt, "뉴욕타임즈 (FinBERT)", "Reds")


# ══════════════════════════════════════════════════════════════════════════════
# %% sentiment_score 분포 - 매일경제
# ══════════════════════════════════════════════════════════════════════════════
MK_SCORED_PATH = "../news_clean_ver/mk_sentiment_scored.csv"

mk_s = pd.read_csv(MK_SCORED_PATH)

print("=" * 50)
print("  매일경제 sentiment_score 기술통계")
print("=" * 50)
print(mk_s["sentiment_score"].describe().round(4))
print(f"\n  양수(긍정 우세): {(mk_s['sentiment_score'] > 0).sum():,}건 ({(mk_s['sentiment_score'] > 0).mean()*100:.1f}%)")
print(f"  중립(0):        {(mk_s['sentiment_score'] == 0).sum():,}건 ({(mk_s['sentiment_score'] == 0).mean()*100:.1f}%)")
print(f"  음수(부정 우세): {(mk_s['sentiment_score'] < 0).sum():,}건 ({(mk_s['sentiment_score'] < 0).mean()*100:.1f}%)")

fig, axes = plt.subplots(1, 3, figsize=(16, 4))
fig.suptitle("매일경제 sentiment_score 분포", fontsize=13, fontweight="bold")

# 전체 분포 히스토그램
ax = axes[0]
ax.hist(mk_s["sentiment_score"], bins=80, color="#4C9BE8", edgecolor="white", alpha=0.85)
ax.axvline(mk_s["sentiment_score"].mean(), color="red", linestyle="--", linewidth=1.2, label=f"mean={mk_s['sentiment_score'].mean():.3f}")
ax.axvline(0, color="black", linestyle="-", linewidth=0.8, alpha=0.4)
ax.set_title("전체 분포")
ax.set_xlabel("sentiment_score")
ax.set_ylabel("건수")
ax.legend(fontsize=8)

# KDE
ax = axes[1]
mk_s["sentiment_score"].plot.kde(ax=ax, color="#4C9BE8", linewidth=2)
ax.axvline(mk_s["sentiment_score"].mean(), color="red", linestyle="--", linewidth=1.2, label=f"mean={mk_s['sentiment_score'].mean():.3f}")
ax.axvline(0, color="black", linestyle="-", linewidth=0.8, alpha=0.4)
ax.set_title("KDE")
ax.set_xlabel("sentiment_score")
ax.legend(fontsize=8)

# 연도별 평균 추이
ax = axes[2]
mk_s["year"] = pd.to_datetime(mk_s["date"]).dt.year
yearly_mean = mk_s.groupby("year")["sentiment_score"].mean()
ax.bar(yearly_mean.index.astype(str), yearly_mean.values,
       color=["#4C9BE8" if v >= 0 else "#E8604C" for v in yearly_mean.values], edgecolor="white")
ax.axhline(0, color="black", linewidth=0.8, alpha=0.4)
ax.set_title("연도별 평균 sentiment_score")
ax.set_xlabel("연도")
ax.set_ylabel("평균 점수")

plt.tight_layout()
plt.show()


# ══════════════════════════════════════════════════════════════════════════════
# %% sentiment_score 분포 - 뉴욕타임즈
# ══════════════════════════════════════════════════════════════════════════════
NYT_SCORED_PATH = "../news_clean_ver/nyt_sentiment_scored.csv"

nyt_s = pd.read_csv(NYT_SCORED_PATH)

print("=" * 50)
print("  뉴욕타임즈 sentiment_score 기술통계")
print("=" * 50)
print(nyt_s["sentiment_score"].describe().round(4))
print(f"\n  양수(긍정 우세): {(nyt_s['sentiment_score'] > 0).sum():,}건 ({(nyt_s['sentiment_score'] > 0).mean()*100:.1f}%)")
print(f"  중립(0):        {(nyt_s['sentiment_score'] == 0).sum():,}건 ({(nyt_s['sentiment_score'] == 0).mean()*100:.1f}%)")
print(f"  음수(부정 우세): {(nyt_s['sentiment_score'] < 0).sum():,}건 ({(nyt_s['sentiment_score'] < 0).mean()*100:.1f}%)")

fig, axes = plt.subplots(1, 3, figsize=(16, 4))
fig.suptitle("뉴욕타임즈 sentiment_score 분포", fontsize=13, fontweight="bold")

# 전체 분포 히스토그램
ax = axes[0]
ax.hist(nyt_s["sentiment_score"], bins=80, color="#E8A84C", edgecolor="white", alpha=0.85)
ax.axvline(nyt_s["sentiment_score"].mean(), color="red", linestyle="--", linewidth=1.2, label=f"mean={nyt_s['sentiment_score'].mean():.3f}")
ax.axvline(0, color="black", linestyle="-", linewidth=0.8, alpha=0.4)
ax.set_title("전체 분포")
ax.set_xlabel("sentiment_score")
ax.set_ylabel("건수")
ax.legend(fontsize=8)

# KDE
ax = axes[1]
nyt_s["sentiment_score"].plot.kde(ax=ax, color="#E8A84C", linewidth=2)
ax.axvline(nyt_s["sentiment_score"].mean(), color="red", linestyle="--", linewidth=1.2, label=f"mean={nyt_s['sentiment_score'].mean():.3f}")
ax.axvline(0, color="black", linestyle="-", linewidth=0.8, alpha=0.4)
ax.set_title("KDE")
ax.set_xlabel("sentiment_score")
ax.legend(fontsize=8)

# 연도별 평균 추이
ax = axes[2]
nyt_s["year"] = pd.to_datetime(nyt_s["date"]).dt.year
yearly_mean = nyt_s.groupby("year")["sentiment_score"].mean()
ax.bar(yearly_mean.index.astype(str), yearly_mean.values,
       color=["#4C9BE8" if v >= 0 else "#E8604C" for v in yearly_mean.values], edgecolor="white")
ax.axhline(0, color="black", linewidth=0.8, alpha=0.4)
ax.set_title("연도별 평균 sentiment_score")
ax.set_xlabel("연도")
ax.set_ylabel("평균 점수")

plt.tight_layout()
plt.show()
