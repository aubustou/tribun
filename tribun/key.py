import json
import re
from base64 import b64decode, b64encode
from dataclasses import InitVar, dataclass
from typing import List, Union

ERROR_MESSAGE_PATTERN = re.compile(r"""key \"(.+)\" doesn't exist""")


@dataclass(frozen=True)
class Key:
    key: str
    value: Union[None, str, List["Key"]] = None
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

    def key_from_namespace(self, namespace: str):
        if namespace:
            object.__setattr__(self, "key", "/".join([namespace, self.key]))


def get_not_existing_keys(body: str) -> List[str]:
    errors = json.loads(body)["Errors"]
    keys = [ERROR_MESSAGE_PATTERN.search(x["What"]).groups()[0] for x in errors]
    return keys
