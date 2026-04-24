import asyncio, schedule, time, feedparser, os, requests
import pytz
from telegram import Bot
from datetime import datetime

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHAT_ID   = os.environ.get('CHAT_ID', '')
ALPHA_KEY = os.environ.get('ALPHA_KEY', '')
KR_TZ = pytz.timezone('Asia/Seoul')
print('ALPHA_KEY 확인:' + ALPHA_KEY[:5] + '...')

KR_STOCKS = {'005930': '삼성전자', '000660': 'SK하이닉스'}
US_STOCKS = ['AAPL', 'NVDA', 'SPY']

def get_price_us(ticker):
    try:
        time.sleep(15)
        url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=' + ticker + '&apikey=' + ALPHA_KEY
        r = requests.get(url).json()
        print('US 응답:' + str(r)[:100])
        q = r['Global Quote']
        price = float(q['05. price'])
        change = float(q['10. change percent'].replace('%',''))
        return price, change
    except Exception as e:
        print('US 오류:' + str(e))
        return None, None

def get_price_kr(ticker):
    try:
        time.sleep(15)
        url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=' + ticker + '.KS&apikey=' + ALPHA_KEY
        r = requests.get(url).json()
        print('KR 응답:' + str(r)[:100])
        q = r['Global Quote']
        price = float(q['05. price'])
        change = float(q['10. change percent'].replace('%',''))
        return price, change
    except Exception as e:
        print('KR 오류:' + str(e))
        return None, None

async def send_newsletter():
    bot = Bot(BOT_TOKEN)
    today = datetime.now(KR_TZ).strftime('%Y.%m.%d')
    msg = '📊 *오늘의 시장 브리핑* (' + today + ')\n\n'
    msg += '🇰🇷 *국내 시장*\n'
    for ticker, name in KR_STOCKS.items():
        price, change = get_price_kr(ticker)
        if price:
            arrow = '▲' if change > 0 else '▼'
            msg += '  ' + name + ': ' + format(price, ',.0f') + '원 ' + arrow + format(abs(change), '.1f') + '%\n'
        else:
            msg += '  ' + name + ': 데이터 없음\n'
    msg += '\n🇺🇸 *미국 시장*\n'
    for ticker in US_STOCKS:
        price, change = get_price_us(ticker)
        if price:
            arrow = '▲' if change > 0 else '▼'
            msg += '  ' + ticker + ': $' + format(price, '.1f') + ' ' + arrow + format(abs(change), '.1f') + '%\n'
        else:
            msg += '  ' + ticker + ': 데이터 없음\n'
    msg += '\n📰 *주요 뉴스*\n'
    try:
        feed = feedparser.parse('https://feeds.reuters.com/reuters/businessNews')
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
