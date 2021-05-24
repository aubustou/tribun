# Tribun

Tribun is a Python library for dealing with Consul Key/Value database revisions.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install tribun.

```bash
pip install tribun
```

## Usage

```python
from tribun import Key, put, get, delete

put([Key("toto", "tutu"]) # Add 'toto' key with 'tutu' value
get([Key("toto"]) # Get 'toto' key
delete([Key("toto", "tutu"]) # Delete 'toto' key
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
