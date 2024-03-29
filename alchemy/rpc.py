import aiorpc
import asyncio
import uvloop
import factom
import plotly.subplots
import plotly.graph_objects as go
import pandas as pd
from typing import List

import alchemy.csv_exporting
from alchemy.db import AlchemyDB


def register_database_functions(database: AlchemyDB):
    aiorpc.register("sync_head", database.get_sync_head)
    aiorpc.register("winners", database.get_winners)
    aiorpc.register("latest-winners", database.get_highest_winners)
    aiorpc.register("balances", database.get_balances)
    aiorpc.register("rates", database.get_rates)


def _make_call(coro):
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    client = aiorpc.RPCClient("127.0.0.1", 6000)
    return loop.run_until_complete(coro(client))


def get_sync_head():
    async def f(client):
        return await client.call_once("sync_head")

    head = _make_call(f)
    return {"sync_head": head}


def get_winners(height: int = None):
    async def f(client):
        if height is not None:
            return await client.call_once("winners", height, True)
        return await client.call_once("latest-winners", True)

    winning_entry_hashes = _make_call(f)
    winners = (
        [{"place": i + 1, "entry_hash": entry_hash} for i, entry_hash in enumerate(winning_entry_hashes)]
        if len(winning_entry_hashes) != 0
        else None
    )
    return {"winners": winners}


def get_balances(address: str):
    async def f(client):
        return await client.call_once("balances", address)

    factomd = factom.Factomd()
    try:
        fct_balance = factomd.factoid_balance(address).get("balance")
    except factom.exceptions.InvalidParams:
        return {"error": "Invalid Address"}

    balances = _make_call(f)
    if balances is None:
        balances = {}
    balances["FCT"] = fct_balance
    return {"balances": balances}


def get_rates(height: int):
    async def f(client):
        return await client.call_once("rates", height)

    return {"rates": _make_call(f)}


def graph_prices(tickers: List[str], is_by_height: bool = False, show: bool = False):
    df = pd.read_csv(alchemy.csv_exporting.prices_filename)
    fig = plotly.subplots.make_subplots(rows=len(tickers), cols=1, subplot_titles=tickers)
    for i, ticker in enumerate(tickers):
        fig.add_trace(
            go.Scatter(x=df["Height"] if is_by_height else df.Date, y=df[ticker], name=f"{ticker} Prices", opacity=0.8),
            row=i + 1,
            col=1,
        )
    fig.update_xaxes(title_text="Block Height" if is_by_height else "Time")
    fig.update_yaxes(title_text="USD")
    fig.update_layout(title_text=f"Time Series Prices for All Assets", height=600 * len(tickers))
    if show:
        fig.show()
    return fig.to_html()


def graph_difficulties(is_by_height: bool = False, show: bool = False):
    df = pd.read_csv(alchemy.csv_exporting.difficulties_filename)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Height"] if is_by_height else df.Date,
            y=df["Top"],
            name=f"Top Difficulty",
            line_color="deepskyblue",
            opacity=0.8,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["Height"] if is_by_height else df.Date,
            y=df["Bottom"],
            name=f"Bottom Difficulty",
            fill="tonexty",
            line_color="darkviolet",
            opacity=0.8,
        )
    )
    fig.update_xaxes(title_text="Block Height" if is_by_height else "Time")
    fig.update_yaxes(title_text="Difficulty")
    fig.update_layout(title_text=f"Time Series Miner Difficulties", height=750, xaxis_rangeslider_visible=True)
    if show:
        fig.show()
    return fig.to_html()
