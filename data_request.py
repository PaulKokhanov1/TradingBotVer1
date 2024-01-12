from bar_logic import Bar
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

class DataRequester(object):
    def __init__(self, interval, symbol):
        self.interval = interval
        self.symbol = symbol
        self._update = False
        self.bars = []
        self.sma = 0
        self.count = 0
        self._callbacks = []
        self.currentBar = Bar()
        self.getHistoricalBars()

    @property
    def update(self):
        return self._update
    
    @update.setter
    def update(self, new_value):
        #print("setter called")
        old_value = self._update
        self._update = new_value
        self.notify_observers(old_value, new_value)

    def notify_observers(self, old_value, new_value):
        #print("notifying users")
        for callback in self._callbacks:
            callback(old_value, new_value)

    def register_callback(self, callback):
        #print("bound")
        self._callbacks.append(callback)

    
    #dont need to do this because just need to request historical data once and then later just keep appending most recent bar
    def run_updates(self):
        self.t = threading.Timer(10.0, self.run_updates)    #when running the bot for real, set timer to about 60s (so 1 min)
        self.t.start()
        self.updateHistoricalBars()
        #self.cancel_updates()
        self.count += 1
    
    def cancel_updates(self):
        if (self.count >= 5):
            print("thread Canceled")
            self.t.cancel()


    def getHistoricalBars(self):
        #given our interval we need to calculate appropriate startTime for 50 cycles since we are doing a 50SMA
        #main use is for day trading so we will for now only use mins
        interval_int = int(self.interval.replace('m', ''))
        startTimeInMins = 50*interval_int

        #define datetime from current date and time to 50 cycles earlier
        startTime = (datetime.now().astimezone(pytz.timezone("America/New_York"))-timedelta(hours=0, minutes=startTimeInMins))
        #print(startTime)

        ticker = yf.Ticker(self.symbol)
        data = ticker.history(interval=self.interval, start=startTime)
        #print(data["Close"])
        #need to keep index var since pandas dataframe doesn't have indexing in this case
        
        index = 0
        for dateTime, row in data.iterrows():
            self.bars.append(Bar())
            self.bars[index].open = round(row['Open'], 2)
            self.bars[index].low = round(row['Low'], 2)
            self.bars[index].high = round(row['High'], 2)
            self.bars[index].close = round(row['Low'], 2)
            self.bars[index].volume = row['Volume']
            self.bars[index].date = str(dateTime)[:-6]
            index += 1
        
        for bar in self.bars: print(" Open: " + str(bar.open) + " Close: " + str(bar.close) + " high: " + str(bar.high) + " low: " + str(bar.low) + " Volume: " + str(bar.volume) + " Date: " + str(bar.date)  )
        self.currentBar.close = si.get_live_price(self.symbol)
        print("Size of bar: ", len(self.bars))
        #print(self.currentBar.close)
        self.calcSMA()
        time.sleep(1)
        self.run_updates()
        
    def updateHistoricalBars(self):
        #given our interval we need to calculate appropriate startTime for 50 cycles since we are doing a 50SMA
        #main use is for day trading so we will for now only use mins
        interval_int = int(self.interval.replace('m', ''))
        startTimeInMins = 50*interval_int

        #define datetime from current date and time to 50 cycles earlier
        startTime = (datetime.now().astimezone(pytz.timezone("America/New_York"))-timedelta(hours=0, minutes=startTimeInMins))
        #print(startTime)

        ticker = yf.Ticker(self.symbol)
        data = ticker.history(interval=self.interval, start=startTime)
        #print(data["Close"])
        #need to keep index var since pandas dataframe doesn't have indexing in this case
        index = 0
        #WEIRD PROBLEM WITH INDEX BEING OUT OF RANGE SOMETIMES
        for dateTime, row in data.iterrows():
            if index >= len(self.bars):
                self.bars.append(Bar())
            self.bars[index].open = round(row['Open'], 2)
            self.bars[index].low = round(row['Low'], 2)
            self.bars[index].high = round(row['High'], 2)
            self.bars[index].close = round(row['Low'], 2)
            self.bars[index].volume = row['Volume']
            self.bars[index].date = str(dateTime)[:-6]
            
            index += 1

        #edge case, but if by some means len(bars) > 50, then popleft() to remove oldest data point
        while (len(self.bars)>50):
            self.bars.pop(0)

        
        for bar in self.bars: print(" Open: " + str(bar.open) + " Close: " + str(bar.close) + " high: " + str(bar.high) + " low: " + str(bar.low) + " Volume: " + str(bar.volume) + " Date: " + str(bar.date)  )
        self.currentBar.close = si.get_live_price(self.symbol)
        print("Size of bar: ", len(self.bars))
        print("Current Price: ", self.currentBar.close)
        self.calcSMA()

    def calcSMA(self):
        closes = []
        for bar in self.bars:
            closes.append(bar.close)
            close_array = pd.Series(np.asarray(closes))
            self.sma = ta.trend.SMAIndicator(close_array,50,True).sma_indicator()
        print("SMA : " + str(self.sma[self.sma.size-1]))

        self.update = not self._update