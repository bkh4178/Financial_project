import pandas as pd
from pykrx import stock

# ============================================================
# 설정
# ============================================================
TEST_TICKER = "411060"   # ACE KRX금현물 (A411060에서 A 제거)
START_DATE = "20250101"
END_DATE = "20250331"

# pykrx 투자자 구분 후보
INVESTOR_TYPES = [
    "개인",
    "외국인",
    "기관합계",
    "금융투자",
    "보험",
    "투신",
    "사모",
    "은행",
    "기타금융",
    "연기금",
    "기타법인",
    "기타외국인",
]


def try_fetch_trading_by_investor(ticker: str, start_date: str, end_date: str) -> None:
    """ETF에 대해 투자자별 거래량/거래대금 조회가 되는지 테스트한다."""
    print("=" * 70)
    print("[TEST 1] ETF 투자자별 거래량/거래대금 조회 테스트")
    print(f"티커: {ticker}")
    print(f"기간: {start_date} ~ {end_date}")
    print("=" * 70)

    tests = [
        ("거래량", stock.get_market_trading_volume_by_investor),
        ("거래대금", stock.get_market_trading_value_by_investor),
    ]

    for label, func in tests:
        print("\n" + "-" * 70)
        print(f"[{label}] 함수 테스트 시작")
        print("-" * 70)

        # pykrx 문서 기준: (fromdate, todate, ticker_or_market, ...)
        call_patterns = [
            (start_date, end_date, ticker),
            (start_date, end_date, ticker, True),
            (start_date, end_date, ticker, False),
        ]

        success = False
        for idx, args in enumerate(call_patterns, start=1):
            try:
                print(f"[TRY {idx}] args={args}")
                df = func(*args)

                if df is None:
                    print("  -> 반환값이 None 입니다.")
                    continue
                if df.empty:
                    print("  -> 빈 DataFrame 입니다.")
                    continue

                df = df.reset_index()
                df.columns = df.columns.str.strip()

                print(f"[OK] {label}: 데이터 발견")
                print(df.head().to_string(index=False))
                print("...")
                print(df.tail().to_string(index=False))
                print(f"총 행 수: {len(df)}")
                print(f"컬럼: {list(df.columns)}")
                success = True
                break
            except Exception as e:
                print(f"  -> 실패: {e}")

        if not success:
            print(f"[FAIL] {label}: 해당 함수 경로로 데이터 조회 실패")


def try_fetch_investor_by_date(ticker: str, start_date: str, end_date: str) -> None:
    """설치된 pykrx 버전에서 날짜별 투자자 관련 함수가 있는지 점검한다."""
    print("\n" + "=" * 70)
    print("[TEST 3] 날짜별 투자자 순매수 추이 테스트")
    print(f"티커: {ticker}")
    print(f"기간: {start_date} ~ {end_date}")
    print("=" * 70)

    candidate_names = [
        name
        for name in dir(stock)
        if "investor" in name.lower()
        or ("net" in name.lower() and "purchase" in name.lower())
    ]

    print("설치된 pykrx에서 투자자 관련 후보 함수명:")
    if candidate_names:
        for name in sorted(candidate_names):
            print(f" - {name}")
    else:
        print(" - 관련 후보 함수를 찾지 못했습니다.")

    print("\n현재 설치된 pykrx에는 `get_market_net_purchases_of_equities_by_date`가 없습니다.")
    print("즉, 이 환경에서는 날짜별 투자자 추이를 바로 못 가져올 가능성이 큽니다.")


if __name__ == "__main__":
    try_fetch_trading_by_investor(TEST_TICKER, START_DATE, END_DATE)
    print("\n" + "#" * 70)
    print("참고: pykrx 문서 기준으로 ETF도 ticker를 넣어 투자자별 거래량/거래대금을 조회할 수 있는지 다시 테스트합니다.")
    print("#" * 70)
    try_fetch_investor_by_date(TEST_TICKER, START_DATE, END_DATE)

#%%
from pykrx import stock
import pandas as pd
# 기본 테스트
df = stock.get_market_trading_value_by_investor(
    "20250101", "20250331", "069500", etf=True
)
print(df)
#%%
# 하루치, 최근 거래일
from pykrx.stock import krx
df_raw2 = krx.get_market_trading_value_and_volume_on_ticker_by_investor(
    "20250328", "20250328", "069500"
)
print(df_raw2)