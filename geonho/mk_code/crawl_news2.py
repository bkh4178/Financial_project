#%%
import time
import pandas as pd
import argparse
import os
import glob

from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# -----------------------------
# 설정
# -----------------------------
save_dir = "/Users/user/Desktop/bitamin/Financial_project/geonho/news"
os.makedirs(save_dir, exist_ok=True)

DELETE_TMP = True


# -----------------------------
# 날짜 보정 (-1일)
# -----------------------------
def adjust_start_date(start_date):
    d = datetime.strptime(start_date, "%Y-%m-%d")
    d -= timedelta(days=1)
    return d.strftime("%Y-%m-%d")


# -----------------------------
# 기간 분할
# -----------------------------
def split_date_range(start_date, end_date, months):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    ranges = []
    current = start

    while current < end:
        next_date = current + timedelta(days=30 * months)
        if next_date > end:
            next_date = end

        ranges.append((current.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d")))
        current = next_date + timedelta(days=1)

    return ranges


# -----------------------------
# totalCount 가져오기
# -----------------------------
def get_total_count(driver, keyword, start_date, end_date):
    url = f"https://www.mk.co.kr/search?word={keyword}&sort=asc&dateType=direct&startDate={start_date}&endDate={end_date}&searchField=all&newsType=all"

    if not safe_get(driver, url):
        return 0

    try:
        total_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "totalCount"))
        )
        total = int(total_elem.text.replace(",", ""))
    except:
        print(f"[{keyword}] totalCount 못 찾음 → fallback 0")
        total = 0

    print(f"[{keyword}] 총 기사 수: {total}")
    return total

def safe_get(driver, url, retries=5):
    for i in range(retries):
        driver.get(url)
        time.sleep(3)

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.news_node"))
            )
            return True
        except:
            print(f"⚠️ 재시도 {i+1}")
            time.sleep(5)

    # 🔥 핵심: driver 리셋
    print("🔥 driver 재시작")
    driver.quit()
    time.sleep(3)
    driver = webdriver.Chrome()

    return False

# -----------------------------
# 실제 크롤링
# -----------------------------
def crawl_range(keyword, start_date, end_date, driver):
    print(f"\n🔍 [{keyword}] {start_date} ~ {end_date}")

    url = f"https://www.mk.co.kr/search?word={keyword}&sort=asc&dateType=direct&startDate={start_date}&endDate={end_date}&searchField=all&newsType=all"

    if not safe_get(driver, url):
        print(f"[{keyword}] ❌ 페이지 로딩 실패 → 스킵")
        return pd.DataFrame()
    time.sleep(3)

    click_count = 0

    while True:
        articles = driver.find_elements(By.CSS_SELECTOR, "li.news_node")
        current_count = len(articles)

        print(f"[{keyword}] 기사 수: {current_count}")

        try:
            btn = driver.find_element(By.CSS_SELECTOR, "button[data-btn-more]")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)

            driver.execute_script("arguments[0].click();", btn)
            click_count += 1

            # 🔥 주기적 쿨다운
            if click_count % 50 == 0:
                print(f"[{keyword}] ⏸ 서버 쿨다운")
                time.sleep(10)

            for _ in range(10):
                time.sleep(4)
                new_count = len(driver.find_elements(By.CSS_SELECTOR, "li.news_node"))
                if new_count > current_count:
                    break
            else:
                print(f"[{keyword}] 증가 없음 → 종료")
                break

        except:
            print(f"[{keyword}] 버튼 없음 → 종료")
            break

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(4)

    articles = driver.find_elements(By.CSS_SELECTOR, "li.news_node")

    results = []

    for art in articles:
        try:
            title = art.find_element(By.CSS_SELECTOR, "h3.news_ttl").text
            date = art.find_element(By.CSS_SELECTOR, "p.time_info").text

            results.append({
                "keyword": keyword,
                "title": title,
                "date": date
            })
        except:
            continue

    df = pd.DataFrame(results).drop_duplicates()

    print(f"[{keyword}] 최종 수집: {len(df)}")
    return df


