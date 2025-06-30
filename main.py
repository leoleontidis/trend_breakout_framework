import backtrader as bt
import pandas as pd
import json
import os
from utils.data_loader import load_price_data
from strategies.breakout_strategy import PortfolioBreakoutStrategy
from utils.walkforward import run_walkforward
from utils.performance import performance_summary, plot_equity_curve
from utils.broker_models import FuturesCommission
from utils.grid_optimizer import run_grid_search, add_composite_score, plot_heatmap
from utils.walkforward_optimizer import run_walkforward_optimizer

def run_backtest():
    with open('config/contracts.json') as f:
        contracts = json.load(f)

    with open('config/config.json') as f:
        config = json.load(f)

    os.makedirs('reports', exist_ok=True)

    cerebro = bt.Cerebro()

    cerebro.broker.set_cash(config['initial_cash'])
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio")

    contract_multipliers = {}
    data_dict = {}

    # Load all symbols
    for symbol_info in config['symbols']:
        short_name = symbol_info['symbol']
        yf_symbol = contracts[short_name]

        print(f"\n[MAIN] - === Loading {yf_symbol} ===")

        df = load_price_data(yf_symbol, interval=config['timeframe'])
        data = bt.feeds.PandasData(dataname=df)

        cerebro.adddata(data, name=yf_symbol)

        contract_multipliers[short_name] = symbol_info['contract_multiplier']

        comminfo = FuturesCommission(
            commission=2.5,
            mult=contract_multipliers[short_name],
            margin=6000
            )
        cerebro.broker.addcommissioninfo(comminfo, name=short_name)


        data_dict[short_name] = df

    cerebro.broker.set_slippage_perc(perc=0.001)
    cerebro.addstrategy(
        PortfolioBreakoutStrategy,
        breakout_window=config['strategy']['breakout_window'],
        trailing_stop_pct=config['strategy']['trailing_stop_pct'],
        risk_per_trade=config['strategy']['risk_per_trade'],
        contract_multipliers=contract_multipliers
    )

    print('[MAIN] - Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    results = cerebro.run()
    print('[MAIN] - Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Export trade logs
    for strat in results:
        for symbol, trades in strat.trade_log.items():
            trade_log = pd.DataFrame(trades)
            if not trade_log.empty:
                filename = f'reports/trade_log_{symbol}.csv'
                trade_log.to_csv(filename, index=False)
                print(f"[MAIN] - Saved trade log for {symbol} to {filename}")
            else:
                print(f"[MAIN] - No trades executed for {symbol}")

        # Performance Summary
        print("\n[MAIN] - ===== PERFORMANCE SUMMARY =====")
        performance_summary(strat.trade_log)
        plot_equity_curve(strat.trade_log)

    cerebro.plot()

    # Walkforward Testing
    print("\n[MAIN] - === Running Walkforward Testing ===")

    walk_results = run_walkforward(
        strategy_class=PortfolioBreakoutStrategy,
        data_dict=data_dict,
        start_date=config['start_date'],
        end_date=config['end_date'],
        train_years=2,
        test_months=6,
        initial_cash=config['initial_cash'],
        breakout_window=config['strategy']['breakout_window'],
        trailing_stop_pct=config['strategy']['trailing_stop_pct'],
        risk_per_trade=config['strategy']['risk_per_trade'],
        contract_multipliers=contract_multipliers
    )

    print("\n[MAIN] - ===== WALKFORWARD RESULTS =====")
    print(walk_results)

    walk_results.to_csv('reports/walkforward_results.csv', index=False)
    print("[MAIN] - Walkforward results saved to reports/walkforward_results.csv")

    # Walk Forward Optimizer
    param_grid = {
        'breakout_window': [10, 20, 30],
        'trailing_stop_pct': [0.02, 0.03],
        'risk_per_trade': [0.005, 0.01],
        'contract_multipliers': [contract_multipliers]
    }

    wf_optimization_results = run_walkforward_optimizer(
        strategy_class=PortfolioBreakoutStrategy,
        data_dict=data_dict,
        start_date=config['start_date'],
        end_date=config['end_date'],
        param_grid=param_grid,
        train_years=2,
        test_months=6,
        initial_cash=config['initial_cash']
    )

    print("\n===== WALKFORWARD OPTIMIZER RESULTS =====")
    print(wf_optimization_results)

    wf_optimization_results.to_csv('reports/walkforward_optimizer_results.csv', index=False)

    param_grid = {
        'breakout_window': [10, 20, 30],
        'trailing_stop_pct': [0.02, 0.03, 0.05],
        'risk_per_trade': [0.005, 0.01],
        'contract_multipliers': [contract_multipliers]
    }

    grid_results = run_grid_search(
        strategy_class=PortfolioBreakoutStrategy,
        data_dict=data_dict,
        param_grid=param_grid,
        initial_cash=config['initial_cash']
    )

    weights = {
        'PnL': 1.0,
        'Sharpe': 1.5,
        'Win_Rate': 1.0,
        'Profit_Factor': 1.0,
        'Max_Drawdown': -2.0
    }

    scored_results = add_composite_score(grid_results, weights=weights)

    print(scored_results)

    scored_results.to_csv('reports/grid_search_with_scores.csv', index=False)

    plot_heatmap(scored_results, x='breakout_window', y='trailing_stop_pct', metric='PnL')
    plot_heatmap(scored_results, x='breakout_window', y='trailing_stop_pct', metric='Sharpe')
    plot_heatmap(scored_results, x='breakout_window', y='trailing_stop_pct', metric='Composite_Score')

if __name__ == '__main__':
    run_backtest()