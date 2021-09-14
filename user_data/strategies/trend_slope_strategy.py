import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from functools import reduce

from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter
import freqtrade.vendor.qtpylib.indicators as qtpylib
import talib.abstract as ta


class TrendSlopeStrategy(IStrategy):
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
        "buy_fast_slope_EMA_space": 9,
        "buy_slow_slope_EMA_space": 21,
        "buy_source_EMA_space": 130,
        "buy_trend_filter_EMA_space": 200,
        "buy_adx_space": 10
    }

    startup_candle_count: int = buy_params["buy_trend_filter_EMA_space"] + 1

    plot_config = {
        'main_plot': {
            f'SourceEMA_{buy_params["buy_source_EMA_space"]}': {'color': 'blue'},
            f'TrendFilterEMA_{buy_params["buy_trend_filter_EMA_space"]}': {'color': 'orange'},
        },
        'subplots': {
            "EMA_slope": {
                f'Slope': {'color': 'red'},
                f'FastSlopeEMA_{buy_params["buy_fast_slope_EMA_space"]}': {'color': 'blue'},
                f'SlowSlopeEMA_{buy_params["buy_slow_slope_EMA_space"]}': {'color': 'orange'},
            }
        }
    }

    # Define optimization space
    buy_fast_slope_EMA_space = IntParameter(5, 100, default=10)
    buy_slow_slope_EMA_space = IntParameter(15, 200, default=30)
    buy_source_EMA_space = IntParameter(30, 200, default=30)
    buy_trend_filter_EMA_space = IntParameter(30, 200, default=30)

    # buy_adx_space = IntParameter(10, 30, default=10)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        for val in self.buy_source_EMA_space.range:
            dataframe[f"SourceEMA_{val}"] = ta.EMA(dataframe["close"], timeperiod=val)
            dataframe["Slope"] = dataframe[f"SourceEMA_{val}"].diff() / dataframe[f"SourceEMA_{val}"]
        for val in self.buy_trend_filter_EMA_space.range:
            dataframe[f"TrendFilterEMA_{val}"] = ta.EMA(dataframe["close"], timeperiod=val)
        for val in self.buy_fast_slope_EMA_space.range:
            dataframe[f"FastSlopeEMA_{val}"] = ta.EMA(dataframe["Slope"], timeperiod=val)
        for val in self.buy_slow_slope_EMA_space.range:
            dataframe[f"SlowSlopeEMA_{val}"] = ta.EMA(dataframe["Slope"], timeperiod=val)



        # ADX hyperopt
        # for val in self.buy_adx_space.range:
        #     dataframe[f"ADX_{val}"] = ta.ADX(dataframe, timeperiod=val)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []
        conditions.append(dataframe[f"FastSlopeEMA_{self.buy_fast_slope_EMA_space.value}"] > dataframe[f"SlowSlopeEMA_{self.buy_slow_slope_EMA_space.value}"])
        conditions.append(dataframe["close"] > dataframe[f"TrendFilterEMA_{self.buy_trend_filter_EMA_space.value}"])
        # conditions.append(dataframe[f"ADX_{self.buy_adx_space.value}"] > 20)
        conditions.append(dataframe["volume"] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                "buy"
            ] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []
        conditions.append(dataframe[f"FastSlopeEMA_{self.buy_fast_slope_EMA_space.value}"] < dataframe[f"SlowSlopeEMA_{self.buy_slow_slope_EMA_space.value}"])
        conditions.append(dataframe["close"] < dataframe[f"TrendFilterEMA_{self.buy_trend_filter_EMA_space.value}"])
        conditions.append(dataframe["volume"] > 0)
        # conditions.append(dataframe["close"] > dataframe[f"FastEMA_{self.buy_fast_EMA_space.value}"])

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                "sell"
            ] = 1

        return dataframe
