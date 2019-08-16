import bottle
import json
from factom_keys.fct import FactoidAddress

import alchemy.rpc as rpc


@bottle.hook("before_request")
def strip_path():
    """Strip trailing '/' on all requests. '/foo' and /foo/' are two unique endpoints in bottle"""
    bottle.request.environ["PATH_INFO"] = bottle.request.environ["PATH_INFO"].rstrip("/")


@bottle.get("/health")
def health_check():
    return {"data": "Healthy!"}


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


@bottle.get("/v1/balances/<height:int>")
def get_winners(height: int):
    if height < 0:
        bottle.abort(404)
    return rpc.get_winners(height)


# Error Handlers

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
