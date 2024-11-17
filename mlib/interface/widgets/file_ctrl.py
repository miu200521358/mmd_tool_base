import os
from typing import Any, Generic, Optional, TypeVar

import wx

from mlib.domain.collection import BaseHashModel
from mlib.domain.logger import MLogger
from mlib.domain.reader import BaseReader
from mlib.interface.notebook_frame import NotebookFrame
from mlib.interface.notebook_panel import NotebookPanel
from mlib.utils.file_utils import (
    get_clear_path,
    get_dir_path,
    insert_history,
    separate_path,
    unwrapped_path,
    validate_file,
    validate_save_file,
)
from mlib.utils.image_utils import ImageModel, ImageReader

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text

TBaseHashModel = TypeVar("TBaseHashModel", bound=BaseHashModel)
TBaseReader = TypeVar("TBaseReader", bound=BaseReader)


class MFilePickerCtrl(Generic[TBaseHashModel, TBaseReader]):
    def __init__(
        self,
        parent: Any,
        frame: NotebookFrame,
        panel: NotebookPanel,
        reader: TBaseReader,
        title: str,
        key: Optional[str] = None,
        is_show_name: bool = True,
        name_spacer: int = 0,
        is_save: bool = False,
        is_aster: bool = False,
        tooltip: str = "",
        file_change_event=None,
        file_choice_names: Optional[list[str]] = None,
    ) -> None:
        self.parent = parent
        self.frame = frame
        self.panel = panel
        self.reader: TBaseReader = reader
        self.original_data: Optional[TBaseHashModel] = None
        self.data: Optional[TBaseHashModel] = None
        self.key = key
        self.title = __(title)
        self.is_save = is_save
        self.is_show_name = is_show_name
        self.file_change_event = file_change_event
        self.root_sizer = wx.BoxSizer(wx.VERTICAL)
        self.is_aster = is_aster
        self.file_choice_names = file_choice_names
        self.paths = []

        self._initialize_ui(name_spacer, tooltip)
        self._initialize_event()

    def set_parent_sizer(self, parent_sizer: wx.Sizer) -> None:
        parent_sizer.Add(self.root_sizer, 1, wx.GROW, 0)

    def _initialize_ui(self, name_spacer: int, tooltip: str) -> None:
        # ファイルタイトル
        self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if self.title:
            self.title_ctrl = wx.StaticText(
                self.parent, wx.ID_ANY, self.title, wx.DefaultPosition, wx.Size(-1, -1), 0
            )
            self.title_ctrl.SetToolTip(__(tooltip))
            self.title_sizer.Add(self.title_ctrl, 0, wx.ALL, 3)
        self.spacer_ctrl = None
        self.name_ctrl = None
        self.name_blank_ctrl = None

        # モデル名等の表示
        if self.is_show_name and not self.is_save:
            if name_spacer:
                self.spacer_ctrl = wx.StaticText(
                    self.parent,
                    wx.ID_ANY,
                    " " * name_spacer,
                    wx.DefaultPosition,
                    wx.Size(-1, -1),
                    0,
                )
                self.title_sizer.Add(self.spacer_ctrl, 0, wx.ALL, 3)

            self.name_ctrl = wx.TextCtrl(
                self.parent,
                wx.ID_ANY,
                __("(未設定)"),
                wx.DefaultPosition,
                wx.Size(-1, -1),
                wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS | wx.ALIGN_RIGHT,
            )
            self.name_ctrl.SetBackgroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT)
            )
            self.name_ctrl.SetToolTip(
                __(
                    "{t}に記録されているモデル名です。\n文字列は選択およびコピー可能です。",
                    t=self.title,
                )
            )
            self.title_sizer.Add(self.name_ctrl, 1, wx.ALL, 3)

            self.name_blank_ctrl = wx.StaticText(
                self.parent, wx.ID_ANY, "   ", wx.DefaultPosition, wx.Size(150, -1), 0
            )
            self.name_blank_ctrl.SetBackgroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT)
            )
            self.title_sizer.Add(self.name_blank_ctrl, 0, wx.ALL, 3)

        self.root_sizer.Add(self.title_sizer, 1, wx.EXPAND | wx.ALL, 3)

        # ------------------------------
        # ファイルコントロール
        self.file_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if self.file_choice_names:
            self.file_choice_ctrl = wx.Choice(
                self.parent,
                wx.ID_ANY,
                choices=self.file_choice_names,
            )
            self.file_choice_ctrl.SetSelection(0)
            self.file_sizer.Add(self.file_choice_ctrl, 0, wx.ALL, 3)
            self.file_choice_ctrl.Bind(wx.EVT_CHOICE, self.choice_event)

        # 読み取りか保存かでスタイルを変える
        file_ctrl_style = (
            wx.FLP_DEFAULT_STYLE
            if not self.is_save
            else wx.FLP_OVERWRITE_PROMPT | wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL
        )
        self.file_ctrl = wx.FilePickerCtrl(
            self.parent,
            wx.ID_ANY,
            path=wx.EmptyString,
            wildcard=self.reader.file_wildcard,
            style=file_ctrl_style,
        )
        self.file_ctrl.GetPickerCtrl().SetLabel(__("開く"))
        self.file_ctrl.SetToolTip(__(tooltip))
        if self.key and self.frame.histories[self.key]:
            self.file_ctrl.SetInitialDirectory(
                os.path.dirname(self.frame.histories[self.key][0])
            )

        self.file_sizer.Add(self.file_ctrl, 1, wx.GROW | wx.ALL, 3)

        if not self.is_save:
            # 保存じゃなければ履歴ボタンを表示
            self.history_ctrl = wx.Button(
                self.parent,
                wx.ID_ANY,
                label=__("履歴"),
            )
            self.history_ctrl.SetToolTip(
                __(
                    "これまでに指定された事のある{t}を再指定することができます。",
                    t=self.title,
                )
            )
            self.file_sizer.Add(self.history_ctrl, 0, wx.ALL, 3)

        self.root_sizer.Add(self.file_sizer, 0, wx.GROW | wx.ALL, 0)

    def choice_event(self, event: wx.Event) -> None:
        if not self.file_choice_ctrl:
            return
        choiceIdx = self.file_choice_ctrl.GetSelection()
        if len(self.paths) > choiceIdx:
            self.file_ctrl.SetPath(self.paths[choiceIdx])

    def _initialize_event(self) -> None:
        # D&Dの実装
        self.file_ctrl.SetDropTarget(MFileDropTarget(self))

        if not self.is_save:
            self.history_ctrl.Bind(wx.EVT_BUTTON, self.on_show_histories)

        if self.file_change_event:
            self.file_ctrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.file_change_event)

    def on_show_histories(self, event: wx.Event) -> None:
        """履歴一覧を表示する"""
        if not self.key:
            return

        histories = self.frame.histories[self.key] + [" " * 200]

        with wx.SingleChoiceDialog(
            self.frame,
            __(
                "ファイルを選んでダブルクリック、またはOKボタンをクリックしてください。"
            ),
            caption=__("ファイル履歴選択"),
            choices=histories,
            style=wx.CAPTION
            | wx.CLOSE_BOX
            | wx.SYSTEM_MENU
            | wx.OK
            | wx.CANCEL
            | wx.CENTRE,
        ) as choiceDialog:
            if choiceDialog.ShowModal() == wx.ID_CANCEL:
                return

            # ファイルピッカーに選択したパスを設定
            self.file_ctrl.SetPath(choiceDialog.GetStringSelection())

            if self.paths and self.file_choice_ctrl:
                for n in range(self.file_choice_ctrl.GetSelection() + 1):
                    if len(self.paths) <= n:
                        self.paths.append("")
                self.paths[self.file_choice_ctrl.GetSelection()] = choiceDialog.GetStringSelection()

            self.file_change_event(wx.FileDirPickerEvent())
            self.file_ctrl.UpdatePickerFromTextCtrl()
            self.file_ctrl.SetInitialDirectory(
                get_dir_path(choiceDialog.GetStringSelection())
            )
            self.data = None

    @property
    def path(self) -> str:
        return self.file_ctrl.GetPath()

    @path.setter
    def path(self, v: str) -> None:
        if self.valid(v):
            self.file_ctrl.SetPath(v)
        elif v:
            _, file_name, _ = separate_path(v)
            if "*" in file_name:
                self.file_ctrl.SetPath(v)

    @property
    def separated_path(self) -> tuple[str, str, str]:
        """パスを「ディレクトリパス」「ファイル名」「ファイル拡張子」に分割して返す"""
        if not self.path:
            return "", "", ""
        return separate_path(self.file_ctrl.GetPath())

    def valid(self, v: Optional[str] = None) -> bool:
        path = v if v else self.file_ctrl.GetPath()
        if not path.strip():
            return False
        return (not self.is_save and validate_file(path, self.reader.file_type)) or (
            self.is_save and validate_save_file(path, self.title)
        )

    def unwrap(self) -> None:
        self.file_ctrl.SetPath(unwrapped_path(self.file_ctrl.GetPath()))

    def save_path(self) -> None:
        if not self.key or not self.valid():
            return
        insert_history(self.file_ctrl.GetPath(), self.frame.histories[self.key])

    def read_name(self) -> bool:
        """
        リーダー対象オブジェクトの名前を読み取る

        Returns
        -------
        bool
            読み取り出来るパスか否か
        """
        if self.name_ctrl and not self.file_ctrl.GetPath().strip():
            self.name_ctrl.SetValue(__("(未設定)"))
            self.clear_data()
            return False

        if self.name_ctrl and self.is_show_name and not self.is_save:
            if validate_file(self.file_ctrl.GetPath(), self.reader.file_type):
                name = self.reader.read_name_by_filepath(self.file_ctrl.GetPath())
                self.name_ctrl.SetValue(f"({name[:20]})")
                return True

        if self.name_ctrl:
            self.name_ctrl.SetValue(__("(読取失敗)"))

        self.clear_data()
        return False

    def read_digest(self) -> None:
        """リーダー対象オブジェクトのハッシュを読み取る"""
        if (
            self.is_show_name
            and not self.is_save
            and validate_file(self.file_ctrl.GetPath(), self.reader.file_type)
        ):
            digest = self.reader.read_hash_by_filepath(self.file_ctrl.GetPath())
            if self.original_data and self.original_data.digest != digest:
                self.clear_data()

    @property
    def digest(self) -> Optional[str]:
        """ハッシュを読み取る"""
        if not self.is_save and validate_file(
            self.file_ctrl.GetPath(), self.reader.file_type
        ):
            return self.reader.read_hash_by_filepath(self.file_ctrl.GetPath())
        return None

    def clear_data(self) -> None:
        """リーダー対象オブジェクトをクリア"""
        if self.original_data is not None:
            self.data = None
            self.original_data = None

    def set_data(self, v: TBaseHashModel) -> None:
        """データを設定"""
        self.clear_data()
        self.original_data = v
        self.data = v.copy()

    def Enable(self, enable: bool) -> None:
        self.file_ctrl.Enable(enable)
        if not self.is_save:
            # 保存じゃなければ履歴ボタンを表示
            self.history_ctrl.Enable(enable)

    def set_color(self, color: wx.Colour) -> None:
        if self.title_ctrl:
            self.title_ctrl.SetBackgroundColour(color)
        self.file_ctrl.SetBackgroundColour(color)

        if self.spacer_ctrl:
            self.spacer_ctrl.SetBackgroundColour(color)

        if self.name_ctrl:
            self.name_ctrl.SetBackgroundColour(color)

        if self.name_blank_ctrl:
            self.name_blank_ctrl.SetBackgroundColour(color)

    def get_name_for_file(self) -> str:
        if not self.name_ctrl:
            return ""
        return get_clear_path(self.name_ctrl.GetValue()[1:-1])


