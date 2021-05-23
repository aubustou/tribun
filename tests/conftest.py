from typing import List
from uuid import uuid4

import pytest
from consul import Consul
from consul.base import ClientError

from tribun import ConfigurationKey


@pytest.fixture
def key_set_size() -> int:
    return 130


@pytest.fixture
def large_key_set(consul: Consul, key_set_size: int):
    keys = [
        ConfigurationKey("tribun/test/a_" + str(index), str(uuid4))
        for index in range(key_set_size)
    ]
    yield keys
    delete_keys(consul)


@pytest.fixture
def consul():
    return Consul()


def delete_keys(consul: Consul):
    try:
        consul.kv.delete("tribun", recurse=True)
    except ClientError:
        pass


@pytest.fixture
def configuration_keys(consul: Consul):
    keys = [
        ConfigurationKey("tribun/test/a", "a"),
        ConfigurationKey("tribun/test/b", "b"),
        ConfigurationKey("tribun/test/c", "c"),
    ]
    yield keys
    delete_keys(consul)


@pytest.fixture
def nested_keys(consul, configuration_keys: List[ConfigurationKey]):
    keys = [
        ConfigurationKey(
            "tribun/tests",
            [
                ConfigurationKey(
                    "nested",
                    [
                        ConfigurationKey("test", "magnifique"),
                        ConfigurationKey("test_2", "bagarre"),
                    ],
                )
            ],
        )
    ]
    yield configuration_keys + keys
    delete_keys(consul)
