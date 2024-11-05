"""
材質色の描画
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import wx
from OpenGL.GL import shaders
from PIL import Image, ImageOps
from wx import glcanvas

from mlib.domain.math import MMatrix4x4, MQuaternion, MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_reader import PmxReader

POSITION_ID = 0
NORMAL_ID = 1
UV_ID = 2
TEXTURE_ID = 3

COLOR_DIFFUSE_ID = 4
COLOR_AMBIENT_ID = 5
COLOR_SPECULAR_ID = 6

vertex_shader = """
#version 440 core
in layout(location = %d) vec3 position;
in layout(location = %d) vec3 normal;
in layout(location = %d) vec2 uv;
in layout(location = %d) int  texture_idx;
in layout(location = %d) vec4 diffuse;
in layout(location = %d) vec3 ambient;
in layout(location = %d) vec4 specular;

uniform vec3 lightPos;
uniform vec3 cameraPos;
uniform mat4 modelMatrix;

out vec4 vertexColor;
out vec3 vertexSpecular;
out vec2 vertexUv;

void main() {
    vec4 pvec = modelMatrix * vec4(position, 1.0);
    gl_Position = vec4( -pvec.x, pvec.y, pvec.z, pvec.w );  // 座標系による反転を行う、カリングも反転

    vertexUv = uv;

    // 頂点法線
    vec3 N = (modelMatrix * normalize(vec4(normal, 1.0))).rgb;
    vec3 vetexNormal = vec3(-N[0], N[1], N[2]); // 座標系による反転

    // 照明位置
    vec3 LightDirection = -normalize(lightPos);

    // 頂点色設定
    vertexColor = clamp(vec4(ambient, diffuse.w), 0.0, 1.0);
    // 色傾向
    float factor = clamp(dot(vetexNormal, LightDirection), 0.0f, 1.0f);

    // ディフューズ色＋アンビエント色 計算
    // TODO TOONでないとき、の条件付与
    vertexColor.rgb += diffuse.rgb * factor;

    // saturate
    vertexColor = clamp(vertexColor, 0.0, 1.0);

    // カメラとの相対位置
    vec3 eye = cameraPos - gl_Position.rgb;

    // スペキュラ色計算
    vec3 HalfVector = normalize( normalize(eye) + LightDirection );
    vertexSpecular = clamp(pow( max(0, dot( HalfVector, vetexNormal )), specular.w ) * specular.rgb, 0.0f, 1.0f);
}
""" % (
    POSITION_ID,
    NORMAL_ID,
    UV_ID,
    TEXTURE_ID,
    COLOR_DIFFUSE_ID,
    COLOR_AMBIENT_ID,
    COLOR_SPECULAR_ID,
)

fragments_shader = """
#version 440 core

uniform mat4 modelMatrix;
uniform sampler2D textureSampler;

in vec4 vertexColor;
in vec3 vertexSpecular;
in vec2 vertexUv;
out vec4  outColor;

