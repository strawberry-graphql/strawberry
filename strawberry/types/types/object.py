from abc import ABC, abstractmethod
from typing import Optional


class StrawberryObject(ABC):

    @property
    @abstractmethod
    def name(self) -> Optional[str]:
        """Optional to support anonymous types"""
        # TODO: Should it actually be optional?
        ...

    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        ...
