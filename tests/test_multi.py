import random
from typing import List

import pytest
from consul import Consul

from tribun import ConfigurationKey
from tribun.main import multi_delete, multi_get, multi_put


@pytest.mark.parametrize("is_large_set", [True, False])
def test_multi_get(
    consul: Consul,
    is_large_set: bool,
    large_key_set: List[ConfigurationKey],
    configuration_keys: List[ConfigurationKey],
):
    if is_large_set:
        key_set = large_key_set
    else:
        key_set = configuration_keys

    assert not multi_get(consul, key_set)

    returned_keys = key_set.copy()
    to_add_key = returned_keys.pop(100 if is_large_set else 0)

    consul.kv.put(to_add_key.key, to_add_key.value)
    assert not (set(multi_get(consul, key_set)) & set(returned_keys))

    hand_modified_value = "toto"
    consul.kv.put(to_add_key.key, hand_modified_value)
    assert multi_get(consul, key_set)[0].value == hand_modified_value


@pytest.mark.parametrize("is_large_set", [True, False])
def test_multi_put(
    consul: Consul,
    is_large_set: bool,
    large_key_set: List[ConfigurationKey],
    configuration_keys: List[ConfigurationKey],
):
    if is_large_set:
        key_set = large_key_set
    else:
        key_set = configuration_keys

    multi_put(consul, key_set)

    assert set(multi_get(consul, key_set)) == set(key_set)


@pytest.mark.parametrize("is_large_set", [True, False])
def test_multi_delete(
    consul: Consul,
    is_large_set: bool,
    large_key_set: List[ConfigurationKey],
    configuration_keys: List[ConfigurationKey],
    key_set_size: int,
):
    if is_large_set:
        key_set = large_key_set
    else:
        key_set = configuration_keys

    multi_put(consul, key_set)
    multi_delete(consul, key_set)

    assert not multi_get(consul, key_set)

    multi_put(consul, key_set)
    deleted_index = random.randrange(0, len(key_set))
    multi_delete(consul, [key_set[deleted_index]])
    assert not set(multi_get(consul, key_set)) & {key_set[deleted_index]}
    multi_delete(consul, key_set)

    if is_large_set:
        left = key_set_size // 3
        multi_delete(consul, key_set[left:key_set_size])
        assert not set(multi_get(consul, key_set)) & set(key_set[left:key_set_size])
