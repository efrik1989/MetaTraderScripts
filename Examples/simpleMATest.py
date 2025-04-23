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
rates_range = 200

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
    date_now = datetime.today()
    start_day_temp = date_now - timedelta(days=days_num + days_num)
    return mt5.copy_rates_range(symbol, timeframe, start_day_temp, date_now)

def moving_avarage(symbol, days_num):
    rates_frame = get_rates_frame(symbol, rates_range)
    close_pos_list = rates_frame['close']
    window_size = days_num

    numbers_series = pd.Series(close_pos_list)
    windows= numbers_series.rolling(window_size)
    moving_avarages = windows.mean()
    moving_avarages_list = moving_avarages.tolist()
    rates_frame['MA'] = moving_avarages_list
    #return moving_avarages_list[window_size - 1:]
    return rates_frame

def get_rates_frame(symbol, days_num):
    rates = get_history(symbol, mt5.TIMEFRAME_D1, days_num)
    rates_frame = pd.DataFrame(rates)
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
    rates_frame['close'] = pd.to_numeric(rates_frame['close'], downcast='float')
    return rates_frame

def ma_analis(ma_list):
    general_frame = ma_list[0]
    
    print(general_frame)
    for idx, ma in enumerate(ma_list):
        # TODO: Определенно MA нужен объект содержащий имя, timeframe, и список значений скользящей
        if (idx != 0):
            general_frame['MA ' + str(idx)] = ma['MA']
        
    print(general_frame)
    general_frame.to_excel('D:\out_frame.xlsx')


def startRobot():
    init_MT5()
    authorization()
    selectSymbol(symbol)
    
    # print(get_price())
    # Парсинг данных
    ma10 = moving_avarage(symbol, 10)
    ma20 = moving_avarage(symbol, 20)
    ma100 = moving_avarage(symbol, 100)
    ma_analis(ma_list=(ma10, ma20, ma100))
    # print("MA10: " + str(ma10))
    # print("MA20: " + str(ma20))
    # print("MA100: " + str(ma100))
    # print(symbol + " Prcie: " + str(get_price(symbol)))
    # print(rates_frame)



startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()