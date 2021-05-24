import copy
import importlib.util
import re
from abc import abstractmethod
from pathlib import Path
from types import ModuleType
from typing import List, Optional

from tribun.consul import consul
from tribun.errors import TribunError
from tribun.key import Key
from tribun.operations import multi_delete, multi_get, multi_put

REVISION_FILENAME_PATTERN = re.compile(r"^([a-zA-Z0-9]{8})_([a-zA-Z0-9-_]*).py$")


def recurse(key: Key, namespace: str = "") -> List[Key]:
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


def get_full_keys(keys: List[Key]) -> List[Key]:
    results = []
    for key in keys:
        results.extend(recurse(key))

    return results


class Revision(ModuleType):
    DOWN_REVISION: Optional[str]
    REVISION: str

    @abstractmethod
    def upgrade(self) -> None:
        pass

    @abstractmethod
    def downgrade(self) -> None:
        pass


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
    dict_ = {}
    for revision in revisions:
        down_revision = revision.DOWN_REVISION
        if dict_.get(down_revision):
            raise TribunError("Multi-head revisions are not supported")
        dict_[down_revision] = revision

    tree = [dict_[None]]

    node = tree[0]
    while node:
        node = dict_.get(tree[-1].REVISION)
        if node:
            tree.append(node)
    return tree


def put(keys: List[Key]) -> List[Key]:
    full_keys = get_full_keys(keys)

    unalterable_keys = [x for x in full_keys if not x.alterable]
    if unalterable_keys:
        found_keys = multi_get(consul, unalterable_keys)
        if found_keys:
            raise TribunError("Keys could not be modified")

    multi_put(consul, full_keys)

    return full_keys


def get(keys: List[Key]) -> List[Key]:
    full_keys = get_full_keys(keys)

    return multi_get(consul, full_keys)


def delete(keys: List[Key]) -> List[Key]:
    full_keys = get_full_keys(keys)
    multi_delete(consul, full_keys)

    return full_keys
