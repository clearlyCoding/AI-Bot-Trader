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
API_KEY = "PK8TNPOIWE1B6PH2PHY0" 
API_SECRET = "RXSRJUYMNJpniHaFAZo7MUfoe1k2WMknbGcLTev8" 
BASE_URL = "https://paper-api.alpaca.markets/v2"
POLYGONKEY = "hwXFX1sSXE4ojhYyeKDA7BBJDlaLf6Pf"
tickertest = 'SOXX'
ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET, 
    "PAPER": True
}

class MLTrader(Strategy): 
    data = []
    order_number = 0
    cash_history = 0
    last_action = ""
    action_price = 0
    diary = {}
    pages = {}
    def initialize(self, symbol:str=tickertest, cash_at_risk:float=.5): 
        self.symbol = symbol
        self.sleeptime = "10M"
        self.cash_at_risk = cash_at_risk
        self.asset = Asset(self.symbol, asset_type=Asset.AssetType.STOCK)
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)

    def position_sizing(self): 
        cash = self.get_cash() 

        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.cash_at_risk / last_price,0)
        if cash - (quantity * last_price) <self.cash_at_risk * cash:
            quantity = 0 

        return cash, last_price, quantity
    def swing_session(self):
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


    def slope_session(self):
        ##best 10 minute interval
        print ("Slope session strategy engaged")
        cash, last_price, quantityz = self.position_sizing()
        print(f"Position: {self.get_position(self.symbol)}")
        pos = self.get_position(self.symbol)
        self.data.append(self.get_last_price(self.symbol))
        slope_action=0
        if len (self.data) >=5:
            x = self.data[-5:]
            y = [1,2,3,4,5]
            coefficients = np.polyfit(x,y,1)
            slope = coefficients[0]
            if slope >0:
                order = self.create_order(self.symbol, quantity= quantityz, side = 'buy')
                self.submit_order(order)
                slope_action =slope
            if pos and slope < slope_action:
                self.sell_all()
    def get_dates(self): 
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def analyze_position(self):
        fcashflow = self.get_cash()
        budget = self.initial_budget
        fpos = self.get_position(self.symbol)
        lastprice = self.get_last_price(self.symbol)
        # total_position_value = float(lastprice*fpos + fcashflow)
        analysis = "+"
        if fcashflow < self.cash_at_risk * budget:
            analysis = "-"
        return analysis


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

    def on_trading_iteration(self):
        cash, last_price, quantityz = self.position_sizing()
        today = self.get_datetime().strftime('%Y-%m-%d')
        time = self.get_datetime().strftime('%H:%M:%S')
        datetimestring = today + " , " + time
        print(datetimestring)
        orderamt = 0
        dellist = []
        # probability, sentiment  = self.get_sentiment() 
        
        pos = self.get_position(self.symbol)
        self.data.append(self.get_last_price(self.symbol))
        if len (self.data) >=5:
            x = self.data[-5:]
            y = [1,2,3,4,5]
            coefficients = np.polyfit(x,y,1)
            slope = coefficients[0]
            if slope> 0 and quantityz>0 and self.analyze_position() == "+":
                order = self.create_order(self.symbol, quantity= quantityz, side = 'buy')
                self.diary[datetimestring] = [last_price, quantityz]
                # self.pages[today] = self.diary[last_price]
                self.submit_order(order)
                slope_action =slope
                self.action_price = last_price
                self.last_action = "buy"
                if cash <self.cash_at_risk*cash:
                    self.sell_all()
                    dellist.clear()
                    orderamt = 0          

        for date, details in self.diary.items():
            date1 = datetime.strptime(today, '%Y-%m-%d').date()
            date2 = self.extract_date(date)
            
            difference_in_days = date1 - date2
            
            if last_price >= details[0]*1.15:
                orderamt += details[1]
                details[1] = 0  
                # print (f"purcahsed {details[1]} for {details[0]} on {date}, current price is {last_price} on {today} - Stale Status {difference_in_days.days}")
                
            if int(difference_in_days.days) >=30 and details[0]*1.06 > last_price>= details[0]*1.001:
                orderamt += details[1]
                details[1] = 0
            if 30> int(difference_in_days.days) >15 and details[0]*1.15 > last_price >= details[0]*1.06:
                orderamt += details[1]  
                details[1] = 0
            

        if orderamt > 0:
            order = self.create_order(self.symbol, quantity= orderamt, side = "sell" ) #sell at 15% threshold profit
            self.submit_order (order)
            orderamt = 0

        # print(f"Position: {self.get_position(self.symbol)}, free cash flow : {cash}")

        # today = self.get_datetime()
        # print (today.strftime('%Y-%m-%d'))
        # print (self.diary)
        if today == ('2023-12-21'):
            self.sell_all()


            



start_date = datetime(2023,1,1)
end_date = datetime(2023,5,31) 
broker = Alpaca(ALPACA_CREDS) 
strategy = MLTrader(name='mlstrat', broker=broker, 
                    parameters={"symbol":tickertest, 
                                "cash_at_risk":.5})


data_source = PolygonDataBacktesting(
    datetime_start=start_date,
    datetime_end=end_date,
    api_key= POLYGONKEY,
    has_paid_subscription=False,  # Set this to True if you have a paid subscription to polygon.io (False assumes you are using the free tier)
)
strategy.backtest(
    PolygonDataBacktesting, 
    start_date, 
    end_date, 
    benchmark_asset = tickertest,
    api_key=POLYGONKEY
)
# trader = Trader()
# trader.add_strategy(strategy)
# trader.run_all()