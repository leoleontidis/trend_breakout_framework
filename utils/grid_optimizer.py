import itertools
import pandas as pd
import backtrader as bt
from joblib import Parallel, delayed
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def compute_metrics(strategy_class, data_dict, params, initial_cash):
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(initial_cash)

    for sym, df in data_dict.items():
        data = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data, name=sym)

    cerebro.addstrategy(strategy_class, **params)

    try:
        results = cerebro.run()
        strat = results[0]

        pnl_df = pd.concat([pd.DataFrame(v) for v in strat.trade_log.values()], ignore_index=True)
        pnl_df = pnl_df.sort_values(by='exit_date')

        pnl_series = pnl_df['pnl']

        cumulative = pnl_series.cumsum()
        rolling_max = cumulative.cummax()
        drawdown = rolling_max - cumulative

        max_drawdown = drawdown.max() if not drawdown.empty else 0
        sharpe = (pnl_series.mean() / pnl_series.std()) * (252 ** 0.5) if pnl_series.std() != 0 else 0

        win_rate = (pnl_series > 0).mean() * 100 if not pnl_series.empty else 0

        gross_profit = pnl_series[pnl_series > 0].sum()
        gross_loss = -pnl_series[pnl_series < 0].sum()
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.inf

        pnl = cerebro.broker.getvalue() - initial_cash

    except Exception as e:
        print(f"[GRID OPTIMIZER] - Error for {params}: {e}")
        pnl = None
        sharpe = None
        max_drawdown = None
        win_rate = None
        profit_factor = None

    return {**params, 'PnL': pnl, 'Sharpe': sharpe, 'Max_Drawdown': max_drawdown,
            'Win_Rate': win_rate, 'Profit_Factor': profit_factor}


def run_grid_search(strategy_class, data_dict, param_grid, initial_cash=100000, n_jobs=-1):
    keys, values = zip(*param_grid.items())
    param_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

    results = Parallel(n_jobs=n_jobs)(
        delayed(compute_metrics)(strategy_class, data_dict, params, initial_cash)
        for params in param_combinations
    )

    results_df = pd.DataFrame(results).sort_values(by='PnL', ascending=False)

    return results_df


def add_composite_score(results_df, weights=None):
    """
    Add composite scoring based on customizable weights.

    :param results_df: DataFrame with metrics.
    :param weights: Dictionary of weights.
    Example:
        {
            'PnL': 1.0,
            'Sharpe': 1.5,
            'Win_Rate': 1.0,
            'Profit_Factor': 1.0,
            'Max_Drawdown': -2.0
        }
    """

    if weights is None:
        weights = {'PnL': 1.0, 'Sharpe': 1.0, 'Win_Rate': 1.0, 'Profit_Factor': 1.0, 'Max_Drawdown': -1.0}

    score = (
        (results_df['PnL'].fillna(0) * weights.get('PnL', 0)) +
        (results_df['Sharpe'].fillna(0) * weights.get('Sharpe', 0)) +
        (results_df['Win_Rate'].fillna(0) * weights.get('Win_Rate', 0) / 100) +
        (results_df['Profit_Factor'].fillna(0) * weights.get('Profit_Factor', 0)) +
        (results_df['Max_Drawdown'].fillna(0) * weights.get('Max_Drawdown', 0))
    )

    results_df['Composite_Score'] = score
    results_df = results_df.sort_values(by='Composite_Score', ascending=False)

    return results_df

def plot_heatmap(results_df, x, y, metric='PnL', subgroup='risk_per_trade'):
    """
    Creates a heatmap for each unique value in `subgroup`.

    :param results_df: The grid search result DataFrame.
    :param x: The column to use for heatmap x-axis (e.g., 'breakout_window').
    :param y: The column to use for heatmap y-axis (e.g., 'trailing_stop_pct').
    :param metric: The metric to display ('PnL', 'Sharpe', etc.).
    :param subgroup: The column to split into multiple heatmaps (e.g., 'risk_per_trade').
    """
    unique_subgroups = results_df[subgroup].unique()

    for subgroup_value in sorted(unique_subgroups):
        subset = results_df[results_df[subgroup] == subgroup_value]
        pivot = subset.pivot_table(index=y, columns=x, values=metric, aggfunc='mean')

        plt.figure(figsize=(8, 6))
        sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu")
        plt.title(f'{metric} Heatmap ({subgroup}={subgroup_value})')
        plt.xlabel(x)
        plt.ylabel(y)
        plt.tight_layout()
        plt.show()