# -----------------------------
# 메인
# -----------------------------
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--keywords", nargs="+", required=True)
    parser.add_argument("--start_date", default="2019-01-01")
    parser.add_argument("--end_date", default="2025-12-31")

    args = parser.parse_args()

    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    for keyword in args.keywords:

        adj_start = adjust_start_date(args.start_date)

        ranges = split_date_range(adj_start, args.end_date, 6)

        for start, end in ranges:

            tmp_file = f"{save_dir}/tmp_{keyword}_{start}_{end}.csv"

            # 🔥 이미 있으면 스킵
            if os.path.exists(tmp_file):
                print(f"[{keyword}] 이미 존재 → 스킵 {start} ~ {end}")
                continue

            total = get_total_count(driver, keyword, start, end)

            try:
                if total == 0:
                    continue
                # -----------------------------
                # 1️⃣ 정상 구간
                # -----------------------------
                if total < 1800:
                    df = crawl_range(keyword, start, end, driver)
                    if len(df) > 0:
                        df.to_csv(tmp_file, index=False, encoding="utf-8-sig")
                    else:
                        print(f"[{keyword}] ⚠️ 데이터 없음 → 저장 스킵")

                # -----------------------------
                # 2️⃣ 많으면 3개월
                # -----------------------------
                else:
                    sub_ranges = split_date_range(start, end, 3)

                    sub_df_list = []

                    for s, e in sub_ranges:
                        sub_total = get_total_count(driver, keyword, s, e)

                        if sub_total < 1800:
                            sub_df = crawl_range(keyword, s, e, driver)
                            sub_df_list.append(sub_df)
                        else:
                            sub_sub_ranges = split_date_range(s, e, 1)

                            for ss, ee in sub_sub_ranges:
                                sub_df = crawl_range(keyword, ss, ee, driver)
                                sub_df_list.append(sub_df)

                    df = pd.concat(sub_df_list)
                    if len(df) > 0:
                        df.to_csv(tmp_file, index=False, encoding="utf-8-sig")
                    else:
                        print(f"[{keyword}] ⚠️ 데이터 없음 → 저장 스킵")

                print(f"[{keyword}] 저장 완료: {start} ~ {end}")

            except Exception as e:
                print(f"[{keyword}] 오류 발생: {start} ~ {end}")
                print(e)
                # 🔥 오류 발생 시 잠깐 쉬고 복구
                time.sleep(5)
                driver.refresh()
                continue

        # -----------------------------
        # 🔥 최종 병합
        # -----------------------------
        # 🔥 tmp 파일 불러오기
        tmp_files = glob.glob(f"{save_dir}/tmp_{keyword}_*.csv")
        df_new = pd.concat([pd.read_csv(f) for f in tmp_files])
        final_path = f"{save_dir}/mk_news_{keyword}.csv"

        # 🔥 기존 파일 있으면 불러오기
        if os.path.exists(final_path):
            df_old = pd.read_csv(final_path)

            final_df = pd.concat([df_old, df_new])
        else:
            final_df = df_new
            
        final_df = final_df.drop_duplicates(subset=["title", "date"])
        final_df = final_df.sort_values("date").reset_index(drop=True)

        final_df.to_csv(final_path, index=False, encoding="utf-8-sig")

        print(f"\n💾 최종 저장 완료: {final_path} ({len(final_df)})")

        # 🔥 브라우저 재시작 (서버 차단 방지)
        driver.quit()
        time.sleep(3)
        driver = webdriver.Chrome(options=options)

        # -----------------------------
        # 🔥 tmp 삭제
        # -----------------------------
        files = glob.glob(f"{save_dir}/tmp_{keyword}_*.csv")
        if DELETE_TMP:
            for f in files:
                os.remove(f)
            print(f"🧹 tmp 삭제 완료 ({len(files)}개)")

    driver.quit()


if __name__ == "__main__":
    main()