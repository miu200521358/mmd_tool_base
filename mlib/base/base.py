from enum import Enum, unique
from pickle import dumps, loads


from mlib.base.logger import parse2str


@unique
class Encoding(Enum):
    UTF_8 = "utf-8"
    UTF_16_LE = "utf-16-le"
    SHIFT_JIS = "shift-jis"
    CP932 = "cp932"


@unique
class FileType(Enum):
    """ファイル種別"""

    VMD_VPD = "VMD/VPDファイル (*.vmd, *.vpd)|*.vmd;*.vpd|すべてのファイル (*.*)|*.*"
    VMD = "VMDファイル (*.vmd)|*.vmd|すべてのファイル (*.*)|*.*"
    PMX = "PMXファイル (*.pmx)|*.pmx|すべてのファイル (*.*)|*.*"
    CSV = "CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*"
    VRM = "VRMファイル (*.vrm)|*.vrm|すべてのファイル (*.*)|*.*"


class BaseModel:
    """基底クラス"""

    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return parse2str(self)

    def copy(self):
        return loads(dumps(self))
