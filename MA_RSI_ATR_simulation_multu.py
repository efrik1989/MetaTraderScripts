from datetime import datetime, timedelta
import os
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import numpy as np
import threading

register_matplotlib_converters()

import core.args_parser as args_parser
parser = args_parser.Args_parser()
args = parser.args_parse()

from core.risk_manager import RiskManager
from core.mt5_actions import MT5_actions as mt5_a
import core.app_logger as app_logger

logger=app_logger.get_logger(__name__)


import MetaTrader5 as mt5
from metatrader5EasyT import tick

from indicators.ma import MA
from indicators.rsi import RSI
from indicators.atr import ATR

from models.order import Order

"""
Основная задача скрипта опрпделеять точки входа в сделку и выхода.
На вход получаем минутный фрейм, будем подоватьт по строчно т.е. будут известны история этих данных и 
чтобы принять решение об открытии позиции нужно подождать закрытия следующего бара.
"""
# TODO: Priority: 1 [general] Необходимл отладить стратегию(ии). На данный момент можно запустить симуляцию, но это не проверка стратегии на исторических данных.
# Нужен отдельный режим history (как simulation\trade), что покажет, где бы по текущей стртегии был бы вход в сделку, выход из нее и профит + расчет итогового профита.
# TODO: Priority: 1 [general] Обложить все юнит тестами
# TODO: Пока выносить параметры, что стоит указывать в аргументах при запуске, а не хардкодить.
# TODO: Сделать возможность выставлять только SL или TP
# Период для индикаторов
window = 50
is_programm_need_to_stop = False



# Проверка нужно ли обновление фрэйма
def is_need_update_lst_bar(symbol, frame: pd.DataFrame, last_bar_frame):
    try:
        if frame.empty:
                logger.critical(str(symbol) + ": is_need_update_lst_bar(): Frame is empty!")
        
        last_bar_time = np.array(last_bar_frame['time'])[-1]
        last_bar_time_frame = np.array(frame['time'].tail(1))[-1]
        if np.array(last_bar_time_frame < last_bar_time):
            return True
        else:
            return False
    except(AttributeError):
        logger.critical(str(symbol) + ": is_need_update_lst_bar(): 1 оr more objects become 'None/Null'")

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
            return frame
    except(AttributeError):
        logger.critical(str(symbol) + ": 1 оr more objects become 'None/Null'")

def isCondition(frame, index, order_id):
    # Выглядит как какое-то порно... Надо подумамть.
    val = "NaN"
    if index == len(frame['target']) - 1: 
        val = order_id
    return val

def position_id_in_frame(order: Order, frame: pd.DataFrame, is_order_open):
    if type(order) == Order or is_order_open:
        value = order.id
    else:
        value = "NaN"

    if 'order_id' in frame.columns:
        frame.loc[frame.index[-1], 'order_id'] = value
        logger.info("order_id обновлен.")
    else:
        logger.info("Столбец 'order_id' не существует и будет создан.")
        close_ser = frame['target'].to_list()
        is_opened_list = []
        for index, item in enumerate(close_ser):
            is_opened_list.append(isCondition(frame, index, value))
        frame['order_id'] = is_opened_list
    return frame

