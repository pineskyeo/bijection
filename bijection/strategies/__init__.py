"""Strategy registry."""
from bijection.strategies.sequential import SequentialStrategy
from bijection.strategies.hash_strategy import HashStrategy
from bijection.strategies.dict_strategy import DictStrategy

STRATEGIES = {
    "sequential": SequentialStrategy,
    "hash": HashStrategy,
    "dict": DictStrategy,
}


def get_strategy(name: str, **kwargs):
    cls = STRATEGIES.get(name)
    if cls is None:
        raise ValueError(f"Unknown strategy '{name}'. Choose from: {list(STRATEGIES)}")
    return cls(**kwargs)
