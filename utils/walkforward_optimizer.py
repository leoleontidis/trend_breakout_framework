import pandas as pd
import itertools
import backtrader as bt


def compute_pnl(strategy_class, data_dict, params, initial_cash):
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(initial_cash)

    for sym, df in data_dict.items():
        data = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data, name=sym)

    cerebro.addstrategy(strategy_class, **params)

    try:
        results = cerebro.run()
        pnl = cerebro.broker.getvalue() - initial_cash
    except Exception:
        pnl = None

    return pnl


def run_walkforward_optimizer(strategy_class, data_dict, start_date, end_date,
                            param_grid, train_years=2, test_months=6,
                            initial_cash=100000):
    keys, values = zip(*param_grid.items())
    param_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

    results = []
    train_start = pd.to_datetime(start_date)

    while True:
        train_end = train_start + pd.DateOffset(years=train_years)
        test_end = train_end + pd.DateOffset(months=test_months)

        if train_end >= pd.to_datetime(end_date) or test_end >= pd.to_datetime(end_date):
            break

        print(f"\n[WALKFORWARD OPTIMIZER] - Walkforward Window:")
        print(f"[WALKFORWARD OPTIMIZER] - Train: {train_start.date()} to {train_end.date()}")
        print(f"[WALKFORWARD OPTIMIZER] - Test: {train_end.date()} to {test_end.date()}")

        # Prepare train data
        train_data = {
            sym: df[(df.index >= train_start) & (df.index <= train_end)]
            for sym, df in data_dict.items()
        }

        # Find best params on training data
        best_pnl = -float('inf')
        best_params = None

        for params in param_combinations:
            pnl = compute_pnl(strategy_class, train_data, params, initial_cash)

            if pnl is not None and pnl > best_pnl:
                best_pnl = pnl
                best_params = params

        print(f"[WALKFORWARD OPTIMIZER] - Best params for train: {best_params} with PnL {best_pnl}")

        # Prepare test data
        test_data = {
            sym: df[(df.index >= train_end) & (df.index <= test_end)]
            for sym, df in data_dict.items()
        }

        # Apply best params to test window
        test_pnl = compute_pnl(strategy_class, test_data, best_params, initial_cash)
        print(f"[WALKFORWARD OPTIMIZER] - Test PnL: {test_pnl}")

        results.append({
            'train_start': train_start.date(),
            'train_end': train_end.date(),
            'test_start': train_end.date(),
            'test_end': test_end.date(),
            'best_params': best_params,
            'train_pnl': best_pnl,
            'test_pnl': test_pnl
        })

        train_start = train_start + pd.DateOffset(months=test_months)

    return pd.DataFrame(results)