import MetaTrader5 as mt5
from datetime import datetime
from metatrader5EasyT import trade

# Класс отвечающий за описание ордера
class Order():

    def __init__(self, open_price, symbol):
        self.open_price = open_price    # Цена открытия сделки.
        self.symbol = symbol
        self.trade_obj = trade.Trade(symbol, 1.0, 100, 100)

    # Запись в файл времени и теукщей цены
    def fake_buy(self):
        output_file = open("simulation.txt", "w")
        output_file.write(self.symbol + ", buy: " + self.open_price + ", " + datetime.timestamp() + "\n") 
        output_file.close()

    def fake_sell(self):
        output_file = open("simulation.txt", "w")
        output_file.write(self.symbol + ", sell: " + self.open_price + ", " + datetime.timestamp() + "\n")
        output_file.close()

    def position_open(self, buy: bool, sell: bool):
        self.trade_obj.position_open(buy, sell)

    def position_close(self):
        self.trade_obj.position_close()

    def position_check(self):
        self.position_check()
    
    # TODO: реализовать трэйлинг стоп
    # def tralingStop():
