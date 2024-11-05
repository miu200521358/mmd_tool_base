import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import wx

from mlib.domain.logger import MLogger
from mlib.pmx.canvas import PmxCanvas
from mlib.pmx.pmx_reader import PmxReader
from mlib.vmd.vmd_reader import VmdReader


class PmxPanel(wx.Panel):
    def __init__(self, parent, model_path: str, motion_path: str):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.model_path = model_path
        self.motion_path = motion_path

        self._initialize_ui()
        self._initialize_event()

        self.fit()

    def _initialize_ui(self):
        self.SetBackgroundColour("#626D58")

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.canvas = PmxCanvas(self, 800, 700)

        self.sizer.Add(self.canvas, 0, wx.ALL | wx.EXPAND, 0)

        # ファイル系
        self.file_sizer = wx.BoxSizer(wx.VERTICAL)

        self.model_file_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY)
        self.file_sizer.Add(self.model_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.model_file_ctrl.SetPath(self.model_path)

        self.motion_file_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY)
        self.file_sizer.Add(self.motion_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.motion_file_ctrl.SetPath(self.motion_path)

        self.sizer.Add(self.file_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 読み込み
        self.load_btn = wx.Button(self, wx.ID_ANY, "Load", wx.DefaultPosition, wx.Size(100, 50))
        self.btn_sizer.Add(self.load_btn, 0, wx.ALL, 5)

        # 再生
        self.play_btn = wx.Button(self, wx.ID_ANY, "Play", wx.DefaultPosition, wx.Size(100, 50))
        self.btn_sizer.Add(self.play_btn, 0, wx.ALL, 5)

        # 録画
        self.record_btn = wx.Button(self, wx.ID_ANY, "Record", wx.DefaultPosition, wx.Size(100, 50))
        self.btn_sizer.Add(self.record_btn, 0, wx.ALL, 5)

        # リセット
        self.reset_btn = wx.Button(self, wx.ID_ANY, "Reset", wx.DefaultPosition, wx.Size(100, 50))
        self.btn_sizer.Add(self.reset_btn, 0, wx.ALL, 5)

        # キャプチャー
        self.capture_btn = wx.Button(self, wx.ID_ANY, "Capture", wx.DefaultPosition, wx.Size(100, 50))
        self.btn_sizer.Add(self.capture_btn, 0, wx.ALL, 5)

        # キーフレ
        self.btn_sizer.Add(self.canvas.frame_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(self.btn_sizer, 0, wx.EXPAND | wx.ALL, 5)

    def _initialize_event(self):
        self.load_btn.Bind(wx.EVT_BUTTON, self.on_load)
        self.play_btn.Bind(wx.EVT_BUTTON, self.on_play)
        self.reset_btn.Bind(wx.EVT_BUTTON, self.on_reset)
        self.capture_btn.Bind(wx.EVT_BUTTON, self.on_capture)
        self.record_btn.Bind(wx.EVT_BUTTON, self.on_record)

    def fit(self):
        self.SetSizer(self.sizer)
        self.Layout()
        self.sizer.Fit(self.parent)

    def on_reset(self, event: wx.Event):
        self.canvas.on_reset(event)

    def on_capture(self, event: wx.Event):
        self.canvas.on_capture(event)

    def on_play(self, event: wx.Event):
        self.canvas.on_play(event)
        self.play_btn.SetLabelText("Stop" if self.canvas.playing else "Play")

    def on_record(self, event: wx.Event):
        self.canvas.on_play(event, record=True)
        self.play_btn.SetLabelText("Stop" if self.canvas.playing else "Play")

    def on_load(self, event: wx.Event):
        self.canvas.model = PmxReader().read_by_filepath(self.model_path)
        self.canvas.model.init_draw(self.canvas.shader)

        self.canvas.motion = VmdReader().read_by_filepath(self.motion_path)
        self.canvas.change_motion(event)


class PmxFrame(wx.Frame):
    def __init__(self, model_path: str, motion_path: str):
        self.size = (1000, 1000)
        wx.Frame.__init__(
            self,
            None,
            title="Pmx wx Frame",
            size=self.size,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
        )

        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.panel = PmxPanel(self, model_path, motion_path)

    def onClose(self, event: wx.Event):
        self.Destroy()
        sys.exit(0)


class PmxApp(wx.App):
    def __init__(self):
        super().__init__()

        parser = argparse.ArgumentParser(description="MMD model viewer sample.")
        parser.add_argument("--model", type=str, help="MMD model file name.")
        parser.add_argument("--motion", type=str, help="MMD motion file name.")
        parser.add_argument("--level", type=int, help="MMD motion file name.")
        args = parser.parse_args()

        MLogger.initialize(
            lang="ja_JP",
            root_dir=os.path.join(os.path.dirname(__file__), "..", "mlib"),
            version_name="1.00.00",
            level=args.level,
        )

        self.frame = PmxFrame(args.model, args.motion)
        self.frame.Show()


if __name__ == "__main__":
    app = PmxApp()
    app.MainLoop()
