import os
import shutil
import sys
from datetime import datetime
from typing import Any, Optional

import numpy as np
import wx
import wx.lib.agw.cubecolourdialog as CCD
import yappi

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


from mlib.domain.exception import MApplicationException  # noqa: E402
from mlib.domain.logger import MLogger  # noqa: E402
from mlib.pmx.canvas import PmxCanvas, SyncSubCanvasWindow  # noqa: E402
from mlib.pmx.pmx_collection import PmxModel  # noqa: E402
from mlib.pmx.pmx_part import (  # noqa: E402
    Bone,
    Face,
    SphereMode,
    Texture,
    ToonSharing,
)
from mlib.pmx.pmx_writer import PmxWriter  # noqa: E402
from mlib.service.base_worker import BaseWorker  # noqa: E402
from mlib.interface.notebook_frame import NotebookFrame  # noqa: E402
from mlib.interface.notebook_panel import NotebookPanel  # noqa: E402
from mlib.interface.widgets.bezier_ctrl import BezierCtrl  # noqa: E402
from mlib.interface.widgets.console_ctrl import ConsoleCtrl  # noqa: E402
from mlib.interface.widgets.exec_btn_ctrl import ExecButton  # noqa: E402
from mlib.interface.widgets.file_ctrl import (  # noqa: E402
    MImagePickerCtrl,
    MPmxFilePickerCtrl,
    MVmdFilePickerCtrl,
)
from mlib.interface.widgets.float_slider_ctrl import FloatSliderCtrl  # noqa: E402
from mlib.interface.widgets.frame_slider_ctrl import FrameSliderCtrl  # noqa: E402
from mlib.interface.widgets.image_btn_ctrl import ImageButton  # noqa: E402
from mlib.interface.widgets.morph_ctrl import MorphChoiceCtrl  # noqa: E402
from mlib.interface.widgets.spin_ctrl import (  # noqa: E402
    WheelSpinCtrl,
    WheelSpinCtrlDouble,
)
from mlib.utils.file_utils import save_histories, separate_path  # noqa: E402
from mlib.vmd.vmd_collection import VmdMotion  # noqa: E402

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class FilePanel(NotebookPanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw):
        super().__init__(frame, tab_idx, *args, **kw)

        self._initialize_ui()

    def _initialize_ui(self) -> None:
        self.model_ctrl = MPmxFilePickerCtrl(
            self,
            self.frame,
            self,
            key="model_pmx",
            title="表示モデル",
            is_show_name=True,
            name_spacer=3,
            is_save=False,
            tooltip="PMXモデル",
            file_change_event=self.on_change_model_pmx,
        )
        self.model_ctrl.set_parent_sizer(self.root_sizer)
        # self.model_ctrl.set_color(wx.Colour("RED"))

        self.dress_ctrl = MPmxFilePickerCtrl(
            self,
            self.frame,
            self,
            key="dress_pmx",
            title="衣装モデル",
            is_show_name=True,
            name_spacer=3,
            is_save=False,
            tooltip="PMX衣装モデル",
            file_change_event=self.on_change_dress_pmx,
        )
        self.dress_ctrl.set_parent_sizer(self.root_sizer)

        self.motion_ctrl = MVmdFilePickerCtrl(
            self,
            self.frame,
            self,
            key="motion_vmd",
            title="表示モーション",
            is_show_name=True,
            name_spacer=1,
            is_save=False,
            tooltip="VMDモーションデータ",
            file_change_event=self.on_change_motion,
        )
        self.motion_ctrl.set_parent_sizer(self.root_sizer)

        self.output_pmx_ctrl = MPmxFilePickerCtrl(
            self,
            self.frame,
            self,
            title="出力先",
            is_show_name=False,
            is_save=True,
            tooltip="実際は動いてないよ",
        )
        self.output_pmx_ctrl.set_parent_sizer(self.root_sizer)

        self.image_ctrl = MImagePickerCtrl(
            self,
            self.frame,
            self,
            key="image",
            title="画像パス",
            is_show_name=False,
            is_save=False,
            tooltip="画像パスの説明",
        )
        self.image_ctrl.set_parent_sizer(self.root_sizer)

        self.exec_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.exec_btn_ctrl = ExecButton(
            self, self, "実行", "実行中", self.exec, 200, "実行ボタンだよ"
        )
        self.exec_btn_ctrl.exec_worker = SaveWorker(self, self.exec_result)
        self.exec_btn_sizer.Add(self.exec_btn_ctrl, 0, wx.ALL, 3)
        self.root_sizer.Add(self.exec_btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 5)

        self.console_ctrl = ConsoleCtrl(self, self.frame, self, rows=300)
        self.console_ctrl.set_parent_sizer(self.root_sizer)

        self.root_sizer.Add(wx.StaticLine(self, wx.ID_ANY), wx.GROW)

    def exec(self, event: wx.Event) -> None:
        if not (self.model_ctrl.data and self.dress_ctrl.data):
            return

        if self.exec_btn_ctrl.exec_worker:
            self.exec_btn_ctrl.exec_worker.start()

    def exec_result(self, result: bool, data: Optional[Any], elapsed_time: str) -> None:
        logger.info(self.output_pmx_ctrl.path, decoration=MLogger.Decoration.BOX)
        self.frame.on_sound()

    def on_change_model_pmx(self, event: wx.Event) -> None:
        self.model_ctrl.unwrap()
        if self.model_ctrl.read_name():
            self.model_ctrl.read_digest()
            dir_path, file_name, file_ext = separate_path(self.model_ctrl.path)
            model_path = os.path.join(
                dir_path,
                f"{datetime.now():%Y%m%d_%H%M%S}",
                f"{file_name}_{self.model_ctrl.get_name_for_file()}_{datetime.now():%Y%m%d_%H%M%S}{file_ext}",
            )
            self.output_pmx_ctrl.path = model_path

    def on_change_dress_pmx(self, event: wx.Event) -> None:
        self.dress_ctrl.unwrap()
        if self.dress_ctrl.read_name():
            self.dress_ctrl.read_digest()

    def on_change_motion(self, event: wx.Event) -> None:
        self.motion_ctrl.unwrap()
        if self.motion_ctrl.read_name():
            self.motion_ctrl.read_digest()

    def Enable(self, enable: bool) -> None:
        self.model_ctrl.Enable(enable)
        self.dress_ctrl.Enable(enable)
        self.motion_ctrl.Enable(enable)


