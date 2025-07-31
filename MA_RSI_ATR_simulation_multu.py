from datetime import datetime, timedelta
import os
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd
import logging
from pandas.plotting import register_matplotlib_converters
import numpy as np
import threading

register_matplotlib_converters()
import MetaTrader5 as mt5
from metatrader5EasyT import tick
from indicators.ma import MA
from indicators.rsi import RSI
from indicators.atr import ATR
from models.order import Order
from models.timframe_enum import Timeframe
from core.risk_manager import RiskManager
from core.mt5_actions import MT5_actions as mt5_a
from core.args_parser import Args_parser as parser

"""
Основная задача скрипта опрпделеять точки входа в сделку и выхода.
На вход получаем минутный фрейм, будем подоватьт по строчно т.е. будут известны история этих данных и 
чтобы принять решение об открытии позиции нужно подождать закрытия следующего бара.
"""
args = parser.args_parse()
parser.create_dirs_if_not_exist(args.logs_directory + "\\" + args.monney_mode)
parser.create_dirs_if_not_exist("frames")

# TODO: Priority: 1 [general] Обложить все юнит тестами
# TODO: Priority: 2 [general] Логи с каждым перезапуском не должны перезаписываться файл лого должен дописываться(готово) и ротироваться каждый день в 00:00
# TODO: Priority: 2 [general\sim] В логи попадает запись об обновлении цены, а она каждую секунду обнавляется. Иих ОЧЕНЬ много.
logging.basicConfig(level=logging.INFO, filename=args.logfile, filemode="a", format="%(asctime)s %(levelname)s %(message)s")

# TODO: Сюда пока выносить параметры, что стоит указывать в аргументах при запуске, а не хардкодить.
# Период для индикаторов
window = 50
is_programm_need_to_stop = False



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

# Обновление данных для анализа и запуск самого анализа по индикаторам
# TODO: Была мысль обезличить запускаемые методы просчета стратегии, но думаю не стоит. Во всяком случае пока...
# Как минимум над этим нужно подумать. Думаю стоит это сделать, но пока нет пониимая каким образом.
def update_frame(symbol, frame: pd.DataFrame, last_bar_frame, ma, rsi, atr):
    try:    
            frame = pd.concat([frame, last_bar_frame], ignore_index=True)
            frame = ma.update_MA_values(frame)
            frame = rsi.update_RSI_values(frame)
            frame = atr.update_ATR_values(frame)
            ma.strategyMA50(frame)
            rsi.startegyRSI_close(frame)
            # print(frame.tail(3))
            frame.to_excel('frames\\out_' + str(symbol) + '_MA50_frame_signal_test.xlsx')
            logging.info(str(symbol) + ": update_frame(): Update complete. Frame in: frames\\out_" + str(symbol) + "_MA50_frame_signal_test.xlsx to manual analis.")
            return frame
    except(AttributeError):
        logging.critical(str(symbol) + ": update_frame(): 1 оr more objects become 'None/Null'")

