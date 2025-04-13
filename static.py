import requests
from bs4 import BeautifulSoup
import csv
import time
import re

class PTTPost:
    def __init__(self, title, link, date, push_count, content=""):
        self.title = title
        self.link = link
        self.date = date
        self.push_count = push_count
        self.content = content

    def to_dict(self):
        return {
            "推文數": self.push_count,
            "標題": self.title,
            "連結": self.link,
            "日期": self.date,
            "內文": self.content
        }

        
class PTTSpider:
    BASE_URL = "https://www.ptt.cc"
    
    def __init__(self, board, max_pages=5):
        self.board = board
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.cookies.set('over18', '1')  # PTT 18歲驗證
        self.posts = []

    def _fetch_page(self, url):
        print(f" Fetching: {url}")
        try:
            # 設定 headers 模擬瀏覽器（避免被擋）
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }

            # 發送 GET 請求（帶入 cookie + headers）
            res = self.session.get(url, headers=headers, timeout=10)

            # 若非成功狀態碼（200 OK），印錯誤並略過
            if res.status_code != 200:
                print(f" 抓取失敗：HTTP {res.status_code} - {url}")
                print("狀態碼：", res.status_code)
                print("回傳頁面前 300 字：", res.text[:300])
                return None

            # 設定編碼，避免亂碼
            res.encoding = 'utf-8'

            # 回傳 BeautifulSoup 物件，供後續解析
            return BeautifulSoup(res.text, "html.parser")

        except requests.RequestException as e:
            # 捕捉網路錯誤，例如連線逾時、DNS 錯誤等
            print(f" 請求錯誤：{e}")
            return None



    def _parse_posts(self, soup, keyword_filter=None):
        # 取得文章列表區塊（每篇文章都是 div.r-ent）
        entries = soup.select("div.r-ent")

        for entry in entries:
            # 取得文章標題與連結元素
            title_tag = entry.select_one("div.title a")
            push_tag = entry.select_one("div.nrec")  # 推文數區塊
            date_tag = entry.select_one("div.date")  # 發文日期

            # 如果文章被刪（沒有 a 標籤），就跳過
            if not title_tag:
                continue

            title = title_tag.text.strip()

            # 跳過公告文
            if "[公告]" in title:
                continue

            link = self.BASE_URL + title_tag['href']  # 組合完整文章連結
            date = date_tag.text.strip()  # 發文日期
            push_text = push_tag.text.strip() if push_tag else "0"  # 推文數字串（如 爆、X1、15）

            # 特殊推文處理
            if push_text == "爆":
                push_count = 100
            elif re.match(r'X\d+', push_text):  # 負推文，例如 X1 → -1
                push_count = -int(push_text[1:])
            else:
                try:
                    push_count = int(push_text)  # 正常推文數
                except:
                    push_count = 0  # 無法解析時預設為 0

            # 抓取內文主文（排除推文）
            content = self._fetch_article_content(link)

            # 若有設定關鍵字，需篩選是否包含（標題＋內文）
            if keyword_filter:
                if not any(keyword.lower() in (title + content).lower() for keyword in keyword_filter):
                    continue  # 若不包含關鍵字則跳過

            # 將符合條件的文章轉為 PTTPost 並存入列表
            post = PTTPost(title, link, date, push_count, content)
            self.posts.append(post)

    def _get_next_page_url(self, soup):
        btns = soup.select("div.btn-group-paging a")
        for btn in btns:
            if "上頁" in btn.text:
                return self.BASE_URL + btn["href"]
        return None
    
    # 主爬蟲邏輯：連續抓多頁文章
    def crawl(self, keyword_filter=None):
        url = f"{self.BASE_URL}/bbs/{self.board}/index.html"
        for _ in range(self.max_pages):
            # 抓取當前頁面的 HTML 內容並轉成 BeautifulSoup 物件
            soup = self._fetch_page(url)    
            # 解析這一頁的所有文章（依據關鍵字過濾）
            self._parse_posts(soup, keyword_filter) 
            # 找到下一頁的 URL 
            url = self._get_next_page_url(soup)
            if not url:
                break
        #time.sleep(1)


    def save_to_csv(self, filename):
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["推文數", "標題", "連結", "日期", "內文"])
            writer.writeheader()
            for post in self.posts:
                writer.writerow(post.to_dict())
        print(f" CSV 檔案已儲存：{filename}")

        
    def _fetch_article_content(self, url):
        try:
            soup = self._fetch_page(url)
            main_content = soup.select_one("#main-content")
            if not main_content:
                return ""

            # Step 1：找出「發信站」在哪個 <span class="f2">
            cut_node = None
            for span in main_content.find_all("span", class_="f2"):
                if "發信站" in span.text:
                    cut_node = span
                    break
            # if url == "https://www.ptt.cc/bbs/Lifeismoney/M.1735838860.A.6F3.html":
            #     print(main_content)
            
            # Step 2：kill div 移除文章頭的作者/時間資訊區塊
            for tag in main_content.find_all(["div"], class_=["article-metaline", "article-metaline-right"]):
                tag.decompose()
                
            
            # if url == "https://www.ptt.cc/bbs/Lifeismoney/M.1735838860.A.6F3.html":
            #     print("\n\nafter\n\n")
            #     print(main_content)
                
            # Step 3：only get 發信站 previous text
            text_lines = []
            # .contents 只抓「最外層的直接子節點」
            for content in main_content.descendants:
                # 停在發信站
                if content == cut_node:
                    break
                # 處理純文字
                elif isinstance(content, str):
                    line = content.strip()
                    if line:
                        text_lines.append(line)

            return "\n".join(text_lines)

        except Exception as e:
            print(f"⚠️ 無法讀取文章：{url}，錯誤：{e}")
            return ""
        
        
if __name__ == "__main__":
    #keywords = ["LINE", "蝦皮", "pChome", "優惠"]
    keywords = ["LINE"]
    spider = PTTSpider("Lifeismoney", max_pages=5)
    try:
        spider.crawl(keyword_filter=keywords)
    except Exception as e:
        print(f"❌ 程式錯誤：{e}")
        exit(1)
    spider.save_to_csv("static.csv")

