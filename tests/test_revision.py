import random
import string
from pathlib import Path
from typing import List

import pytest

from tribun import ConfigurationKey, put
from tribun.revision import delete, get, get_full_keys

RESOURCES_FOLDER = Path(__file__).parent / "resources.d"


@pytest.fixture
def revision():
    revision = RESOURCES_FOLDER / (
        "".join(random.choices(string.ascii_uppercase + string.digits, k=8)) + ".py"
    )
    with revision.open("w") as file_:
        file_.write("toto")
    yield revision
    revision.unlink()


def test_get_revisions(revision: Path):
    pass


def test_get_full_keys(nested_keys: List[ConfigurationKey]):
    assert len(get_full_keys(nested_keys)) == len(nested_keys) + 1
    full_keys = get_full_keys(nested_keys)
    assert full_keys[-1].key == "tribun/tests/nested/test_2"
    assert full_keys[-1].value == "bagarre"


def test_put(nested_keys: List[ConfigurationKey]):
    assert put(nested_keys)


def test_get(nested_keys: List[ConfigurationKey]):
    put(nested_keys)
    assert get(nested_keys)


def test_delete(nested_keys: List[ConfigurationKey]):
    assert delete(nested_keys)