def lets_trade(symbol):
    mt5_a.selectSymbol(symbol)
    risk_manager = RiskManager(args.monney_manager, args.lost_risk)
    tick_obj = tick.Tick(symbol)
    frame = mt5_a.get_rates_frame(symbol, 2, args.range, args.timeframe)
    ma50 = MA('MA50', window) 
    rsi = RSI("RSI14", 14, True)
    atr = ATR("ATR", 14)
    is_order_open = mt5_a.check_order(symbol)
    order_sell = None
    order_buy = None
    is_bar_used = False
    while True:
        time.sleep(1)
        last_bar_frame = mt5_a.get_last_bar(symbol, args.timeframe, index=np.array(frame.index)[-1] + 1)
        if is_need_update_lst_bar(symbol, frame, last_bar_frame):
            frame = update_frame(symbol, frame, last_bar_frame,  ma50, rsi, atr)
            # TODO: Priority: 3 Можно оставить один если будет только order.
            frame = position_id_in_frame(order_buy, frame, is_order_open)
            frame = position_id_in_frame(order_sell, frame, is_order_open)
            frame.to_excel(args.logs_directory + '\\frames\\out_' + str(symbol) + '_MA50_frame_signal_test.xlsx')
            logger.info(f"{str(symbol)}: Frames update complete. Frame in: {args.logs_directory}\\frames\\{str(symbol)}_MA50_RSI_ATR_signals_test.xlsx to manual analis.")
            is_bar_used = False
            if not risk_manager.is_equity_satisfactory():
                raise Exception("Balance is too low!!!")
        
        signal = np.array(frame['signal'])[-1]
        close_signal = np.array(frame['close_signal'])[-1]

        current_price = mt5_a.get_price(tick_obj)
        # TODO: Возможно стоит ATR записывать в 2 отдельныйх столбца SL и TP. 
        # А затем пост обработкой все значения кроме тех где сигнал на покупку\продажу выставлять NaN. Для более простого анализа.
        atr_value = float(np.array(frame['ATR'])[-1] * 2)
        
        # signal = "Open_buy"
        signal = "Open_sell"
        # close_signal = "Close_buy"
        try:
            # TODO: Очень много if-ов надо прикинуть как сделать логику проще или раскидать по функциям (что мне кажется более реально)
            # if-ы раскидал немного но чет все еще громоздко
            # После добавления risk_managera стало хуже. надо снова рефакторить. 
            if args.monney_mode == "trade":
                if not is_bar_used:

                    if not is_order_open  and signal == "Open_buy":
                        logger.info(str(symbol) + ": Signal to open position find: " + signal)
                        if risk_manager.is_tradable():
                            order_buy = Order(current_price, symbol, atr_value)
                            order_buy.position_open(True, False)
                            frame = position_id_in_frame(order_buy, frame, is_order_open)
                
                    if (not is_order_open and signal == "Open_sell") and args.buy_sell == True:
                        logger.info(str(symbol) + ": Signal to open position find: " + signal)
                        if risk_manager.is_tradable():
                            order_sell = Order(current_price, symbol, atr_value)
                            order_sell.position_open(False, True)
                            frame = position_id_in_frame(order_sell, frame, is_order_open)
                        
                    if is_order_open and close_signal == "Close_buy":
                        logger.info(str(symbol) + ": Signal to close position find: " + close_signal)
                        order_buy.position_close()
                        order_buy = None

                    if (is_order_open and close_signal == "Close_sell") and args.buy_sell == True:
                        logger.info(str(symbol) + ": Signal to close position find: " + close_signal)
                        order_sell.position_close() 
                        order_sell = None

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
                        logger.info(str(symbol) + ": Signal to open position find: " + signal)
                        if risk_manager.is_tradable():
                            order_buy = Order(current_price, symbol, atr_value)
                            order_buy.fake_buy()
                            is_bar_used = True
                            frame = position_id_in_frame(order_buy, frame, is_order_open)

                    # Открытие сделки Sell
                    if args.buy_sell == True and (type(order_sell ) != Order and signal == "Open_sell"):
                        logger.info(str(symbol) + ": Signal to open position find: " + signal)
                        if risk_manager.is_tradable():
                            order_sell = Order(current_price, symbol, atr_value)
                            order_sell.fake_sell()
                            is_bar_used = True
                            frame = position_id_in_frame(order_sell, frame, is_order_open)

                    if type(order_buy) == Order and close_signal == "Close_buy":
                        logger.info(str(symbol) + ": Signal to close position find: " + close_signal)
                        order_buy.fake_buy_sell_close(current_price)
                        order_buy = None

                    if (type(order_sell) == Order and close_signal == "Close_sell"):
                        logger.info(str(symbol) + ": Signal to close position find: " + close_signal)
                        order_sell.fake_buy_sell_close(current_price)
                        order_sell = None

                    # Проверка SLTP
                    if (type(order_buy) == Order and (current_price >= order_buy.take_profit or current_price <= order_buy.stop_loss )):
                        logger.info(str(symbol) + ": Signal to close position find: SLTP")
                        order_buy.fake_buy_sell_close(current_price)
                        order_buy = None

                    if (type(order_sell) == Order and (current_price <= order_sell.take_profit or current_price >= order_sell.stop_loss )):
                        logger.info(str(symbol) + ": Signal to close position find: SLTP")
                        order_sell.fake_buy_sell_close(current_price)
                        order_sell = None

                # Функция Trailing stop
                if type(order_buy) == Order and args.trailing_stop != 0:
                    order_buy.fake_traling_stop(current_price, args.trailing_stop)
                if type(order_sell) == Order and args.trailing_stop != 0:
                    order_sell.fake_traling_stop(current_price, args.trailing_stop)

        except(UnboundLocalError):
            logger.exception(str(symbol) + ": lets_trade(): Переменная или объект не в том месте.!!!")

def startRobot():
    mt5_a.init_MT5()
    mt5_a.authorization(args.account, args.password)
    
    if len(args.symbols) != 0:
        logger.debug("Symbols lenght: " + str(len(args.symbols)))
        for symbol in args.symbols:
            logger.info(str(symbol) + ": start()")
            thread=threading.Thread(target=lets_trade, args=(symbol,), daemon=True)
            thread.start()
    # TODO: Priority: 2 [general] Добавить "Уровень риска". Процент от общего счета который может использовать робот. 
    # TODO: Priority: 1 [general] И предохранитель, если баланс опустил на n-% от максимального кидаем ошибку и останавливаемся.
    # Или например нет больше денег на болансе и сделку совершить не возможно.
    print("Posible commands:")
    print("exit - exit from programm")
    print("Please enter command:")
    try: 
        while True:
            command = input()
            if command == "exit":
                logger.info("Exit from programm.")
                break
            else:
                print("Please enter correct command.")
    except Exception as e:
        logger.warning("Ошибка при работе с вводом! Экстренное завершение программы.")    

startRobot()
# shut down connection to MetaTrader 5
mt5.shutdown()
sys.exit