class PmxLoadWorker(BaseWorker):
    def __init__(self, panel: NotebookPanel, result_event: wx.Event) -> None:
        super().__init__(panel, result_event)

    def thread_execute(self) -> None:
        file_panel: FilePanel = self.panel
        model: Optional[PmxModel] = None
        dress: Optional[PmxModel] = None
        motion: Optional[VmdMotion] = None

        model = self.load_model()

        if not file_panel.dress_ctrl.data and file_panel.dress_ctrl.valid():
            dress = file_panel.dress_ctrl.reader.read_by_filepath(
                file_panel.dress_ctrl.path
            )
            PmxWriter(
                dress, "C:/MMD/mmd_base/tests/resources/result.pmx", include_system=True
            ).save()
        elif file_panel.dress_ctrl.data:
            dress = file_panel.dress_ctrl.data
        else:
            dress = PmxModel()

        if not file_panel.motion_ctrl.data and file_panel.motion_ctrl.valid():
            motion = file_panel.motion_ctrl.reader.read_by_filepath(
                file_panel.motion_ctrl.path
            )
        elif file_panel.motion_ctrl.data:
            motion = file_panel.motion_ctrl.data
        else:
            motion = VmdMotion("empty")

        self.result_data = (model, dress, motion)

    def load_model(self) -> PmxModel:
        file_panel: FilePanel = self.panel
        model: Optional[PmxModel] = None

        if not file_panel.model_ctrl.data and file_panel.model_ctrl.valid():
            model = file_panel.model_ctrl.reader.read_by_filepath(
                file_panel.model_ctrl.path
            )

            if "首" not in model.bones:
                raise MApplicationException("{b}ボーン不足", b="首")
        elif file_panel.model_ctrl.data:
            model = file_panel.model_ctrl.data
        else:
            model = PmxModel()

        return model

    def output_log(self):
        pass


