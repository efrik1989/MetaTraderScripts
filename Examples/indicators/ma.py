from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import MetaTrader5 as mt5


"""
symbol - инструмент
timeframe - от 1 минуты до 1 месяца примеры тут https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrom_py
window - число значений для расчета обозначается как окно.
"""
class MA():

    def __init__(self, name:str, frame, window:int):
        self.name = name
        self.frame = frame
        self.window = window

    def createMA(self):
        
        close_pos_list = self.frame['close']
        window_size = self.window

        numbers_series = pd.Series(close_pos_list)
        windows= numbers_series.rolling(window_size)
        moving_avarages = windows.mean()
        moving_avarages_list = moving_avarages.tolist()
        self.frame[self.name] = moving_avarages_list
        # self.frame.dropna(inplace=True)
        # del self.frame['open']
        # Как я понял работа вся ведется в одном фрэйме. Это не проблема если индикатор 1. А что будет если несколько?
        # return moving_avarages_list[window_size - 1:]

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
        # frame.dropna(inplace=True)
        # del self.frame['open']
        # del frame['spread']
        # del frame['high']
        # del frame['low']
        # del frame['tick_volume']
        # del frame['real_volume']
        return frame