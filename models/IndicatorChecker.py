import MetaTrader5 as mt5

# В теории индикатор должен проверять список, что приходит аргументом
# и брать нужные индикаторы. Ну в теории...
#TODO: оставим на потом пока надо сделать попроще.
class IndicatorChecker:

    def __init__(self, indicatorsList):
        self.indicatorsList = indicatorsList

        for indicator in indicatorsList:
            try:
                indiCl = indicator.capitalize()
                from indicators.indicator import indiCl
            except:
                print("An exception occured")