import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def performance_summary(trade_logs):
    if isinstance(trade_logs, dict):
        logs = pd.concat([pd.DataFrame(v) for v in trade_logs.values()], ignore_index=True)
    else:
        logs = pd.DataFrame(trade_logs)

    if logs.empty:
        print("[PERFORMANCE] - No trades executed.")
        return None

    logs['entry_date'] = pd.to_datetime(logs['entry_date'])
    logs['exit_date'] = pd.to_datetime(logs['exit_date'])
    logs['holding_period'] = (logs['exit_date'] - logs['entry_date']).dt.days

    total_pnl = logs['pnl'].sum()
    win_rate = (logs['pnl'] > 0).mean() * 100
    total_trades = len(logs)
    avg_pnl = logs['pnl'].mean()

    gross_profit = logs.loc[logs['pnl'] > 0, 'pnl'].sum()
    gross_loss = -logs.loc[logs['pnl'] < 0, 'pnl'].sum()

    profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.inf

    pnl_series = logs['pnl'].cumsum()
    rolling_max = pnl_series.cummax()
    drawdown = rolling_max - pnl_series
    max_drawdown = drawdown.max()

    sharpe = (avg_pnl / logs['pnl'].std()) * np.sqrt(252) if logs['pnl'].std() != 0 else np.nan
    avg_holding = logs['holding_period'].mean()

    summary = {
        'Total PnL': total_pnl,
        'Win Rate (%)': win_rate,
        'Total Trades': total_trades,
        'Average PnL': avg_pnl,
        'Profit Factor': profit_factor,
        'Sharpe Ratio': sharpe,
        'Max Drawdown': max_drawdown,
        'Average Holding (days)': avg_holding
    }

    print("\n[PERFORMANCE] - ===== Portfolio Performance Summary =====")
    for k, v in summary.items():
        print(f"[PERFORMANCE] - {k}: {v}")

    return summary


def plot_equity_curve(trade_logs):
    if isinstance(trade_logs, dict):
        logs = pd.concat([pd.DataFrame(v) for v in trade_logs.values()], ignore_index=True)
    else:
        logs = pd.DataFrame(trade_logs)

    logs = logs.sort_values(by='exit_date')
    logs['cumulative_pnl'] = logs['pnl'].cumsum()

    plt.figure(figsize=(14, 6))
    plt.plot(logs['exit_date'], logs['cumulative_pnl'], marker='o')
    plt.title('Equity Curve')
    plt.xlabel('Date')
    plt.ylabel('Cumulative PnL')
    plt.grid(True)
    plt.show()