class SaveWorker(BaseWorker):
    def __init__(self, panel: NotebookPanel, result_event: wx.Event) -> None:
        super().__init__(panel, result_event)

    def output_log(self):
        pass

    def thread_execute(self):
        file_panel: FilePanel = self.panel

        if not (file_panel.model_ctrl.data and file_panel.dress_ctrl.data):
            return

        os.makedirs(os.path.dirname(file_panel.output_pmx_ctrl.path), exist_ok=True)
        model: PmxModel = file_panel.model_ctrl.data
        dress: PmxModel = file_panel.dress_ctrl.data
        dress_model = PmxModel(file_panel.output_pmx_ctrl.path)
        dress_model.comment = model.comment + "\n------------------\n" + dress.comment
        dress_model.initialize_display_slots()

        bone_map: dict[int, dict[str, list[str]]] = {}

        # 最初にルートを追加する
        root_bone = Bone(name=Bone.SYSTEM_ROOT_NAME, index=-1)
        root_bone.parent_index = -9
        root_bone.is_system = True
        dress_model.bones.append(root_bone, is_positive_index=False)
        bone_map[-1] = {
            "parent": [Bone.SYSTEM_ROOT_NAME],
            "tail": [Bone.SYSTEM_ROOT_NAME],
            "effect": [Bone.SYSTEM_ROOT_NAME],
            "ik_target": [Bone.SYSTEM_ROOT_NAME],
            "ik_link": [],
        }

        model_bone_map: dict[int, int] = {-1: -1}
        dress_bone_map: dict[int, int] = {-1: -1}

        for bone in model.bones.writable():
            if bone.name in dress_model.bones:
                continue

            for dress_bone in dress.bones.writable():
                if (
                    0 <= dress_bone.tail_index
                    and dress_bone.name not in model.bones
                    and dress.bones[dress_bone.tail_index].name == bone.name
                ):
                    # 衣装だけのボーンが表示先が人物のボーンに繋がってる場合、その前に追加しておく
                    copy_bone = dress_bone.copy()
                    copy_bone.index = len(dress_model.bones.writable())
                    bone_map[copy_bone.index] = {
                        "parent": [dress.bones[dress_bone.parent_index].name],
                        "tail": [dress.bones[dress_bone.tail_index].name],
                        "effect": [dress.bones[dress_bone.effect_index].name],
                        "ik_target": [
                            (
                                dress.bones[dress_bone.ik.bone_index].name
                                if dress_bone.ik
                                else Bone.SYSTEM_ROOT_NAME
                            )
                        ],
                        "ik_link": (
                            [
                                dress.bones[link.bone_index].name
                                for link in dress_bone.ik.links
                            ]
                            if dress_bone.ik
                            else []
                        ),
                    }
                    dress_model.bones.append(copy_bone, is_sort=False)
                    dress_bone_map[bone.index] = copy_bone.index

            copy_bone = bone.copy()
            copy_bone.index = len(dress_model.bones.writable())
            bone_map[copy_bone.index] = {
                "parent": [model.bones[bone.parent_index].name],
                "tail": [model.bones[bone.tail_index].name],
                "effect": [model.bones[bone.effect_index].name],
                "ik_target": [
                    (
                        model.bones[bone.ik.bone_index].name
                        if bone.ik
                        else Bone.SYSTEM_ROOT_NAME
                    )
                ],
                "ik_link": (
                    [model.bones[link.bone_index].name for link in bone.ik.links]
                    if bone.ik
                    else []
                ),
            }
            dress_model.bones.append(copy_bone, is_sort=False)
            model_bone_map[bone.index] = copy_bone.index

        for bone in dress.bones.writable():
            if bone.name in dress_model.bones:
                # 既に登録済みのボーンは追加しない
                continue
            copy_bone = bone.copy()
            copy_bone.index = len(dress_model.bones.writable())
            bone_map[copy_bone.index] = {
                "parent": [dress.bones[bone.parent_index].name],
                "tail": [dress.bones[bone.tail_index].name],
                "effect": [dress.bones[bone.effect_index].name],
                "ik_target": [
                    (
                        dress.bones[bone.ik.bone_index].name
                        if bone.ik
                        else Bone.SYSTEM_ROOT_NAME
                    )
                ],
                "ik_link": (
                    [dress.bones[link.bone_index].name for link in bone.ik.links]
                    if bone.ik
                    else []
                ),
            }
            dress_model.bones.append(copy_bone, is_sort=False)
            dress_bone_map[bone.index] = copy_bone.index

        for bone in dress_model.bones:
            bone_setting = bone_map[bone.index]
            bone.parent_index = dress_model.bones[bone_setting["parent"][0]].index
            bone.tail_index = dress_model.bones[bone_setting["tail"][0]].index
            bone.effect_index = dress_model.bones[bone_setting["effect"][0]].index
            if bone.is_ik and bone.ik:
                bone.ik.bone_index = dress_model.bones[
                    bone_setting["ik_target"][0]
                ].index
                for n in range(len(bone.ik.links)):
                    bone.ik.links[n].bone_index = dress_model.bones[
                        bone_setting["ik_link"][n]
                    ].index

        model_vertex_map: dict[int, int] = {-1: -1}
        dress_vertex_map: dict[int, int] = {-1: -1}

        model_material_map: dict[int, int] = {-1: -1}
        dress_material_map: dict[int, int] = {-1: -1}

        prev_faces_count = 0
        for material in model.materials:
            if "01_Onepiece_02" in material.name:
                prev_faces_count += material.vertices_count // 3
                continue
            copy_material = material.copy()
            copy_material.index = len(dress_model.materials)

            if 0 <= material.texture_index:
                copy_texture = self.copy_texture(
                    dress_model, model.textures[material.texture_index], model.path
                )
                copy_material.texture_index = copy_texture.index

            if (
                material.toon_sharing_flg == ToonSharing.INDIVIDUAL
                and 0 <= material.toon_texture_index
            ):
                copy_texture = self.copy_texture(
                    dress_model, model.textures[material.toon_texture_index], model.path
                )
                copy_material.toon_texture_index = copy_texture.index

            if (
                material.sphere_mode != SphereMode.INVALID
                and 0 < material.sphere_texture_index
            ):
                copy_texture = self.copy_texture(
                    dress_model,
                    model.textures[material.sphere_texture_index],
                    model.path,
                )
                copy_material.sphere_texture_index = copy_texture.index

            dress_model.materials.append(copy_material, is_sort=False)
            model_material_map[material.index] = copy_material.index

            for face_index in range(
                prev_faces_count, prev_faces_count + copy_material.vertices_count // 3
            ):
                faces = []
                for vertex_index in model.faces[face_index].vertices:
                    if vertex_index not in model_vertex_map:
                        copy_vertex = model.vertices[vertex_index].copy()
                        copy_vertex.index = -1
                        copy_vertex.deform.indexes = np.vectorize(model_bone_map.get)(
                            copy_vertex.deform.indexes
                        )
                        faces.append(len(dress_model.vertices))
                        model_vertex_map[vertex_index] = len(dress_model.vertices)
                        dress_model.vertices.append(copy_vertex, is_sort=False)
                    else:
                        faces.append(model_vertex_map[vertex_index])
                dress_model.faces.append(
                    Face(
                        vertex_index0=faces[0],
                        vertex_index1=faces[1],
                        vertex_index2=faces[2],
                    ),
                    is_sort=False,
                )

            prev_faces_count += material.vertices_count // 3

        prev_faces_count = 0
        for material in dress.materials:
            if "腕" in material.name:
                prev_faces_count += material.vertices_count // 3
                continue
            copy_material = material.copy()
            copy_material.name = f"Cos:{copy_material.name}"
            copy_material.index = len(dress_model.materials)

            if 0 <= material.texture_index:
                copy_texture = self.copy_texture(
                    dress_model, dress.textures[material.texture_index], dress.path
                )
                copy_material.texture_index = copy_texture.index

            if (
                material.toon_sharing_flg == ToonSharing.INDIVIDUAL
                and 0 <= material.toon_texture_index
            ):
                copy_texture = self.copy_texture(
                    dress_model, dress.textures[material.toon_texture_index], dress.path
                )
                copy_material.toon_texture_index = copy_texture.index

            if (
                material.sphere_mode != SphereMode.INVALID
                and 0 < material.sphere_texture_index
            ):
                copy_texture = self.copy_texture(
                    dress_model,
                    dress.textures[material.sphere_texture_index],
                    dress.path,
                )
                copy_material.sphere_texture_index = copy_texture.index

            dress_model.materials.append(copy_material, is_sort=False)
            dress_material_map[material.index] = copy_material.index

            for face_index in range(
                prev_faces_count, prev_faces_count + copy_material.vertices_count // 3
            ):
                faces = []
                for vertex_index in dress.faces[face_index].vertices:
                    if vertex_index not in dress_vertex_map:
                        copy_vertex = dress.vertices[vertex_index].copy()
                        copy_vertex.index = -1
                        copy_vertex.deform.indexes = np.vectorize(model_bone_map.get)(
                            copy_vertex.deform.indexes
                        )
                        faces.append(len(dress_model.vertices))
                        dress_vertex_map[vertex_index] = len(dress_model.vertices)
                        dress_model.vertices.append(copy_vertex, is_sort=False)
                    else:
                        faces.append(dress_vertex_map[vertex_index])
                dress_model.faces.append(
                    Face(
                        vertex_index0=faces[0],
                        vertex_index1=faces[1],
                        vertex_index2=faces[2],
                    ),
                    is_sort=False,
                )

            prev_faces_count += material.vertices_count // 3

        PmxWriter(dress_model, file_panel.output_pmx_ctrl.path).save()

        self.result_data = True

    def copy_texture(
        self, dest_model: PmxModel, texture: Texture, src_model_path: str
    ) -> Texture:
        copy_texture = texture.copy()
        copy_texture.index = len(dest_model.textures)
        texture_path = os.path.abspath(
            os.path.join(os.path.dirname(src_model_path), copy_texture.name)
        )
        if (
            copy_texture.name
            and os.path.exists(texture_path)
            and os.path.isfile(texture_path)
        ):
            new_texture_path = os.path.join(
                os.path.dirname(dest_model.path), copy_texture.name
            )
            os.makedirs(os.path.dirname(new_texture_path), exist_ok=True)
            shutil.copyfile(texture_path, new_texture_path)
        copy_texture.index = len(dest_model.textures)
        dest_model.textures.append(copy_texture, is_sort=False)

        return copy_texture


