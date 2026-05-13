"""
NYT 뉴스 기사 수집기 - Article Search API (최종 v2)
====================================================
2025년 4월 8일 NYT API 변경사항 반영:
  - response.meta → response.metadata
  - fq 필드: headline.default, Article.body 는 여전히 유효
  - q 파라미터 대신 fq로 정확한 키워드 필터링 유지

python geonho/nyt_code/crawl_nyt2.py global_bond
python geonho/nyt_code/crawl_nyt2.py korea_bond
python geonho/nyt_code/crawl_nyt2.py real_asset


의존성: pip install requests
"""

import os
import sys
import csv
import time
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

# ── API 키 ────────────────────────────────────────────
load_dotenv()
NYT_API_KEY = os.environ.get("NYT_API_KEY")

# ── 날짜 범위 ─────────────────────────────────────────
START_YEAR, END_YEAR = 2019, 2025

# ── 출력 디렉터리 ───────────────────────────────────────
OUTPUT_DIR = Path(".")

# ── Rate limit: 분당 10회 → 호출 간 6.5초 ───────────
SEARCH_SLEEP = 6.5
PAGE_SPLIT_THRESHOLD = 15

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


SECTOR_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "global_bond": {
        "US Investment Grade Corporate Bond": [
            "investment-grade corporate bond",
            "investment grade bond",
            "corporate bond spreads",
        ],
        "US High Yield Bond": [
            "high-yield bond",
            "high yield bond",
            "junk bond",
            "high-yield debt",
        ],
        "Short Duration High Yield Bond": [
            "short-duration high-yield bond",
            "short term junk bond",
            "0-5 year high yield bond",
        ],
        "US Long Term Treasury": [
            "30-year Treasury",
            "long-term Treasury bond",
            "long-dated Treasury",
            "20+ year Treasury",
        ],
        "Treasury STRIPS": [
            "Treasury STRIPS",
            "principal strips",
            "zero-coupon Treasury",
            "long US Treasury principal strips",
        ],
        "Short Term US Treasury": [
            "Treasury bill",
            "Treasury bills",
            "T-bill",
            "short-term Treasury",
            "1-year Treasury",
        ],
        "US 10 Year Treasury": [
            "10-year Treasury",
            "10-year Treasury yield",
            "Treasury note",
            "U.S. Treasury note",
        ],
        "Japan Government Bond": [
            "Japanese government bond",
            "Japan government bond",
            "JGB",
            "Japanese government bond yield",
            "Japan bond market",
        ],
    },
    "korea_bond": {
        "Korea Treasury Bond": [
            "South Korea government bond",
            "Korean government bond",
            "Korea Treasury bond",
            "KTB",
            "Korea bond market",
        ],
        "Korea Government Bond Futures": [
            "Korea Treasury futures",
            "Korean Treasury futures",
            "KTB futures",
            "South Korea bond futures",
        ],
        "Korea Aggregate Bond": [
            "Korean bond market",
            "Korea aggregate bond",
            "Korea composite bond",
            "South Korea bonds",
        ],
        "Korea Corporate Bond": [
            "Korean corporate bond",
            "Korea corporate bond",
            "South Korea corporate debt",
            "monetary stabilization bond",
        ],
    },
    "real_asset": {
        "Gold": [
            "gold price",
            "spot gold",
            "gold futures",
            'gold spot price',
        ],
        "Silver": [
            "silver price",
            "spot silver",
            "silver futures",
        ],
        "WTI Crude Oil": [
            "WTI crude oil",
            "West Texas Intermediate",
            "crude oil price",
            "oil futures",
        ],
        "Grains": [
            "grain futures",
            "corn futures",
            "wheat futures",
            "soybean futures",
            "agricultural commodities",
        ],
        "Japanese Yen": [
            "Japanese yen",
            "yen exchange rate",
            "yen futures",
            "USD/JPY",
        ],
        "US Dollar": [
            "U.S. dollar index",
            "dollar index",
            "dollar futures",
            "U.S. dollar exchange rate",
            'DXY'
        ],
    },
}
def fetch_meta(fq: str, begin: str, end: str) -> tuple[dict, int, int]:
    """page=0만 호출해서 hits와 total_pages를 확인한다."""
    data0 = fetch_page(fq, begin, end, page=0)
    hits = get_hits(data0)
    total_pages = min((hits + 9) // 10, 100) if hits else 0
    return data0, hits, total_pages


def quarter_ranges(year: int) -> list[tuple[str, str, str]]:
    return [
        (f"{year}0101", f"{year}0331", f"{year} Q1"),
        (f"{year}0401", f"{year}0630", f"{year} Q2"),
        (f"{year}0701", f"{year}0930", f"{year} Q3"),
        (f"{year}1001", f"{year}1231", f"{year} Q4"),
    ]


def output_path_for_sector(sector_name: str) -> Path:
    return OUTPUT_DIR / f"nyt_{sector_name}_raw.csv"


# ═════════════════════════════════════════════════════
# Article Search API 수집
# ═════════════════════════════════════════════════════
SEARCH_BASE = "https://api.nytimes.com/svc/search/v2/articlesearch.json"


def build_fq(variants: list[str]) -> str:
    """제목 OR 본문에 변형 키워드 중 하나라도 있으면 수집."""
    quoted = " ".join(f'"{v}"' for v in variants)
    return f'headline.default:({quoted}) OR Article.body:({quoted})'


def get_hits(data: dict) -> int:
    """
    API 응답에서 hits 추출.
    2025.04.08 변경: response.meta → response.metadata
    두 필드 모두 시도해서 안전하게 처리.
    """
    resp = data.get("response", {})
    # 신규 필드명 우선
    hits = resp.get("metadata", {}).get("hits")
    if hits is None:
        # 구 필드명 fallback
        hits = resp.get("meta", {}).get("hits", 0)
    return hits or 0


def fetch_page(fq: str, begin: str, end: str, page: int) -> dict:
    """단일 페이지 API 호출 (최대 3회 재시도, 실패 시 중단)."""
    params = {
        "fq":         fq,
        "begin_date": begin,
        "end_date":   end,
        "page":       page,
        "api-key":    NYT_API_KEY,
    }
    last_error = None

    for attempt in range(3):
        try:
            resp = requests.get(SEARCH_BASE, params=params, timeout=30)
            if resp.status_code == 429:
                last_error = RuntimeError(
                    f"Rate limit 429 (page={page}, begin={begin}, end={end}, attempt={attempt+1}/3)"
                )
                log.warning("  Rate limit 429 → 30초 대기 후 재시도")
                time.sleep(30)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            log.error(f"  fetch_page 오류 (시도 {attempt+1}/3): {e}")
            time.sleep(10)

    raise RuntimeError(
        f"NYT API 호출 실패: page={page}, begin={begin}, end={end}, fq={fq[:120]}... | last_error={last_error}"
    )


def extract_row(sector: str, keyword: str, doc: dict) -> dict | None:
    """doc에서 sector / keyword / title / date 추출."""
    title = doc.get("headline", {}).get("main", "").strip()
    if not title:
        return None
    return {
        "sector":  sector,
        "keyword": keyword,
        "title":   title,
        "date":    doc.get("pub_date", "")[:10],
    }


def collect_period(sector: str, keyword: str, variants: list[str],
                   begin: str, end: str) -> tuple[list[dict], int]:
    """
    특정 기간 수집.
    hits > 1,000이면 빈 리스트와 hits 반환 → 호출부에서 기간 재쪼개기.
    """
    fq = build_fq(variants)
    rows = []
    seen = set()

    data0, hits, total_pages = fetch_meta(fq, begin, end)

    log.debug(f"    fq={fq[:80]}... hits={hits}")

    if hits == 0:
        return [], 0
    if hits > 1000:
        return [], hits

    log.info(f"    hits={hits}, pages={total_pages}")

    for doc in data0.get("response", {}).get("docs", []):
        row = extract_row(sector, keyword, doc)
        if row and row["title"] not in seen:
            seen.add(row["title"])
            rows.append(row)

    for page in range(1, total_pages):
        time.sleep(SEARCH_SLEEP)
        data = fetch_page(fq, begin, end, page)
        for doc in data.get("response", {}).get("docs", []):
            row = extract_row(sector, keyword, doc)
            if row and row["title"] not in seen:
                seen.add(row["title"])
                rows.append(row)

    return rows, hits

def collect_period_rows(sector: str, keyword: str, variants: list[str], begin: str, end: str) -> tuple[list[dict], int, int]:
    """기간 수집 결과와 함께 hits, total_pages를 반환."""
    fq = build_fq(variants)
    _, hits, total_pages = fetch_meta(fq, begin, end)

    if hits == 0:
        return [], 0, 0
    if hits > 1000 or total_pages > PAGE_SPLIT_THRESHOLD:
        return [], hits, total_pages

    rows, _ = collect_period(sector, keyword, variants, begin, end)
    return rows, hits, total_pages


def month_end(year: int, month: int) -> str:
    if month == 2:
        return f"{year}{month:02d}28"
    elif month in [4, 6, 9, 11]:
        return f"{year}{month:02d}30"
    else:
        return f"{year}{month:02d}31"


def collect_keyword(sector: str, keyword: str, variants: list[str]) -> list[dict]:
    """
    연도별 호출
    → pages가 크면 분기별 재쪼개기
    → 분기도 pages가 크면 월별 재쪼개기
    → 월도 hits > 1,000이면 2주 단위 재쪼개기.
    """
    all_rows = []
    seen_titles = set()

    def add_rows(rows: list[dict]):
        for r in rows:
            if r["title"] not in seen_titles:
                seen_titles.add(r["title"])
                all_rows.append(r)

    for year in range(START_YEAR, END_YEAR + 1):
        begin = f"{year}0101"
        end = f"{year}1231"
        log.info(f"  [{keyword}] {year}년 수집 중...")

        rows, hits, total_pages = collect_period_rows(sector, keyword, variants, begin, end)

        if hits > 1000 or total_pages > PAGE_SPLIT_THRESHOLD:
            reason = f"hits={hits} > 1,000" if hits > 1000 else f"pages={total_pages} > {PAGE_SPLIT_THRESHOLD}"
            log.info(f"    {reason} → 분기별 재쪼개기")

            for q_begin, q_end, q_label in quarter_ranges(year):
                log.info(f"    [{keyword}] {q_label} ...")
                q_rows, q_hits, q_pages = collect_period_rows(sector, keyword, variants, q_begin, q_end)
                time.sleep(SEARCH_SLEEP)

                if q_hits > 1000 or q_pages > PAGE_SPLIT_THRESHOLD:
                    q_reason = f"hits={q_hits} > 1,000" if q_hits > 1000 else f"pages={q_pages} > {PAGE_SPLIT_THRESHOLD}"
                    log.info(f"      {q_reason} → 월별 재쪼개기")

                    start_month = int(q_begin[4:6])
                    end_month = int(q_end[4:6])
                    for month in range(start_month, end_month + 1):
                        m_begin = f"{year}{month:02d}01"
                        m_end = month_end(year, month)
                        log.info(f"      [{keyword}] {year}-{month:02d} ...")
                        m_rows, m_hits, m_pages = collect_period_rows(sector, keyword, variants, m_begin, m_end)
                        time.sleep(SEARCH_SLEEP)

                        if m_hits > 1000 or m_pages > PAGE_SPLIT_THRESHOLD:
                            m_reason = f"hits={m_hits} > 1,000" if m_hits > 1000 else f"pages={m_pages} > {PAGE_SPLIT_THRESHOLD}"
                            log.info(f"        {m_reason} → 2주 단위 재쪼개기")
                            for d_begin, d_end in [
                                (f"{year}{month:02d}01", f"{year}{month:02d}15"),
                                (f"{year}{month:02d}16", m_end),
                            ]:
                                h_rows, _ = collect_period(sector, keyword, variants, d_begin, d_end)
                                add_rows(h_rows)
                                time.sleep(SEARCH_SLEEP)
                        else:
                            add_rows(m_rows)
                            log.info(f"      [{keyword}] {year}-{month:02d} 완료 → 누적 {len(all_rows)}건")
                else:
                    add_rows(q_rows)
                    log.info(f"    [{keyword}] {q_label} 완료 → 누적 {len(all_rows)}건")
        else:
            add_rows(rows)

        log.info(f"  [{keyword}] {year}년 완료 → 누적 {len(all_rows)}건")
        time.sleep(SEARCH_SLEEP)

    return all_rows


def run_collection(sector_name: str):
    keyword_dict = SECTOR_KEYWORDS[sector_name]
    output_csv = output_path_for_sector(sector_name)

    log.info("=" * 60)
    log.info("▶ NYT Article Search API 수집 시작")
    log.info(f"  섹터: {sector_name}")
    log.info(f"  기간: {START_YEAR} ~ {END_YEAR}")
    log.info(f"  키워드: {len(keyword_dict)}개")
    log.info("=" * 60)

    if output_csv.exists():
        output_csv.unlink()

    first_write = True
    total = 0

    for idx, (keyword, variants) in enumerate(keyword_dict.items()):
        log.info(f"\n[{idx+1}/{len(keyword_dict)}] 키워드: {keyword}")
        log.info(f"  변형: {variants}")

        rows = collect_keyword(sector_name, keyword, variants)

        if rows:
            with open(output_csv, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["sector", "keyword", "title", "date"])
                if first_write:
                    writer.writeheader()
                    first_write = False
                writer.writerows(rows)
            total += len(rows)
            log.info(f"  ✓ {len(rows)}건 저장  (전체 누적 {total}건)")
        else:
            log.warning("  ! 수집 결과 없음")

    log.info(f"\n{'=' * 60}")
    log.info(f"✅ 수집 완료! 총 {total}건 → {output_csv.resolve()}")


# ═════════════════════════════════════════════════════
# 실행
# ═════════════════════════════════════════════════════
if __name__ == "__main__":
    if not NYT_API_KEY:
        log.error("NYT_API_KEY 환경변수를 설정해주세요.")
        log.error("  export NYT_API_KEY='your_key'")
        raise SystemExit(1)

    if len(sys.argv) != 2 or sys.argv[1] not in SECTOR_KEYWORDS:
        log.error("실행할 섹터를 지정해주세요.")
        log.error(f"  사용 가능 섹터: {', '.join(SECTOR_KEYWORDS.keys())}")
        log.error("  예시: python crawl_nyt2.py global_bond")
        raise SystemExit(1)

    target_sector = sys.argv[1]
    try:
        run_collection(target_sector)
    except Exception as e:
        log.error(f"수집 중단: {e}")
        raise SystemExit(1)