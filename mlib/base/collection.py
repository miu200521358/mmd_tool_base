import hashlib
from typing import Generic, Optional, TypeVar

from bisect import bisect_left

from mlib.base.base import BaseModel, Encoding
from mlib.base.part import BaseIndexModel, BaseIndexNameModel

TBaseIndexModel = TypeVar("TBaseIndexModel", bound=BaseIndexModel)
TBaseIndexNameModel = TypeVar("TBaseIndexNameModel", bound=BaseIndexNameModel)


class BaseIndexListModel(Generic[TBaseIndexModel], BaseModel):
    """BaseIndexModelのリスト基底クラス"""

    __slots__ = ["data", "__iter_index"]

    def __init__(self, data: Optional[list[TBaseIndexModel]] = None) -> None:
        """
        モデルリスト

        Parameters
        ----------
        data : list[TBaseIndexModel], optional
            リスト, by default []
        """
        super().__init__()
        self.data = data or []
        self.__iter_index = 0

    def __getitem__(self, index: int) -> TBaseIndexModel:
        if index < 0:
            # マイナス指定の場合、後ろからの順番に置き換える
            return self.get(len(self.data) + index)
        return self.get(index)

    def __setitem__(self, index: int, value: TBaseIndexModel):
        self.data[index] = value

    def __delitem__(self, index: int):
        del self.data[index]

    def get(self, index: int) -> TBaseIndexModel:
        """
        リストから要素を取得する

        Parameters
        ----------
        index : int
            インデックス番号

        Returns
        -------
        TBaseIndexModel
            要素
        """
        if index >= len(self.data):
            raise KeyError(f"Not Found: {index}")
        return self.data[index]

    def append(self, v: TBaseIndexModel) -> None:
        if v.index < 0:
            v.index = len(self.data)
        self.data.append(v)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        self.__iter_index = -1
        return self

    def __next__(self) -> TBaseIndexModel:
        self.__iter_index += 1
        if self.__iter_index >= len(self.data):
            raise StopIteration
        return self.data[self.__iter_index]


TBaseIndexListModel = TypeVar("TBaseIndexListModel", bound=BaseIndexListModel)


class BaseIndexNameListModel(Generic[TBaseIndexNameModel], BaseModel):
    """BaseIndexNameModelのリスト基底クラス"""

    __slots__ = ["data", "__names", "__iter_index"]

    def __init__(self, data: Optional[list[TBaseIndexNameModel]] = None) -> None:
        """
        モデルリスト

        Parameters
        ----------
        data : list[TBaseIndexNameModel], optional
            リスト, by default []
        """
        super().__init__()
        self.data: list[TBaseIndexNameModel] = data or []
        self.__names = self.names
        self.__iter_index = 0

    def __getitem__(self, key: int | str) -> TBaseIndexNameModel:
        if isinstance(key, int):
            return self.get_by_index(key)
        else:
            return self.get_by_name(key)

    # def __setitem__(self, index: int, v: TBaseIndexNameModel):
    #     self.data[index] = v
    #     if v.name not in self.__names:
    #         # 名前は先勝ちで保持
    #         self.__names[v.name] = v.index

    @property
    def names(self) -> dict[str, int]:
        return dict([(v.name, v.index) for v in self.data])

    def get_by_index(self, index: int) -> TBaseIndexNameModel:
        """
        リストから要素を取得する

        Parameters
        ----------
        index : int
            インデックス番号

        Returns
        -------
        TBaseIndexNameModel
            要素
        """
        if index >= len(self.data):
            raise KeyError(f"Not Found: {index}")
        return self.data[index]

    def get_by_name(self, name: str) -> TBaseIndexNameModel:
        """
        リストから要素を取得する

        Parameters
        ----------
        name : str
            名前

        Returns
        -------
        TBaseIndexNameModel
            要素
        """
        if name not in self.names:
            raise KeyError(f"Not Found: {name}")
        return self.data[self.__names[name]]

    def append(self, v: TBaseIndexNameModel) -> None:
        if v.index < 0:
            v.index = len(self.data)
        if v.name not in self.names:
            # 名前は先勝ちで保持
            self.__names[v.name] = v.index
        self.data.append(v)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        self.__iter_index = -1
        return self

    def __next__(self) -> TBaseIndexNameModel:
        self.__iter_index += 1
        if self.__iter_index >= len(self.data):
            raise StopIteration
        return self.data[self.__iter_index]

    def __contains__(self, v) -> bool:
        return v in [v.name for v in self.data] or v in [v.index for v in self.data]


