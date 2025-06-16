from datetime import datetime, timedelta
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd
import logging
from pandas.plotting import register_matplotlib_converters
import numpy as np
import argparse
import threading

register_matplotlib_converters()
import MetaTrader5 as mt5
from metatrader5EasyT import tick
from indicators.ma import MA
from indicators.rsi import RSI
from indicators.atr import ATR
from models.order import Order
from models.timframe_enum import Timeframe
"""
Основная задача скрипта опрпделеять точки входа в сделку и выхода.
На вход получаем минутный фрейм, будем подоватьт по строчно т.е. будут известны история этих данных и 
чтобы принять решение об открытии позиции нужно подождать закрытия следующего бара.
"""

# TODO: Prioroty: 4 [general] Возможно стоит парсер аргументов в отдельный класс вынести...
# TODO: Prioroty: 2 [general] Не все аргумены сделал. Точнее не все работает. Нужно будет с этим разобраться.
# TODO: Priority: 1 [general] Обложить все юнит тестами
# TODO: Priority: 2 [general] Добавить переключение между симуляцией и боевым режимом работы.
parser = argparse.ArgumentParser()
# Символы по умолчанию: "LKOH", "TATN", "SBER", "MAGN", "VTBR", "NLMK", "CHMF", "X5", "MGNT", "YDEX", "OZON"
parser.add_argument("-s", "--symbols", help="List of instrument symbols. Enter like a strings list(Example: 'LKOH' 'TATN')\n" \
" Default: 'LKOH', 'TATN', 'SBER', 'MAGN', 'VTBR', 'NLMK', 'CHMF', 'X5', 'MGNT', 'YDEX', 'OZON'", nargs="+", action="store", default=["LKOH", "TATN", "SBER", "MAGN", "VTBR", "NLMK", "CHMF", "X5", "MGNT", "YDEX", "OZON"] )
parser.add_argument("-l", "--logfile", help="Logfile path. Default: 'D:\Project_Robot\everything.log'", action="store", default="D:\Project_Robot\everything.log")
parser.add_argument("-r", "--range", help="Range of bar at first analis.", action="store", default=100)
parser.add_argument("-t", "--timeframe", help="Timeframe of instrument grafic. Default: 'M5' (5 minuts).\n" \
    " Posible values:\n" \
    " M5 - 5 minutes,\n" \
    " M10 - 10 minutes,\n" \
    " M15 - 15 minutes,\n" \
    " M30 - 30 minutes,\n" \
    " H1 - 1 hour,\n" \
    " H2 - 2 hours,\n" \
    " H3 - 3 hours,\n" \
    " H4 - 4 hours,\n" \
    " H6 - 6 hours,\n" \
    " H8 - 8 hours,\n" \
    " H12 - 12 hours,\n" \
    " D1 - 1 day,\n" \
    " W 1 weak,\n" \
    " MN = 1 month", action="store", default="M5")
parser.add_argument("-i", "--indicators", help="List of indicators.", action="store_true") # TODO: Под вопросом.
parser.add_argument("-a", "--account", help="Account number in Finam.", action="store_true", default=23677)
parser.add_argument("-p", "--password", help="Account password number in Finam.", action="store_true", default="3C$ap3%H")
parser.add_argument("-d", "--logs_directory", help="Logs store directory.", action="store_true", default="D:\Project_Robot")
parser.add_argument("-m", "--monney_mode", help="Mode of start. Posible values: \n" \
                    "simulation - trade simulation,\n" \
                    "trade - real trade.", action="store", default="simulation")
args = parser.parse_args()

# TODO: Priority: 2 [general] Логи с каждым перезапуском не должны перезаписываться файл лого должен дописываться(готово) и ротироваться каждый день в 00:00
logging.basicConfig(level=logging.INFO, filename=args.logfile, filemode="a", format="%(asctime)s %(levelname)s %(message)s")


# TODO: Сюда пока выносить параметры, что стоит указывать в аргументах при запуске, а не хардкодить.
# Период для индикаторов
window = 50
threads_stop = False
# Timeframe данных (графика)
# time_frame = mt5.TIMEFRAME_M5



def init_MT5():
    # connect to MetaTrader 5
    if not mt5.initialize("C:\\Program Files\\FINAM MetaTrader 5\\terminal64.exe"):
        logging.critical("initialize(): failed")
    
    # request connection status and parameters,0000
    # print(mt5.terminal_info())
    # get data on MetaTrader 5 version
    # print(mt5.version())

