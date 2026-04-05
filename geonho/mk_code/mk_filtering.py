#%%
import pandas as pd

DATA_PATH = "../mk_news_data/mk_news_geonho_clean.csv"
df = pd.read_csv(DATA_PATH)
print(f"전체 행 수: {len(df):,}")
print(df["title"].head(20))

#%%
# 랜덤 샘플 100건 출력 - 노이즈 패턴 파악용
sample = df["title"].sample(100, random_state=42).reset_index(drop=True)
for i, title in enumerate(sample):
    print(f"{i+1:>3}. {title}")

#%%
# 의심 패턴 키워드 탐색
patterns = {
    "매-세-지(뉴스레터형)": df["title"].str.contains(r"매.세.지", regex=True, na=False),
    "포토/사진":            df["title"].str.contains(r"\[?포토\]?|\[?사진\]?", regex=True, na=False),
    "카드뉴스":             df["title"].str.contains(r"카드뉴스", na=False),
    "광고/PR":              df["title"].str.contains(r"\[광고\]|\[PR\]|advertorial", regex=True, na=False),
    "동영상/영상":          df["title"].str.contains(r"동영상|영상|유튜브|[Vv]ideo", regex=True, na=False),
    "부고/인사":            df["title"].str.contains(r"부고|별세|인사발령|승진|취임|퇴임", regex=True, na=False),
    "날씨":                 df["title"].str.contains(r"날씨|기온|강수", regex=True, na=False),
    "스포츠":               df["title"].str.contains(r"야구|축구|농구|올림픽|월드컵|스포츠", regex=True, na=False),
    "연예/문화":            df["title"].str.contains(r"드라마|영화|배우|가수|아이돌|콘서트", regex=True, na=False),
    "공고/모집":            df["title"].str.contains(r"공고|모집|채용|접수|신청", regex=True, na=False),
}

print(f"\n{'패턴':<20} {'건수':>6}  {'비율':>6}  {'예시'}")
print("-" * 90)
for name, mask in patterns.items():
    cnt = mask.sum()
    pct = cnt / len(df) * 100
    examples = df.loc[mask, "title"].head(3).tolist()
    ex_str = " / ".join(examples[:2])[:60]
    print(f"{name:<20} {cnt:>6,}  {pct:>5.1f}%  {ex_str}")

#%%
# 패턴별 실제 예시 상세 확인
for name, mask in patterns.items():
    print(f"\n{'='*60}")
    print(f"[{name}] {mask.sum():,}건")
    print("-" * 60)
    for t in df.loc[mask, "title"].head(10):
        print(f"  {t}")

#%%
# ── 명확한 노이즈 제거 ────────────────────────────────────────────────────────
OUTPUT_PATH = "../mk_news_data/mk_news_geonho_filtered.csv"

NOISE_PATTERNS = [
    r"매.세.지",                          # 매-세-지 뉴스레터
    r"\[?포토\]?",                        # 포토 기사
    r"카드뉴스",                           # 카드뉴스
    r"\[광고\]|\[PR\]|advertorial",       # 광고/PR
    r"동영상|영상|유튜브|[Vv]ideo",        # 동영상 콘텐츠
]

noise_mask = df["title"].str.contains(
    "|".join(NOISE_PATTERNS), regex=True, na=False
)

removed = df[noise_mask].copy()
df_filtered = df[~noise_mask].copy().reset_index(drop=True)

print(f"필터링 전: {len(df):,}건")
print(f"제거된 노이즈: {noise_mask.sum():,}건")
print(f"필터링 후: {len(df_filtered):,}건")
print(f"\n[제거된 항목 샘플 20건]")
for t in removed["title"].sample(min(20, len(removed)), random_state=42):
    print(f"  {t}")

#%%
# 저장
df_filtered.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print(f"저장 완료 → {OUTPUT_PATH}")
