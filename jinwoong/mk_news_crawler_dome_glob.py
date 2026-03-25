from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import quote
from datetime import datetime, timedelta
import random
import os


class MKNewsCrawler:
    """
    매일경제 뉴스 크롤러
    - 키워드별 1년 단위 크롤링
    - 저장: mk_news_{키워드}_{연도}.csv
    - 봇 감지 우회
    """

    BASE_URL    = "https://www.mk.co.kr/search"
    WAIT_SHORT  = 2
    WAIT_LONG   = 3
    WAIT_PERIOD = 3


    KEYWORDS_KR = [
        '코스피',
        '코스닥',
        'MSCI Korea',
        'S&P500',
        '나스닥',
        '다우존스',
        '러셀',
        '니케이',
        'TOPIX',
        '유로스탁스',
        'DAX',
        'MSCI World',
        'MSCI EAFE',
        'MSCI ACWI'
    ]

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver   = self._create_driver()

    def _create_driver(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return driver

    def _restart_driver(self):
        try:
            self.driver.quit()
        except:
            pass
        time.sleep(2)
        self.driver = self._create_driver()
        print("  브라우저 재시작 완료")

    def _build_url(self, keyword: str, start_date: str, end_date: str) -> str:
        kw = quote(keyword)
        return (
            f"{self.BASE_URL}"
            f"?word={kw}"
            f"&sort=desc"
            f"&dateType=direct"
            f"&startDate={start_date}"
            f"&endDate={end_date}"
            f"&searchField=all"
            f"&includeWord={kw}"
            f"&newsType=all"
        )

    def _generate_6month_periods(self, start: str, end: str) -> list:
        """6개월 단위 기간 생성"""
        periods = []
        current = datetime.strptime(start, '%Y-%m-%d')
        end_dt  = datetime.strptime(end,   '%Y-%m-%d')

        while current <= end_dt:
            month   = current.month + 6
            year    = current.year + (month - 1) // 12
            month   = ((month - 1) % 12) + 1
            next_dt = datetime(year, month, 1) - timedelta(days=1)
            if next_dt > end_dt:
                next_dt = end_dt
            periods.append((
                current.strftime('%Y-%m-%d'),
                next_dt.strftime('%Y-%m-%d')
            ))
            current = next_dt + timedelta(days=1)

        return periods

    def _get_total_count(self) -> int:
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            btn  = soup.find('input', {'data-total': True})
            if btn:
                return int(btn.get('data-total', 0))
        except:
            pass
        return 0

    def _parse_articles(self, keyword: str) -> list:
        soup  = BeautifulSoup(self.driver.page_source, 'html.parser')
        items = soup.find_all('li', class_='news_node')
        data  = []
        for item in items:
            title = item.find('h3', class_='news_ttl')
            date  = item.find('p',  class_='time_info')
            if title:
                data.append({
                    'keyword': keyword,
                    'date':    date.get_text(strip=True)[:10] if date else '',
                    'title':   title.get_text(strip=True),
                })
        return data

    def _click_more_and_wait(self, prev_count: int) -> bool:
        try:
            btn = self.driver.find_element(By.CLASS_NAME, 'drop_sub_news_btn')
            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", btn)
            for _ in range(10):
                time.sleep(0.5)
                soup  = BeautifulSoup(self.driver.page_source, 'html.parser')
                items = soup.find_all('li', class_='news_node')
                if len(items) > prev_count:
                    return True
            return False
        except:
            return False

    def _crawl_period(self, keyword: str, start_date: str, end_date: str) -> list:
        """6개월 단위로 쪼개서 크롤링"""
        periods = self._generate_6month_periods(start_date, end_date)
        all_data = []

        for s, e in periods:
            url = self._build_url(keyword, s, e)

            for attempt in range(3):
                try:
                    self.driver.get(url)
                    time.sleep(self.WAIT_LONG)
                    break
                except Exception as ex:
                    print(f"  접속 실패 ({attempt+1}/3): {ex}")
                    self._restart_driver()
                    time.sleep(2)

            total = self._get_total_count()
            print(f"  [{s}~{e}] 총 {total}개")

            page = 1
            while True:
                curr_data  = self._parse_articles(keyword)
                curr_count = len(curr_data)
                print(f"    페이지 {page}: 누적 {curr_count}개")

                loaded = self._click_more_and_wait(curr_count)
                if not loaded:
                    break
                page += 1
                time.sleep(random.uniform(0.5, 1.5))

            period_data = self._parse_articles(keyword)
            all_data.extend(period_data)
            print(f"  → {len(period_data)}개 수집 완료")
            time.sleep(random.uniform(self.WAIT_PERIOD, self.WAIT_PERIOD + 2))

        return all_data

    def crawl_all(self, save_dir: str, start_year: int = 2019, end_year: int = 2025):
        """
        전체 키워드 × 전체 연도 크롤링
        저장: mk_news_{키워드}_{연도}.csv
        """
        os.makedirs(save_dir, exist_ok=True)
        years = list(range(start_year, end_year + 1))

        try:
            for keyword in self.KEYWORDS_KR:
                print(f"\n{'='*60}")
                print(f"키워드: [{keyword}] 크롤링 시작")
                print(f"{'='*60}")

                for year in years:
                    # 저장 파일명: mk_news_키워드_연도.csv
                    safe_keyword = keyword.replace('/', '_').replace(' ', '_')
                    save_path = os.path.join(
                        save_dir,
                        f"mk_news_{safe_keyword}_{year}.csv"
                    )

                    # 이미 수집된 파일 스킵
                    if os.path.exists(save_path):
                        print(f"\n[{year}] 이미 존재 → 스킵: {save_path}")
                        continue

                    start_date = f"{year}-01-01"
                    end_date   = f"{year}-12-31"

                    print(f"\n[{keyword}] {year}년 크롤링 중...")

                    for attempt in range(3):
                        try:
                            data = self._crawl_period(keyword, start_date, end_date)
                            break
                        except Exception as ex:
                            print(f"  오류 ({attempt+1}/3): {ex}")
                            self._restart_driver()
                            time.sleep(3)
                            data = []

                    # 저장
                    df = pd.DataFrame(data)
                    df = df.drop_duplicates(subset=['title'])
                    df = df.reset_index(drop=True)
                    df.to_csv(save_path, index=False, encoding='utf-8-sig')
                    print(f"  저장: {save_path} ({len(df)}개)")

                    # 연도 사이 딜레이
                    time.sleep(random.uniform(3, 5))

                print(f"\n[{keyword}] 전체 연도 완료!")

        finally:
            try:
                self.driver.quit()
            except:
                pass

        print("\n전체 크롤링 완료!")

# ============================================================
# 실행
# ============================================================
if __name__ == "__main__":

    SAVE_DIR = "/Users/jinwoong/Desktop/Bitamin/project/time-series_project_2/dataset/"

    crawler = MKNewsCrawler(headless=False)
    crawler.crawl_all(
        save_dir   = SAVE_DIR,
        start_year = 2019,
        end_year   = 2025
    )

