import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from functools import reduce

from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter
import freqtrade.vendor.qtpylib.indicators as qtpylib
import talib.abstract as ta


class RangeFollowingStrategy(IStrategy):
    INTERFACE_VERSION = 2

    minimal_roi = {
        "0": 10
    }

    stoploss = -0.10

    trailing_stop = False

    process_only_new_candles = False

    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    startup_candle_count: int = 32

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

    plot_config = {
        'main_plot': {
            'bb_lowerband': {'color': 'yellow'},
            'bb_upperband': {'color': 'yellow'}
        },
        'subplots': {
            "ADX": {
                'adx': {'color': 'red'}
            }
        }
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']

        # Average Directional Index
        dataframe["adx"] = ta.ADX(dataframe)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []

        conditions.append(dataframe["adx"] < 20)
        conditions.append(dataframe["close"] <= dataframe["bb_lowerband"])
        conditions.append(dataframe["volume"] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                "buy"
            ] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []

        conditions.append(dataframe["close"] >= dataframe["bb_upperband"])
        conditions.append(dataframe["volume"] > 0)

        dataframe.loc[
            (
                (dataframe["close"] >= dataframe["bb_upperband"]) &
                (dataframe['volume'] > 0)
            ),
            'sell'] = 1

        # if conditions:
        #     dataframe.loc[
        #         reduce(lambda x, y: x & y, conditions),
        #         "sell"
        #     ] = 1

        return dataframe
