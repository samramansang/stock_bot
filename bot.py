import asyncio, schedule, time, feedparser
import yfinance as yf
from telegram import Bot
from datetime import datetime

BOT_TOKEN = "8652666937:AAEysm8U-78BHbUSyqIa-rLZLyzzecHGZfM"   
CHAT_ID   = "5310810623"   

KR_STOCKS = {"005930.KS": "삼성전자", "000660.KS": "SK하이닉스"}
US_STOCKS = ["AAPL", "NVDA", "SPY"]

async def send_newsletter():
    bot = Bot(BOT_TOKEN)
    today = datetime.now().strftime("%Y.%m.%d")
    msg = f"📊 *오늘의 시장 브리핑* ({today})\n\n"

    msg += "🇰🇷 *국내 시장*\n"
    for ticker, name in KR_STOCKS.items():
        try:
            info = yf.Ticker(ticker).fast_info
            price = info.last_price
            prev  = info.previous_close
            change = (price - prev) / prev * 100
            arrow = "▲" if change > 0 else "▼"
            msg += f"  {name}: {price:,.0f}원 {arrow}{abs(change):.1f}%\n"
        except:
            pass

    msg += "\n🇺🇸 *미국 시장*\n"
    for ticker in US_STOCKS:
        try:
            info = yf.Ticker(ticker).fast_info
            price = info.last_price
            prev  = info.previous_close
            change = (price - prev) / prev * 100
            arrow = "▲" if change > 0 else "▼"
            msg += f"  {ticker}: ${price:.1f} {arrow}{abs(change):.1f}%\n"
        except:
            pass

    try:
        krw = yf.Ticker("USDKRW=X").fast_info.last_price
        msg += f"\n💱 달러/원: {krw:.0f}원\n"
    except:
        pass

    msg += "\n📰 *주요 뉴스*\n"
    feed = feedparser.parse("https://feeds.finance.yahoo.com/rss/2.0/headline")
    for entry in feed.entries[:3]:
        msg += f"  • {entry.title[:40]}...\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    print(f"✅ 발송 완료: {datetime.now()}")

def job():
    asyncio.run(send_newsletter())

schedule.every().day.at("08:00").do(job)
print("🤖 봇 시작됨! 매일 오전 8시에 발송됩니다.")
job()
while True:
    schedule.run_pending()
    time.sleep(60)
