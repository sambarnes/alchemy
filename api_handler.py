import bottle
import json
from dataclasses import dataclass
from factom_keys.ec import ECAddress
from factom_keys.fct import FactoidAddress, FactoidPrivateKey
from typing import Any, Dict, Union

import alchemy.consts as consts
import alchemy.rpc as rpc
import alchemy.transactions.models as tx_models


@bottle.hook("before_request")
def strip_path():
    """Strip trailing '/' on all requests. '/foo' and /foo/' are two unique endpoints in bottle"""
    bottle.request.environ["PATH_INFO"] = bottle.request.environ["PATH_INFO"].rstrip("/")


@bottle.get("/health")
def health_check():
    return {"data": "Healthy!"}


# -------------------------------------
# Web app endpoints


@bottle.get("/graphs/assets")
def graph_assets():
    is_by_height = bottle.request.query.get("by-height", "false").lower() == "true"
    tickers = bottle.request.query.get("tickers", "").split(",")
    if len(tickers) == 1 and tickers[0] == "":
        tickers = sorted(consts.ALL_ASSETS)
    elif not set(tickers).issubset(consts.ALL_ASSETS):
        print(tickers)
        bottle.abort(400)
    return rpc.graph_prices(tickers, is_by_height)


@bottle.get("/graphs/miners")
def graph_difficulties():
    is_by_height = bottle.request.query.get("by-height", "false").lower() == "true"
    return rpc.graph_difficulties(is_by_height)


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


# -------------------------------------
# API handlers


@dataclass
class JSONRPCError(Exception):
    code: int
    message: str
    http_status_code: int

    def to_dict(self):
        return {"code": self.code, "message": self.message}


class ParseError(JSONRPCError):
    def __init__(self):
        self.code = -32700
        self.message = "Parse error"
        self.http_status_code = 500


class InvalidRequestError(JSONRPCError):
    def __init__(self):
        self.code = -32600
        self.message = "Invalid Request"
        self.http_status_code = 400


class MethodNotFoundError(JSONRPCError):
    def __init__(self):
        self.code = -32601
        self.message = "Method not found"
        self.http_status_code = 404


class InvalidParamsError(JSONRPCError):
    def __init__(self):
        self.code = -32602
        self.message = "Invalid params"
        self.http_status_code = 500


class InternalError(JSONRPCError):
    def __init__(self):
        self.code = -32603
        self.message = "Internal error"
        self.http_status_code = 500


class AlchemyConnectionRefusedError(JSONRPCError):
    def __init__(self):
        self.code = -32000
        self.message = "Alchemy connection refused"
        self.http_status_code = 500


def get_balances(params: Dict[str, Any]):
    address = params.get("address")
    if not FactoidAddress.is_valid(address):
        raise InvalidParamsError()
    try:
        return rpc.get_balances(address)
    except ConnectionRefusedError:
        raise AlchemyConnectionRefusedError()


def get_rates(params: Dict[str, Any]):
    height = params.get("height")
    if type(height) != int or height < 0:
        raise InvalidParamsError()
    try:
        return rpc.get_rates(height)
    except ConnectionRefusedError:
        raise AlchemyConnectionRefusedError()


def get_sync_head(params: Dict[str, Any]):
    try:
        return rpc.get_sync_head()
    except ConnectionRefusedError:
        raise AlchemyConnectionRefusedError()


def get_winners(params: Dict[str, Any]):
    height = params.get("height")
    if type(height) != int or height < 0:
        raise InvalidParamsError()
    try:
        return rpc.get_winners(height)
    except ConnectionRefusedError:
        raise AlchemyConnectionRefusedError()


def get_latest_winners(params: Dict[str, Any]):
    try:
        return rpc.get_winners()
    except ConnectionRefusedError:
        raise AlchemyConnectionRefusedError()


def send_transactions(params: Dict[str, Any]):
    transactions = params.get("transactions")
    ec_address = params.get("ec_address")
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


app = bottle.default_app()
method_map = {
    "get_balances": get_balances,
    "get_rates": get_rates,
    "get_sync_head": get_sync_head,
    "get_winners": get_winners,
    "get_latest_winners": get_latest_winners,
    "send_transactions": send_transactions,
}


@bottle.post("/v1")
def handle_json_rpc():
    try:
        request_id, method, params = parse_request(bottle.request.json)
    except JSONRPCError as e:
        bottle.response.status = e.http_status_code
        return {"id": None, "result": None, "error": e.to_dict()}

    try:
        result = method_map[method](params)
    except JSONRPCError as e:
        bottle.response.status = e.http_status_code
        return {"id": request_id, "result": None, "error": e.to_dict()}

    return {"id": request_id, "result": result, "error": None}


def parse_request(request_json: Dict[str, Any]) -> (Union[str, int, None], str, Dict[str, Any]):
    """Takes a JSON-RPC request dictionary and try to return (id, method, params)"""
    if request_json is None or request_json.get("jsonrpc") != "2.0":
        raise InvalidRequestError()

    method = request_json.get("method")
    if method not in method_map:
        raise MethodNotFoundError()

    request_id = request_json.get("id")
    if "id" not in request_json or type(request_id) not in {int, str, None}:
        raise InvalidRequestError()

    params = request_json.get("params", {})
    if type(params) != dict:
        raise InvalidParamsError()

    return request_id, method, params


# Entry point ONLY when run locally. The docker setup uses gunicorn and this block will not be executed.
if __name__ == "__main__":
    bottle.run(host="localhost", port=8000)
