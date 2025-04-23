from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import logging
from pandas.plotting import register_matplotlib_converters

from models.order import Order
register_matplotlib_converters()
import MetaTrader5 as mt5
import metatrader5EasyT
from metatrader5EasyT import tick
from metatrader5EasyT import timeframe
from metatrader5EasyT import trade

tick_obj = None
symbol = "ROSN"

def init_MT5():
    # connect to MetaTrader 5
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()
    
    # request connection status and parameters
    print(mt5.terminal_info())
    # get data on MetaTrader 5 version
    print(mt5.version())

# Выбираем символ(инструмент)
def selectSymbol(symbol):
    selected=mt5.symbol_select(symbol,True)
    if not selected:
        print("Failed to select " + symbol + ", error code =",mt5.last_error())
    else:
        symbol_info=mt5.symbol_info(symbol)
        print(symbol_info)

# Авторизация под аккаунтом
#TODO: вынести входными параметрами или в конфиг какой. Тут подумать надо.
def authorization():
    account = 23677 
    authorized = mt5.login(login=account, server="FINAM-AO",password="3C$ap3%H")  
    if authorized:
        print("connected to account #{}".format(account))
    else:
        print("failed to connect at account #{}, error code: {}".format(account, mt5.last_error()))

# Получение цены
def get_price(symbol):
    if tick_obj == None: 
        tick_obj = tick.Tick(symbol)
    tick_obj.get_new_tick()
    return tick_obj.bid

def isOrderOpen(symbol):
    orders=mt5.orders_get(symbol)
    if orders is None:
        isOrderExist=False
    else:
        isOrderExist-True
    return isOrderExist

def getIndicatorWeight(indicatorsWeightList):
    for weight in indicatorsWeightList:
        weightSumm += weight
    return weightSumm

def startRobot():
    init_MT5()
    selectSymbol(symbol)

    while (True):
        if input() == "exit":
            mt5.shutdown()
            break

        # Стоит ли делать трейлинг стоп на данном этапе?
        if isOrderOpen():
            #current_price, order.open_price, order.open_price - определить значения.
            current_price=get_price()
            if current_price >= current_order.open_price + (current_order.open_price * 0.01):
               continue
        else:
            del current_order
            indicators_weight = getIndicatorWeight(indecatorsWeightList)

            # Проверка суммы весов индикаторов.
            if indicators_weight >= 1:
                if isReadyToOpen:
                    current_order = Order(current_price, symbol)
                    if isBuy:
                        current_order.open_buy()
                    else:
                        current_order.open_sell()