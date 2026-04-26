import asyncio, schedule, time, feedparser, os, requests
import pytz
from telegram import Bot
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHAT_ID   = os.environ.get('CHAT_ID', '')
ALPHA_KEY = os.environ.get('ALPHA_KEY', '')
KR_TZ = pytz.timezone('Asia/Seoul')

KR_STOCKS = {'005930': '삼성전자', '000660': 'SK하이닉스'}
US_STOCKS = ['AAPL', 'NVDA', 'SPY']

def get_price_kr(code):
    try:
        url = 'https://finance.naver.com/item/main.naver?code=' + code
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        price = soup.select_one('.no_today .blind')
        change = soup.select_one('.no_exday .blind')
        if price and change:
            p = float(price.text.replace(',',''))
            c = float(change.text.replace(',','').replace('%',''))
            return p, c
    except Exception as e:
        print('KR오류:' + str(e))
    return None, None

def get_price_us(ticker):
    try:
        time.sleep(15)
        url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=' + ticker + '&apikey=' + ALPHA_KEY
        r = requests.get(url, timeout=10).json()
        q = r.get('Global Quote', {})
        if not q or '05. price' not in q:
            return None, None
        price = float(q['05. price'])
        change = float(q['10. change percent'].replace('%',''))
        return price, change
    except Exception as e:
        print('US오류:' + str(e))
        return None, None

def get_news():
    urls = [
        'https://feeds.bbci.co.uk/news/business/rss.xml',
        'https://rss.cnn.com/rss/money_latest.rss',
    ]
    for url in urls:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                return feed.entries[:3]
        except:
            continue
    return []

async def send_newsletter():
    bot = Bot(BOT_TOKEN)
    today = datetime.now(KR_TZ).strftime('%Y.%m.%d')
    msg = '📊 *오늘의 시장 브리핑* (' + today + ')\n\n'
    msg += '🇰🇷 *국내 시장*\n'
    for code, name in KR_STOCKS.items():
        price, change = get_price_kr(code)
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
    news = get_news()
    if news:
        for entry in news:
            msg += '  • ' + entry.title[:35] + '\n'
    else:
        msg += '  뉴스 없음\n'
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
