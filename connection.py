from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *

#used to setup connection
class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId):
        self.nextValidId = orderId

    # def error(self, id, errorCode, errorMsg):
    #     print(errorCode)
    #     print(errorMsg)