def authorization():
    # account = 23677 
    authorized = mt5.login(login=args.account, server="FINAM-AO",password=args.password)  
    if authorized:
        logging.info("authorization(): connected to account #{}".format(args.account))
    else:
        logging.error("authorization(): failed to connect at account #{}, error code: {}".format(args.account, mt5.last_error()))

# Выбираем символ(инструмент)
def selectSymbol(symbol):
    selected=mt5.symbol_select(symbol,True)
    if not selected:
        logging.error("selectSymbol(): Failed to select " + str(symbol) + ", error code =",mt5.last_error())
    else:
        # symbol_info=mt5.symbol_info(symbol)
        logging.info("selectSymbol(): " + str(symbol))

def get_price(tick_obj):        
    tick_obj.get_new_tick()
    return tick_obj.bid

# Получение торговых данных инструмента за определенный промежуток
def get_rates_frame(symbol, start_bar, bars_count):
    rates = mt5.copy_rates_from_pos(symbol, Timeframe[args.timeframe].value, start_bar, bars_count)
    if len(rates) == 0:
        logging.error(symbol + ": get_rates_frame(): Failed to get history data. " + str(mt5.last_error()))
    rates_frame = pd.DataFrame(rates)
    # rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
    rates_frame['close'] = pd.to_numeric(rates_frame['close'], downcast='float')
    return rates_frame

# Получение последнего бара
def get_last_bar(symbol, index):
    last_rates = mt5.copy_rates_from_pos(symbol, Timeframe[args.timeframe].value, 1, 1)
    if not last_rates:
        logging.critical(str(symbol) + ": get_last_bar(): Failed to get last rate: " + mt5.last_error())
        
    last_rates_df = pd.DataFrame(last_rates, index=[index])
    return last_rates_df

# Проверка нужно ли обновление фрэйма
def is_need_update_lst_bar(symbol, frame: pd.DataFrame, last_bar_frame):
    try:
        if frame.empty:
                logging.critical(str(symbol) + ": is_need_update_lst_bar(): Frame is empty!")
        
        last_bar_time = np.array(last_bar_frame['time'])[-1]
        last_bar_time_frame = np.array(frame['time'].tail(1))[-1]
        if np.array(last_bar_time_frame < last_bar_time):
            return True
        else:
            return False
    
    except(AttributeError):
        logging.critical(str(symbol) + ": is_need_update_lst_bar(): 1 оr more objects become 'None/Null'")

def check_order(symbol, monney_mode, order_buy, order_sell):
        result = False
        if monney_mode == "trade":
            positions = pd.DataFrame(mt5.positions_get(symbol)) 
            result = len(positions) > 0
        elif monney_mode == "simulation":
            result = (type(order_buy) == Order) or (type(order_sell) == Order)
        else:
            logging.error("Wrong monney mode. Posible values: 'simulation' or 'trade'.")
        return result

# Обновление данных для анализа и запуск самого анализа по индикаторам
# TODO: Была мысль обезличить запускаемые методы просчета стратегии, но думаю не стоит. Во всяком случае пока...
# Как минимум над этим нужно подумать.
def update_frame(symbol, frame: pd.DataFrame,last_bar_frame, ma, rsi, atr):
    try:    
            frame = pd.concat([frame, last_bar_frame], ignore_index=True)
            frame = ma.update_MA_values(frame)
            frame = rsi.update_RSI_values(frame)
            frame = atr.update_ATR_values(frame)
            ma.strategyMA50(frame)
            rsi.startegyRSI_close(frame)
            # print(frame.tail(3))
            frame.to_excel(args.logs_directory + '\out_' + str(symbol) + '_MA50_frame_signal_test.xlsx')
            logging.info(str(symbol) + ": update_frame(): Update complete. Frame in: " + args.logs_directory + "\out_" + str(symbol) + "_MA50_frame_signal_test.xlsx to manual analis.")
            return frame
    except(AttributeError):
        logging.critical(str(symbol) + ": update_frame(): 1 оr more objects become 'None/Null'")

