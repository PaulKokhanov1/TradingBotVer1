from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *
import ta
import numpy as np
import pandas as pd
import pytz
import math
from datetime import datetime, timedelta
import threading
import time
import yfinance as yf
import yahoo_fin.stock_info as si

#used to setup connection
class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId):
        self.nextValidId = orderId

    def realtimeBar(self, reqId, time, open_, high, low, close,volume, wap, count):
        super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        try:
            print("WORKING")
        except Exception as e:
            print(e)

class Bot():
    ib = None
    def __init__(self):
        self.ib = IBApi()
        self.data_requester = DataRequester()
        self.ib.connect("127.0.0.1", 7497, 1 ) #set for Paper Trading Account
        ib_thread = threading.Thread(target=self.run_loop, daemon=True)
        ib_thread.start()
        self.data_requester.printit()
        print("Test")
    

    def run_loop(self):
        #Create Seperate Thread for running the bot
        self.ib.run()


class DataRequester:
    def __init__(self):
        print("started")
    
    def printit(self):
        threading.Timer(5.0, self.printit).start()
        print ("Hello, World!")


bot = Bot()