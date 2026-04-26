import asyncio, schedule, time, feedparser, os, requests
import pytz
from telegram import Bot
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "")
KR_TZ = pytz.timezone("Asia/Seoul")

KR_STOCKS = {
    "005930": "삼성전자", "000660": "SK하이닉스",
    "373220": "LG에너지솔루션", "207940": "삼성바이오로직스",
    "005380": "현대차", "000270": "기아",
    "068270": "셀트리온", "005490": "POSCO홀딩스",
    "006400": "삼성SDI", "105560": "KB금융",
}

US_STOCKS = {
    "AAPL": "애플", "MSFT": "마이크로소프트",
    "NVDA": "엔비디아", "AMZN": "아마존",
    "META": "메타", "GOOGL": "구글",
    "TSLA": "테슬라", "AVGO": "브로드컴",
    "COST": "코스트코", "NFLX": "넷플릭스",
}

def get_price_kr(code):
    try:
        url = "https://finance.naver.com/item/main.naver?code=" + code
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        tags = soup.select(".no_today .blind, .no_exday .blind")
        if len(tags) >= 3:
            p = float(tags[0].text.replace(",",""))
            c = float(tags[2].text.replace(",","").replace("%",""))
            return p, c
    except Exception as e:
        print("KR오류:" + str(e))
    return None, None

def get_price_us(ticker):
    try:
        url = "https://finance.naver.com/item/main.naver?code=" + ticker + "&fdtc=0"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        tags = soup.select(".no_today .blind, .no_exday .blind")
        if len(tags) >= 3:
            p = float(tags[0].text.replace(",",""))
            c = float(tags[2].text.replace(",","").replace("%",""))
            return p, c
    except Exception as e:
        print("US오류:" + str(e))
    return None, None

def get_news():
    urls = [
        "https://www.yonhapnewstv.co.kr/browse/feed/",
        "https://rss.joins.com/joins_economy_list.xml",
        "https://rss.etnews.com/Section901.xml",
    ]
    result = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                result.extend(feed.entries[:4])
        except:
            continue
    return result[:10]

async def send_newsletter():
    bot = Bot(BOT_TOKEN)
    today = datetime.now(KR_TZ).strftime("%Y.%m.%d")
    msg = "📊 *오늘의 시장 브리핑* (" + today + ")\n\n"
    msg += "🇰🇷 *코스피 시총 TOP 10*\n"
    for code, name in KR_STOCKS.items():
        price, change = get_price_kr(code)
        if price:
            arrow = "▲" if change > 0 else "▼"
            msg += "  " + name + ": " + format(price, ",.0f") + "원 " + arrow + format(abs(change), ".1f") + "%\n"
        else:
            msg += "  " + name + ": 데이터 없음\n"
    msg += "\n🇺🇸 *나스닥 시총 TOP 10*\n"
    for ticker, name in US_STOCKS.items():
        price, change = get_price_us(ticker)
        if price:
            arrow = "▲" if change > 0 else "▼"
            msg += "  " + name + "(" + ticker + "): $" + format(price, ".1f") + " " + arrow + format(abs(change), ".1f") + "%\n"
        else:
            msg += "  " + name + "(" + ticker + "): 데이터 없음\n"
    msg += "\n📰 *주요 뉴스*\n"
    news = get_news()
    if news:
        for entry in news:
            msg += "  • " + entry.title + "\n"
    else:
        msg += "  뉴스 없음\n"
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    print("✅ 발송 완료: " + str(datetime.now(KR_TZ)))

def job():
    asyncio.run(send_newsletter())

schedule.every().day.at("08:00").do(job)
print("🤖 봇 시작됨! 매일 한국시간 오전 8시에 발송됩니다.")
job()
while True:
    schedule.run_pending()
    time.sleep(60)
