import time
import MetaTrader5 as mt5
import logging
from datetime import datetime
from metatrader5EasyT import trade

# Класс отвечающий за описание ордера
class Order():

    def __init__(self, open_price, symbol):
        self.open_price = open_price    # Цена открытия сделки.
        self.symbol = symbol
        self.trade_obj = trade.Trade(symbol, 1.0, 100, 100)

    def position_check(self):
        self.position_check()

    # Запись в файл времени и теукщей цены
    def fake_buy(self):
        logging.info("fake_buy()")
        output_file = open("D:\Project_Robot\simulation.txt", "a")
        #TODO: Уровни SL и TP захардкожены в этом классе. Нужно вынести в основной скрипт. А то это порно. конечно.
        output_file.write(self.symbol + ", buy: " + str(self.open_price) + ", SL: " + str(self.open_price - 100) 
                          + ", TP: " + str(self.open_price + 100) + ", " + str(time.asctime()) + "\n") 
        output_file.close()

    def fake_sell(self):
        logging.info("fake_sell()")
        output_file = open("D:\Project_Robot\simulation.txt", "a")
        output_file.write(self.symbol + ", sell: " + str(self.open_price) + ", SL: " + str(self.open_price + 100) 
                          + ", TP: " + str(self.open_price - 100) + ", " + str(time.asctime()) + "\n")
        output_file.close()

    def fake_buy_sell_close(self, current_price):
        logging.info("fake_close()")
        output_file = open("D:\Project_Robot\simulation.txt", "a")
        output_file.write(self.symbol + ", close_position: " + str(current_price) + ", " + str(time.asctime()) + "\n") 
        output_file.close()

    def position_open(self, buy: bool, sell: bool):
        logging.info("position_open()")
        self.trade_obj.position_open(buy, sell)

    def position_close(self):
        logging.info("position_close()")
        self.trade_obj.position_close()
    
    # TODO: реализовать трэйлинг стоп
    # def tralingStop():
