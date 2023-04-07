import sys

import wx
from mlib.form.base_notebook import BaseNotebook
from mlib.utils.file_utils import read_histories


class BaseFrame(wx.Frame):
    def __init__(self, app: wx.App, title: str, history_keys: list[str], size: wx.Size, *args, **kw):
        wx.Frame.__init__(
            self,
            None,
            title=title,
            size=size,
            style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
        )
        self.app = app

        self._initialize_ui()
        self._initialize_event()

        self.history_keys = history_keys
        self.histories = read_histories(self.history_keys)

        self.Centre(wx.BOTH)
        self.Layout()

    def _initialize_ui(self):
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNSHADOW))

        self.notebook = BaseNotebook(self)

    def _initialize_event(self):
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event: wx.Event):
        self.Destroy()
        sys.exit(0)