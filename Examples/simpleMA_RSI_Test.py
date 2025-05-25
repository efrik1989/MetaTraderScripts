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
# symbols = ("LKOH", "TATN", "SBER", "MAGN", "VTBR", "NLMK", "CHMF", "X5", "MGNT", "YDEX", "OZON")
# Роснефть, Х5, Сургутнефтегаз, МТС, Ростелеком, Астра, М-Видео, Алроса, ГМК Норникель, ЭН+Групп
# symbols = ("ROSN", "X5", "SNGS", "MTSS", "RTKM", "ASTR", "MVID", "ALRS", "GMKN", "ENPG")
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

def rsi(df, periods = 14, ema = True):
    """
    Возвращает pd.Series с индексом относительной силы.
    """
    close_delta = df['close'].diff()
    # Делаем две серий: одну для низких закрытий и одну для высоких закрытий
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    
    if ema == True:
	# Использование экспоненциальной скользящей средней
        ma_up = up.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
        ma_down = down.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
    else:
        # Использование простой скользящей средней
        ma_up = up.rolling(window = periods, adjust=False).mean()
        ma_down = down.rolling(window = periods, adjust=False).mean()
        
    rsi = ma_up / ma_down
    rsi = 100 - (100/(1 + rsi))
    return rsi

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
                general_frame['MA ' + str(idx)] = ma['MA']
        
    print(general_frame)
    general_frame.to_excel('D:\out_' + symbol + '_MA50_MA20_MA10_D1_frame.xlsx')
    # return general_frame

    # Добавляем колоноку rsi к фрейму для анализа 
def startegyRSI_close(frame, rsi_period):
    frame['rsi'] = rsi(frame, rsi_period, True)
    conditions = [
        (frame['rsi'] > 70),
        ((frame['rsi'] < 30))]
    chois = ["Close_buy", "Close_Sell"]
    frame['close_signal'] = np.select(conditions, chois, default="NaN")

# Стратегия подсвечивает сигналы при работе с индикатором MA50 на исторических данных
def strategyMA50(symbol, frame):
    
    frame['diff'] = pd.to_numeric(frame['close']) - pd.to_numeric(frame['MA'])
    frame['trend'] = pd.Series(frame['diff']) > 0

    d = {True: 'UP', False: 'DOWN'}
    frame['trend'] = frame['trend'].map(d)

    # TODO: Смысл такой находим максималььно близкиеи точки к MA (возможно проверяем цену открытия плюсом)
    # Добавляем в frame булевое значение true, после смотрим и\или жджем и смотрим следующую цену закрытия, 
    # если при растущем тренде цена выше MA открываем buy, если тренд наснижение и цена закрытия ниже MA sell
    
    frame['target'] = (pd.to_numeric(frame['diff']) < 50) & (-50 < pd.to_numeric(frame['diff']))
    frame['day_next'] = frame['close'].shift(-1)

    # Ну вроде как ок. стоит зафиксировать!!!
    conditions = [
        (frame['target'] == True) & (frame['trend'] == "UP") & (frame['day_next'] > frame['MA']),
        (frame['target'] == True) & (frame['trend'] == "DOWN") & (frame['day_next'] < frame['MA'])]
    chois = ["Open_buy", "Open_Sell"]
    frame['signal'] = np.select(conditions, chois, default="NaN")

    #TODO: Поправить логику. А то в SL и TP весь фрэйм пишется.


    # frame['take_profit'] = frame.where(frame['signal'] == "Open_buy") 
    """
    frame['take_profit'] = frame['signal'] == "Open_buy"
    frame['stop_loss'] = frame['signal'] == "Open_buy"

    tp_mask = {True: (frame['close'] * 1.05) , False: 'NaN'}
    frame['take_profit'] = frame['take_profit'].map(tp_mask)

    sl_mask = {True: (frame['close'] * 0.95) , False: 'NaN'}
    frame['stop_loss'] = frame['stop_loss'].map(sl_mask)

    frame['take_profit'] = frame['signal'] == "Open_Sell"
    frame['stop_loss'] = frame['signal'] == "Open_Sell"

    tp_mask = {True: (frame['close'] * 0.95) , False: 'NaN'}
    frame['take_profit'] = frame['take_profit'].map(tp_mask)

    sl_mask = {True: (frame['close'] * 1.05) , False: 'NaN'}
    frame['stop_loss'] = frame['stop_loss'].map(sl_mask)
    """
    #TODO: Пока не понятно как выходить из сделки. точнее как условия брать для выхода.
    # Обсуждались:
    #       1) SL, TP
    #       2) только SL
    #       3) трейлиинг стоп (или преследующий sl цену)
    #       4) останавливаться на 5%
    #       5) цены закрытия двух баров подряд ниже (если buy) выше (если sell) предыдущих
    # 
    
    frame['day_befor_1'] = frame['close'].shift(1)
    frame['day_befor_2'] = frame['close'].shift(2)
    frame['day_befor_3'] = frame['close'].shift(3)
    
    startegyRSI_close(frame, 14)

    frame.to_excel('D:\out_' + symbol + '_MA50_frame_Buy_Sell_signals.xlsx')

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
        strategyMA50(symbol, ma50)
    """
        # ma200 = moving_avarage(symbol, 200)
    
        # Похоже это стоит пихать только в определенную стратегию т.к. поведение робота должно быть разным при разных скользящих средних
        # ma_analis(symbol, ma_list=(ma50, ma200))
    print(symbol)
    selectSymbol(symbol)
    ma50 = moving_avarage(symbol, 50)
    strategyMA50(symbol, ma50)

startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()