def lets_trade(symbol):
    selectSymbol(symbol)
    tick_obj = tick.Tick(symbol)
    frame = get_rates_frame(symbol, 2, args.range)
    ma50 = MA('MA50', window) 
    rsi = RSI("RSI14", 14, True)
    atr = ATR("ATR", 14)
    order_sell = None
    order_buy = None
    is_bar_used = False
    while True:
        time.sleep(1)
        last_bar_frame = get_last_bar(symbol, index=np.array(frame.index)[-1] + 1)
        if is_need_update_lst_bar(symbol, frame, last_bar_frame):
            frame = update_frame(symbol, frame, last_bar_frame,  ma50, rsi, atr)
            is_bar_used = False

        ma_last = np.array(pd.to_numeric(frame[ma50.name]))[-1]
        
        signal = np.array(frame['signal'])[-1]
        close_signal = np.array(frame['close_signal'])[-1]

        current_price = get_price(tick_obj)
        atr_value = float(np.array(frame['ATR'])[-1] * 2)
        
        try:
            if check_order(symbol, args.monney_mode, order_buy, order_sell): 
                if current_price >= ma_last and signal == "Open_buy":
                    logging.info(str(symbol) + ": Signal to open position find: " + signal)
                    if not is_bar_used:
                        order_buy = Order(current_price, symbol, atr_value)
                        if args.monney_mode == "trade":
                            order_buy.position_open(True, False)
                    
                        # Для Симуляции
                        if args.monney_mode == "simulation":
                            order_buy.fake_buy()
                            take_profit = current_price + (atr_value)
                            stop_loss = current_price - (atr_value)
                            is_bar_used = True
            
                if current_price <= ma_last and signal == "Open_sell":
                    logging.info(str(symbol) + ": Signal to open position find: " + signal)
                    if not is_bar_used:
                        order_sell = Order(current_price, symbol, atr_value)
                        if args.monney_mode == "trade":
                            order_sell.position_open(False, True)
                        
                        # Для Симуляции
                        if args.monney_mode == "simulation":
                            order_sell.fake_sell()
                            take_profit = current_price - (atr_value)
                            stop_loss = current_price + (atr_value)
                            is_bar_used = True
            else:
                
                
                if type(order_buy) == Order and close_signal == "Close_buy":
                    logging.info(str(symbol) + ": Signal to close position find: " + close_signal)
                    if not is_bar_used:
                        if args.monney_mode == "trade":
                            order_buy.position_close()
                        if args.monney_mode == "simulation":
                            order_buy.fake_buy_sell_close(current_price)
                            order_buy = None

                if (type(order_sell) == Order and close_signal == "Close_sell"):
                    logging.info(str(symbol) + ": Signal to close position find: " + close_signal)
                    if not is_bar_used:
                        # order_sell.position_close() 
                        if args.monney_mode == "simulation":
                            order_sell.fake_buy_sell_close(current_price)
                            order_sell = None
                
                # Проверка на значений SL и TP не нужна для боевого робота. После симуляции удалить или закомментировать.
                # Надо разобраться по какой-то причине по SLTP сделки не завершаются.
                if args.monney_mode == "simulation":
                    if (type(order_buy) == Order and (current_price >= take_profit or current_price <= stop_loss )):
                        logging.info(str(symbol) + ": Signal to close position find: SLTP")
                        order_buy.fake_buy_sell_close(current_price)
                        order_buy = None

                    if (type(order_sell) == Order and (current_price <= take_profit or current_price >= stop_loss )):
                        logging.info(str(symbol) + ": Signal to close position find: SLTP")
                        order_sell.fake_buy_sell_close(current_price)
                        order_sell = None

        except(UnboundLocalError):
            logging.exception(str(symbol) + ": lets_trade(): Переменная или объект не в том месте.!!!")

def startRobot():
    init_MT5()
    authorization()
    
    if len(args.symbols) != 0:
        logging.info("Symbols lenght: " + str(len(args.symbols)))
        for symbol in args.symbols:
            logging.info(str(symbol) + ": start()")
            thread=threading.Thread(target=lets_trade, args=(symbol,), daemon=True)
            thread.start()
    # TODO: Priority: 2 [general] Добавить "Уровень риска". Процент от общего счета который может использовать робот. 
    # TODO: Priority: 2 [general] И предохранитель, если баланс опустил на n-% от максимального кидаем ошибку и останавливаемся.
    # Или например нет больше денег на болансе и сделку совершить не возможно.
    print("Posible commands:")
    print("exit - exit from programm")
    print("Please enter command:")
    while True:
        command = input()
        if command == "exit":
            logging.info("Exit from programm.")
            break
        else:
            print("Please enter correct command.")
            

startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()
sys.exit