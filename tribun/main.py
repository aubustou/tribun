from typing import List

from consul import Consul

from tribun.key import Key
from tribun.operations import multi_get


def run(
    keys: List[Key],
    exist_ok: bool = False,
):
    consul = Consul()

    if not exist_ok and multi_get(consul, keys):
        raise TribunError("Existing keys")

    # multi_put(consul, keys)


def main():
    run(
        exist_ok=False,
        keys=[],
    )


if __name__ == "__main__":
    main()
