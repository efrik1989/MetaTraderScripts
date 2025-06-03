from datetime import datetime, timedelta
import time
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
from indicators.rsi import RSI
from indicators.atr import ATR
from models.order import Order
"""
Основная задача скрпта опрпделеять точки входа в сделку и выхода.
На вход получаем минутный фрейм, будем подоватьт по строчно т.е. будут известны история этих данных и 
чтобы принять решение об открытии позиции нужно подождать закрытия следующего бара.
"""
log_file_path = "D:\Project_Robot\everything.log"
logging.basicConfig(level=logging.INFO, filename=log_file_path, filemode="w", format="%(asctime)s %(levelname)s %(message)s")


symbol="LKOH"
# данные по 50 и 200 на Лукойл, Татнефть, Сбер, ВТБ, ммк, НЛМК, Северсталь, х5, магнит, Яндекс и озон
# symbols = ("LKOH", "TATN", "SBER", "MAGN", "VTBR", "NLMK", "CHMF", "X5", "MGNT", "YDEX", "OZON")
# Число баров для анализа
# rates_range = 700
rates_range = 100
# Период для индикаторов
window = 50
# Timeframe данных (графика)
time_frame = mt5.TIMEFRAME_M5
def init_MT5():
    # connect to MetaTrader 5
    if not mt5.initialize("C:\\Program Files\\FINAM MetaTrader 5\\terminal64.exe"):
        logging.critical("initialize(): failed")
    
    # request connection status and parameters,0000
    # print(mt5.terminal_info())
    # get data on MetaTrader 5 version
    # print(mt5.version())

def authorization():
    account = 23677 
    authorized = mt5.login(login=account, server="FINAM-AO",password="3C$ap3%H")  
    if authorized:
        logging.info("authorization(): connected to account #{}".format(account))
    else:
        logging.error("authorization(): failed to connect at account #{}, error code: {}".format(account, mt5.last_error()))

# Выбираем символ(инструмент)
def selectSymbol(symbol):
    selected=mt5.symbol_select(symbol,True)
    if not selected:
        logging.error("selectSymbol(): Failed to select " + symbol + ", error code =",mt5.last_error())
    else:
        symbol_info=mt5.symbol_info(symbol)
        logging.info("selectSymbol(): " + str(symbol_info))

def get_price(tick_obj):
        
    tick_obj.get_new_tick()
    return tick_obj.bid

# Получение торговых данных инструмента за определенный промежуток
def get_rates_frame(symbol, start_bar, bars_count):
    rates = mt5.copy_rates_from_pos(symbol, time_frame, start_bar, bars_count)
    if len(rates) == 0:
        logging.error("get_rates_frame(): Failed to get history data. " + str(mt5.last_error()))
    rates_frame = pd.DataFrame(rates)
    # rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
    rates_frame['close'] = pd.to_numeric(rates_frame['close'], downcast='float')
    return rates_frame

# Обновление данных для анализа и запуск самого анализа по индикаторам
# Была мысль обезличить запускаемые методы просчета стратегии, но думаю не стоит. Во всяком случае пока...
# TODO: Как минимум над этим нужно подумать.
def update_frame(frame: pd.DataFrame, ma, rsi, atr):
    try:
        if frame.empty:
            logging.critical("update_frame(): Frame is empty!")
        last_rates = mt5.copy_rates_from_pos(symbol, time_frame, 1, 1)
        if not last_rates:
            logging.critical("update_frame(): Failed to get last rate: " + mt5.last_error())
        
        last_rates_df = pd.DataFrame(last_rates, index=[np.array(frame.index)[-1] + 1])
        
        last_bar_time = np.array(last_rates_df['time'])[-1]
        last_bar_time_frame = np.array(frame['time'].tail(1))[-1]
        print("Время Последнего бара текущего фрейма: " + str(last_bar_time_frame))
        print("Время последнего полученого рэйта: " + str(last_bar_time))
        if np.array(last_bar_time_frame < last_bar_time):
            frame = pd.concat([frame, last_rates_df], ignore_index=True)
            frame = ma.update_MA_values(frame)
            frame = rsi.update_RSI_values(frame)
            frame = atr.update_ATR_values(frame)
            ma.strategyMA50(frame)
            rsi.startegyRSI_close(frame)
            print(frame.tail(5))
            frame.to_excel('D:\Project_Robot\out_' + symbol + '_MA50_frame_signal_test.xlsx')
            logging.info("update_frame(): Update complete. Frame in: D:\Project_Robot\out_" + symbol + "_MA50_frame_signal_test.xlsx to manual analis.")
            return frame
        return frame
    except(AttributeError):
        logging.critical("update_frame(): 1 оr more objects become 'None/Null'")