class MFileDropTarget(wx.FileDropTarget):
    def __init__(self, parent: MFilePickerCtrl):
        self.parent = parent

        wx.FileDropTarget.__init__(self)

    def OnDropFiles(self, x, y, files):
        if validate_file(files[0], self.parent.reader.file_type):
            # 拡張子を許容してたらOK
            self.parent.file_ctrl.SetPath(files[0])

            if self.parent.paths and self.parent.file_choice_ctrl:
                for n in range(self.parent.file_choice_ctrl.GetSelection() + 1):
                    if len(self.parent.paths) <= n:
                        self.parent.paths.append("")
                self.parent.paths[self.parent.file_choice_ctrl.GetSelection()] = files[0]

            # ファイル変更処理
            self.parent.data = None
            self.parent.file_change_event(wx.FileDirPickerEvent())

            return True

        # アスタリスクOKの場合、フォルダの投入を許可する
        if os.path.isdir(files[0]) and self.parent.is_aster:
            # フォルダを投入された場合、フォルダ内に許容拡張子があれば、受け付ける
            child_file_name_exts = [os.path.splitext(filename) for filename in os.listdir(files[0])
                                        if os.path.isfile(os.path.join(files[0], filename))]
            for ft in self.parent.reader.file_exts:
                # 親の許容ファイルパス
                for child_file_name, child_file_ext in child_file_name_exts:
                    if child_file_ext[1:].lower() == ft:
                        # 子のファイル拡張子が許容拡張子である場合、アスタリスクを入れて許可する
                        astr_path = "{0}\\*.{1}".format(files[0], ft)
                        self.parent.file_ctrl.SetPath(astr_path)

                        # ファイル変更処理
                        if self.parent.file_change_event:
                            self.parent.file_change_event(wx.FileDirPickerEvent())

                        return True

        logger.warning(
            "{t}に入力されたファイル拡張子を受け付けられませんでした。{y}拡張子のファイルを入力してください。\n入力ファイルパス: {p}",
            decoration=MLogger.Decoration.BOX,
            t=self.parent.title,
            y=self.parent.reader.file_type.name.lower(),
            p=files[0],
        )

        # 許容拡張子外の場合、不許可
        return False


class MImagePickerCtrl(MFilePickerCtrl[ImageModel, ImageReader]):
    def __init__(
        self,
        parent: Any,
        frame: NotebookFrame,
        panel: NotebookPanel,
        title: str,
        key: Optional[str] = None,
        is_show_name: bool = False,
        name_spacer: int = 0,
        is_save: bool = False,
        is_aster = False,
        tooltip: str = "",
        file_change_event=None,
        file_choice_names: Optional[list[str]] = None,
    ) -> None:
        super().__init__(
            parent,
            frame,
            panel,
            ImageReader(),
            title,
            key,
            is_show_name,
            name_spacer,
            is_save,
            is_aster,
            tooltip,
            file_change_event,
            file_choice_names,
        )
