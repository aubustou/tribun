import random
import string
from pathlib import Path
from types import ModuleType
from typing import List

import pytest

from tribun.key import Key
from tribun.revision import (
    delete,
    get,
    get_full_keys,
    get_revisions,
    put,
    sort_revisions,
)

RESOURCES_FOLDER = Path(__file__).parent / "resources.d"
REVISION_BODY = """
from tribun import put

DOWN_REVISION = "hgsqa54a"
REVISION = "{revision}"

def upgrade():
    put([
        Key("tribun/test/yet_another_revision", "totot")
    ])

def downgrade():
    delete([
        Key("tribun/test/yet_another_revision", "totot")
    ])
"""


@pytest.fixture
def revision():
    revision_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    revision = RESOURCES_FOLDER / (revision_id + "_joe_la_mouke.py")

    with revision.open("w") as file_:
        file_.write(REVISION_BODY.format(revision=revision_id))
    yield revision
    revision.unlink()


def test_get_revisions(revision: Path):
    revisions = get_revisions(RESOURCES_FOLDER)
    assert len(revisions) == 2
    assert all(isinstance(x, ModuleType) for x in revisions)


def test_sort_revisions(revision: Path):
    revisions = sort_revisions(get_revisions(RESOURCES_FOLDER))
    assert all(
        revisions[i].REVISION == revisions[i + 1].DOWN_REVISION
        for i in range(len(revisions) - 1)
    )


def test_get_full_keys(nested_keys: List[Key]):
    assert len(get_full_keys(nested_keys)) == len(nested_keys) + 1
    full_keys = get_full_keys(nested_keys)
    assert full_keys[-1].key == "tribun/tests/nested/test_2"
    assert full_keys[-1].value == "bagarre"


def test_put(nested_keys: List[Key]):
    assert put(nested_keys)


def test_get(nested_keys: List[Key]):
    put(nested_keys)
    assert get(nested_keys)


def test_delete(nested_keys: List[Key]):
    assert delete(nested_keys)