def startRobot():
    init_MT5()
    authorization()
    
    # Разница между MA и пока показала свою полезность - используем. Возможно стоит в проценты перевести, а буфер для открытия сделки может быть разным. 
    # И для открытия\закрытия может быть не достаточно фиксированных цифер.

    selectSymbol(symbol)
    tick_obj = tick.Tick(symbol)
    frame = get_rates_frame(symbol, 2, rates_range)
    ma50 = MA('MA50', window) 
    rsi = RSI("RSI14", 14, True)
    atr = ATR("ATR", 14)
    frame.to_excel('D:\Project_Robot\out_' + symbol + '_MA50_frame_signal_test.xlsx')
    order_sell = None
    order_buy = None
    while True:
        time.sleep(1)
        # TODO: Priority:3 [general] Сделать корректный выход из утилиты.
        # if input() == "exit":
        #    mt5.shutdown()
        #   logging.info("Exit from programm.")
        #    break

        frame = update_frame(frame, ma50, rsi, atr)
        ma_last = np.array(pd.to_numeric(frame[ma50.name]))[-1]
        
        signal = np.array(frame['signal'])[-1]
        if signal == "Open_buy" or signal == "Open_sell":
            logging.info("Signal to open position find: " + signal)

        close_signal = np.array(frame['close_signal'])[-1]
        if close_signal == "Close_buy" or signal == "Close_buy":
            logging.info("Signal to close position find: " + close_signal)

        current_price = get_price(tick_obj)
        atr_value = np.array(frame['ATR'])[-1]
        # Для симуляции это не подходит...
        # result = pd.DataFrame(mt5.positions_get(symbol))
        # Версия проверки для симуляции
        if (order_sell != None) or (order_buy != None):
            result = 1
        else:
            result = 0 
        # TODO: Priority:1 [sim] Добавить логику сверки со значениями SL, TP для полноценной симуляции, с подсчетом прибыли и убытков.
        # TODO: Priority:2 [general] Описать индикатор ATR для установки значений SL
        # TODO: Priority:3 [general] Добавить запуск с параметрами.
        # TODO: Priority:4 [general] Добавить многопоточность. Каждый инструмент должен запупскаться в своем потоке.

        # TODO: Priority:1 [general] !!! Сигнал о покупке или продаже расчитывается на основе цены закрытия последнего бара. И пробои и касания ценой(хвостом свечи) не учитываются. Это стоит обдумать...
        # Понаблюдал. анализ проводится на барах что уже прошли, но сделка открывается при пересечении MA. Думаю пока этого достаточно. Набллюдаем. 
        # Боевой вариант if len(result) == 0:
        # Для симуляции
        if result == 0:
            if current_price >= ma_last and signal == "Open_buy":
                order_buy = Order(current_price, symbol, atr_value)
                # order_buy.position_open(True, False)
                
                # Для Симуляции
                order_buy.fake_buy()
                take_profit = current_price + (atr_value * 2)
                stop_loss = current_price - (atr_value * 2)
        
            if current_price <= ma_last and signal == "Open_sell":
                order_sell = Order(current_price, symbol, atr_value)
                # order_buy.position_open(True, False)
                
                # Для Симуляции
                order_sell.fake_sell()
                take_profit = current_price + (atr_value * 2)
                stop_loss = current_price - (atr_value * 2)
        else:
            # Проверка на значений SL и TP не нужна для боевого робота. После симуляции удалить или закомментировать.
            if (close_signal == "Close_buy" and order_buy != None) or (current_price == stop_loss or current_price == take_profit):
                # order_buy.position_close()
                order_buy.fake_buy_sell_close(current_price)
                del order_buy

            if (close_signal == "Close_sell" and order_sell != None) or (current_price == stop_loss or current_price == take_profit):
                # order_sell.position_close() 
                order_sell.fake_buy_sell_close(current_price)
                del order_buy
        
        
        

startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()