import asyncio, schedule, time, feedparser, os
import yfinance as yf
import pytz
from telegram import Bot
from datetime import datetime

BOT_TOKEN = os.environ.get('BOT_TOKEN', '여기에_봇_토큰_입력')
CHAT_ID   = os.environ.get('CHAT_ID', '여기에_채팅ID_입력')
KR_TZ = pytz.timezone('Asia/Seoul')

KR_STOCKS = {'005930.KS': '삼성전자', '000660.KS': 'SK하이닉스'}
US_STOCKS = ['AAPL', 'NVDA', 'SPY']

def get_price(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period='1mo')
        if len(hist) >= 2:
            price = hist['Close'].iloc[-1]
            prev  = hist['Close'].iloc[-2]
            change = (price - prev) / prev * 100
            return price, change
        elif len(hist) == 1:
            return hist['Close'].iloc[0], 0
    except:
        pass
    return None, None

async def send_newsletter():
    bot = Bot(BOT_TOKEN)
    today = datetime.now(KR_TZ).strftime('%Y.%m.%d')
    weekday = datetime.now(KR_TZ).strftime('%A')
    msg = '📊 *오늘의 시장 브리핑* (' + today + ')\n\n'
    msg += '🇰🇷 *국내 시장*\n'
    for ticker, name in KR_STOCKS.items():
        price, change = get_price(ticker)
        if price:
            arrow = '▲' if change > 0 else '▼'
            msg += '  ' + name + ': ' + format(price, ',.0f') + '원 ' + arrow + format(abs(change), '.1f') + '%\n'
        else:
            msg += '  ' + name + ': 데이터 없음\n'
    msg += '\n🇺🇸 *미국 시장*\n'
    for ticker in US_STOCKS:
        price, change = get_price(ticker)
        if price:
            arrow = '▲' if change > 0 else '▼'
            msg += '  ' + ticker + ': $' + format(price, '.1f') + ' ' + arrow + format(abs(change), '.1f') + '%\n'
        else:
            msg += '  ' + ticker + ': 데이터 없음\n'
    try:
        price, _ = get_price('USDKRW=X')
        if price:
            msg += '\n💱 달러/원: ' + format(price, '.0f') + '원\n'
    except:
        pass
    msg += '\n📰 *주요 뉴스*\n'
    try:
        feed = feedparser.parse('https://feeds.finance.yahoo.com/rss/2.0/headline')
        for entry in feed.entries[:3]:
            msg += '  • ' + entry.title[:40] + '...\n'
    except:
        pass
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
    print('✅ 발송 완료: ' + str(datetime.now(KR_TZ)))

def job():
    asyncio.run(send_newsletter())

schedule.every().day.at('08:00').do(job)
print('🤖 봇 시작됨! 매일 한국시간 오전 8시에 발송됩니다.')
job()
while True:
    schedule.run_pending()
    time.sleep(60)