class BaseIndexDictModel(Generic[TBaseIndexModel], BaseModel):
    """BaseIndexModelの辞書基底クラス"""

    __slots__ = ["data", "__indices", "__iter_index"]

    def __init__(self, data: Optional[dict[int, TBaseIndexModel]] = None) -> None:
        """
        モデル辞書

        Parameters
        ----------
        data : Dict[TBaseIndexModel], optional
            辞書, by default {}
        """
        super().__init__()
        self.data: dict[int, TBaseIndexModel] = data or {}
        self.__indices: list[int] = []
        self.__iter_index: int = 0

    @property
    def indices(self) -> list[int]:
        return self.__indices

    def __getitem__(self, index: int) -> TBaseIndexModel:
        return self.get(index)

    def __setitem__(self, index: int, value: TBaseIndexModel):
        self.data[index] = value
        self.__indices = list(self.data.keys())
        self.__indices.sort()

    def __delitem__(self, index: int):
        del self.data[index]

    def append(self, value: TBaseIndexModel):
        self.data[value.index] = value

    def get(self, index: int) -> TBaseIndexModel:
        """
        辞書から要素を取得する

        Parameters
        ----------
        index : int
            インデックス番号
        required : bool, optional
            必須要素であるか, by default False

        Returns
        -------
        TBaseIndexModel
            要素
        """
        if index not in self:
            raise KeyError(f"Not Found: {index}")
        return self.data[index]

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        self.__iter_index = -1
        return self

    def __next__(self) -> TBaseIndexModel:
        self.__iter_index += 1
        if self.__iter_index >= len(self.__indices):
            raise StopIteration
        return self.data[self.__indices[self.__iter_index]]

    def __contains__(self, v) -> bool:
        return v in self.data


TBaseIndexDictModel = TypeVar("TBaseIndexDictModel", bound=BaseIndexDictModel)


class BaseIndexNameDictInnerModel(Generic[TBaseIndexNameModel], BaseModel):
    """BaseIndexNameModelの内部辞書基底クラス"""

    __slots__ = ["data", "__indices", "__iter_index", "name", "cache"]

    def __init__(self, name: str, data: Optional[dict[int, TBaseIndexNameModel]] = None) -> None:
        """
        モデル辞書

        Parameters
        ----------
        data : Dict[str, TBaseIndexNameModel], optional
            辞書データ, by default {}
        """
        super().__init__()
        self.data: dict[int, TBaseIndexNameModel] = data or {}
        self.__indices: list[int] = []
        self.name = data[0].name if data else name if name else ""
        self.cache: dict[int, TBaseIndexNameModel] = {}

    def range_indexes(self, index: int, indices: list[int] = []) -> tuple[int, int, int]:
        """
        指定されたINDEXの前後を返す

        Parameters
        ----------
        index : int
            指定INDEX

        Returns
        -------
        tuple[int, int]
            INDEXがデータ内にある場合: index, index, index
            INDEXがデータ内にない場合: 前のindex, 対象INDEXに相当する場所にあるINDEX, 次のindex
                prev_idx == idx: 指定されたINDEXが一番先頭
                idx == next_idx: 指定されたINDEXが一番最後
        """
        if not indices:
            indices = self.indices
        if index in indices:
            return index, index, index

        # index がない場合、前後のINDEXを取得する

        idx = bisect_left(indices, index)
        if idx == 0:
            prev_idx = 0
        else:
            prev_idx = idx - 1
        if idx == len(indices):
            next_idx = len(indices) - 1
        else:
            next_idx = idx

        return (
            indices[prev_idx],
            index,
            indices[next_idx],
        )

    @property
    def indices(self) -> list[int]:
        return self.__indices

    def __getitem__(self, index: int) -> TBaseIndexNameModel:
        return self.get(index)

    def get(self, index: int) -> TBaseIndexNameModel:
        """
        辞書から要素を取得する

        Parameters
        ----------
        index : int
            インデックス番号

        Returns
        -------
        TBaseIndexNameModel
        """
        if index not in self:
            raise KeyError(f"Not Found index: {index}")
        return self.data[index]

    def __delitem__(self, index: int):
        del self.data[index]

    def append(self, value: TBaseIndexNameModel):
        self.data[value.index] = value
        self.name = value.name
        self.__indices = list(self.data.keys())
        self.__indices.sort()

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        self.__iter_index = -1
        return self

    def __next__(self) -> TBaseIndexNameModel:
        self.__iter_index += 1
        if self.__iter_index >= len(self.__indices):
            raise StopIteration
        return self.data[self.__indices[self.__iter_index]]

    def __contains__(self, v) -> bool:
        return v in self.data


