import pyupbit
import math
import time

# Upbit API 연동
access_key = 'fM9Ya2lyy4o6xbPs8McKztx1U3XxDtPWz5N6i10d'
secret_key = 'o2tmwu5cKeeSBMlwtKRk3ayJ4BiUcMfbiphzN0aO'
upbit = pyupbit.Upbit(access_key, secret_key)

balances = upbit.get_balances()

ticker_count = 3                                        # 티커의 갯수
tickers = ["KRW-SUI", "KRW-SOL", "KRW-XRP"]				        # 코인을 티커로 지정

my_money = float(balances[0]['balance'])     # 내 원화
money = my_money / ticker_count                # 비트코인에 할당할 비용
money = math.floor(money)		             # 소수점 버림

buy_coin = math.floor(money/2)    # 첫 매수 비중
buy_coin_plus = -0.8 #분할 매수 타이밍
sell_coin = -1.1     #손절타이밍

target_revenue = 3       # 목표 수익률 
min_target_revenue = 0.2   # 첫 번째 익절 수익률
max_target_revenue = 0.5   # 두 번째 익절 수익률
min_sell = 0.4 #첫 번째 익절 비율
max_sell = 0.3 #두 번째 익절 비율

sell_count = [0,0,0]
buy_count = [0,0,0]
rsi_sell_count = [0,0,0]

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


# 이미 매수한 코인인지 확인
def has_coin(ticker, balances):
    result = False
    
    for coin in balances:
        coin_ticker = coin['unit_currency'] + "-" + coin['currency']
        
        if ticker == coin_ticker:
            result = True
            
    return result
    
def get_revenue_rate(balances, ticker):
    revenue_rate = 0.0

    for coin in balances:
        # 티커 형태로 전환
        coin_ticker = coin['unit_currency'] + "-" + coin['currency']

        if ticker == coin_ticker:
            # 현재 시세
            now_price = pyupbit.get_current_price(coin_ticker)
             
            # 수익률 계산을 위한 형 변환
            revenue_rate = ((now_price / float(coin['avg_buy_price']))-1) * 100.0

    return revenue_rate

def start_code(ticker):
    balances = upbit.get_balances()
    my_money = float(balances[0]['balance'])
    df_day = pyupbit.get_ohlcv(ticker, interval="minute5")     # 5분봉 정보
    time.sleep(0.3)
    rsi_data = get_rsi(df_day, 14)                           

    if rsi_data is not None:
        rsi14 = rsi_data.iloc[-1]                           # 현재 RSI
        before_rsi14 = rsi_data.iloc[-2]                    # 5분전 RSI
        if ticker == tickers[0]:
            ticker_number = 0
        elif ticker == tickers[1]:
            ticker_number = 1

        if has_coin(ticker, balances):

            ticker_rate = get_revenue_rate(balances, ticker)     # 수익률 확인
            #첫 번째 익절 수익률 돌파시 첫 번째 분할 매도
            if ticker_rate >= min_target_revenue and ticker_rate < max_target_revenue and sell_count[ticker_number] == 0 and rsi_sell_count[ticker_number] == 0:
                amount = upbit.get_balance(ticker)                  # 현재 코인 보유 수량
                upbit.sell_market_order(ticker, amount * min_sell)             # 시장가에 매도 
                balances = upbit.get_balances()                     # 매도했으니 잔고를 최신화!
                sell_count[ticker_number] = 1

            elif ticker_rate >= max_target_revenue and ticker_rate < target_revenue and sell_count[ticker_number] == 1 and rsi_sell_count[ticker_number] == 0:
                amount = upbit.get_balance(ticker)                  # 현재 코인 보유 수량
                upbit.sell_market_order(ticker, amount * max_sell)             # 시장가에 매도 
                balances = upbit.get_balances()                     # 매도했으니 잔고를 최신화!
                sell_count[ticker_number] = 2
            elif ticker_rate >= target_revenue and rsi_sell_count[ticker_number] == 0:
                amount = upbit.get_balance(ticker)                  # 현재 코인 보유 수량
                upbit.sell_market_order(ticker, amount)             # 시장가에 매도 
                balances = upbit.get_balances()                     # 매도했으니 잔고를 최신화!
                sell_count[ticker_number] = 0
                rsi_sell_count[ticker_number] = 0

            if ticker_rate >= target_revenue:
                # 과매수 상태이면 rsi14 >= 70
                if rsi14 >= 70 and rsi14 < before_rsi14:
                    amount = upbit.get_balance(ticker)                  # 현재 코인 보유 수량
                    upbit.sell_market_order(ticker, amount)             # 시장가에 매도 
                    balances = upbit.get_balances()                     # 매도했으니 잔고를 최신화!
                    sell_count[ticker_number] = 0
                    rsi_sell_count[ticker_number] = 0
                    time.sleep(3)
                elif rsi14 >= 70 and rsi_sell_count[ticker_number] == 0 and rsi_sell_count[ticker_number] == 0:
                    amount = upbit.get_balance(ticker)                  # 현재 코인 보유 수량
                    upbit.sell_market_order(ticker, amount * 0.5)             # 시장가에 매도 
                    balances = upbit.get_balances()                     # 매도했으니 잔고를 최신화!
                    rsi_sell_count[ticker_number] = 1

                    time.sleep(3)

        else:
            # 매수 조건 충족
            if rsi14 > before_rsi14 and before_rsi14 < 30:
                print("매수조건충족")
                upbit.buy_market_order(ticker, buy_coin)   # 시장가에 코인 매수
                balances = upbit.get_balances()         		   # 매수했으니 잔고를 최신화!
                time.sleep(3)

        print("my_money : " + str(my_money))
        print("price : " + str(pyupbit.get_current_price(ticker)))
        print("rsi14 : " + str(rsi14))
        print("coin : " + str(upbit.get_balance(ticker)))

        ticker_rate = get_revenue_rate(balances, ticker)
        balances = upbit.get_balances()
        have_coin = 0.0
        for coin in balances:
            coin_ticker = coin['unit_currency'] + "-" + coin['currency']

            if ticker == coin_ticker:
                have_coin = float(coin['avg_buy_price']) * float(coin['balance'])
                ticker_rate = get_revenue_rate(balances, ticker)

                # 실제 매수된 금액의 오차 감안
                if have_coin >= 5500:
                    if ticker_rate <= sell_coin:
                        amount = upbit.get_balance(ticker)       # 현재 코인 보유 수량	  
                        upbit.sell_market_order(ticker, amount)   # 시장가에 매도
                        balances = upbit.get_balances()         		   # 매도했으니 잔고를 최신화!
                        time.sleep(3)

                    elif ticker_rate <= buy_coin_plus and money >= 5500:
                        upbit.buy_market_order(ticker, buy_coin)   # 시장가에 코인 매수
                        balances = upbit.get_balances()         		   # 매수했으니 잔고를 최신화!
                        time.sleep(3)
    else:
        print("오류: RSI를 계산할 수 없습니다. 입력 데이터 또는 get_rsi 함수를 확인하세요.")

    
while True:

    for count_ticker in range(ticker_count):
        start_code(tickers[count_ticker])
    