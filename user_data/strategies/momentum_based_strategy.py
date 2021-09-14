# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame

from freqtrade.strategy.interface import IStrategy

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


# This class is a sample. Feel free to customize it.
class MomentumBasedStrategy(IStrategy):
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "0": 10
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -100

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Optimal ticker interval for the strategy.
    # timeframe = '15m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 200

    # Optional order type mapping.
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }

    plot_config = {
        'main_plot': {
            'FastSMA': {'color': 'blue'},
            'SlowSMA': {'color': 'orange'},
        },
        'subplots': {
            "StochSlow": {
                'StochSlowK': {'color': 'blue'},
                'StochSlowD': {'color': 'orange'}
            },
            "NATR": {
                'NATR': {'color': 'blue'}
            }
        }
    }

    def informative_pairs(self):
        return []

    # def calculate_tii(self, dataframe: DataFrame, n_period_sma) -> DataFrame:
    #     df = DataFrame(dataframe["close"], columns=["close"])
    #
    #     df["sma"] = ta.SMA(df, timeperiod=n_period_sma)
    #
    #     df["pos_dev"] = df.loc[df["close"] > df["sma"], "close"] - df["sma"]
    #     df["pos_dev"] = df["pos_dev"].fillna(0)
    #
    #     df["neg_dev"] = abs(df.loc[df["close"] < df["sma"], "close"] - df["sma"])
    #     df["neg_dev"] = df["neg_dev"].fillna(0)
    #
    #     m = int(n_period_sma / 2 if (n_period_sma % 2 == 0) else int((n_period_sma + 1) / 2))
    #
    #     df["total_up"] = df["pos_dev"].rolling(min_periods=m, window=m).sum()
    #     df["total_down"] = df["neg_dev"].rolling(min_periods=m, window=m).sum()
    #
    #     df["TII"] = 100 * df["total_up"] / (df["total_up"] + df["total_down"])
    #
    #     return df.loc[:, ["TII", "sma"]]

    def calculate_tii(self, df: DataFrame, n_period_sma) -> DataFrame:
        df = DataFrame(df["close"], columns=["close"])

        df["sma"] = ta.SMA(df, timeperiod=n_period_sma)

        df["pos_dev"] = df.loc[df["close"] > df["sma"], "close"] - df["sma"]
        df["pos_dev"] = df["pos_dev"].fillna(0)

        df["neg_dev"] = abs(df.loc[df["close"] < df["sma"], "close"] - df["sma"])
        df["neg_dev"] = df["neg_dev"].fillna(0)

        m = int(n_period_sma / 2 if (n_period_sma % 2 == 0) else int((n_period_sma + 1) / 2))

        df["sd_pos"] = df.apply(lambda x: 1 if x["pos_dev"] > 0 else 0, axis=1)
        df["sd_neg"] = df.apply(lambda x: 1 if x["neg_dev"] > 0 else 0, axis=1)

        df["total_up"] = df["sd_pos"].rolling(min_periods=m, window=m).sum()
        df["total_down"] = df["sd_neg"].rolling(min_periods=m, window=m).sum()

        df["TII"] = 100 * df["total_up"] / (df["total_up"] + df["total_down"])

        return df.loc[:, ["TII", "sma"]]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # FastSMA and SlowSMA
        dataframe["FastSMA"] = ta.SMA(dataframe, timeperiod=80)
        dataframe["SlowSMA"] = ta.SMA(dataframe, timeperiod=120)

        # Trend Intnsity Index
        # tii = self.calculate_tii(dataframe, 60)
        # dataframe["TII"] = tii["TII"]
        # dataframe["TiiSma"] = tii["sma"]

        # Stochastic Slow
        dataframe["StochSlowK"], dataframe["StochSlowD"] = ta.STOCH(dataframe["high"], dataframe["low"],
                                                                    dataframe["close"], fastk_period=5, slowk_period=3,
                                                                    slowk_matype=0, slowd_period=3,
                                                                    slowd_matype=0)

        # Stochastic Fast
        dataframe["StochFastK"], dataframe["StochFastD"] = ta.STOCHF(dataframe["high"], dataframe["low"],
                                                                     dataframe["close"], fastk_period=5, fastd_period=3,
                                                                     fastd_matype=0)

        # Stochastic RSI
        dataframe["StochRSIK"], dataframe["StochRSID"] = ta.STOCHRSI(dataframe["close"], timeperiod=14, fastk_period=5,
                                                                     fastd_period=3, fastd_matype=0)

        # Average True Index
        dataframe["ATR"] = ta.ATR(dataframe["high"], dataframe["low"],
                                  dataframe["close"], timeperiod=14)
        dataframe["NATR"] = ta.NATR(dataframe["high"], dataframe["low"],
                                    dataframe["close"], timeperiod=14)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe["StochSlowK"] > dataframe["StochSlowD"]) &
                    (dataframe["StochSlowK"] < 20) &
                    (dataframe["StochSlowD"] < 20) &
                    (dataframe["NATR"] > 0.50) &
                    (dataframe['volume'] > 0)
            ),

            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe["StochSlowK"] < dataframe["StochSlowD"]) &
                    (dataframe["StochSlowK"] > 80) &
                    (dataframe["StochSlowD"] > 80) &
                    (dataframe['volume'] > 0)
            ),

            'sell'] = 1

        return dataframe
