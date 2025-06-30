import pandas as pd
import backtrader as bt
from datetime import timedelta

def run_walkforward(strategy_class, data_dict, start_date, end_date, 
                    train_years=2, test_months=6, 
                    initial_cash=100000, **strategy_params):
    
    results = []
    train_start = pd.to_datetime(start_date)

    while True:
        train_end = train_start + pd.DateOffset(years=train_years)
        test_end = train_end + pd.DateOffset(months=test_months)

        if train_end >= pd.to_datetime(end_date) or test_end >= pd.to_datetime(end_date):
            break

        print(f"\n[WALKFORWARD] - Walkforward window:")
        print(f"[WALKFORWARD] - Training: {train_start.date()} to {train_end.date()}")
        print(f"[WALKFORWARD] - Testing: {train_end.date()} to {test_end.date()}")

        cerebro = bt.Cerebro()
        cerebro.broker.set_cash(initial_cash)

        for sym, df in data_dict.items():
            test_data = df[(df.index >= train_end) & (df.index <= test_end)]
            if test_data.empty:
                print(f"[WALKFORWARD] - No test data for {sym} in this window.")
                continue

            feed = bt.feeds.PandasData(dataname=test_data)
            cerebro.adddata(feed, name=sym)

        cerebro.addstrategy(strategy_class, **strategy_params)

        if not cerebro.datas:
            print("[WALKFORWARD] -  No data feeds for this test window. Skipping.")
            train_start = train_start + pd.DateOffset(months=test_months)
            continue

        cerebro.run()

        pnl = cerebro.broker.getvalue() - initial_cash
        print(f"[WALKFORWARD] - PNL for test period: {pnl:.2f}")

        results.append({
            'train_start': train_start.date(),
            'train_end': train_end.date(),
            'test_start': train_end.date(),
            'test_end': test_end.date(),
            'pnl': pnl
        })
        train_start = train_start + pd.DateOffset(months=test_months)

    return pd.DataFrame(results)