import bottle
import json
from factom_keys.ec import ECAddress
from factom_keys.fct import FactoidAddress, FactoidPrivateKey

import alchemy.consts as consts
import alchemy.rpc as rpc
import alchemy.transactions.models as tx_models


# -------------------------------------
# Web app endpoints


@bottle.get("/v1/graph-assets")
def graph_assets():
    is_by_height = bottle.request.query.get("by-height", "false").lower() == "true"
    tickers = bottle.request.query.get("tickers", "").split(",")
    if len(tickers) == 0:
        tickers = sorted(consts.ALL_ASSETS)
    elif not set(tickers).issubset(consts.ALL_ASSETS):
        bottle.abort(400)
    return rpc.graph_prices(tickers, is_by_height)


@bottle.get("/v1/graph-difficulties")
def graph_difficulties():
    is_by_height = bottle.request.query.get("by-height", "false").lower() == "true"
    return rpc.graph_difficulties(is_by_height)


# -------------------------------------
# API handlers


@bottle.get("/v1/balances/<address>")
def get_balances(address):
    if not FactoidAddress.is_valid(address):
        bottle.abort(404)
    return rpc.get_balances(address)


@bottle.get("/v1/rates/<height:int>")
def get_rates(height: int):
    if height < 0:
        bottle.abort(404)
    return rpc.get_rates(height)


@bottle.get("/v1/sync_head/")
def get_sync_head():
    return rpc.get_sync_head()


@bottle.get("/v1/winners/<height:int>")
def get_winners(height: int):
    if height < 0:
        bottle.abort(404)
    return rpc.get_winners(height)


@bottle.get("/v1/winners/latest")
def get_latest_winners():
    return rpc.get_winners()


@bottle.post("/v1/transactions")
def send_transaction():
    request_json = bottle.request.json
    transactions = request_json.get("transactions")
    ec_address = request_json.get("ec_address")
    if type(transactions) != list or len(transactions) == 0:
        bottle.abort(400)
    if type(ec_address) != str or not ECAddress.is_valid():
        bottle.abort(400)

    import factom.exceptions
    from factom import Factomd, FactomWalletd

    factomd = Factomd()
    walletd = FactomWalletd()

    tx_entry = tx_models.TransactionEntry()
    for tx_dict in transactions:
        # Make sure it's a valid transaction
        tx = tx_models.Transaction.from_dict(tx_dict)
        if not tx.is_valid():
            bottle.abort(400)

        # Make sure the input addresses is valid and in the wallet
        input_address = tx.input["address"]
        try:
            input_secret = walletd.address(input_address)["secret"]
        except factom.exceptions.InternalError:
            bottle.abort(400)
            return
        signer = FactoidPrivateKey(key_string=input_secret)

        # All good
        tx_entry.add_transaction(tx)
        tx_entry.add_signer(signer)

    external_ids, content = tx_entry.sign()
    entry_reveal_response = walletd.new_entry(
        factomd=factomd,
        chain_id=consts.TRANSACTIONS_CHAIN_ID,
        ext_ids=external_ids,
        content=content,
        ec_address=ec_address,
    )
    return entry_reveal_response


# -------------------------------------
# Hooks, health checks, and error handlers


@bottle.hook("before_request")
def strip_path():
    """Strip trailing '/' on all requests. '/foo' and /foo/' are two unique endpoints in bottle"""
    bottle.request.environ["PATH_INFO"] = bottle.request.environ["PATH_INFO"].rstrip("/")


@bottle.get("/health")
def health_check():
    return {"data": "Healthy!"}


@bottle.error(400)
def error400(e):
    body = {"errors": {"detail": "Bad request"}}
    return json.dumps(body, separators=(",", ":"))


@bottle.error(404)
def error404(e):
    body = {"errors": {"detail": "Page not found"}}
    return json.dumps(body, separators=(",", ":"))


@bottle.error(405)
def error405(e):
    body = {"errors": {"detail": "Method not allowed"}}
    return json.dumps(body, separators=(",", ":"))


@bottle.error(500)
def error500(e):
    body = {"errors": {"detail": "Internal server error"}}
    return json.dumps(body, separators=(",", ":"))


# Entry point ONLY when run locally. The docker setup uses gunicorn and this block will not be executed.
if __name__ == "__main__":
    bottle.run(host="localhost", port=8000)

app = bottle.default_app()
