from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *
from bar_logic import Bar
from connection import IBApi
from data_request import DataRequester
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



#class for bot logic
class Bot(object):
    global order_id
    initialbartime = datetime.now().astimezone(pytz.timezone("America/New_York"))
    def __init__(self):
        self.ib = IBApi()
        self.ib.connect("127.0.0.1", 7497, 1 ) #set for Paper Trading Account
        ib_thread = threading.Thread(target=self.run_loop, daemon=True)
        ib_thread.start()
        time.sleep(1)
        self.symbol = input("Enter Symbol you Want to Trade : ")
        self.interval = input("Enter the barsize you want to trade in minutes (format: ex: 1m) : ")
        #Get all historical Data
        self.dataRequest = DataRequester(self.interval, self.symbol)
        self.dataRequest.register_callback(self.buyDesicion)
        
        self.order_id = self.ib.nextValidId

        #Place Order
        # self.ib.placeOrder(self.order_id, contract, order)
    
    #function to decide whether to buy or not
    #let "bar" be the current/most recent bar
    #still need to consider edge case when most recent bar in bars list is the same as live price bar
    def buyDesicion(self, old_value, new_value):
        print("buyDesicion initiated")
        self.bars = self.dataRequest.bars
        self.sma = self.dataRequest.sma
        self.currentBar = self.dataRequest.currentBar
        lastLow = self.bars[len(self.bars)-1].low
        secondLastLow = self.bars[len(self.bars)-2].low
        lastHigh = self.bars[len(self.bars)-1].high
        secondLastHigh = self.bars[len(self.bars)-2].high
        lastClose = self.bars[len(self.bars)-1].close
        lastBar = self.bars[len(self.bars)-1]
        #checking whether we want to buy
        #remember we want to buy when break point is in a positive direction
        #last two lines ensure it crossed over the sma
        #I will also add a check to check if the current price is above the previous close
        today_now = datetime.now().astimezone(pytz.timezone("America/New_York"))
        today_930am = today_now.replace(hour=9, minute=30, second=0, microsecond=0)
        today_4pm = today_now.replace(hour=16, minute=0, second=0, microsecond=0)
        #only deciding on buying while markets are open
        if ( today_930am <  today_now):
            if (lastHigh > secondLastHigh
                and lastLow > secondLastLow
                and self.currentBar.close >= lastHigh
                and self.currentBar.close > str(self.sma[len(self.sma)-1])
                and lastClose < str(self.sma[len(self.sma)-2])):
                print("BUY")
            else:
                print("Don't BUY")

    
    def run_loop(self):
        #Create Seperate Thread for running the bot
        self.ib.run()

    def contract_object(self, secType='STK', Currency='USD', exchange = 'SMART'):
        contract=Contract()
        contract.symbol = self.symbol.upper()
        contract.secType = secType
        contract.currency = Currency
        contract.exchange = exchange
        return contract

    def order_object(self, action="BUY", quantity= 1):
        order=Order()
        order.action = action
        order.orderType = 'MKT'
        order.totalQuantity = quantity
        return order
    
    #order setup for IB trading, basically a bracket order allows you to place a profit target and stop loss on a parent order
    #think of the parent order as the main order you make, whether to buy or sell
    def bracketOrder(self, parentOrderId, action, quantity, profitTarget, stopLoss):
        #Create Parent Order, 
        parent = Order()
        parent.orderId = parentOrderId
        parent.orderType = "MKT"
        parent.action = action
        parent.totalQuantity = quantity
        parent.transmit = False
        #Now establish the Profit Target Order
        profitTargetOrder = Order()
        profitTargetOrder.orderId = parent.orderId + 1
        profitTargetOrder.orderType = "LMT"
        profitTargetOrder.action = "SELL"
        profitTargetOrder.totalQuantity = quantity
        profitTargetOrder.lmtPrice = round(profitTarget,2)
        profitTargetOrder.transmit = False
        #Stop loss
        stopLossOrder = Order()
        stopLossOrder.orderId = parent.orderId + 2
        stopLossOrder.orderType = "STP"
        stopLossOrder.action = "SELL"
        stopLossOrder.totalQuantity = quantity
        stopLossOrder.auxPrice = round(stopLoss,2)
        stopLossOrder.transmit = True

        bracketOrders = [parent, profitTargetOrder, stopLossOrder]
        return bracketOrders


#Starting the Bot
bot = Bot()