TBaseIndexNameDictInnerModel = TypeVar("TBaseIndexNameDictInnerModel", bound=BaseIndexNameDictInnerModel)


class BaseIndexNameDictModel(Generic[TBaseIndexNameModel, TBaseIndexNameDictInnerModel], BaseModel):
    """BaseIndexNameModelの辞書基底クラス"""

    __slots__ = ["data", "__iter_index", "__names"]

    def __init__(self, data: Optional[dict[str, TBaseIndexNameDictInnerModel]] = None) -> None:
        """
        モデル辞書

        Parameters
        ----------
        data : TBaseIndexNameDictInnerModel, optional
            辞書データ, by default {}
        """
        super().__init__()
        self.data: dict[str, TBaseIndexNameDictInnerModel] = data or {}
        self.__names: list[str] = []
        self.__iter_index: int = 0

    @property
    def names(self) -> list[str]:
        return self.__names

    def __getitem__(self, name: str) -> TBaseIndexNameDictInnerModel:
        return self.get(name)

    def __delitem__(self, name: str, index: Optional[int] = None):
        if index is None:
            del self.data[name]
        else:
            del self.data[name][index]

    def create_inner(self, name: str) -> TBaseIndexNameDictInnerModel:
        raise NotImplementedError()

    def append(self, value: TBaseIndexNameModel):
        if value.name not in self:
            self.data[value.name] = self.create_inner(value.name)
        self.data[value.name].append(value)
        self.__names = list(self.data.keys())

    def get(self, name: str) -> TBaseIndexNameDictInnerModel:
        """
        辞書から要素を取得する

        Parameters
        ----------
        name : str
            キー名
        index : int
            インデックス番号

        Returns
        -------
        TBaseIndexNameDictInnerModel
        """
        if name not in self:
            raise KeyError(f"Not Found Name: {name}")

        return self.data[name]

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        self.__iter_index = -1
        return self

    def __next__(self) -> TBaseIndexNameDictInnerModel:
        self.__iter_index += 1
        if self.__iter_index >= len(self.__names):
            raise StopIteration
        return self.data[self.__names[self.__iter_index]]

    def __contains__(self, v) -> bool:
        return v in self.data


TBaseIndexNameDictModel = TypeVar("TBaseIndexNameDictModel", bound=BaseIndexNameDictModel)


class BaseHashModel(BaseModel):
    """
    ハッシュ機能付きモデル

    Parameters
    ----------
    path : str, optional
        パス, by default ""
    """

    def __init__(self, path: str = "") -> None:
        super().__init__()
        self.path = path
        self.digest = ""

    @property
    def name(self) -> str:
        """モデル内の名前に相当する値を返す"""
        raise NotImplementedError()

    @property
    def hexdigest(self) -> str:
        """モデルデータのハッシュ値を取得する"""
        return self.digest

    def update_hexdigest(self) -> None:
        sha1 = hashlib.sha1()

        with open(self.path, "rb") as f:
            for chunk in iter(lambda: f.read(2048 * sha1.block_size), b""):
                sha1.update(chunk)

        sha1.update(chunk)

        # ファイルパスをハッシュに含める
        sha1.update(self.path.encode(Encoding.UTF_8.value))

        self.digest = sha1.hexdigest()

    def __bool__(self) -> bool:
        # パスが定義されていたら、中身入り
        return len(self.path) > 0
