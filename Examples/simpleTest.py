from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import logging
from pandas.plotting import register_matplotlib_converters
import pytz

register_matplotlib_converters()
import MetaTrader5 as mt5
import metatrader5EasyT
from metatrader5EasyT import tick
from metatrader5EasyT import timeframe
from metatrader5EasyT import trade


symbol="ROSN"

def init_MT5():
    # connect to MetaTrader 5
    if not mt5.initialize("C:\\Program Files\\FINAM MetaTrader 5\\terminal64.exe"):
        print("initialize() failed")
    
    # request connection status and parameters
    # print(mt5.terminal_info())
    # get data on MetaTrader 5 version
    # print(mt5.version())

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
        # print(symbol_info)
# Получение цены
def get_price(symbol):
    tick_obj = tick.Tick(symbol)
    tick_obj.get_new_tick()
    return tick_obj.bid

# Получениея списка данных для скользящей средней
def get_history(symbol, timeframe, days_num):
    # timezone = pytz.timezone("Europe/Moscow")

    date_now = datetime.today()
    start_day_temp = datetime.today() - timedelta(days=days_num)
    # start_day = start_day_temp.timestamp() * 1000
    return mt5.copy_rates_range(symbol, timeframe, start_day_temp, date_now)

def startRobot():
    init_MT5()
    authorization()
    selectSymbol(symbol)
    
    # print(get_price())
    rates = get_history(symbol, mt5.TIMEFRAME_M1, 15)
    rates_from_pos = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 15)

    print("=== Rates===")
    print(rates)
    print("=== Rates===")
    print(rates_from_pos)



startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()