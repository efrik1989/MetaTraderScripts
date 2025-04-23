from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import logging
import time
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()
import MetaTrader5 as mt5
import metatrader5EasyT
from models.order import Order
from metatrader5EasyT import tick
from metatrader5EasyT import timeframe
from metatrader5EasyT import trade


symbol="IRAO"

def init_MT5():
    # connect to MetaTrader 5
    if not mt5.initialize("C:\\Program Files\\FINAM MetaTrader 5\\terminal64.exe"):
        print("initialize() failed")
    
    # request connection status and parameters
    print(mt5.terminal_info())
    # get data on MetaTrader 5 version
    print(mt5.version())

def authorization():
    account = 23677 
    authorized = mt5.login(login=account, server="FINAM-AO",password="3C$ap3%H")  
    if authorized:
        print("connected to account #{}".format(account))
    else:
        print("failed to connect at account #{}, error code: {}".format(account, mt5.last_error()))

# Выбираем символ(инструмент)
def selectSymbol(symbol):
    selected=mt5.symbol_select(symbol,True)
    if not selected:
        print("Failed to select " + symbol + ", error code =",mt5.last_error())
    else:
        symbol_info=mt5.symbol_info(symbol)
        print(symbol_info)
# Получение цены
def get_price(symbol):
    tick_obj = tick.Tick(symbol)
    tick_obj.get_new_tick()
    return tick_obj.bid

def startRobot():
    init_MT5()
    authorization()
    selectSymbol(symbol)
    
    current_price = get_price()
    print("current_price: " + current_price)

    # Чисто теоретически с помощью этого можно торговать. Надо проверить.
    # Делать ли отдельный класс для симуляции купли продажи? Вопрос...
    trade_obj = trade.Trade(symbol, 1, current_price - 100, current_price + 100)
    trade_obj.position_open(True, False)
    time.sleep(5)
    trade_obj.position_check()
    time.sleep(5)
    trade_obj.position_close()

startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()