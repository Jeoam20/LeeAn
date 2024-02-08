import pyupbit
import discord
import asyncio



tickers = pyupbit.get_tickers(fiat="KRW")
rsi_list = []


# 메시지를 여러 개로 나누는 함수


def get_rsi(df, period=14):
    if df is None or len(df) < period:
        return None
    
    # 5분전 대비 변동 평균
    df['change'] = df['close'].diff()

    # 상승한 가격과 하락한 가격
    df['up'] = df['change'].apply(lambda x: x if x > 0 else 0)
    df['down'] = df['change'].apply(lambda x: -x if x < 0 else 0)

    # 상승 평균과 하락 평균
    df['avg_up'] = df['up'].ewm(alpha=1/period).mean()
    df['avg_down'] = df['down'].ewm(alpha=1/period).mean()

    # 상대강도지수(RSI) 계산
    df['rs'] = df['avg_up'] / df['avg_down']
    df['rsi'] = 100 - (100 / (1 + df['rs']))
    rsi = df['rsi']


    return rsi



class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == 'rsi30':
            await message.channel.send("과매도 상태인 코인을 탐색중입니다.")
            while True:
                print("탐색중")
                for ticker in tickers:
                    await asyncio.sleep(0.1)
                    df_day = pyupbit.get_ohlcv(ticker, interval="minute5")

                    # 데이터가 없을 경우 처리
                    if df_day is not None:
                        rsi14 = get_rsi(df_day, 14).iloc[-1]

                        if rsi14 is not None:
                            if rsi14 <= 30:
                                await message.channel.send(str(ticker) + ":" + str(rsi14))
                        else:
                            print("rsi14의 데이터가 누락되었습니다.")
                    else:
                        print("df_day의 데이터가 누락되었습니다.")

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run("토큰")
