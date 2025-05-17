from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import logging
from pandas.plotting import register_matplotlib_converters
import pytz
import numpy as np


register_matplotlib_converters()
import MetaTrader5 as mt5
import metatrader5EasyT
from metatrader5EasyT import tick
from metatrader5EasyT import timeframe
from metatrader5EasyT import trade


symbol="LKOH"
# анные по 50 и 200 на Лукойл, Татнефть, Сбер, ВТБ, ммк, НЛМК, Северсталь, х5, магнит, Яндекс и озон
symbols = ("LKOH", "TATN", "SBER", "MAGN", "VTBR", "NLMK", "CHMF", "X5", "MGNT", "YDEX", "OZON")
# rates_range = 700
rates_range = 300

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
    rates_frame.dropna(inplace=True)
    # return moving_avarages_list[window_size - 1:]
    return rates_frame

    # Получение торговых данных инструмента за рпеделенный промежуток
def get_rates_frame(symbol, days_num):
    rates = get_history(symbol, mt5.TIMEFRAME_D1, days_num)
    rates_frame = pd.DataFrame(rates)
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
    rates_frame['close'] = pd.to_numeric(rates_frame['close'], downcast='float')
    return rates_frame

def ma_analis(symbol, ma_list):
    general_frame = ma_list[0]
    
    print(general_frame)
    if len(ma_list) != 1:
        for idx, ma in enumerate(ma_list):
            # TODO: Определенно MA нужен объект содержащий имя, timeframe, и список значений скользящей
            if (idx != 0):
                general_frame['MA' + str(idx)] = ma['MA']
        
    print(general_frame)
    # general_frame.to_excel('D:\out_' + symbol + '_MA50_MA20_MA10_D1_frame.xlsx')
    # return general_frame


# Стратегия подсвечивает сигналы при работе с индикатором MA50 на исторических данных
def strategyMA50(frame):
    print(frame)
    frame['diff'] = pd.to_numeric(frame['close']) - pd.to_numeric(frame['MA1'])
    frame['trend'] = pd.Series(frame['diff']) > 0

    d = {True: 'UP', False: 'DOWN'}
    frame['trend'] = frame['trend'].map(d)

    # TODO: Смысл такой находим максималььно близкиеи точки к MA (возможно проверяем цену открытия плюсом)
    # Добавляем в frame булевое значение true, после смотрим и\или жджем и смотрим следующую цену закрытия, 
    # если при растущем тренде цена выше MA открываем buy, если тренд наснижение и цена закрытия ниже MA sell
    
    frame['target'] = (pd.to_numeric(frame['diff']) < 50) & (-50 < pd.to_numeric(frame['diff']))
    frame['close_shift_-1'] = frame['close'].shift(-1)

    # Ну вроде как ок. стоит зафиксировать!!!
    conditions = [
        (frame['target'] == True) & (frame['trend'] == "UP") & (frame['close_shift_-1'] > frame['MA1']),
        (frame['target'] == True) & (frame['trend'] == "DOWN") & (frame['close_shift_-1'] < frame['MA1'])]
    chois = ["Open_buy", "Open_Sell"]
    frame['signal'] = np.select(conditions, chois, default="NaN")

    #TODO: Пока не понятно как выходить из сделки. точнее как условия брать для выхода.
    # Обсуждались:
    #       1) SL, TP
    #       2) только SL
    #       3) трейлиинг стоп (или преследующий sl цену)
    #       4) останавливаться на 5% (или сколько то)
    #       5) использовать линии Болинджера
    
    # frame.to_excel('D:\out_' + symbol + '_MA50_frame_signal.xlsx')

    #TODO: выглядит не сложно. Надо попробовать https://habr.com/ru/articles/783384/
def strategyBolingerLines(frame, period):
    std = np.std(frame['close'][-period:], ddof=1)

        # calculate Bollinger
    frame['bb_high'] = frame['MA'] + 2 * std
    frame['bb_low'] = frame['MA'] - 2 * std

    frame['bb_high-p.close'] = frame['bb_high'] - frame['close']
    frame['bb_low-p.close'] = frame['bb_low'] - frame['close']
    frame['target_high_bb'] = (pd.to_numeric(frame['bb_high-p.close']) < 25) & (-25 < pd.to_numeric(frame['bb_high-p.close']))
    frame['target_low_bb'] = (pd.to_numeric(frame['bb_low-p.close']) < 25) & (-25 < pd.to_numeric(frame['bb_low-p.close']))

    frame.to_excel('D:\out_' + symbol + '_MA20_Bollinger20_frame_signal.xlsx')


def startRobot():
    init_MT5()
    authorization()
    
    # print(get_price())
    # Парсинг данных
    
    """ 
    for symbol in symbols:
        print(symbol)
        selectSymbol(symbol)
        ma50 = moving_avarage(symbol, 50)
        # ma200 = moving_avarage(symbol, 200)
    """
        # Похоже это стоит пихать только в определенную стратегию т.к. поведение робота должно быть разным при разных скользящих средних
        # ma_analis(symbol, ma_list=(ma50, ma200))
    selectSymbol(symbol)

    # ma10 = moving_avarage(symbol, 10)
    ma20 = moving_avarage(symbol, 20)
    ma50 = moving_avarage(symbol, 50)

    ma_analis(symbol, ma_list=(ma20, ma50))
    strategyMA50(ma50)
    strategyBolingerLines(ma50, 20)
    # print("MA10: " + str(ma10))
    # print("MA20: " + str(ma20))
    # print("MA100: " + str(ma100))
    # print(symbol + " Prcie: " + str(get_price(symbol)))
    # print(rates_frame)

startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()