class ConfigPanel(NotebookPanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw):
        super().__init__(frame, tab_idx, *args, **kw)
        self.canvas_width_ratio = 0.5
        self.canvas_height_ratio = 1.0
        self.canvas = PmxCanvas(self, False)

        self._initialize_ui()
        self._initialize_event()

    def get_canvas_size(self) -> wx.Size:
        w, h = self.frame.GetClientSize()
        canvas_width = w * self.canvas_width_ratio
        if canvas_width % 2 != 0:
            # 2で割り切れる値にする
            canvas_width += 1
        canvas_height = h * self.canvas_height_ratio
        return wx.Size(int(canvas_width), int(canvas_height))

    def _initialize_ui(self) -> None:
        self.config_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.config_sizer.Add(self.canvas, 0, wx.EXPAND | wx.ALL, 0)

        self.scrolled_window = wx.ScrolledWindow(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL,
        )
        self.scrolled_window.SetScrollRate(5, 5)

        self.btn_sizer = wx.BoxSizer(wx.VERTICAL)

        # キーフレ
        self.frame_ctrl = WheelSpinCtrl(
            self.scrolled_window,
            change_event=self.on_change_frame,
            initial=0,
            min=-100,
            max=10000,
            size=wx.Size(80, -1),
        )
        self.btn_sizer.Add(self.frame_ctrl, 0, wx.ALL, 5)

        # キーフレ
        self.double_ctrl = WheelSpinCtrlDouble(
            self.scrolled_window,
            change_event=self.on_change_frame,
            initial=0,
            min=-100,
            max=10000,
            inc=0.01,
            size=wx.Size(80, -1),
        )
        self.btn_sizer.Add(self.double_ctrl, 0, wx.ALL, 5)

        # 再生
        self.play_btn = wx.Button(
            self.scrolled_window,
            wx.ID_ANY,
            "Play",
            wx.DefaultPosition,
            wx.Size(100, 50),
        )
        self.btn_sizer.Add(self.play_btn, 0, wx.ALL, 5)

        # スライダー
        self.float_slider = FloatSliderCtrl(
            self.scrolled_window,
            value=0.5,
            min_value=0,
            max_value=3,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            position=wx.DefaultPosition,
            size=wx.Size(200, -1),
            tooltip="スライダーツールチップ",
        )
        self.btn_sizer.Add(self.float_slider.sizer, 0, wx.ALL, 0)

        # スライダー
        self.frame_slider = FrameSliderCtrl(
            self.scrolled_window,
            border=3,
            position=wx.DefaultPosition,
            size=wx.Size(200, -1),
            tooltip="キーフレスライダー",
        )
        self.btn_sizer.Add(self.frame_slider.sizer, 0, wx.ALL, 0)

        # 選択色
        self.color_ctrl = wx.TextCtrl(
            self.scrolled_window,
            wx.ID_ANY,
            f"{self.canvas.color[0]},{self.canvas.color[1]},{self.canvas.color[2]}",
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS,
        )
        self.btn_sizer.Add(self.color_ctrl, 0, wx.ALL, 0)

        self.color_panel = wx.Panel(self.scrolled_window, size=(50, 50))
        self.color_panel.SetBackgroundColour(wx.Colour(*self.canvas.color))
        self.btn_sizer.Add(self.color_panel, 0, wx.ALL, 0)

        self.palette_btn_ctrl = ImageButton(
            self.scrolled_window,
            "C:/MMD/pmx_dressup/src/resources/icon/palette.png",
            wx.Size(10, 10),
            self.on_click_color_picker,
            "カラーツールチップ",
        )
        self.btn_sizer.Add(self.palette_btn_ctrl, 0, wx.ALL, 0)

        # 再生
        self.capture_btn = wx.Button(
            self.scrolled_window,
            wx.ID_ANY,
            "Capture",
            wx.DefaultPosition,
            wx.Size(100, 50),
        )
        self.btn_sizer.Add(self.capture_btn, 0, wx.ALL, 5)
        self.scrolled_window.SetSizer(self.btn_sizer)

        # 顔アップ
        self.sub_window_btn = wx.Button(
            self.scrolled_window,
            wx.ID_ANY,
            "サブウィンドウ",
            wx.DefaultPosition,
            wx.Size(100, 50),
        )
        self.btn_sizer.Add(self.sub_window_btn, 0, wx.ALL, 5)

        # ベジェ
        self.bezier_ctrl = BezierCtrl(
            self.frame, self.scrolled_window, wx.Size(150, 150)
        )
        self.btn_sizer.Add(self.bezier_ctrl.sizer, 0, wx.ALL, 5)

        # モーフ選択肢
        self.morph_choice_ctrl = MorphChoiceCtrl(
            self, self.scrolled_window, "モーフ", 150, "モーフ選べるよ"
        )
        self.morph_choice_ctrl.initialize(["あ", "い", "う", "え", "お"])
        self.btn_sizer.Add(self.morph_choice_ctrl.sizer, 0, wx.ALL, 5)

        self.config_sizer.Add(
            self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 0
        )

        self.root_sizer.Add(self.config_sizer, 0, wx.ALL, 0)
        self.scrolled_window.Layout()
        self.scrolled_window.Fit()
        self.Layout()

        self.on_resize(wx.EVT_SIZE)

    def _initialize_event(self) -> None:
        self.play_btn.Bind(wx.EVT_BUTTON, self.on_play)
        self.capture_btn.Bind(wx.EVT_BUTTON, self.canvas.on_capture)
        self.canvas.color_changed_event = self.on_change_color
        self.color_panel.Bind(wx.EVT_LEFT_DOWN, self.on_click_color_picker)
        self.sub_window_btn.Bind(wx.EVT_BUTTON, self.frame.on_show_sub_window)

    def on_click_color_picker(self, event: wx.Event):
        data = wx.ColourData()
        data.SetColour(self.color_panel.GetBackgroundColour())
        with CCD.CubeColourDialog(self, data) as color_dialog:
            if color_dialog.ShowModal() == wx.ID_CANCEL:
                return

            self.color_panel.SetBackgroundColour(data.GetColour())
            self.color_panel.Refresh()

    def on_change_color(self):
        self.color_ctrl.ChangeValue(
            f"{self.canvas.color[0]},{self.canvas.color[1]},{self.canvas.color[2]}"
        )
        self.color_panel.SetBackgroundColour(wx.Colour(*self.canvas.color))
        self.color_panel.Refresh()

    def on_play(self, event: wx.Event) -> None:
        if self.canvas.playing:
            self.stop_play()
            yappi.stop()

            columns = {
                0: ("name", 100),
                1: ("ncall", 10),
                2: ("tsub", 8),
                3: ("ttot", 8),
                4: ("tavg", 8),
            }

            threads = yappi.get_thread_stats()
            for thread in threads:
                print(
                    "Function stats for (%s) (%d)" % (thread.name, thread.id)
                )  # it is the Thread.__class__.__name__

                yappi.get_func_stats(ctx_id=thread.id).sort("ttot").print_all(
                    columns=columns
                )

                print("--------------------------")

                yappi.get_func_stats(ctx_id=thread.id).sort("tavg").print_all(
                    columns=columns
                )

        else:
            yappi.set_clock_type("cpu")
            yappi.start()

            self.start_play()
        self.canvas.on_play(event)

    @property
    def fno(self) -> int:
        return self.frame_ctrl.GetValue()

    @fno.setter
    def fno(self, v: int) -> None:
        self.frame_ctrl.SetValue(v)

    @property
    def is_calc_ik(self) -> bool:
        return True

    def start_play(self) -> None:
        pass

    def stop_play(self) -> None:
        self.play_btn.SetLabel("Play")

    def on_change_frame(self, event: wx.Event) -> None:
        self.fno = self.frame_ctrl.GetValue()
        self.canvas.change_motion(event)

    def on_resize(self, event: wx.Event):
        w, h = self.frame.GetClientSize()
        size = self.get_canvas_size()

        self.scrolled_window.SetPosition(wx.Point(size.width, 0))
        self.scrolled_window.SetSize(wx.Size(w - size.width, h))