void main() {
    outColor = vertexColor;
    // テクスチャ適用
    // outColor *= texture(textureSampler, vertexUv).rgba;
    // スペキュラ適用
    outColor.rgb += vertexSpecular;
}
"""


class Geometries:
    def __init__(self) -> None:
        self.model = PmxReader().read_by_filepath(
            "C:/MMD/mmd_base/test/resources/曲げ柱tex.pmx"
            # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式初音ミク・アペンドVer1.10/Tda式初音ミク・アペンド_Ver1.10.pmx",
            # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/初音ミクVer2 準標準.pmx"
        )
        vertex_position_list = []
        vertex_normal_list = []
        vertex_uv_list = []
        texture_index_list = []
        diffuse_color_list = []
        specular_color_list = []
        ambient_color_list = []
        prev_face_count = 0
        for material in self.model.materials:
            face_count = material.vertices_count // 3
            for face_index in range(prev_face_count, prev_face_count + face_count):
                vertex_position_list.append(
                    np.array(
                        [
                            ((self.model.vertices[vidx].position + MVector3D(0, -10, 0)) / 15).vector
                            for vidx in self.model.faces[face_index].vertices
                        ],
                        dtype=np.float64,
                    )
                )
                vertex_normal_list.append(
                    np.array(
                        [self.model.vertices[vidx].normal.vector for vidx in self.model.faces[face_index].vertices],
                        dtype=np.float64,
                    )
                )
                vertex_uv_list.append(
                    np.array(
                        [self.model.vertices[vidx].uv.vector for vidx in self.model.faces[face_index].vertices],
                        dtype=np.float64,
                    )
                )
                texture_index_list.append(
                    np.array(
                        np.array(
                            [material.texture_index for _ in range(len(self.model.faces[face_index].vertices))],
                            dtype=np.float64,
                        ),
                        dtype=np.float64,
                    )
                )
                diffuse_color_list.append(
                    np.array(
                        np.array(
                            [material.diffuse.vector for _ in range(len(self.model.faces[face_index].vertices))],
                            dtype=np.float64,
                        ),
                        dtype=np.float64,
                    )
                )
                specular_color_list.append(
                    np.array(
                        np.array(
                            [
                                [
                                    material.specular.x,
                                    material.specular.y,
                                    material.specular.z,
                                    material.specular_factor,
                                ]
                                for _ in range(len(self.model.faces[face_index].vertices))
                            ],
                            dtype=np.float64,
                        ),
                        dtype=np.float64,
                    )
                )
                ambient_color_list.append(
                    np.array(
                        np.array(
                            [
                                [
                                    material.ambient.x,
                                    material.ambient.y,
                                    material.ambient.z,
                                ]
                                for _ in range(len(self.model.faces[face_index].vertices))
                            ],
                            dtype=np.float64,
                        ),
                        dtype=np.float64,
                    )
                )
            prev_face_count += face_count
        self.vertices = np.array(vertex_position_list, dtype=np.float64)
        self.normals = np.array(vertex_normal_list, dtype=np.float64)
        self.uvs = np.array(vertex_uv_list, dtype=np.float64)
        self.textures = np.array(texture_index_list, dtype=np.float64)
        self.diffuses = np.array(diffuse_color_list, dtype=np.float64)
        self.speculars = np.array(specular_color_list, dtype=np.float64)
        self.ambients = np.array(ambient_color_list, dtype=np.float64)
        self.texture_indecies = list(range(len(self.model.textures)))

        # ---------------------
        # 頂点の設定

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

        gl.glEnableVertexAttribArray(POSITION_ID)
        gl.glVertexAttribPointer(POSITION_ID, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(0))

        # ---------------------
        # Normalの描画

        vbo_normals = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_normals)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.normals.nbytes,
            self.normals,
            gl.GL_STATIC_DRAW,
        )

        gl.glEnableVertexAttribArray(NORMAL_ID)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_normals)
        gl.glVertexAttribPointer(NORMAL_ID, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(0))

        # ---------------------
        # UVの描画

        vbo_uvs = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_uvs)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.uvs.nbytes,
            self.uvs,
            gl.GL_STATIC_DRAW,
        )

        gl.glEnableVertexAttribArray(UV_ID)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_uvs)
        gl.glVertexAttribPointer(UV_ID, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(0))

        # ---------------------
        # TextureIndexの描画

        vbo_textures = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_textures)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.textures.nbytes,
            self.textures,
            gl.GL_STATIC_DRAW,
        )

        gl.glEnableVertexAttribArray(TEXTURE_ID)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_textures)
        gl.glVertexAttribPointer(TEXTURE_ID, 1, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(0))

        # ---------------------
        # Diffuseの描画

        vbo_diffuses = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_diffuses)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.diffuses.nbytes,
            self.diffuses,
            gl.GL_STATIC_DRAW,
        )

        gl.glEnableVertexAttribArray(COLOR_DIFFUSE_ID)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_diffuses)
        gl.glVertexAttribPointer(COLOR_DIFFUSE_ID, 4, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(0))

        # ---------------------
        # Ambientの描画

        vbo_ambients = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_ambients)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.ambients.nbytes,
            self.ambients,
            gl.GL_STATIC_DRAW,
        )

        gl.glEnableVertexAttribArray(COLOR_AMBIENT_ID)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_ambients)
        gl.glVertexAttribPointer(COLOR_AMBIENT_ID, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(0))

        # ---------------------
        # Specularの描画

        vbo_speculars = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_speculars)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.speculars.nbytes,
            self.speculars,
            gl.GL_STATIC_DRAW,
        )

        gl.glEnableVertexAttribArray(COLOR_DIFFUSE_ID)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_speculars)
        gl.glVertexAttribPointer(COLOR_DIFFUSE_ID, 4, gl.GL_FLOAT, gl.GL_FALSE, 0, gl.ctypes.c_void_p(0))

        # ---------------------
        # Texture
        self.vbo_textures = list(range(len(self.model.textures)))
        gl.glGenTextures(len(self.model.textures), self.vbo_textures)
        for index in range(len(self.model.textures)):
            self.load_texture(self.model, index)
        gl.glEnable(gl.GL_TEXTURE_2D)

    def load_texture(self, model: PmxModel, index: int):
        # global texture
        tex_path = os.path.abspath(os.path.join(os.path.dirname(model.path), model.textures[index].texture_path))
        image = Image.open(tex_path).convert("RGBA")
        image = ImageOps.flip(image)
        ix, iy = image.size
        gl.glBindTexture(gl.GL_TEXTURE_2D, index)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            ix,
            iy,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            image.tobytes(),
        )
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_DECAL)


class OpenGLCanvas(glcanvas.GLCanvas):
    def __init__(self, parent, *args, **kw):
        self.size = wx.Size(600, 600)
        glcanvas.GLCanvas.__init__(self, parent, -1, size=self.size)
        self.init = False
        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)
        gl.glClearColor(0.1, 0.15, 0.1, 1)
        self.rotate = False
        self.rot_y = MMatrix4x4()
        # self.rot_y.identity()

        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, event: wx.Event):
        wx.PaintDC(self)
        if not self.init:
            self.InitGL()
            self.init = True

        self.OnDraw(event)

    def InitGL(self):
        self.mesh = Geometries()
        gl.glBindVertexArray(self.mesh.vao_vertices)

        gl.glClearColor(0.1, 0.15, 0.1, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)  # enable shading

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        CAMERA_LENGTH = 160.0

        # set perspective
        glu.gluPerspective(30.0, float(self.size.width) / float(self.size.height), 0.10, CAMERA_LENGTH)

        # modeling transform
        gl.glMatrixMode(gl.GL_MODELVIEW)

        # light color
        self.light_ambient = [0.25, 0.25, 0.25]
        self.light_diffuse = [1.0, 1.0, 1.0]
        self.light_specular = [1.0, 1.0, 1.0]

        # light position
        self.light_position = [-0.5, -1.0, 0.5]

        # light setting
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, self.light_ambient)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, self.light_diffuse)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, self.light_specular)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, self.light_position)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glEnable(gl.GL_LIGHTING)

        # gl.glClearColor(0.1, 0.15, 0.1, 1.0)
        # # gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

        shader = shaders.compileProgram(
            shaders.compileShader(vertex_shader, gl.GL_VERTEX_SHADER),
            shaders.compileShader(fragments_shader, gl.GL_FRAGMENT_SHADER),
        )

        gl.glUseProgram(shader)

        self.bone_matrix_uniform = gl.glGetUniformLocation(shader, "modelMatrix")

        # ライトの位置
        self.light_vec_uniform = gl.glGetUniformLocation(shader, "lightPos")
        gl.glUniform3f(self.light_vec_uniform, *self.light_position)

        # カメラの位置
        self.camera_vec_uniform = gl.glGetUniformLocation(shader, "cameraPos")
        gl.glUniform3f(self.camera_vec_uniform, 0, 0, CAMERA_LENGTH)

        # テクスチャの設定
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        self.texture_uniform = gl.glGetUniformLocation(shader, "texture")
        gl.glUniform1i(self.texture_uniform, 0)

        # # ライトAmbient
        # self.light_ambient_uniform = gl.glGetUniformLocation(shader, "lightAmbient")
        # gl.glUniform3fv(self.light_ambient_uniform, *self.light_ambient)

        # # ライトDiffuse
        # self.light_diffuse_uniform = gl.glGetUniformLocation(shader, "lightDiffuse")
        # gl.glUniform3fv(self.light_diffuse_uniform, *self.light_diffuse)

        # # ライトSpecular
        # self.light_diffuse_uniform = gl.glGetUniformLocation(shader, "lightSpecular")
        # gl.glUniform3fv(self.light_diffuse_uniform, *self.light_diffuse)

    def OnDraw(self, event: wx.Event):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # set camera
        # gluLookAt(0.0, 10.0, 80.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        glu.gluLookAt(0.0, 10.0, -30.0, 0.0, 10.0, 0.0, 0.0, 1.0, 0.0)

        """  /**** **** **** **** **** **** **** ****/  """
        gl.glPushMatrix()

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        if self.rotate:
            self.rot_y.rotate(MQuaternion.from_euler_degrees(0, 1, 0))
            gl.glUniformMatrix4fv(self.bone_matrix_uniform, 1, gl.GL_FALSE, self.rot_y.vector)
            self.Refresh()
        else:
            gl.glUniformMatrix4fv(self.bone_matrix_uniform, 1, gl.GL_FALSE, self.rot_y.vector)
            self.Refresh()

        gl.glPopMatrix()
        """  /**** **** **** **** **** **** **** ****/  """

        gl.glDrawArrays(
            gl.GL_TRIANGLES,
            0,
            self.mesh.vertices.shape[0] * self.mesh.vertices.shape[1],
        )
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
        self.size = (800, 600)
        wx.Frame.__init__(
            self,
            None,
            title="My wx Frame",
            size=self.size,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
        )
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
