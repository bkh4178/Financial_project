'''
cd /Users/user/Desktop/bitamin/Financial_project
python geonho/nyt_code/crawl_nyt3.py --category real_assets
python geonho/nyt_code/crawl_nyt3.py --category overseas_bond
python geonho/nyt_code/crawl_nyt3.py --category domestic_bond
'''

import argparse
import os
import time
from urllib.parse import quote_plus

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. 설정
DEFAULT_CATEGORY = "real_assets"
SAVE_DIR = "/Users/user/Desktop/bitamin/Financial_project/geonho/nyt_news_data"

CATEGORY_KEYWORDS = {
    "real_assets": [
        "gold prices",
        "gold futures",
        "silver futures",
        "crude oil prices",
        "wti crude",
        "u.s. dollar index",
        "japanese yen",
        "grain prices"
    ],

    "overseas_bond": [
        "u.s. treasury",
        "treasury yields",
        "investment grade corporate bond",
        "high yield bond",
        "credit spreads",
        "junk bond"
    ],
    
    "domestic_bond": [
        "south korea bond market",
        "south korea government bond",
        "korea treasury bond",
        "korea corporate bond",
        "bank of korea rate",
        "korean credit market"
    ]
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="NYT 기사 크롤링: 카테고리별 키워드로 2019~2025 기사 수집"
    )
    parser.add_argument(
        "--category",
        type=str,
        default=DEFAULT_CATEGORY,
        choices=list(CATEGORY_KEYWORDS.keys()),
        help="수집할 카테고리 선택"
    )
    return parser.parse_args()


args = parse_args()
CATEGORY = args.category
CSV_NAME = f"nyt_{CATEGORY}_2019_2025.csv"
KEYWORDS = CATEGORY_KEYWORDS[CATEGORY]
YEARS = range(2019, 2026)
all_results = []

os.makedirs(SAVE_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(SAVE_DIR, CSV_NAME)
CHECKPOINT_PATH = os.path.join(SAVE_DIR, f"checkpoint_{CATEGORY}.csv")
PROGRESS_PATH = os.path.join(SAVE_DIR, f"checkpoint_{CATEGORY}_progress.txt")


def save_checkpoint(results):
    checkpoint_df = pd.DataFrame(results)
    if not checkpoint_df.empty:
        checkpoint_df = checkpoint_df.drop_duplicates(subset=["URL"]).reset_index(drop=True)
    checkpoint_df.to_csv(CHECKPOINT_PATH, index=False, encoding='utf-8-sig')


def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        checkpoint_df = pd.read_csv(CHECKPOINT_PATH)
        if not checkpoint_df.empty and "URL" in checkpoint_df.columns:
            checkpoint_df = checkpoint_df.drop_duplicates(subset=["URL"]).reset_index(drop=True)
        return checkpoint_df.to_dict("records")
    return []


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def save_progress(keyword, year):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        f.write(f"{keyword}\t{year}")


def clear_progress():
    if os.path.exists(PROGRESS_PATH):
        os.remove(PROGRESS_PATH)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.set_page_load_timeout(180)

all_results = load_checkpoint()
completed_urls = {row["URL"] for row in all_results if "URL" in row and pd.notna(row["URL"])}
last_progress = load_progress()
resume_mode = last_progress is not None
resume_started = not resume_mode

if resume_mode:
    last_keyword, last_year = last_progress.split("\t")
    last_year = int(last_year)
    print(f"🟡 체크포인트 발견: keyword={last_keyword}, year={last_year} 다음 작업부터 재개")
else:
    print("🟢 체크포인트 없음: 처음부터 시작")

for keyword in KEYWORDS:
    for year in YEARS:
        if resume_mode and not resume_started:
            if keyword == last_keyword and year == last_year:
                resume_started = True
                continue
            else:
                continue

        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        print(f"🚀 [{keyword}] {year}년 리스트 수집 시작...")

        encoded_keyword = quote_plus(keyword)
        search_url = (
            f"https://www.nytimes.com/search?"
            f"dropmab=false&endDate={end_date}&lang=en&query={encoded_keyword}"
            f"&sort=newest&startDate={start_date}&types=article"
        )

        driver.get(search_url)
        time.sleep(5)

        # --- 1. Show More 버튼이 안 나올 때까지 끝까지 펼치기 ---
        prev_item_count = -1
        stable_rounds = 0

        while True:
            current_items = driver.find_elements(By.CSS_SELECTOR, 'li[data-testid="search-bodega-result"]')
            current_count = len(current_items)

            if current_count == prev_item_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
                prev_item_count = current_count

            if stable_rounds >= 3:
                print(f"  > [{year}] 모든 리스트 펼치기 완료 (item count stable: {current_count})")
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            try:
                wait = WebDriverWait(driver, 5)
                show_more_btn = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="search-show-more-button"]'))
                )

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_btn)
                time.sleep(0.7)

                if show_more_btn.is_displayed() and show_more_btn.is_enabled():
                    try:
                        show_more_btn.click()
                    except:
                        driver.execute_script("arguments[0].click();", show_more_btn)
                    time.sleep(2)
                else:
                    stable_rounds += 1
            except TimeoutException:
                stable_rounds += 1

        # --- 2. 펼쳐진 화면에서 정보 긁어오기 ---
        items = driver.find_elements(By.CSS_SELECTOR, 'li[data-testid="search-bodega-result"]')

        added_count = 0
        for item in items:
            try:
                date = item.find_element(By.CSS_SELECTOR, 'span[data-testid="todays-date"]').text
                title = item.find_element(By.CSS_SELECTOR, 'h4').text
                link = item.find_element(By.CSS_SELECTOR, 'a').get_attribute("href").split("?")[0]

                try:
                    summary = item.find_element(By.CSS_SELECTOR, 'p').text
                except:
                    summary = ""

                if link in completed_urls:
                    continue

                all_results.append({
                    "키워드": keyword,
                    "날짜": date,
                    "제목": title,
                    "요약": summary,
                    "URL": link
                })
                completed_urls.add(link)
                added_count += 1
            except:
                continue

        save_checkpoint(all_results)
        save_progress(keyword, year)
        print(f"  > 이번 배치 추가: {added_count}건 | 현재까지 총 {len(all_results)}건")

# 3. CSV 저장
df = pd.DataFrame(all_results)

before_dedup = len(df)
if not df.empty:
    df = df.drop_duplicates(subset=["URL"]).reset_index(drop=True)

after_dedup = len(df)
df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
clear_progress()

print(f"\n✨ 수집 완료! '{OUTPUT_PATH}' 파일을 확인하세요.")
print(f"중복 제거 전: {before_dedup}건 | 중복 제거 후: {after_dedup}건")
print(f"체크포인트 파일: '{CHECKPOINT_PATH}'")
driver.quit()