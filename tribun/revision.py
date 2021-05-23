import copy
from typing import List

from consul.std import Consul

from tribun import ConfigurationKey
from tribun.main import TribunError, multi_delete, multi_get, multi_put


def recurse(key: ConfigurationKey, namespace: str = "") -> List[ConfigurationKey]:
    keys = []

    if isinstance(key.value, list):
        if namespace:
            namespace = "/".join([namespace, key.key])
        else:
            namespace = key.key
        for sub in key.value:
            keys.extend(recurse(sub, namespace))
    else:
        key = copy.deepcopy(key)
        key.key_from_namespace(namespace)
        keys.append(key)
    return keys


def get_full_keys(keys: List[ConfigurationKey]) -> List[ConfigurationKey]:
    results = []
    for key in keys:
        results.extend(recurse(key))

    return results


consul: Consul = None  # type: ignore


def with_consul(func):
    def wrap(*args, **kwargs):
        global consul

        if not consul:
            consul = Consul()
        return func(*args, **kwargs)

    return wrap


@with_consul
def put(keys: List[ConfigurationKey]) -> List[ConfigurationKey]:
    full_keys = get_full_keys(keys)

    unalterable_keys = [x for x in full_keys if not x.alterable]
    if unalterable_keys:
        found_keys = multi_get(consul, unalterable_keys)
        if found_keys:
            raise TribunError("Keys could not be modified")

    multi_put(consul, full_keys)

    return full_keys


@with_consul
def get(keys: List[ConfigurationKey]) -> List[ConfigurationKey]:
    full_keys = get_full_keys(keys)

    return multi_get(consul, full_keys)


@with_consul
def delete(keys: List[ConfigurationKey]) -> List[ConfigurationKey]:
    full_keys = get_full_keys(keys)
    multi_delete(consul, full_keys)

    return full_keys
