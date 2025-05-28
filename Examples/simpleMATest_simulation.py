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
symbols = ("LKOH", "TATN", "SBER", "MAGN", "VTBR", "NLMK", "CHMF", "X5", "MGNT", "YDEX", "OZON")
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
    
    # request connection status and parameters
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
# Получение цены
def get_price(symbol):
    tick_obj = tick.Tick(symbol)
    tick_obj.get_new_tick()
    return tick_obj.bid

# Получениея списка данных для скользящей средней
def get_history(symbol, timeframe, days_num):
    date_now = datetime.today()
    date_yesterday = date_now - timedelta(days=1)
    start_day_temp = date_now - timedelta(days=days_num + days_num)
    return mt5.copy_rates_range(symbol, timeframe, start_day_temp, date_yesterday)

# Получение торговых данных инструмента за рпеделенный промежуток
def get_rates_frame(symbol, start_bar, bars_count):
    # rates = get_history(symbol, time_frame, days_num)
    rates = mt5.copy_rates_from_pos(symbol, time_frame, start_bar, bars_count)
    if len(rates) == 0:
        logging.error("get_rates_frame(): Failed to get history data. " + str(mt5.last_error()))
    rates_frame = pd.DataFrame(rates)
    # rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
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
    
    #Функция опрделения точки выходи из сделки
def startegyRSI_close(columnName: str, frame):
    conditions = [
        (frame[columnName] > 70),
        ((frame[columnName] < 30))]
    chois = ["Close_buy", "Close_Sell"]
    frame['close_signal'] = np.select(conditions, chois, default="NaN")

# Стратегия подсвечивает сигналы при работе с индикатором MA50 на исторических данных
def strategyMA50(ma, frame, period):
    logging.info("strategyMA50(): start frame analis...")
    frame['diff'] = pd.to_numeric(frame['close']) - pd.to_numeric(frame[ma.name])
    frame['trend'] = pd.Series(frame['diff']) > 0

    d = {True: 'UP', False: 'DOWN'}
    frame['trend'] = frame['trend'].map(d)

    # TODO: Смысл такой находим максималььно близкиеи точки к MA (возможно проверяем цену открытия плюсом)
    # Добавляем в frame булевое значение true, после смотрим и\или жджем и смотрим следующую цену закрытия, 
    # если при растущем тренде цена выше MA открываем buy, если тренд наснижение и цена закрытия ниже MA sell

    # В отдельную функцию вынести
    frame['target'] = (pd.to_numeric(frame['diff']) < 5) & (-5 < pd.to_numeric(frame['diff']))
    frame['target_day_befor_1'] = frame['target'].shift(1)
    frame['close_day_befor_1'] = frame['close'].shift(1)

    # Ну вроде как ок. стоит зафиксировать!!!
    conditions = [
        (frame['target_day_befor_1'] == True) & (frame['trend'] == "UP") & (frame['close_day_befor_1'] > frame[ma.name]),
        (frame['target_day_befor_1'] == True) & (frame['trend'] == "DOWN") & (frame['close_day_befor_1'] < frame[ma.name])]
    chois = ["Open_buy", "Open_sell"]
    frame['signal'] = np.select(conditions, chois, default="NaN")


    # Выход из сделки сыровать пока. Дорабатывать надо. Можно в отдельную функцию выделить.
    frame['day_befor_1'] = frame['close'].shift(1)
    frame['day_befor_2'] = frame['close'].shift(2)
    frame['day_befor_3'] = frame['close'].shift(3)
    
    # conditions = [
    #    (frame['day_befor_1'] > frame['close']) & (frame['day_befor_2'] > frame['day_befor_1']) & (frame['day_befor_3'] > frame['day_befor_2']),
    #    (frame['day_befor_1'] < frame['close']) & (frame['day_befor_2'] < frame['day_befor_1']) & (frame['day_befor_3'] < frame['day_befor_2'])]
    # chois = ["Close_buy", "Close_Sell"]
    # frame['close_signal'] = np.select(conditions, chois, default="NaN")

    logging.info("strategyMA50(): Analis complete.")

def update_frame(frame: pd.DataFrame, ma, rsi):
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
        strategyMA50(ma,frame, "all")
        startegyRSI_close(rsi.name, frame)
        print(frame.tail(5))
        frame.to_excel('D:\Project_Robot\out_' + symbol + '_MA50_frame_signal_test.xlsx')
        logging.info("update_frame(): Update complete. Frame in: D:\Project_Robot\out_" + symbol + "_MA50_frame_signal_test.xlsx to manual analis.")
        return frame
    return frame

def startRobot():
    init_MT5()
    authorization()
    
        # Похоже это стоит пихать только в определенную стратегию т.к. поведение робота должно быть разным при разных скользящих средних
        # ma_analis(symbol, ma_list=(ma50, ma200))

    # Сейчас используется для выгрузки данных за определенный переиод. Так ну по сути для посторения MA все равно нужны исторические данные
    # Возможно все равно нужно первым делом исторические данные брать. Строить MA, а после сверять с плавающей ценой.
    # Разница между MA и пока показала свою полезность - используем.

    selectSymbol(symbol)

    frame = get_rates_frame(symbol, 2, rates_range)
    ma50 = MA('MA50', frame, window) 
    # TODO: Priority 2: Функцию createMA(): убрать надо ее может заменить update_MA_values(). Причем без последствий
    ma50.createMA()    
    rsi = RSI("RSI14", 14, True)
    rsi.update_RSI_values(frame)
    strategyMA50(ma50, frame, "all") # тут весь фрейм тащиться и анализируется, может его шринкануть? по сути нам нужны только 60-100 строк. Даже вероятно много...
    startegyRSI_close(rsi.name, frame)
    frame.to_excel('D:\Project_Robot\out_' + symbol + '_MA50_frame_signal_test.xlsx')
    while True:
        time.sleep(1)
        # if input() == "exit":
        #    mt5.shutdown()
        #   logging.info("Exit from programm.")
        #    break

        # TODO: Priority 1. Интересно, как лучше сделать делать перерасчет MA из текущей стоимости 
        # или с периодичностью в timeframe выгружать историю и с новой свечой получать последнее значение? 
        # Не уверено, что данная функция подойдет. Возможно нужна функция обновления фрейма.

        #TODO: Нужен метод, что будет обновлять последние значения frame-а а не перефигачивать весь каждый раз

        frame = update_frame(frame, ma50, rsi)
        ma_last = np.array(frame[ma50.name])[-1]
        # trend = np.array(ma50.get_MA_values()['trend'])[-1]
        signal = np.array(frame['signal'])[-1]

        if signal == "Open_buy" or signal == "Open_sell":
            logging.info("Signal to open position find: " + signal)
        close_signal = np.array(frame['close_signal'])[-1]
        if close_signal == "Close_buy" or signal == "Close_buy":
            logging.info("Signal to close position find: " + close_signal)

        current_price = get_price(symbol)

        result = pd.DataFrame(mt5.positions_get(symbol))

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
            if close_signal == "Close_buy" and order_buy != None:
                # order_buy.position_close()
                order_buy.fake_buy_sell_close(current_price)
                del order_buy

            if close_signal == "Close_sell" and order_sell != None:
                # order_sell.position_close() 
                order_sell.fake_buy_sell_close(current_price)
                del order_buy
        
        
        

startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()