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
from indicators.ma import MA
from models.order import Order
"""
Основная задача скрпта опрпделеять точки входа в сделку и выхода.
На вход получаем минутный фрейм, будем подоватьт по строчно т.е. будут известны история этих данных и 
чтобы принять решение об открытии позиции нужно подождать закрытия следующего бара.
"""

symbol="LKOH"
# данные по 50 и 200 на Лукойл, Татнефть, Сбер, ВТБ, ммк, НЛМК, Северсталь, х5, магнит, Яндекс и озон
symbols = ("LKOH", "TATN", "SBER", "MAGN", "VTBR", "NLMK", "CHMF", "X5", "MGNT", "YDEX", "OZON")
# rates_range = 700
rates_range = 100
window = 50

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
    #return moving_avarages_list[window_size - 1:]
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
    general_frame.to_excel('D:\out_' + symbol + '_MA50_MA200_D1_frame.xlsx')
    # return general_frame


# Стратегия подсвечивает сигналы при работе с индикатором MA50 на исторических данных
def strategyMA50(ma):
    frame = ma.get_MA_values()
    frame['diff'] = pd.to_numeric(frame['close']) - pd.to_numeric(frame[ma.name])
    frame['trend'] = pd.Series(frame['diff']) > 0

    mask = frame.applymap(type) != bool
    d = {True: 'UP', False: 'DOWN'}
    frame = frame.where(mask, frame.replace(d))


    # TODO: Смысл такой находим максималььно близкиеи точки к MA (возможно проверяем цену открытия плюсом)
    # Добавляем в frame булевое значение true, после смотрим и\или жджем и смотрим следующую цену закрытия, 
    # если при растущем тренде цена выше MA открываем buy, если тренд наснижение и цена закрытия ниже MA sell
    
    frame['target'] = (pd.to_numeric(frame['diff']) < 50) & (-50 < pd.to_numeric(frame['diff']))
    frame['target_day_befor_1'] = frame['target'].shift(1)
    frame['close_day_befor_1'] = frame['close'].shift(1)

    # Ну вроде как ок. стоит зафиксировать!!!
    conditions = [
        (frame['target_day_befor_1'] == True) & (frame['trend'] == "UP") & (frame['close_day_befor_1'] > frame[ma.name]),
        (frame['target_day_befor_1'] == True) & (frame['trend'] == "DOWN") & (frame['close_day_befor_1'] < frame[ma.name])]
    chois = ["Open_buy", "Open_sell"]
    frame['signal'] = np.select(conditions, chois, default="NaN")


    # Выход из сделки сыровать пока. Дорабатывать надо.
    frame['day_befor_1'] = frame['close'].shift(1)
    frame['day_befor_2'] = frame['close'].shift(2)
    frame['day_befor_3'] = frame['close'].shift(3)
    
    conditions = [
        (frame['day_befor_1'] > frame['close']) & (frame['day_befor_2'] > frame['day_befor_1']) & (frame['day_befor_3'] > frame['day_befor_2']),
        (frame['day_befor_1'] < frame['close']) & (frame['day_befor_2'] < frame['day_befor_1']) & (frame['day_befor_3'] < frame['day_befor_2'])]
    chois = ["Close_buy", "Close_Sell"]
    frame['close_signal'] = np.select(conditions, chois, default="NaN")
    
    frame.to_excel('D:\out_' + symbol + '_MA50_frame_signal_test.xlsx')

def startRobot():
    init_MT5()
    authorization()
    
        # Похоже это стоит пихать только в определенную стратегию т.к. поведение робота должно быть разным при разных скользящих средних
        # ma_analis(symbol, ma_list=(ma50, ma200))

    # Сейчас используется для выгрузки данных за определенный переиод. Так ну по сути для посторения MA все равно нужны исторические данные
    # Возможно все равно нужно первым делом исторические данные брать. Строить MA, а после сверять с плавающей ценой.
    # Разница между MA и пока показала свою полезность - используем.

    selectSymbol(symbol)

    frame = get_rates_frame(symbol, window)
    ma50 = MA('MA50', frame, window) 
    ma50.createMA()    
    strategyMA50(ma50) # тут весь фрейм тащиться и анализируется, может его шринкануть? по сути нам нужны только 60-100 строк. Даже вероятно много...
    while True:
        if input() == "exit":
            mt5.shutdown()
            break

        # TODO: Priority 1. Интересно, как лучше сделать делать перерасчет MA из текущей стоимости 
        # или с периодичностью в timeframe выгружать историю и с новой свечой получать последнее значение? 
        # Не уверено, что данная функция подойдет. Возможно нужна функция обновления фрейма.
        

        ma_last = np.array(ma50.get_MA_values()[ma50.name])[-1]
        # trend = np.array(ma50.get_MA_values()['trend'])[-1]
        signal = np.array(ma50.get_MA_values()['signal'])[-1]
        close_signal = np.array(ma50.get_MA_values()['close_signal'])


        current_price = get_price(symbol)

        result = mt5.positions_get(symbol)
        if len(result) == 0:
            if current_price >= ma_last and signal == "Open_buy":
                order_buy = Order(current_price, symbol)
                # order_buy.position_open(True, False)
                order_buy.fake_buy()
        
            if current_price <= ma_last and signal == "Open_sell":
                order_sell = Order(current_price, symbol)
                # order_buy.position_open(True, False)
                order_sell.fake_sell()
        else:
            if close_signal == "Close_buy":
                # order_buy.position_close()
                order_buy.fake_buy_sell_close(current_price)
                del order_buy

            if close_signal == "Close_sell":
                # order_sell.position_close() 
                order_buy.fake_buy_sell_close(current_price)
                del order_buy
        

        

startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()