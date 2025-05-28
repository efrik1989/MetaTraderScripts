from datetime import datetime, timedelta
import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import MetaTrader5 as mt5


"""
timeframe - от 1 минуты до 1 месяца примеры тут https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrom_py
window - число значений для расчета обозначается как окно.
"""
class MA():

    def __init__(self, name:str, window:int):
        self.name = name
        self.window = window

    def get_MA_values(self, period):
            if period == "all" or period == None or period == "":
                return self.frame
            elif period > 0:
                 return self.frame.tail(period)
            
    def update_MA_values(self, frame):
        close_pos_list = frame['close']
        window_size = self.window

        numbers_series = pd.Series(close_pos_list)
        windows= numbers_series.rolling(window_size)
        moving_avarages = windows.mean()
        moving_avarages_list = moving_avarages.tolist()
        frame[self.name] = moving_avarages_list
        return frame
    
    # Стратегия подсвечивает сигналы при работе с индикатором MA50 на исторических данных
    def strategyMA50(self, frame):
        logging.info("strategyMA50(): start frame analis...")
        frame['diff'] = pd.to_numeric(frame['close']) - pd.to_numeric(frame[self.name])
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
            (frame['target_day_befor_1'] == True) & (frame['trend'] == "UP") & (frame['close_day_befor_1'] > frame[self.name]),
            (frame['target_day_befor_1'] == True) & (frame['trend'] == "DOWN") & (frame['close_day_befor_1'] < frame[self.name])]
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