from base64 import b64encode
from typing import Callable, Dict, List

from consul import Consul
from consul.base import ClientError

from tribun.errors import TribunError
from tribun.key import Key, get_not_existing_keys

MAX_OPERATIONS_IN_TXN = 64


def paginate(func: Callable, keys: List[Key], *args, **kwargs) -> List[Key]:
    results = []
    end = len(keys) // MAX_OPERATIONS_IN_TXN + 1
    for sl in range(0, end):
        response = func(
            keys=keys[sl * MAX_OPERATIONS_IN_TXN : (sl + 1) * 64], *args, **kwargs
        )
        results.extend(
            [
                Key(x["KV"]["Key"], from_b64_value=x["KV"]["Value"])
                for x in response.get("Results", [])
                if x.get("KV")
            ]
        )
    return results


def _multi_get(consul: Consul, keys: List[Key]) -> Dict:
    return consul.txn.put(
        payload=[
            {
                "KV": {
                    "Verb": "get",
                    "Key": x.key,
                }
            }
            for x in keys
        ]
    )


def atomic_multi_get(
    consul: Consul, keys: List[Key], raise_errors: bool = False
) -> Dict:
    try:
        response = _multi_get(consul, keys)
    except ClientError as e:
        code, body = e.args[0].split(" ", 1)
        if code == "413":
            raise TribunError(f"Too many keys ({len(keys)} > {MAX_OPERATIONS_IN_TXN})")

        if not raise_errors and code == "409":
            existing = [x for x in keys if x.key not in get_not_existing_keys(body)]
            if not existing:
                return {}
            response = _multi_get(consul, existing)
        else:
            raise
    return response


def multi_get(consul: Consul, keys: List[Key], raise_errors: bool = False) -> List[Key]:

    return paginate(
        atomic_multi_get, consul=consul, keys=keys, raise_errors=raise_errors
    )


def _multi_put(consul: Consul, keys: List[Key]):
    return consul.txn.put(
        payload=[
            {
                "KV": {
                    "Verb": "set",
                    "Key": x.key,
                    "Value": b64encode(str(x.value).encode()).decode(),
                }
            }
            for x in keys
        ]
    )


def multi_put(
    consul: Consul,
    keys: List[Key],
) -> List[Key]:

    return paginate(_multi_put, consul=consul, keys=keys)


def _multi_delete(consul: Consul, keys: List[Key]):
    return consul.txn.put(
        payload=[
            {
                "KV": {
                    "Verb": "delete-tree" if x.is_tree else "delete",
                    "Key": x.key,
                }
            }
            for x in keys
        ]
    )


def multi_delete(
    consul: Consul,
    keys: List[Key],
) -> List[Key]:

    return paginate(_multi_delete, consul=consul, keys=keys)
