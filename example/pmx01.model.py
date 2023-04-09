"""
MMDモデルの描画
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import OpenGL.GL as gl
import wx
from mlib.math import MMatrix4x4, MQuaternion, MVector3D
from OpenGL.GL import shaders
from wx import glcanvas

from mlib.pmx.pmx_reader import PmxReader

vertex_shader = """
# version 330
in layout(location = 0) vec3 positions;
in layout(location = 1) vec3 colors;

out vec3 newColor;
uniform mat4 model;

void main() {
    vec4            pvec;
    pvec = model * vec4(positions, 1.0);
    gl_Position = vec4( -pvec[ 0 ], pvec[ 1 ], pvec[ 2 ], pvec[ 3 ] );  // 座標系による反転を行う、カリングも反転
    newColor = colors;
}
"""

fragments_shader = """
# version 330

in vec3 newColor;
out vec4  outColor;

void main() {
    outColor = vec4(newColor, 1.0);
}
"""


class Geometries:
    def __init__(self) -> None:
        # self.triangle = np.array(
        #     [
        #         -0.5,
        #         -0.5,
        #         0.0,
        #         1.0,
        #         0.0,
        #         0.0,
        #         0.5,
        #         -0.5,
        #         0.0,
        #         0.0,
        #         1.0,
        #         0.0,
        #         0.0,
        #         0.5,
        #         0.0,
        #         0.0,
        #         0.0,
        #         1.0,
        #     ],
        #     dtype=np.float64,
        # )

        # self.vao_triangle = gl.glGenVertexArrays(1)
        # gl.glBindVertexArray(self.vao_triangle)

        # vbo_triangle = gl.glGenBuffers(1)
        # gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_triangle)
        # gl.glBufferData(
        #     gl.GL_ARRAY_BUFFER, self.triangle.nbytes, self.triangle, gl.GL_STATIC_DRAW
        # )

        # gl.glVertexAttribPointer(
        #     0, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, gl.ctypes.c_void_p(0)
        # )
        # gl.glEnableVertexAttribArray(0)

        # gl.glVertexAttribPointer(
        #     1, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, gl.ctypes.c_void_p(12)
        # )
        # gl.glEnableVertexAttribArray(1)
        # gl.glBindVertexArray(0)

        # # quad ------------------

        # self.quad = np.array(
        #     [
        #         -0.5,
        #         -0.5,
        #         0.0,
        #         1.0,
        #         0.0,
        #         0.0,
        #         0.5,
        #         -0.5,
        #         0.0,
        #         0.0,
        #         1.0,
        #         0.0,
        #         -0.5,
        #         0.5,
        #         0.0,
        #         0.0,
        #         0.0,
        #         1.0,
        #         0.5,
        #         0.5,
        #         0.0,
        #         1.0,
        #         1.0,
        #         1.0,
        #     ],
        #     dtype=np.float64,
        # )

        # self.vao_quad = gl.glGenVertexArrays(1)
        # gl.glBindVertexArray(self.vao_quad)

        # vbo_quad = gl.glGenBuffers(1)
        # gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_quad)
        # gl.glBufferData(
        #     gl.GL_ARRAY_BUFFER, self.quad.nbytes, self.quad, gl.GL_STATIC_DRAW
        # )

        # gl.glVertexAttribPointer(
        #     0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(0)
        # )
        # gl.glEnableVertexAttribArray(0)

        # gl.glVertexAttribPointer(
        #     1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(12)
        # )
        # gl.glEnableVertexAttribArray(1)
        # gl.glBindVertexArray(0)

        # # ------------------

        self.model = PmxReader().read_by_filepath(
            # "C:/MMD/mmd_base/test/resources/曲げ柱tex.pmx"
            # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式初音ミク・アペンドVer1.10/Tda式初音ミク・アペンド_Ver1.10.pmx",
            "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/初音ミクVer2 準標準.pmx"
        )
        self.model.init_draw()
        if not self.model.meshs:
            return
        vertex_position_list = []
        prev_face_count = 0
        for material in self.model.materials:
            face_count = material.vertices_count // 3
            for face_index in range(prev_face_count, prev_face_count + face_count):
                vertex_position_list.append(
                    np.array(
                        [((self.model.vertices[vidx].position + MVector3D(0, -10, 0)) / 15).vector for vidx in self.model.faces[face_index].vertices],
                        dtype=np.float64,
                    )
                )
            prev_face_count += face_count
        self.vertices = np.array(vertex_position_list, dtype=np.float64)

        self.vao_vertices = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao_vertices)

        vbo_vertices = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_vertices)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.vertices.nbytes,
            self.vertices,
            gl.GL_STATIC_DRAW,
        )

        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)

        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

    def bind_triangle(self):
        gl.glBindVertexArray(self.vao_triangle)
        self.count = len(self.triangle) // 3

    def bind_quad(self):
        gl.glBindVertexArray(self.vao_quad)
        self.count = len(self.quad) // 3

    def bind_vertices(self):
        gl.glBindVertexArray(self.vao_vertices)
        self.count = self.vertices.shape[0] * self.vertices.shape[1]


class OpenGLCanvas(glcanvas.GLCanvas):
    def __init__(self, parent, *args, **kw):
        glcanvas.GLCanvas.__init__(self, parent, -1, size=(600, 600))
        self.init = False
        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)
        gl.glClearColor(0.1, 0.15, 0.1, 1)
        self.rotate = False
        self.rot_y = MMatrix4x4()
        self.rot_y.identity()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)

    def OnResize(self, event: wx.Event):
        size = self.GetClientSize()
        gl.glViewport(0, 0, size.width, size.height)

    def OnPaint(self, event: wx.Event):
        wx.PaintDC(self)
        if not self.init:
            self.InitGL()
            self.init = True

        self.OnDraw(event)

    def InitGL(self):
        self.mesh = Geometries()
        self.mesh.bind_vertices()

        shader = shaders.compileProgram(
            shaders.compileShader(vertex_shader, gl.GL_VERTEX_SHADER),
            shaders.compileShader(fragments_shader, gl.GL_FRAGMENT_SHADER),
        )

        gl.glClearColor(0.1, 0.15, 0.1, 1.0)
        # gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

        gl.glUseProgram(shader)

        self.model_loc = gl.glGetUniformLocation(shader, "model")

    def OnDraw(self, event: wx.Event):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        if self.rotate:
            self.rot_y.rotate(MQuaternion.from_euler_degrees(0, 1, 0))
            gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, self.rot_y.vector)
            self.Refresh()
        else:
            gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, self.rot_y.vector)
            self.Refresh()
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, self.mesh.count)
        self.SwapBuffers()


class MyPanel(wx.Panel):
    def __init__(self, parent, *args, **kw):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour("#626D58")
        self.canvas = OpenGLCanvas(self)
        self.rot_btn = wx.Button(self, -1, label="Start/Stop\nrotation", pos=(620, 10), size=(100, 50))
        self.rot_btn.BackgroundColour = (125, 125, 125)
        self.rot_btn.ForegroundColour = (0, 0, 0)

        self.Bind(wx.EVT_BUTTON, self.rotate, self.rot_btn)

    def rotate(self, event: wx.Event):
        if not self.canvas.rotate:
            self.canvas.rotate = True
            self.canvas.Refresh()
        else:
            self.canvas.rotate = False


class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        self.size = (800, 720)
        wx.Frame.__init__(
            self,
            None,
            title="My wx Frame",
            size=self.size,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
        )
        self.SetMinSize(self.size)
        self.SetMaxSize(self.size)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.panel = MyPanel(self)

    def onClose(self, event: wx.Event):
        self.Destroy()
        sys.exit(0)


class MyApp(wx.App):
    def __init__(self, redirect=False, filename=None, useBestVisual=False, clearSigInt=True):
        super().__init__(redirect, filename, useBestVisual, clearSigInt)
        self.frame = MyFrame()
        self.frame.Show()


if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
