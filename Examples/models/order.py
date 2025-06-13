import time
import MetaTrader5 as mt5
import logging
from datetime import datetime
from metatrader5EasyT import trade

# Класс отвечающий за описание ордера
class Order():

    def __init__(self, open_price, symbol, atr_value):
        self.open_price = open_price    # Цена открытия сделки.
        self.symbol = symbol
        self.trade_obj = trade.Trade(symbol, 1.0, atr_value, atr_value)
        self.atr_value = atr_value
        self.isBuy = None

    def position_check(self):
        self.position_check()

    # Запись в файл времени и теукщей цены
    def fake_buy(self):
        logging.info("fake_buy()")
        self.isBuy = True
        output_file = open("D:\Project_Robot\simulation.txt", "a")
        output_file.write(self.symbol + ", buy: " + str(self.open_price) + ", SL: " + str(self.open_price - (self.atr_value)) 
                          + ", TP: " + str(self.open_price + (self.atr_value)) + ", " + str(time.asctime()) + "\n") 
        output_file.close()

    def fake_sell(self):
        logging.info("fake_sell()")
        self.isBuy = False
        output_file = open("D:\Project_Robot\simulation.txt", "a")
        output_file.write(self.symbol + ", sell: " + str(self.open_price) + ", SL: " + str(self.open_price + (self.atr_value)) 
                          + ", TP: " + str(self.open_price - (self.atr_value)) + ", " + str(time.asctime()) + "\n")
        output_file.close()

    def fake_buy_sell_close(self, current_price):
        logging.info("fake_close()")
        output_file = open("D:\Project_Robot\simulation.txt", "a")
        output_file.write(self.symbol + ", close_position: " + str(current_price) + ", " + str(time.asctime()) + "\n")
        profit = None
        if self.isBuy==True:
            profit = current_price - self.open_price    
        elif self.isBuy==True:
            profit = self.open_price - current_price
        output_file.write(self.symbol + ", profit: " + str(profit) + ", " + str(time.asctime()) + "\n")
        output_file.close()

    def position_open(self, buy: bool, sell: bool):
        logging.info("position_open()")
        self.trade_obj.position_open(buy, sell)

    def position_close(self):
        logging.info("position_close()")
        self.trade_obj.position_close()
    
    # TODO: реализовать трэйлинг стоп
    # def tralingStop():
