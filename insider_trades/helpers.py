import datetime
import os
from typing import List

from insider_trades.handlers.lemon import LemonMarketsAPI
from insider_trades.transactions import Transactions


class Helpers:
    def __init__(self, lemon_api: LemonMarketsAPI):
        self._lemon_api = lemon_api

    def get_isins(self, transactions: Transactions):
        isins = []

        for ticker in transactions.get_gm_tickers():
            try:
                instrument = self._lemon_api.get_instrument(ticker)
            except Exception as e:
                print(e)
                raise
            else:
                if instrument.get("total") > 0:
                    isins.append(instrument.get("results")[0].get("isin"))
                else:
                    isins.append("NA")
        transactions.set_isins(isins)

    def place_trades(self, buy: List[str], sell: List[str]):
        orders = []

        space_id = os.environ.get("SPACE_ID")
        expires_at = "p0d"

        # place buy orders
        for isin in buy:
            side = "buy"
            quantity = 1
            order = self._lemon_api.place_order(
                isin, expires_at, quantity, side, space_id
            )
            orders.append(order)
            print(f"You are {side}ing {quantity} share(s) of instrument {isin}.")

        portfolio = self._lemon_api.get_portfolio(space_id)

        # place sell orders
        for isin in sell:
            if isin in portfolio:
                side = "sell"
                quantity = 1
                order = self._lemon_api.place_order(
                    isin, expires_at, quantity, side, space_id
                )
                orders.append(order)
                print(f"You are {side}ing {quantity} share(s) of instrument {isin}.")
            else:
                print(
                    f"You do not have sufficient holdings of instrument {isin} to place a sell order."
                )

        return orders

    def activate_order(self, orders):
        for order in orders:
            self._lemon_api.activate_order(order["results"].get("id"))
            print(f'Activated {order["results"].get("isin")}')
        return orders

    def is_venue_open(self):
        return self._lemon_api.get_venue()["is_open"]

    def seconds_until_open(self):
        venue = self._lemon_api.get_venue()
        today = datetime.datetime.today()
        next_opening_time = datetime.datetime.strptime(venue["opening_hours"]["start"], "%H:%M")
        next_opening_day = datetime.datetime.strptime(venue["opening_days"][0], "%Y-%m-%d")

        date_difference = next_opening_day - today
        days = date_difference.days + 1
        if not self.is_venue_open():
            print("Trading venue is not open")
            time_delta = datetime.datetime.combine(
                datetime.datetime.now().date() + datetime.timedelta(days=1), next_opening_time.time()
            ) - datetime.datetime.now()
            print(time_delta.seconds + (days * 86400))
            return time_delta.seconds
        else:
            print("Trading venue is open")
            return 0


