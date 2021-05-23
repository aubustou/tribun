import json
import re
from base64 import b64decode, b64encode
from dataclasses import InitVar, dataclass
from typing import Callable, Dict, List, Optional

from consul import Consul
from consul.base import ClientError

ERROR_MESSAGE_PATTERN = re.compile(r"""key \"(.+)\" doesn't exist""")
MAX_OPERATIONS_IN_TXN = 64


class TribunError(Exception):
    pass


@dataclass(frozen=True)
class ConfigurationKey:
    key: str
    value: Optional[str] = None
    alterable: bool = False
    is_tree: bool = False

    from_b64_value: InitVar[str] = ""

    def __post_init__(self, from_b64_value: str):
        if self.value is None and from_b64_value:
            object.__setattr__(
                self, "value", b64decode(from_b64_value.encode()).decode()
            )

    @property
    def b64_value(self):
        return b64encode(str(self.value).encode()).decode()


def get_not_existing_keys(body: str) -> List[str]:
    errors = json.loads(body)["Errors"]
    keys = [ERROR_MESSAGE_PATTERN.search(x["What"]).groups()[0] for x in errors]
    return keys


def _multi_get(consul: Consul, keys: List[ConfigurationKey]) -> Dict:
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
    consul: Consul, keys: List[ConfigurationKey], raise_errors: bool = False
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


def paginate(
    func: Callable, keys: List[ConfigurationKey], *args, **kwargs
) -> List[ConfigurationKey]:
    results = []
    end = len(keys) // MAX_OPERATIONS_IN_TXN + 1
    for sl in range(0, end):
        response = func(
            keys=keys[sl * MAX_OPERATIONS_IN_TXN : (sl + 1) * 64], *args, **kwargs
        )
        results.extend(
            [
                ConfigurationKey(x["KV"]["Key"], from_b64_value=x["KV"]["Value"])
                for x in response.get("Results", [])
                if x.get("KV")
            ]
        )
    return results


def multi_get(
    consul: Consul, keys: List[ConfigurationKey], raise_errors: bool = False
) -> List[ConfigurationKey]:

    return paginate(
        atomic_multi_get, consul=consul, keys=keys, raise_errors=raise_errors
    )


def _multi_put(consul: Consul, keys: List[ConfigurationKey]):
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
    keys: List[ConfigurationKey],
) -> List[ConfigurationKey]:

    return paginate(_multi_put, consul=consul, keys=keys)


def _multi_delete(consul: Consul, keys: List[ConfigurationKey]):
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
    keys: List[ConfigurationKey],
) -> List[ConfigurationKey]:

    return paginate(_multi_delete, consul=consul, keys=keys)


def run(
    keys: List[ConfigurationKey],
    exist_ok: bool = False,
):
    consul = Consul()

    if not exist_ok and multi_get(consul, keys):
        raise TribunError("Existing keys")

    # multi_put(consul, keys)


def main():
    run(
        exist_ok=False,
        keys=[
            ConfigurationKey("intel/globl/tout", "tata"),
            ConfigurationKey("intel/global/test", "cling"),
            ConfigurationKey("intel/global/velo", "cling"),
        ],
    )


if __name__ == "__main__":
    main()
