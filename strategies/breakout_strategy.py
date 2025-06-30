import backtrader as bt


class PortfolioBreakoutStrategy(bt.Strategy):
    params = (
        ('breakout_window', 20),
        ('trailing_stop_pct', 0.03),
        ('risk_per_trade', 0.01),
        ('contract_multipliers', {}),
    )

    def __init__(self):
        self.highest = {d._name: bt.indicators.Highest(d.high, period=self.p.breakout_window) for d in self.datas}
        self.lowest = {d._name: bt.indicators.Lowest(d.low, period=self.p.breakout_window) for d in self.datas}

        # Trade state dictionaries per symbol
        self.entry_price = {}
        self.stop_price = {}
        self.trailing_stop = {}
        self.direction = {}

        # Tracking
        self.open_trades = {}
        self.trade_log = {d._name: [] for d in self.datas}


    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f'[STRATEGY] - [{dt}] {txt}')

    def next(self):
        for data in self.datas:
            sym = data._name
            price = data.close[0]

            self.log(f"[{sym}] Close: {price} | High_Break: {self.highest[sym][-1]} | Low_Break: {self.lowest[sym][-1]}")

            pos = self.getposition(data)

            if not pos:
                if price > self.highest[sym][-1]:
                    self.enter_trade(data, sym, price, direction='long')

                elif price < self.lowest[sym][-1]:
                    self.enter_trade(data, sym, price, direction='short')

            else:
                self.manage_trade(data, sym, price)

    def enter_trade(self, data, sym, price, direction):
        if direction == 'long':
            entry = price
            stop = self.lowest[sym][-1]
            risk_per_unit = entry - stop

        else:  # short
            entry = price
            stop = self.highest[sym][-1]
            risk_per_unit = stop - entry

        if risk_per_unit <= 0:
            self.log(f"[{sym}] Invalid risk, skipping trade.")
            return

        # Risk-based sizing
        cash = self.broker.get_cash()
        risk_amount = cash * self.p.risk_per_trade
        multiplier = self.p.contract_multipliers.get(sym, 1)

        size = int(risk_amount / (risk_per_unit * multiplier))

        if size <= 0:
            self.log(f"[{sym}] Size zero, skipping trade.")
            return

        if direction == 'long':
            self.buy(data=data, size=size)
            trailing = entry * (1 - self.p.trailing_stop_pct)

        else:
            self.sell(data=data, size=size)
            trailing = entry * (1 + self.p.trailing_stop_pct)

        self.entry_price[sym] = entry
        self.stop_price[sym] = stop
        self.trailing_stop[sym] = trailing
        self.direction[sym] = direction

        self.open_trades[sym] = {
            'direction': direction,
            'entry_price': entry
        }

        self.log(f"[{sym}] ENTRY {direction.upper()} @ {entry} | Size: {size} | Stop: {stop} | Trailing: {trailing}")

    def manage_trade(self, data, sym, price):
        entry = self.entry_price.get(sym)
        stop = self.stop_price.get(sym)
        trailing = self.trailing_stop.get(sym)
        direction = self.direction.get(sym)

        if entry is None or stop is None or direction is None:
            return

        if direction == 'long':
            if price > entry:
                trailing = max(trailing, price * (1 - self.p.trailing_stop_pct))
                self.trailing_stop[sym] = trailing

            if price <= trailing:
                self.log(f"[{sym}] EXIT LONG on Trailing Stop @ {price}")
                self.close(data=data)
                self.reset_trade(sym)

            elif price <= stop:
                self.log(f"[{sym}] EXIT LONG on Hard Stop @ {price}")
                self.close(data=data)
                self.reset_trade(sym)

        elif direction == 'short':
            if price < entry:
                trailing = min(trailing, price * (1 + self.p.trailing_stop_pct))
                self.trailing_stop[sym] = trailing

            if price >= trailing:
                self.log(f"[{sym}] EXIT SHORT on Trailing Stop @ {price}")
                self.close(data=data)
                self.reset_trade(sym)

            elif price >= stop:
                self.log(f"[{sym}] EXIT SHORT on Hard Stop @ {price}")
                self.close(data=data)
                self.reset_trade(sym)

    def notify_trade(self, trade):
        if trade.isclosed:
            data = trade.data
            sym = data._name

            try:
                dt_entry = bt.num2date(data.datetime[trade.baropen])
            except IndexError:
                dt_entry = bt.num2date(data.datetime[0])

            dt_exit = bt.num2date(data.datetime[0])

            pnl = trade.pnlcomm

            meta = self.open_trades.get(sym, {})
            direction = meta.get('direction', 'unknown')

            self.trade_log[sym].append({
                'symbol': sym,
                'direction': direction,
                'entry_date': dt_entry.date(),
                'exit_date': dt_exit.date(),
                'entry_price': trade.price,
                'exit_price': data.close[0],
                'size': trade.size,
                'pnl': pnl,
                'holding_days': (dt_exit.date() - dt_entry.date()).days
            })

            self.log(f"[{sym}] TRADE CLOSED | {direction.upper()} | Entry: {trade.price} | Exit: {data.close[0]} | PnL: {pnl}")

            self.open_trades.pop(sym, None)

    def reset_trade(self, sym):
        self.entry_price.pop(sym, None)
        self.stop_price.pop(sym, None)
        self.trailing_stop.pop(sym, None)
        self.direction.pop(sym, None)