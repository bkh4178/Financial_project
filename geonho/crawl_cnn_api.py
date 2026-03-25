#%%
import requests
import argparse
import csv
from datetime import datetime
import time
import uuid

BASE_URL = "https://search.prod.di.api.cnn.io/content"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://edition.cnn.com/",
    "Origin": "https://edition.cnn.com"
}

def get_articles(keyword, offset):

    params = {
        "q": keyword,
        "size": 10,
        "from": offset,
        "sort": "newest",
        "site": "cnn",
        "types": "all",
        "request_id": str(uuid.uuid4())
    }

    res = requests.get(BASE_URL, params=params, headers=HEADERS)
    print("STATUS:", res.status_code)
    print("RESPONSE SAMPLE:", res.text[:300])
    data = res.json()
    print("RESULT COUNT:", len(data.get("result", [])))

    articles = []

    for item in data.get("result", []):
        try:
            title = item.get("headline")
            url = item.get("url") or item.get("path")
            date_str = item.get("firstPublishDate") or item.get("lastModifiedDate") or item.get("date")

            if not (title and url and date_str):
                continue

            date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)

            articles.append({
                "title": title,
                "url": url,
                "date": date
            })

        except:
            continue

    return articles


def crawl(keyword, start_date, end_date, max_pages):
    start = datetime.fromisoformat(start_date).replace(tzinfo=None)
    end = datetime.fromisoformat(end_date).replace(tzinfo=None)

    results = []
    seen = set()

    offset = 0
    page = 1
    while True:
        print(f"[Page {page}] offset={offset}")

        articles = get_articles(keyword, offset)
        if not articles:
            print("No more articles from API → STOP")
            break

        stop_flag = False

        for article in articles:

            # 날짜 필터
            if article["date"] < start:
                stop_flag = True
                break

            if article["date"] > end:
                continue

            if article["title"] in seen:
                continue

            seen.add(article["title"])
            results.append(article)

        if stop_flag:
            print(f"Reached older than start date → STOP at {article['date']}")
            break

        offset += 10
        page += 1
        time.sleep(0.5)

    print(f"\nCollected: {len(results)} articles for keyword: {keyword}")

    safe_keyword = keyword.replace(" ", "_")
    filename = f"cnn_{safe_keyword}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "title", "url"])

        for r in results:
            writer.writerow([
                r["date"].isoformat(),
                r["title"],
                r["url"]
            ])
    print(f"Saved to {filename}")


# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", nargs="+", required=True)
    parser.add_argument("--pages", type=int, default=5)
    parser.add_argument("--start", type=str, default="2019-01-01")
    parser.add_argument("--end", type=str, default="2025-12-31")

    args = parser.parse_args()

    for kw in args.keywords:
        print(f"\n===== Crawling keyword: {kw} =====")
        crawl(
            keyword=kw,
            start_date=args.start,
            end_date=args.end,
            max_pages=args.pages
        )
        