class TestFrame(NotebookFrame):
    def __init__(self, app) -> None:
        super().__init__(
            app,
            history_keys=["model_pmx", "dress_pmx", "motion_vmd", "image"],
            title="Mu Test Frame",
            size=wx.Size(1000, 800),
            is_saving=False,
        )
        # ファイルタブ
        self.file_panel = FilePanel(self, 0)
        self.notebook.AddPage(self.file_panel, __("ファイル"), False)

        # 設定タブ
        self.config_panel = ConfigPanel(self, 1)
        self.notebook.AddPage(self.config_panel, __("設定"), False)

        self.sub_window_size = wx.Size(300, 300)
        self.sub_window: Optional[SyncSubCanvasWindow] = None

        self.worker = PmxLoadWorker(self.file_panel, self.on_result)

    def on_change_tab(self, event: wx.Event) -> None:
        if self.notebook.GetSelection() == self.config_panel.tab_idx:
            self.notebook.ChangeSelection(self.file_panel.tab_idx)
            if not self.worker.started:
                if not self.file_panel.model_ctrl.valid():
                    logger.warning(
                        "モデル欄に有効なパスが設定されていない為、タブ遷移を中断します。"
                    )
                    return
                if not self.file_panel.dress_ctrl.valid():
                    logger.warning(
                        "衣装欄に有効なパスが設定されていない為、タブ遷移を中断します。"
                    )
                    return
                if (
                    not self.file_panel.model_ctrl.data
                    or not self.file_panel.dress_ctrl.data
                    or not self.file_panel.motion_ctrl.data
                ):
                    # 設定タブにうつった時に読み込む
                    self.config_panel.canvas.clear_model_set()
                    self.save_histories()

                    self.worker.start()
                else:
                    # 既に読み取りが完了していたらそのまま表示
                    self.notebook.ChangeSelection(self.config_panel.tab_idx)

    def save_histories(self) -> None:
        self.file_panel.model_ctrl.save_path()
        self.file_panel.dress_ctrl.save_path()
        self.file_panel.motion_ctrl.save_path()
        self.file_panel.image_ctrl.save_path()

        save_histories(self.histories)

    def on_result(self, result: bool, data: Optional[Any], elapsed_time: str) -> None:
        self.file_panel.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data):
            return

        data1, data2, data3 = data
        model: PmxModel = data1
        dress: PmxModel = data2
        motion: VmdMotion = data3
        self.file_panel.model_ctrl.set_data(model)
        self.file_panel.dress_ctrl.set_data(dress)
        self.file_panel.motion_ctrl.set_data(motion)

        if not (
            self.file_panel.motion_ctrl.data
            and self.file_panel.model_ctrl.data
            and self.file_panel.dress_ctrl.data
        ):
            return

        # logger.info("上半身3削除")
        # model.remove_bone("上半身3")
        # logger.info("上半身3削除完了")

        dress_motion = self.file_panel.motion_ctrl.data.copy()

        # bf = VmdBoneFrame(0, "右腕")
        # bf.local_position = MVector3D(0, 1, 0)
        # bf.local_rotation = MQuaternion.from_euler_degrees(0, 20, 0)
        # dress_motion.bones["右腕"].append(bf)

        # dress_motion.bones.clear()
        # dress_matrixes = dress_motion.bones.get_matrix_by_indexes([0], ["左肩"], dress, is_calc_ik=False)
        # left_shoulder_position = dress_matrixes[0, "左肩"].position

        # bf2 = VmdBoneFrame(0, "右肩")
        # bf2.local_scale = MVector3D(0, 0.5, 0.5)
        # dress_motion.bones["右肩"].append(bf2)

        # dress_motion.bones.clear()
        # dress_scaled_matrixes = dress_motion.bones.get_matrix_by_indexes([0], ["左肩"], dress, is_calc_ik=False)
        # scaled_left_shoulder_position = dress_scaled_matrixes[0, "左肩"].position
        # scale_diff = left_shoulder_position - scaled_left_shoulder_position

        # bf = VmdBoneFrame(0, "左肩C")
        # # bf.local_scale = MVector3D(0, 1.5, 1.5)
        # bf.position2 = scale_diff
        # dress_motion.bones["左肩C"].append(bf)

        # bf = VmdBoneFrame(0, "左肩")
        # # bf.local_scale = MVector3D(0, 1.5, 1.5)
        # bf.position2 = scale_diff
        # dress_motion.bones["左肩"].append(bf)

        # bf = VmdBoneFrame(0, "左肩")
        # bf.local_scale = MVector3D(0, 1.5, 1.5)
        # # bf.local_position = MVector3D(0, 1, 0)
        # dress_motion.bones["左肩"].append(bf)

        # bf = VmdBoneFrame(0, "左腕")
        # bf.local_scale = MVector3D(0, -0.5, -0.5)
        # dress_motion.bones["左腕"].append(bf)

        # bf = VmdBoneFrame(0, "左ひじ")
        # bf.local_scale = MVector3D(0, 1.2, 1.2)
        # dress_motion.bones["左ひじ"].append(bf)

        # bf = VmdBoneFrame(0, "頭")
        # bf.local_scale = MVector3D(0, 1, 1)
        # dress_motion.bones["頭"].append(bf)

        # # -------------------
        # # モーフ追加
        # morph_bone_name = "上半身"
        # morph = Morph(name=morph_bone_name)
        # morph.morph_type = MorphType.BONE
        # offset1 = BoneMorphOffset(
        #     # dress.bones[morph_bone_name].index, local_scale=MVector3D(1, 0, 0)
        #     dress.bones[morph_bone_name].index,
        #     qq=MQuaternion.from_euler_degrees(90, 0, 0),
        # )
        # morph.offsets.append(offset1)
        # offset2 = BoneMorphOffset(
        #     dress.bones["左腕捩"].index, local_scale=MVector3D(1, 0, 0)
        # )
        # morph.offsets.append(offset2)
        # dress.morphs.append(morph)

        # dress_motion.morphs[morph_bone_name].append(
        #     VmdMorphFrame(0, morph_bone_name, 1)
        # )
        # -------------------

        # dress.update_vertices_by_bone()

        # # モーフ追加
        # morph2 = Morph(name="左足頂点")
        # morph2.morph_type = MorphType.AFTER_VERTEX
        # for vertex_index in dress.vertices_by_bones[dress.bones["左足"].index]:
        #     offset2 = VertexMorphOffset(vertex_index, position=MVector3D(2, 0, 0))
        #     morph2.offsets.append(offset2)
        # dress.morphs.append(morph2)

        # dress_motion.morphs["左足頂点"].append(VmdMorphFrame(0, "左足頂点", 1))

        # # モーフ追加
        # morph = Morph(name="上半身")
        # morph.morph_type = MorphType.BONE
        # offset = BoneMorphOffset(dress.bones["上半身"].index, local_qq=MQuaternion.from_euler_degrees(0, 30, 0))
        # morph.offsets.append(offset)
        # dress.morphs.append(morph)

        # dress_motion.morphs["上半身"].append(VmdMorphFrame(0, "上半身", 1))

        try:
            self.config_panel.frame_slider.SetMaxFrameNo(dress_motion.max_fno)
            self.config_panel.frame_slider.SetKeyFrames(
                [f for f in range(0, dress_motion.max_fno, 100)]
            )
            self.config_panel.canvas.set_context()
            self.config_panel.canvas.append_model_set(
                self.file_panel.model_ctrl.data,
                self.file_panel.motion_ctrl.data.copy(),
                0.5,
            )
            self.config_panel.canvas.append_model_set(dress, dress_motion, 0.7)
            self.config_panel.canvas.animations[0].selected_bone_indexes = [
                bone.index
                for bone in self.file_panel.model_ctrl.data.bones
                if bone.name in ["右肩", "右肩C", "右腕", "右腕捩"]
            ]
            self.config_panel.canvas.animations[1].selected_bone_indexes = [
                bone.index
                for bone in dress.bones
                if bone.name in ["右肩", "右肩C", "右腕", "右腕捩"]
            ]
            self.config_panel.canvas.Refresh()
            self.notebook.ChangeSelection(self.config_panel.tab_idx)
        except Exception:
            logger.critical("モデル描画初期化処理失敗")

    def on_show_sub_window(self, event: wx.Event) -> None:
        self.create_sub_window()

        if self.sub_window:
            if not self.sub_window.IsShown():
                self.sub_window.Show()
                # self.sub_window.panel.canvas.Refresh()
            elif self.sub_window.IsShown():
                self.sub_window.Hide()
        event.Skip()

    def create_sub_window(self) -> None:
        model: Optional[PmxModel] = self.file_panel.model_ctrl.data
        if not self.sub_window and model:
            self.sub_window = SyncSubCanvasWindow(
                self,
                self.config_panel.canvas,
                "サブウィンドウ",
                self.sub_window_size,
                [model.name],
                [model.bones.names],
            )
            frame_x, frame_y = self.GetPosition()
            self.sub_window.SetPosition(
                wx.Point(max(0, frame_x - self.sub_window_size.x - 10), max(0, frame_y))
            )


class MuApp(wx.App):
    def __init__(
        self, redirect=False, filename=None, useBestVisual=False, clearSigInt=True
    ) -> None:
        super().__init__(redirect, filename, useBestVisual, clearSigInt)
        self.frame = TestFrame(self)
        self.frame.Show()


if __name__ == "__main__":
    MLogger.initialize(
        lang="en",
        root_dir=os.path.join(os.path.dirname(__file__), "..", "mlib"),
        version_name="1.00.00",
        level=10,
        is_out_log=True,
    )

    app = MuApp()
    app.MainLoop()
