from enum import Enum, unique
from typing import TypeVar

from mlib.domain.base import BaseModel

@unique
class Switch(Enum):
    """ON/OFFスイッチ"""

    OFF = 0
    ON = 1


TBaseIndexModel = TypeVar("TBaseIndexModel", bound="BaseIndexModel")


class BaseIndexModel(BaseModel):
    """
    INDEXを持つ基底クラス
    """

    def __init__(self, index: int = -1) -> None:
        """
        初期化

        Parameters
        ----------
        index : int, optional
            INDEX, by default -1
        """
        self.index = index

    def __bool__(self) -> bool:
        return 0 <= self.index

    def __iadd__(self: TBaseIndexModel, v: TBaseIndexModel) -> None:
        raise NotImplementedError()

    def __add__(self: TBaseIndexModel, v: TBaseIndexModel) -> TBaseIndexModel:
        raise NotImplementedError()


TBaseIndexNameModel = TypeVar("TBaseIndexNameModel", bound="BaseIndexNameModel")


class BaseIndexNameModel(BaseModel):
    """
    INDEXと名前を持つ基底クラス
    """

    def __init__(self, index: int = -1, name: str = "", english_name: str = "") -> None:
        """
        初期化

        Parameters
        ----------
        index : int, optional
            INDEX, by default -1
        name : str, optional
            名前, by default ""
        english_name : str, optional
            英語名, by default ""
        """
        self.index: int = index
        self.name: str = name
        self.english_name: str = english_name

    def __bool__(self) -> bool:
        return 0 <= self.index and 0 <= len(self.name)

    def __iadd__(self: TBaseIndexNameModel, v: TBaseIndexNameModel) -> None:
        raise NotImplementedError()

    def __add__(
        self: TBaseIndexNameModel, v: TBaseIndexNameModel
    ) -> TBaseIndexNameModel:
        raise NotImplementedError()
