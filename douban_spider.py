import requests
from bs4 import BeautifulSoup
import json
import os
import time
import ssl  # 新增：解决SSL问题

# 忽略SSL证书验证（针对HTTPS）
ssl._create_default_https_context = ssl._create_unverified_context

# 从环境变量读取豆瓣链接（用HTTPS，浏览器会强制跳转）
DOUBAN_COLLECT_URL = os.getenv("DOUBAN_COLLECT_URL")
if not DOUBAN_COLLECT_URL:
    print("错误：未设置 DOUBAN_COLLECT_URL 环境变量")
    exit(1)

# 配置请求头（模拟浏览器，适配HTTPS）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://movie.douban.com/",  # HTTPS对应
    "Upgrade-Insecure-Requests": "1"  # 告诉服务器允许HTTPS跳转
}

all_poster_urls = set()


def get_total_page_count():
    """从链接参数解析总页数（兼容HTTPS）"""
    try:
        # 允许重定向（应对HTTP自动跳HTTPS）
        response = requests.get(DOUBAN_COLLECT_URL, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paginator = soup.find("div", class_="paginator")

        if not paginator:
            return 1

        page_nums = []
        for a_tag in paginator.find_all("a"):
            href = a_tag.get("href", "")
            if "start=" in href:
                start_num = href.split("start=")[-1].split("&")[0]
                if start_num.isdigit():
                    page = int(start_num) // 20 + 1
                    page_nums.append(page)

        total = max(page_nums) if page_nums else 1
        print(f"解析到总页数：{total}")
        return total

    except Exception as e:
        print(f"获取总页数失败：{e}")
        return 1


def crawl_page(page_num):
    """爬取单页海报（适配HTTPS）"""
    start = (page_num - 1) * 20
    # 用HTTPS链接，避免跳转问题
    page_url = f"{DOUBAN_COLLECT_URL}?start={start}&sort=time&rating=all&filter=all&mode=grid"

    try:
        response = requests.get(page_url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        movie_items = soup.find_all("div", class_="item")

        if not movie_items:
            print(f"第{page_num}页无内容，跳过")
            return

        count = 0
        for item in movie_items:
            img_tag = item.find("img", class_="cover")
            if img_tag and img_tag.get("src"):
                poster_url = img_tag["src"].replace("s_ratio_poster", "m_ratio_poster")
                all_poster_urls.add(poster_url)
                count += 1

        print(f"第{page_num}页爬取完成，新增{count}张海报")

    except Exception as e:
        print(f"第{page_num}页爬取失败：{e}")


def main():
    total_pages = get_total_page_count()
    for page in range(1, total_pages + 1):
        crawl_page(page)
        time.sleep(2)  # 降低频率，避免反爬

    posters = list(all_poster_urls)
    with open("posters.json", "w", encoding="utf-8") as f:
        json.dump(posters, f, ensure_ascii=False, indent=2)

    print(f"\n全部完成！共{len(posters)}张海报")


if __name__ == "__main__":
    main()