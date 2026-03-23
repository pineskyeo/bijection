"""Abstract base lexer."""
from abc import ABC, abstractmethod
from typing import List

from bijection.core.token import Token


class BaseLexer(ABC):
    """Tokenise a source string into a lossless token stream.

    Contract:
        ''.join(t.value for t in tokenize(source)) == source
    """

    @abstractmethod
    def tokenize(self, source: str) -> List[Token]:
        raise NotImplementedError

    @staticmethod
    def verify_lossless(source: str, tokens: List[Token]) -> None:
        """Raise AssertionError if the token stream is not lossless."""
        reconstructed = "".join(t.value for t in tokens)
        if reconstructed != source:
            raise AssertionError(
                f"Lexer is not lossless!\n"
                f"  source length:        {len(source)}\n"
                f"  reconstructed length: {len(reconstructed)}\n"
                f"  first diff at byte:   "
                f"{next((i for i,(a,b) in enumerate(zip(source,reconstructed)) if a!=b), '?')}"
            )
