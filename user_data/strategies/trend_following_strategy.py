import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from functools import reduce

from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter
import freqtrade.vendor.qtpylib.indicators as qtpylib
import talib.abstract as ta
import technical.indicators as ftt


class TrendFollowingStrategy(IStrategy):
    INTERFACE_VERSION = 2

    minimal_roi = {
        "0": 10
    }

    stoploss = -10
    trailing_stop = False

    process_only_new_candles = False

    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False


    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }

    # Buy hyperspace params:
    buy_params = {
        "buy_fast_EMA_space": 9,
        "buy_slow_EMA_space": 21,
        "buy_tenkan_sen_space": 4,
        "buy_kijun_sen_space": 12,
        "buy_adx_space": 10
    }

    startup_candle_count: int = buy_params["buy_slow_EMA_space"] + 1


    plot_config = {
        'main_plot': {
            # f'FastEMA_{buy_params["buy_fast_EMA_space"]}': {'color': 'blue'},
            # f'SlowEMA_{buy_params["buy_slow_EMA_space"]}': {'color': 'orange'},
            f'tenkan_sen_{buy_params["buy_tenkan_sen_space"]}': {'color': 'blue'},
            f'kijun_sen_{buy_params["buy_kijun_sen_space"]}': {'color': 'orange'}

        },
        'subplots': {
            "ADX": {
                f'ADX_{buy_params["buy_adx_space"]}': {'color': 'red'}
            }
        }
    }

    # Define optimization space
    # buy_fast_EMA_space = IntParameter(9, 10, default=9)
    # buy_slow_EMA_space = IntParameter(20, 21, default=21)
    buy_adx_space = IntParameter(7, 60, default=10)

    buy_tenkan_sen_space = IntParameter(3, 30, default=9)
    buy_kijun_sen_space = IntParameter(9, 60, default=9)


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        for val in self.buy_tenkan_sen_space.range:
            ichimoku = ftt.ichimoku(dataframe, conversion_line_period=val, base_line_periods=26, laggin_span=52, displacement=26)
            dataframe[f"tenkan_sen_{val}"] = ichimoku["tenkan_sen"]
        for val in self.buy_kijun_sen_space.range:
            ichimoku = ftt.ichimoku(dataframe, conversion_line_period=9, base_line_periods=val, laggin_span=52, displacement=26)
            dataframe[f"kijun_sen_{val}"] = ichimoku["kijun_sen"]

        # for val in self.buy_fast_EMA_space.range:
        #     dataframe[f"FastEMA_{val}"] = ta.EMA(dataframe, timeperiod=val)
        # for val in self.buy_slow_EMA_space.range:
        #     dataframe[f"SlowEMA_{val}"] = ta.EMA(dataframe, timeperiod=val)
        for val in self.buy_adx_space.range:
            dataframe[f"ADX_{val}"] = ta.ADX(dataframe, timeperiod=val)

        # Average Directional Index
        # adx = ta.ADX(dataframe)
        # dataframe["adx"] = adx

        # FastEMA and SlowEMA
        # dataframe["FastEMA"] = ta.EMA(dataframe, timeperiod=10)
        # dataframe["SlowEMA"] = ta.EMA(dataframe, timeperiod=30)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []
        # conditions.append(dataframe[f"FastEMA_{self.buy_fast_EMA_space.value}"] > dataframe[f"SlowEMA_{self.buy_slow_EMA_space.value}"])
        conditions.append(dataframe[f"tenkan_sen_{self.buy_tenkan_sen_space.value}"] > dataframe[f"kijun_sen_{self.buy_kijun_sen_space.value}"])
        conditions.append(dataframe[f"ADX_{self.buy_adx_space.value}"] > 20)
        conditions.append(dataframe["volume"] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                "buy"
            ] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []
        # conditions.append(dataframe[f"FastEMA_{self.buy_fast_EMA_space.value}"] < dataframe[f"SlowEMA_{self.buy_slow_EMA_space.value}"])
        conditions.append(dataframe[f"tenkan_sen_{self.buy_tenkan_sen_space.value}"] < dataframe[f"kijun_sen_{self.buy_kijun_sen_space.value}"])
        conditions.append(dataframe["volume"] > 0)
        # conditions.append(dataframe["close"] > dataframe[f"FastEMA_{self.buy_fast_EMA_space.value}"])

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                "sell"
            ] = 1

        return dataframe
