import argparse

class Args_parser():

    def __init__(self):
        pass

    def args_parse():
        parser = argparse.ArgumentParser()
        # Символы по умолчанию: "LKOH", "TATN", "SBER", "MAGN", "VTBR", "NLMK", "CHMF", "X5", "MGNT", "YDEX", "OZON"
        parser.add_argument("-s", "--symbols", help="List of instrument symbols. Enter like a strings list(Example: 'LKOH' 'TATN')\n" \
        " Default: 'LKOH', 'TATN', 'SBER', 'MAGN', 'VTBR', 'NLMK', 'CHMF', 'X5', 'MGNT', 'YDEX', 'OZON'", nargs="+", action="store", default=["LKOH", "TATN", "SBER", "MAGN", "VTBR", "NLMK", "CHMF", "X5", "MGNT", "YDEX", "OZON"] )
        parser.add_argument("-l", "--logfile", help="Logfile path. Default: 'D:\Project_Robot\everything.log'", action="store", default="D:\Project_Robot\everything.log")
        parser.add_argument("-r", "--range", type=int, help="Range of bar at first analis.", action="store", default=100)
        parser.add_argument("-t", "--timeframe", help="Timeframe of instrument grafic. Default: 'M5' (5 minuts).\n" \
            " Posible values:\n" \
            " M5 - 5 minutes,\n" \
            " M10 - 10 minutes,\n" \
            " M15 - 15 minutes,\n" \
            " M30 - 30 minutes,\n" \
            " H1 - 1 hour,\n" \
            " H2 - 2 hours,\n" \
            " H3 - 3 hours,\n" \
            " H4 - 4 hours,\n" \
            " H6 - 6 hours,\n" \
            " H8 - 8 hours,\n" \
            " H12 - 12 hours,\n" \
            " D1 - 1 day,\n" \
            " W 1 weak,\n" \
            " MN = 1 month", action="store", default="M5")
        parser.add_argument("-i", "--indicators", help="List of indicators.", action="store_true") # TODO: Под вопросом. Думаю надо... Пока только думаю.
        parser.add_argument("-a", "--account", help="Account number in Finam.", action="store_true", default=23677)
        parser.add_argument("-p", "--password", help="Account password number in Finam.", action="store_true", default="3C$ap3%H")
        parser.add_argument("-mm", "--monney_manager", help="Percentage of the total balance that will be involved in trading.", action="store", default=100)
        parser.add_argument("-lr", "--lost_risk", help="Percentage of total balance that is allowed to be lost.", action="store", default=100)
        parser.add_argument("-ts", "--trailing_stop", type=int, help="price indent from Stop Loss.", action="store", default=0)
        parser.add_argument("-d", "--logs_directory", help="Logs store directory.", action="store_true", default="D:\Project_Robot")
        parser.add_argument("-m", "--monney_mode", help="Mode of start. Posible values: \n" \
                            "simulation - trade simulation,\n" \
                            "trade - real trade.", action="store", default="simulation")
        args = parser.parse_args()
        print("Выбраны иснтрументы:")
        print(args.symbols)
        print("Выбран таймфрэйм:")
        print(args.timeframe)
        print("Выбран период для предварительного анализа:")
        print(args.range)
        print("Выбран режим работы")
        print(args.monney_mode)
        print("Используется аккаунт")
        print(args.account)
        return args