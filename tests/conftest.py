from typing import List
from uuid import uuid4

import pytest
from consul import Consul
from consul.base import ClientError

from tribun.key import Key


@pytest.fixture
def key_set_size() -> int:
    return 130


@pytest.fixture
def large_key_set(consul: Consul, key_set_size: int):
    keys = [
        Key("tribun/test/a_" + str(index), str(uuid4)) for index in range(key_set_size)
    ]
    yield keys
    delete_keys(consul)


@pytest.fixture
def consul():
    import tribun.consul

    tribun.consul.consul = Consul()
    return tribun.consul.consul


def delete_keys(consul: Consul):
    try:
        consul.kv.delete("tribun", recurse=True)
    except ClientError:
        pass


@pytest.fixture
def configuration_keys(consul: Consul):
    keys = [
        Key("tribun/test/a", "a"),
        Key("tribun/test/b", "b"),
        Key("tribun/test/c", "c"),
    ]
    yield keys
    delete_keys(consul)


@pytest.fixture
def nested_keys(consul, configuration_keys: List[Key]):
    keys = [
        Key(
            "tribun/tests",
            [
                Key(
                    "nested",
                    [
                        Key("test", "magnifique"),
                        Key("test_2", "bagarre"),
                    ],
                )
            ],
        )
    ]
    yield configuration_keys + keys
    delete_keys(consul)
