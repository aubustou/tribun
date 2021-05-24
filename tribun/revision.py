import copy
import importlib.util
import re
from pathlib import Path
from types import ModuleType
from typing import List, Optional

from consul import Consul

from tribun import ConfigurationKey
from tribun.main import TribunError, multi_delete, multi_get, multi_put

REVISION_FILENAME_PATTERN = re.compile(r"^([a-zA-Z0-9]{8})_([a-zA-Z0-9-_]*).py$")

consul: Consul = None  # type: ignore


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


class Revision(ModuleType):
    down_revision: Optional[str]
    revision: str


def get_revisions(folder: Path) -> List[Revision]:
    revisions = []
    for file_ in folder.iterdir():
        match = REVISION_FILENAME_PATTERN.match(file_.name)
        if not match:
            continue

        revision_id = match.groups()[0]
        spec = importlib.util.spec_from_file_location(
            f"tribun.revisions.{revision_id}", str(file_)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        revisions.append(mod)

    return revisions


def sort_revisions(revisions: List[Revision]) -> List[Revision]:
    dict_ = {x.DOWN_REVISION: x for x in revisions}

    tree = [dict_[None]]

    node = tree[0]
    while node:
        node = dict_.get(tree[-1].REVISION)
        if node:
            tree.append(node)
    return tree


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
