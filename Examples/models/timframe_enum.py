import MetaTrader5 as mt5
from enum import Enum

class Timeframe(Enum):
    M5 = mt5.TIMEFRAME_M5
    M10 = mt5.TIMEFRAME_M10
    M15 = mt5.TIMEFRAME_M15
    M30 = mt5.TIMEFRAME_M30
    H1 = mt5.TIMEFRAME_H1
    H2 = mt5.TIMEFRAME_H2
    H3 = mt5.TIMEFRAME_H3
    H4 = mt5.TIMEFRAME_H4
    H6 = mt5.TIMEFRAME_H6
    H8 = mt5.TIMEFRAME_H8
    H12 = mt5.TIMEFRAME_H12
    D1 = mt5.TIMEFRAME_D1
    W = mt5.TIMEFRAME_W1
    MN = mt5.TIMEFRAME_MN1

    