import time
import MetaTrader5 as mt5
from datetime import datetime
from metatrader5EasyT import trade
import pandas as pd
import core.global_vars as gv
import core.app_logger as app_logger
import random

logger=app_logger.get_logger(__name__)


# Класс отвечающий за описание ордера
class Order():

    def __init__(self, open_price, symbol, atr_value):
        self.open_price = open_price    # Цена открытия сделки.
        self.symbol = symbol
        self.trade_obj = trade.Trade(symbol, 1.0, atr_value, atr_value)
        self.atr_value = atr_value
        self.isBuy = None
        self.stop_loss = None
        self.take_profit = None
        self.id = random.randint(0, 100000)
        self.sim_log_path = gv.global_args.logs_directory + "\\" + gv.global_args.monney_mode + "\\simulation.txt"


    def position_check(self):
        self.position_check()

    # Запись в файл времени и теукщей цены
    def fake_buy(self):
        logger.info("Order.id = " + str(self.id))
        self.isBuy = True
        self.stop_loss = self.open_price - self.atr_value
        self.take_profit = self.open_price + self.atr_value
        output_file = open(self.sim_log_path, "a")
        output_file.write(self.symbol + ", buy: " + str(self.open_price) + ", SL: " + str(self.stop_loss) 
                          + ", TP: " + str(self.take_profit) + ", " + str(time.asctime()) + "\n") 
        output_file.close()

    def fake_sell(self):
        logger.info("Order.id = " + str(self.id))
        self.isBuy = False
        self.stop_loss = self.open_price + self.atr_value
        self.take_profit = self.open_price - self.atr_value
        output_file = open(self.sim_log_path, "a")
        output_file.write(self.symbol + ", sell: " + str(self.open_price) + ", SL: " + str(self.stop_loss) 
                          + ", TP: " + str(self.take_profit) + ", " + str(time.asctime()) + "\n")
        output_file.close()

    def fake_buy_sell_close(self, current_price):
        logger.info("Order.id = " + str(self.id))
        output_file = open(self.sim_log_path, "a")
        output_file.write(self.symbol + ", close_position: " + str(current_price) + ", " + str(time.asctime()) + "\n")
        profit = None
        if self.isBuy==True:
            profit = current_price - self.open_price    
        elif self.isBuy==False:
            profit = self.open_price - current_price
        output_file.write(self.symbol + ", profit: " + str(profit) + ", " + str(time.asctime()) + "\n")
        output_file.close()

    def position_open(self, buy: bool, sell: bool):
        logger.info("Order.id = " + str(self.id))
        self.trade_obj.position_open(buy, sell)

    def position_close(self):
        logger.info("Order.id = " + str(self.id))
        self.trade_obj.position_close()
    
    # TODO: Priority: 1 [general\sim]Реализовать трэйлинг стоп
    #  аргумент теукщая цена. Если цена увеличилась на фиксированое значение(значение или % тут надо подумать), то сдвигаем стоп лосс.
    def fake_traling_stop(self, current_price, indent):
        isNeedToMoveSL = None
        new_value = None
        point=mt5.symbol_info(self.symbol).point
        if self.isBuy:
            new_value = current_price - self.atr_value
            isNeedToMoveSL = (self.stop_loss + (indent * point)) <= new_value
        else:
            new_value = current_price + self.atr_value
            isNeedToMoveSL = (self.stop_loss - (indent * point)) >= new_value

        if isNeedToMoveSL: 
            self.stop_loss = new_value
            output_file = open(self.sim_log_path, "a")
            output_file.write(self.symbol + ", SL changed: " + str(self.stop_loss) + ", " + str(time.asctime()) + "\n") 
            output_file.close()
    
    def traling_stop(self, current_price, indent):
        isNeedToMoveSL = None
        order_type = None
        new_value = None
        point=mt5.symbol_info(self.symbol).point
        position = pd.DataFrame(mt5.positions_get(self.symbol))
        # Вот тут дыра конечно... т.к. список может прийти с несколькими позициями.
        #  Чисто теоретически если будет 1 позиция на символ, то должно рабоатт корректно.
        self.stop_loss = pd.to_numeric(position['sl'])[-1]
        if self.isBuy:
            new_value = current_price - self.atr_value
            isNeedToMoveSL = (self.stop_loss + indent * point) <= current_price
            order_type = mt5.ORDER_TYPE_BUY
        else:
            new_value = current_price + self.atr_value
            isNeedToMoveSL = (self.stop_loss - indent * point) >= current_price
            order_type = mt5.ORDER_TYPE_SELL
        if isNeedToMoveSL: self.stop_loss = new_value
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": self.symbol,
            "volume": 1.0,
            "type": order_type,
            "price": current_price,
            "sl": self.stop_loss,
            "magic": 7777,
           "comment": "trailing stop, python",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        result=mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error("4. order_send failed, retcode={}".format(result.retcode))
            logger.error("   result",result)
        else:
            # request the result as a dictionary and display it element by element
            result_dict=result._asdict()
            logger.info("Value of Stop Loss is changed. SL = " + str(result_dict.get('sl')))