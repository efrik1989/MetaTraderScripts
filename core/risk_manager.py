from datetime import datetime, timedelta
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import numpy as np
import core.app_logger as app_logger

register_matplotlib_converters()
import MetaTrader5 as mt5

logger = app_logger.get_logger(__name__)

class RiskManager():
    def __init__(self, trade_risk, lost_risk):
        self.trade_risk = trade_risk
        self.lost_risk = lost_risk
        self.account_info_dict = None
        self.equity = None

    def get_equity(self):
        # connect to the trade account specifying a password and a server
        account_info=mt5.account_info()
        if account_info!=None:
            self.account_info_dict = mt5.account_info()._asdict()
            self.equity = float(self.account_info_dict.get("equity"))
        
    def get_trade_risk_volue(self):
         risk_value = (self.equity / 100) * self.trade_risk
         return float(risk_value)
    
    def get_lost_risk_volue(self):
         low_balance = self.equity - ((self.equity / 100) * self.lost_risk)
         return float(low_balance)

     # TODO: Prioriry:1 [general] Возможно рисковое значения общего счета меняется в процессе. Нужно проверить.
    def is_tradable(self):
         self.get_equity()
         free_margin = float(self.account_info_dict.get("margin_free"))
         risk_equity_value = self.equity - self.get_trade_risk_volue()
         if free_margin >= risk_equity_value:
              logger.info("is_tradable(): Robot can trading. risk_equity_value: " + str(risk_equity_value))
              return True
         else:
              logger.warning("is_tradable(): Robot can't trading.")
              return False
         
    def is_equity_satisfactory(self):
         self.get_equity()        
         if self.equity >= self.get_lost_risk_volue():
            return True
         else:
              logger.warning("is_balance_too_low(): Balances have gone beyond the risk value.")
              return False
"""    
def start():
    if not mt5.initialize():
            print("initialize() failed, error code =",mt5.last_error())
            quit()
    authorized = mt5.login(login=23677, server="FINAM-AO",password="3C$ap3%H")
    risk_manager = RiskManager(10, 5)
    risk_manager.get_equity()
    print(risk_manager.equity)
    print(risk_manager.account_info_dict)
    print(risk_manager.is_tradable())
    print(risk_manager.is_equity_satisfactory()) 

start()"""