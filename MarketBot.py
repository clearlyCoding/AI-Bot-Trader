from lumibot.brokers import Alpaca # type: ignore
from lumibot.backtesting import PolygonDataBacktesting
from lumibot.entities import Asset
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime 
from alpaca_trade_api import REST  # type: ignore
from timedelta import Timedelta  # type: ignore
from finbert_utils import estimate_sentiment
import numpy as np
import requests
import json
import random
API_KEY = "PKJYF05FPJGXH57IXVUK" 
API_SECRET = "t4siryHdAd5gfwTxsfZbMCkwfafvPzJIFEspuuaq" 
BASE_URL = "https://paper-api.alpaca.markets/v2"
POSITIONS_URL = "https://paper-api.alpaca.markets/v2/positions"
POLYGONKEY = "hwXFX1sSXE4ojhYyeKDA7BBJDlaLf6Pf"
tickertest = ['NVDA','SOXX','AAPL', 'SPY']
ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET, 
    "PAPER": True
}

class MLTrader(Strategy): 
    data = {}
    order_number = 0
    cash_history = 0
    last_action = ""
    action_price = 0
    diary = {}
    pages = {}
    order =[]
    def initialize(self, symbol:str=tickertest, budget_buffer_risk:float=.75): 
        self.symbol = symbol
        for items in self.symbol:
            self.data[items] = []
        self.sleeptime = "1s"
        self.risk_p = budget_buffer_risk
        self.asset = Asset(self.symbol, asset_type=Asset.AssetType.STOCK)
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)

    def position_sizing(self, symbol, list):
        SLOPE_PERIODS = 5
        r = self.risk_p
        b = self.initial_budget
        t = len(self.symbol)
        lpt = self.get_last_price(symbol)
        print(f"{lpt} current for {symbol}")
        temperment = "+"
        cash = self.get_cash()
        fcf_t = r*b/t 
        if len(list) >=SLOPE_PERIODS:
            slope = self.slope_extract(list)
            if slope > 0 and cash > (b - (r*b)): #keeps budget floor
                qty_t = round(fcf_t/lpt,0)
                print (f"{qty_t} qty determined.")
            else:
                print (f"conditions not met, PROC= {slope} current cash = {cash}, willing {b-(r*b)}.")
                qty_t = 0
                temperment = '-'

        return fcf_t, qty_t, lpt, temperment

    def swing_session(self): #old 
        print ("Swing session strategy engaged")
        cash, last_price, quantityz = self.position_sizing()
        print(f"Position: {self.get_position(self.symbol)}")
        pos = self.get_position(self.symbol)
        self.data.append(self.get_last_price(self.symbol))
        if len (self.data) >3:
            temp = self.data[-3:]
            if temp[-1] > temp[1] > temp[0] and self.last_action != "buy" and quantityz>0:
                order = self.create_order(self.symbol, quantity = quantityz, side= "buy")
                self.action_price = last_price
                self.submit_order(order)
                self.last_action = "buy"
        if pos and last_price*1.45 > self.action_price and self.last_action == "buy":
            self.sell_all()
            self.last_action = "sell"

    def simple_check(self):
        symbol = 'SOXX'
        order = self.create_order(symbol, quantity= 10, side = 'buy')
        self.submit_order(order)
    def slope_extract (self, list):
        y = [1,2,3,4,5]
        coefficients = np.polyfit(list,y,1)    #make a line of best fit
        slope = coefficients[0] #get the slope lol
        return slope
    
    def slope_session(self, symbol):
        #initializating the strat
        lossexitper = 0.9975
        highexit= 1.0005
        midexit = 1.001
        lowexit = 1.0005

        today = self.get_datetime().strftime('%Y-%m-%d')
        time = self.get_datetime().strftime('%H:%M:%S')
        datetimestring = today + " , " + time
        orderamt = 0
        # probability, sentiment  = self.get_sentiment() 
        self.data[symbol].append(self.get_last_price(symbol)) #uses the last 5 intervals to collect interval cost data (so collect costs and store them in this list)
        if len (self.data[symbol]) >=5:
            fcf_t, qty_f, lpt, temperment  = self.position_sizing(symbol, self.data[symbol][-5:]) #check the last 5 intervals            
            if qty_f > 0 and temperment == "+": #if position analysis is good then use the trend is moving positive - make a buy order at current price
                self.cash_history+= qty_f*lpt
                if self.get_cash() - self.cash_history > self.initial_budget - (self.risk_p * self.initial_budget): #ensures that budget floor is mantained
                    self.order.append(self.create_order(symbol, quantity= qty_f, side = 'buy'))
                    self.diary[datetimestring] = [lpt, qty_f, symbol] #creating diary of date as key, buy price and quantity as values
                else:
                    print (f"Trade not added: current cost for purchase: {qty_f*lpt}, current cash requirement for orders = {self.cash_history}, current cash available = {self.get_cash()}, current floor = {self.initial_budget - (self.risk_p * self.initial_budget)}")
                    self.cash_history-= qty_f*lpt
            #iterate over buy data dict
            for date, details in self.diary.items():
                date1 = datetime.strptime(today, '%Y-%m-%d').date()
                date2 = self.extract_date(date)
                current_tick = details[2]
                qty_f = details[1]
                ppt = details[0]
                lpt = self.get_last_price(symbol)
                difference_in_days = date1 - date2 #counter for days passed
                
                if current_tick ==symbol:
                    print(f"Current strat - sell {qty_f} of {current_tick} if {lpt} drops below {round(ppt*lossexitper,2)} or >= to {round(ppt*highexit,2)}, right now holding for {difference_in_days} days - if between 15 and 30 days then sell at anywhere b/w {round(ppt*highexit,2)} and {round(ppt*midexit,2)}  - if more than 30 days then sell at anywhere b/w {round(ppt*midexit,2)} and {round(ppt*lowexit,2)}")
                if current_tick == symbol and qty_f > 0 and lpt <= details[0]*lossexitper : #doesn't matter time passed - if ur 99.5% or below, sell that position
                    print (f"Sell decision of {symbol} at {lpt} for {details[1]} pieces | Price difference = {lpt- details[0]} ")
                    orderamt += details[1]
                    self.order.append(self.create_order(current_tick, quantity= qty_f, side = "sell" ))
                    details[1] = 0  # quantity gets zeroed

                if current_tick == symbol and qty_f > 0 and lpt >= details[0]*highexit : #doesn't matter time passed - if ur 15% above, sell that position
                    print (f"Sell decision of {symbol} at {lpt} for {details[1]} pieces | Price difference = {lpt- details[0]} ")
                    orderamt += details[1]
                    self.order.append(self.create_order(current_tick, quantity= qty_f, side = "sell" ))
                    details[1] = 0  # quantity gets zeroed
                    
                if current_tick == symbol and qty_f > 0 and int(difference_in_days.days) >=30 and details[0]*midexit > lpt>= details[0]*lowexit: # if the days passed are over 30, then sell possiitions taking all profits you can
                    print (f"Sell decision of {symbol} at {lpt} for {details[1]} pieces | Price difference = {lpt- details[0]} ")
                    orderamt += details[1]
                    self.order.append(self.create_order(current_tick, quantity= qty_f, side = "sell" ))
                    details[1] = 0
                if current_tick == symbol and qty_f > 0 and 30> int(difference_in_days.days) >15 and details[0]*highexit > lpt >= details[0]*midexit: #if the days passed are over 15 days but under 30, then sell the positionsif you have atleast a 6% profit
                    orderamt += details[1]
                    self.order.append(self.create_order(current_tick, quantity= qty_f, side = "sell" ))  
                    details[1] = 0
        else:
            print (f"Collecting 5 iterations for {symbol}. Currently at {len(self.data[symbol])}")    

        # if orderamt > 0:
        #     self.order.append(self.create_order(current_tick, quantity= orderamt, side = "sell" )) #Make a sell with the order amount - determined from above. 
        #     orderamt = 0

    def get_dates(self): 
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self): 
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=self.symbol, 
                                 start=three_days_prior, 
                                 end=today) 
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment 

    def extract_date(self, datetimestring):
    # Split the string on the comma and strip any leading/trailing whitespace
        date_part = datetimestring.split(',')[0].strip()
        date_part = datetime.strptime(date_part, '%Y-%m-%d').date()
        return date_part

    def before_starting_trading(self): #Necessary for live trading - need to be commented for backtesting
        today = self.get_datetime().strftime('%Y-%m-%d')
        self.headers = {"accept": "application/json", "APCA-API-KEY-ID": API_KEY, "APCA-API-SECRET-KEY": API_SECRET}
        self.response = requests.get(POSITIONS_URL, headers= self.headers)
        if self.response:
            self.json_data = json.loads(self.response.text)
            for diction in self.json_data:
                time = random.getrandbits(128)
                datetimestring = today + " , " + str(time)
                self.diary[datetimestring] = [float(diction['avg_entry_price']),float(diction['qty']), diction['symbol']] 
    
    
    def on_trading_iteration(self):
        
        # self.simple_check()
        self.cash_history = 0
        for items in self.symbol:
            self.slope_session(items)
        if len(self.order) > 0:
            print (self.order)
            for order in self.order:
                self.submit_order(order)
            # self.submit_orders(self.order)
            self.order.clear()
            


            
start_date = datetime(2023,1,1)
end_date = datetime(2023,12,31) 
broker = Alpaca(ALPACA_CREDS) 
strategy = MLTrader(name='mlstrat', broker=broker, budget = 100000, 
                    parameters={"symbol":tickertest, 
                                "budget_buffer_risk":.75})
data_source = PolygonDataBacktesting(
    datetime_start=start_date,
    datetime_end=end_date,
    api_key= POLYGONKEY,
    has_paid_subscription=False,  # Set this to True if you have a paid subscription to polygon.io (False assumes you are using the free tier)
)
# strategy.backtest(
#     PolygonDataBacktesting, 
#     start_date, 
#     end_date, 
#     benchmark_asset = 'SPY',
#     api_key=POLYGONKEY,
# )
trader = Trader()
trader.add_strategy(strategy)
trader.run_all()