import cProfile
import os
import sys
from multiprocessing import freeze_support

import wx

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mlib.domain.logger import MLogger  # noqa: E402
from mlib.pmx.canvas import PmxCanvas  # noqa: E402
from mlib.pmx.pmx_reader import PmxReader  # noqa: E402
from mlib.interface.notebook_frame import NotebookFrame  # noqa: E402
from mlib.interface.notebook_panel import NotebookPanel  # noqa: E402
from mlib.interface.widgets.frame_slider_ctrl import FrameSliderCtrl  # noqa: E402
from mlib.interface.widgets.spin_ctrl import WheelSpinCtrl  # noqa: E402
from mlib.vmd.vmd_reader import VmdReader  # noqa: E402

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text

import line_profiler

profile = line_profiler.LineProfiler()

# 全体プロファイル
# python -m cProfile -s cumtime crumb\profile_canvas.py
#
# 行プロファイル
#
# import line_profiler
# profile = line_profiler.LineProfiler()
#
# kernprof -l crumb\profile_canvas.py
# python -m line_profiler profile_canvas.py.lprof


class ConfigPanel(NotebookPanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw):
        super().__init__(frame, tab_idx, *args, **kw)
        self.canvas_width_ratio = 0.5
        self.canvas_height_ratio = 1.0
        self.canvas = PmxCanvas(self, False)

        self._initialize_ui()
        self._initialize_event()

        self.profiler = cProfile.Profile()
        self.profiler.enable()

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

        # 再生
        self.play_btn = wx.Button(
            self.scrolled_window,
            wx.ID_ANY,
            "Play",
            wx.DefaultPosition,
            wx.Size(100, 50),
        )
        self.btn_sizer.Add(self.play_btn, 0, wx.ALL, 5)

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

        # スライダー
        self.frame_slider = FrameSliderCtrl(
            self.scrolled_window,
            border=3,
            position=wx.DefaultPosition,
            size=wx.Size(200, -1),
            tooltip="キーフレスライダー",
        )
        self.btn_sizer.Add(self.frame_slider.sizer, 0, wx.ALL, 0)

        # Close
        self.close_btn = wx.Button(
            self.scrolled_window,
            wx.ID_ANY,
            "Close",
            wx.DefaultPosition,
            wx.Size(100, 50),
        )
        self.btn_sizer.Add(self.close_btn, 0, wx.ALL, 5)

        self.scrolled_window.SetSizer(self.btn_sizer)
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
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)

    def on_close(self, event: wx.Event) -> None:
        self.profiler.disable()
        self.profiler.dump_stats("profile_canvas.prof")
        self.frame.Close()

    def on_play(self, event: wx.Event) -> None:
        if self.canvas.playing:
            self.stop_play()
            # yappi.stop()

            # columns = {
            #     0: ("name", 100),
            #     1: ("ncall", 10),
            #     2: ("tsub", 8),
            #     3: ("ttot", 8),
            #     4: ("tavg", 8),
            # }

            # threads = yappi.get_thread_stats()
            # for thread in threads:
            #     print(
            #         "Function stats for (%s) (%d)" % (thread.name, thread.id)
            #     )  # it is the Thread.__class__.__name__
            #     yappi.get_func_stats(ctx_id=thread.id).sort("tavg").print_all(
            #         columns=columns
            #     )
        else:
            # yappi.set_clock_type("cpu")  # Use set_clock_type("wall") for wall time
            # yappi.start()
            self.start_play()
        self.canvas.on_play(event)

    @property
    def fno(self) -> int:
        return self.frame_ctrl.GetValue()

    @fno.setter
    def fno(self, v: int) -> None:
        self.frame_ctrl.SetValue(v)

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


class ProfileFrame(NotebookFrame):
    def __init__(self, app) -> None:
        super().__init__(
            app,
            history_keys=[],
            title="Mu Test Frame",
            size=wx.Size(1000, 800),
            is_saving=False,
        )

        self.pmx_data = PmxReader().read_by_filepath(
            "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/どっと式初音ミク_ハニーウィップ_ver.2.01/どっと式初音ミク_ハニーウィップ.pmx"
        )
        self.vmd_data = VmdReader().read_by_filepath(
            "D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/日常動作/シャイニングミラクル グレイ/シャイニングミラクル_バーバラ.vmd"
        )

        # 設定タブ
        self.config_panel = ConfigPanel(self, 1)
        self.notebook.AddPage(self.config_panel, __("設定"), False)

        try:
            self.config_panel.frame_slider.SetMaxFrameNo(self.vmd_data.max_fno)
            self.config_panel.frame_slider.SetKeyFrames(
                [f for f in range(0, self.vmd_data.max_fno, 100)]
            )
            self.config_panel.canvas.set_context()
            self.config_panel.canvas.append_model_set(
                self.pmx_data,
                self.vmd_data,
                0.2,
            )
            self.config_panel.canvas.Refresh()
        except Exception:
            logger.critical("モデル描画初期化処理失敗")


class MuApp(wx.App):
    def __init__(
        self, redirect=False, filename=None, useBestVisual=False, clearSigInt=True
    ) -> None:
        super().__init__(redirect, filename, useBestVisual, clearSigInt)
        self.frame = ProfileFrame(self)
        self.frame.Show()


if __name__ == "__main__":
    freeze_support()

    MLogger.initialize(
        lang="en",
        root_dir=os.path.join(os.path.dirname(__file__), "..", "mlib"),
        version_name="1.00.00",
        level=10,
        is_out_log=True,
    )

    app = MuApp()
    app.MainLoop()
