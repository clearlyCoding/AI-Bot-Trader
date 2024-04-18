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
tickertest = 'AAPL'
ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET, 
    "PAPER": True
}

class MLTrader(Strategy): 
    data = []
    order_number = 0
    counter = 0
    last_action = ""
    action_price = 0
    diary = {}
    pages = {}
    def initialize(self, symbol:str=tickertest, cash_at_risk:float=.25): 
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
        fpos = self.get_position(self.symbol)
        lastprice = self.get_last_price(self.symbol)
        total_position_value = float(lastprice*fpos + fcashflow)
        
        return total_position_value


    def get_sentiment(self): 
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=self.symbol, 
                                 start=three_days_prior, 
                                 end=today) 
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment 

    def on_trading_iteration(self):
        cash, last_price, quantityz = self.position_sizing()
        today = self.get_datetime().strftime('%Y-%m-%d')
        orderamt = 0
        dellist = []
        # probability, sentiment  = self.get_sentiment() 
        print(f"Position: {self.get_position(self.symbol)}, free cash flow : {cash}")
        pos = self.get_position(self.symbol)
        self.data.append(self.get_last_price(self.symbol))
        slope_action=0
        if len (self.data) >=5:
            x = self.data[-5:]
            y = [1,2,3,4,5]
            coefficients = np.polyfit(x,y,1)
            slope = coefficients[0]
            if slope> 0 and quantityz>0:
                order = self.create_order(self.symbol, quantity= quantityz, side = 'buy')
                self.diary[today] = [last_price, quantityz]
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
            
            
            if last_price > details[0]*1.15:
                orderamt += details[1]
                print (f"purcahsed {details[1]} for {details[0]} on {date}, current price is {last_price} on {today}")
                # details[1] =  0
                
        # for keys in self.diary:
        #     if last_price > keys*1.15:
        #         print(f"bought {self.diary[keys]} for {keys}")
        #         orderamt += self.diary[keys]
        #         dellist.append(keys)
        # if pos and orderamt >0 and pos.quantity >= orderamt:
        #     order = self.create_order(self.symbol, quantity= orderamt, side = "sell" )
        #     self.submit_order (order)
        # for items in dellist:
        #     del self.diary[items]

        today = self.get_datetime()
        if today.strftime('%Y-%m-%d') == ('2023-12-29'):
            self.sell_all()
        # total_value = self.analyze_position()
        # print(total_value)


            



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