def lets_trade(symbol):
    mt5_a.selectSymbol(symbol)
    risk_manager = RiskManager(args.monney_manager, args.lost_risk)
    tick_obj = tick.Tick(symbol)
    frame = mt5_a.get_rates_frame(symbol, 2, args.range, args.timeframe)
    ma50 = MA('MA50', window) 
    rsi = RSI("RSI14", 14, True)
    atr = ATR("ATR", 14)
    order_sell = None
    order_buy = None
    is_bar_used = False
    while True:
        time.sleep(1)
        last_bar_frame = mt5_a.get_last_bar(symbol, args.timeframe, index=np.array(frame.index)[-1] + 1)
        if is_need_update_lst_bar(symbol, frame, last_bar_frame):
            frame = update_frame(symbol, frame, last_bar_frame,  ma50, rsi, atr)
            is_bar_used = False
            if not risk_manager.is_equity_satisfactory():
                raise Exception("Balance is too low!!!")

        ma_last = np.array(pd.to_numeric(frame[ma50.name]))[-1]
        
        signal = np.array(frame['signal'])[-1]
        close_signal = np.array(frame['close_signal'])[-1]

        current_price = mt5_a.get_price(tick_obj)
        # TODO: Возможно стоит ATR записывать в 2 отдельныйх столбца SL и TP. 
        # А затем пост обработкой все значения кроме тех где сигнал на покупку\продажу выставлять NaN. Для более простого анализа.
        atr_value = float(np.array(frame['ATR'])[-1] * 2)
        
        # signal = "Open_buy"
        # close_signal = "Close_buy"
        try:
            # TODO: Очень много if-ов надо прикинуть как сделать логику проще или раскидать по функциям (что мне кажется более реально)
            # if-ы раскидал немного но чет все еще громоздко
            # После добавления risk_managera стало хуже. надо снова рефакторить. 
            if args.monney_mode == "trade":
                if not is_bar_used:

                    is_order_open = mt5_a.check_order(symbol)

                    if not is_order_open  and signal == "Open_buy":
                        logging.info(str(symbol) + ": Signal to open position find: " + signal)
                        if risk_manager.is_tradable():
                            order_buy = Order(current_price, symbol, atr_value)
                            order_buy.position_open(True, False)
                
                    if (not is_order_open and signal == "Open_sell") and args.buy_sell == True:
                        logging.info(str(symbol) + ": Signal to open position find: " + signal)
                        if risk_manager.is_tradable():
                            order_sell = Order(current_price, symbol, atr_value)
                            order_sell.position_open(False, True)
                        
                    if is_order_open and close_signal == "Close_buy":
                        logging.info(str(symbol) + ": Signal to close position find: " + close_signal)
                        order_buy.position_close()

                    if (is_order_open and close_signal == "Close_sell") and args.buy_sell == True:
                        logging.info(str(symbol) + ": Signal to close position find: " + close_signal)
                        order_sell.position_close() 

                    # Функция Trailing stop
                    if type(order_buy) == Order and args.trailing_stop != 0:
                        order_buy.traling_stop(current_price, args.trailing_stop)
                    if type(order_sell) == Order and args.trailing_stop != 0:
                        order_sell.traling_stop(current_price, args.trailing_stop)
            
            # Проверка на значений SL и TP не нужна для боевого робота. После симуляции удалить или закомментировать.
            # Надо разобраться по какой-то причине по SLTP сделки не завершаются.
            if args.monney_mode == "simulation":

                if not is_bar_used:
                    # Открытие сделки Buy
                    if type(order_buy) != Order and signal == "Open_buy":
                        logging.info(str(symbol) + ": Signal to open position find: " + signal)
                        if risk_manager.is_tradable():
                            order_buy = Order(current_price, symbol, atr_value)
                            order_buy.fake_buy()
                            is_bar_used = True

                    # Открытие сделки Sell
                    if args.buy_sell == True and (type(order_sell ) != Order and signal == "Open_sell"):
                        logging.info(str(symbol) + ": Signal to open position find: " + signal)
                        if risk_manager.is_tradable():
                            order_sell = Order(current_price, symbol, atr_value)
                            order_sell.fake_sell()
                            is_bar_used = True

                    if type(order_buy) == Order and close_signal == "Close_buy":
                        logging.info(str(symbol) + ": Signal to close position find: " + close_signal)
                        order_buy.fake_buy_sell_close(current_price)
                        order_buy = None

                    if (type(order_sell) == Order and close_signal == "Close_sell"):
                        logging.info(str(symbol) + ": Signal to close position find: " + close_signal)
                        order_sell.fake_buy_sell_close(current_price)
                        order_sell = None

                # Проверка SLTP
                if (type(order_buy) == Order and (current_price >= order_buy.take_profit or current_price <= order_buy.stop_loss )):
                    logging.info(str(symbol) + ": Signal to close position find: SLTP")
                    order_buy.fake_buy_sell_close(current_price)
                    order_buy = None

                if (type(order_sell) == Order and (current_price <= order_sell.take_profit or current_price >= order_sell.stop_loss )):
                    logging.info(str(symbol) + ": Signal to close position find: SLTP")
                    order_sell.fake_buy_sell_close(current_price)
                    order_sell = None

                # Функция Trailing stop
                if type(order_buy) == Order and args.trailing_stop != 0:
                    order_buy.fake_traling_stop(current_price, args.trailing_stop)
                if type(order_sell) == Order and args.trailing_stop != 0:
                    order_sell.fake_traling_stop(current_price, args.trailing_stop)

        except(UnboundLocalError):
            logging.exception(str(symbol) + ": lets_trade(): Переменная или объект не в том месте.!!!")

def startRobot():
    mt5_a.init_MT5()
    mt5_a.authorization(args.account, args.password)
    
    if len(args.symbols) != 0:
        logging.debug("Symbols lenght: " + str(len(args.symbols)))
        for symbol in args.symbols:
            logging.info(str(symbol) + ": start()")
            thread=threading.Thread(target=lets_trade, args=(symbol,), daemon=True)
            thread.start()
    # TODO: Priority: 2 [general] Добавить "Уровень риска". Процент от общего счета который может использовать робот. 
    # TODO: Priority: 1 [general] И предохранитель, если баланс опустил на n-% от максимального кидаем ошибку и останавливаемся.
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