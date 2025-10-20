import requests
import json
import os
import time

# 读取环境变量（必须配置正确）
DOUBAN_URL = os.getenv("DOUBAN_COLLECT_URL")
COOKIE = os.getenv("DOUBAN_COOKIE", "")

if not DOUBAN_URL:
    print("错误：未设置 DOUBAN_COLLECT_URL")
    exit(1)

# 关键：模拟真实浏览器请求头（包含Cookie）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": COOKIE,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://movie.douban.com/",
    "Connection": "keep-alive"
}

# 存储海报链接（去重）
posters = set()

def crawl_all_posters():
    """循环爬取所有页面，直到没有新海报"""
    page = 0  # 从第0页开始（start=0, 20, 40...）
    while True:
        start = page * 20
        url = f"{DOUBAN_URL}?start={start}&sort=time&rating=all&filter=all&mode=grid"
        print(f"爬取页面：{url}")
        
        try:
            # 发送请求（带Cookie，允许重定向）
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()  # 检查请求是否成功
            html = response.text
            
            # 关键：从HTML中直接提取海报链接（豆瓣海报链接格式固定）
            # 海报链接格式：https://img9.doubanio.com/view/photo/s_ratio_poster/public/p1234567.jpg
            start_marker = 'src="https://img'
            end_marker = '" class="cover"'
            
            # 循环提取当前页所有海报
            page_posters = []
            index = 0
            while True:
                # 找到海报链接的起始位置
                index = html.find(start_marker, index)
                if index == -1:
                    break  # 没有更多海报了
                # 找到链接结束位置
                end_index = html.find(end_marker, index)
                if end_index == -1:
                    break
                # 提取完整链接
                poster_url = html[index + 5 : end_index]  # 去掉开头的 'src="'
                # 替换为中等清晰度
                poster_url = poster_url.replace("s_ratio_poster", "m_ratio_poster")
                page_posters.append(poster_url)
                index = end_index  # 继续查找下一个
            
            # 检查当前页是否有新海报
            if not page_posters:
                print(f"第{page+1}页未找到海报，停止爬取")
                break
            
            # 添加到集合（自动去重）
            posters.update(page_posters)
            print(f"第{page+1}页爬取成功，新增{len(page_posters)}张海报（累计：{len(posters)}）")
            
            # 翻页（最多爬50页，避免无限循环，可根据需要调整）
            page += 1
            if page >= 50:
                print("已爬取50页，自动停止")
                break
            
            time.sleep(3)  # 延迟3秒，降低反爬风险
            
        except Exception as e:
            print(f"爬取失败：{str(e)}，停止爬取")
            break

# 主逻辑
if __name__ == "__main__":
    crawl_all_posters()
    # 保存结果到posters.json
    with open("posters.json", "w", encoding="utf-8") as f:
        json.dump(list(posters), f, ensure_ascii=False, indent=2)
    print(f"\n爬取完成，共获取{len(posters)}张海报，已保存到posters.json")
