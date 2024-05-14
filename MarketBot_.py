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
import decimal
API_KEY = "PKJYF05FPJGXH57IXVUK" 
API_SECRET = "t4siryHdAd5gfwTxsfZbMCkwfafvPzJIFEspuuaq" 
BASE_URL = "https://paper-api.alpaca.markets/v2"
POSITIONS_URL = "https://paper-api.alpaca.markets/v2/positions"
POLYGONKEY = "hwXFX1sSXE4ojhYyeKDA7BBJDlaLf6Pf"
tickertest = ['NVDA']
BUY_STOP_LIMIT = 27500
FLOOR = 25000
# LIVE_TRADE = False
LIVE_TRADE = True
ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET, 
    "PAPER": True
}


class MLTrader(Strategy): 

    def initialize(self, symbol:str=tickertest, budget_buffer_risk:float=.75, live_trading = LIVE_TRADE): 
        self.symbol = symbol 
        self.live = LIVE_TRADE
        for items in self.symbol:
            self.data[items] = []
        self.sleeptime = "10s"
        self.risk_p = budget_buffer_risk
        self.asset = Asset(self.symbol, asset_type=Asset.AssetType.STOCK)
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)
    
    def on_trading_iteration(self):
        for symbol in self.symbol:
            self.get_last_price(symbol)
            
            


start_date = datetime(2023,1,1)
end_date = datetime(2023,1,31) 
broker = Alpaca(ALPACA_CREDS) 
strategy = MLTrader(name='mlstrat', broker=broker, budget = 100000, 
                    parameters={"symbol":tickertest, 
                                "budget_buffer_risk":.75},
                    live_trading = LIVE_TRADE)
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