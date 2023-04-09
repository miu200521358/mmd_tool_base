from typing import Dict, Optional

import numpy as np
import OpenGL.GL as gl

from mlib.base.exception import MViewerException
from mlib.base.part import BaseIndexModel
from mlib.pmx.pmx_part import DrawFlg, Material, ShaderMaterial, Texture
from mlib.pmx.shader import MShader, VsLayout


class VAO:
    """
    VAO（Vertex Array Object） ･･･ 頂点情報と状態を保持するオブジェクト
    """

    def __init__(self) -> None:
        self.vao_id = gl.glGenVertexArrays(1)

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"VAO glGenVertexArrays Failure\n{error_code}")

    def bind(self) -> None:
        gl.glBindVertexArray(self.vao_id)

    def unbind(self) -> None:
        gl.glBindVertexArray(0)

    def __del__(self):
        if not self.vao_id:
            return

        gl.glDeleteVertexArrays(1, [self.vao_id])

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"VAO glDeleteVertexArrays Failure\n{self.vao_id}: {error_code}")


class VBO:
    """
    VBO（Vertex Buffer Object）･･･ 頂点バッファオブジェクト
    """

    def __init__(self, data: np.ndarray, components: Dict[int, Dict[str, int]]) -> None:
        self.vbo_id = gl.glGenBuffers(1)

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"VBO glGenBuffers Failure\n{error_code}")

        self.dsize = np.dtype(data.dtype).itemsize
        self.components = components
        self.data = data
        stride = sum([v["size"] for v in self.components.values()])
        for v in self.components.values():
            v["stride"] = stride * self.dsize
            v["pointer"] = v["offset"] * self.dsize

    def __del__(self) -> None:
        if not self.vbo_id:
            return

        gl.glDeleteBuffers(1, [self.vbo_id])

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"VBO glDeleteBuffers Failure\n{self.vbo_id}: {error_code}")

    def bind(self) -> None:
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_id)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.data.nbytes, self.data, gl.GL_STATIC_DRAW)

    def unbind(self) -> None:
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def set_slot(self, slot: VsLayout) -> None:
        gl.glEnableVertexAttribArray(slot.value)
        gl.glVertexAttribPointer(
            slot.value,
            self.components[slot.value]["size"],
            gl.GL_FLOAT,
            gl.GL_FALSE,
            self.components[slot.value]["stride"],
            gl.ctypes.c_void_p(self.components[slot.value]["pointer"]),
        )


class IBO:
    """
    IBO（Index Buffer Object） ･･･ インデックスバッファオブジェクト
    """

    def __init__(self, data: np.ndarray) -> None:
        self.ibo_id = gl.glGenBuffers(1)

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"IBO glGenBuffers Failure\n{error_code}")

        self.dtype = gl.GL_UNSIGNED_BYTE if data.dtype == np.uint8 else gl.GL_UNSIGNED_SHORT if data.dtype == np.uint16 else gl.GL_UNSIGNED_INT
        self.dsize = np.dtype(data.dtype).itemsize

        self.bind()
        self.set_indices(data)
        self.unbind()

    def __del__(self) -> None:
        if not self.ibo_id:
            return

        gl.glDeleteBuffers(1, [self.ibo_id])

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"IBO glDeleteBuffers Failure\n{self.ibo_id}: {error_code}")

    def bind(self) -> None:
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ibo_id)

    def unbind(self) -> None:
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

    def set_indices(self, data: np.ndarray) -> None:
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER,
            data.nbytes,
            data,
            gl.GL_STATIC_DRAW,
        )


class Mesh(BaseIndexModel):
    """
    メッシュデータ（描画用）
    """

    def __init__(
        self,
        material: Material,
        texture: Optional[Texture],
        toon_texture: Optional[Texture],
        sphere_texture: Optional[Texture],
        prev_vertices_count: int,
        face_dtype: type,
    ):
        super().__init__()
        self.material = material
        self.texture = texture
        self.toon_texture = toon_texture
        self.sphere_texture = sphere_texture
        self.prev_vertices_count = prev_vertices_count
        self.prev_vertices_pointer = prev_vertices_count * np.dtype(face_dtype).itemsize

    def draw_model(
        self,
        bone_matrixes: np.ndarray,
        material_morphs: ShaderMaterial,
        shader: MShader,
        ibo: IBO,
    ):
        if DrawFlg.DOUBLE_SIDED_DRAWING in self.material.draw_flg:
            # 両面描画
            # カリングOFF
            gl.glDisable(gl.GL_CULL_FACE)
        else:
            # 片面描画
            # カリングON
            gl.glEnable(gl.GL_CULL_FACE)
            gl.glCullFace(gl.GL_BACK)

        # ボーンデフォームテクスチャ設定
        self.bind_bone_matrixes(bone_matrixes, shader, False)

        # ------------------
        # 材質色設定
        # full.fx の AmbientColor相当
        gl.glUniform4f(shader.diffuse_uniform[False], *material_morphs.diffuse.vector)
        gl.glUniform3f(shader.ambient_uniform[False], *material_morphs.ambient.vector)
        gl.glUniform4f(shader.specular_uniform[False], *material_morphs.specular.vector)

        # テクスチャ使用有無
        gl.glUniform1i(shader.use_texture_uniform[False], self.texture is not None and self.texture.valid)
        if self.texture and self.texture.valid:
            self.texture.bind()
            gl.glUniform1i(shader.texture_uniform[False], self.texture.texture_type.value)
            gl.glUniform4f(shader.texture_factor_uniform[False], *material_morphs.texture_factor.vector)

        # Toon使用有無
        gl.glUniform1i(shader.use_toon_uniform[False], self.toon_texture is not None and self.toon_texture.valid)
        if self.toon_texture and self.toon_texture.valid:
            self.toon_texture.bind()
            gl.glUniform1i(shader.toon_uniform[False], self.toon_texture.texture_type.value)
            gl.glUniform4f(shader.toon_factor_uniform[False], *material_morphs.toon_texture_factor.vector)

        # Sphere使用有無
        gl.glUniform1i(shader.use_sphere_uniform[False], self.sphere_texture is not None and self.sphere_texture.valid)
        if self.sphere_texture and self.sphere_texture.valid:
            self.sphere_texture.bind()
            gl.glUniform1i(shader.sphere_mode_uniform[False], self.material.sphere_mode)
            gl.glUniform1i(shader.sphere_uniform[False], self.sphere_texture.texture_type.value)
            gl.glUniform4f(shader.sphere_factor_uniform[False], *material_morphs.sphere_texture_factor.vector)

        gl.glDrawElements(
            gl.GL_TRIANGLES,
            self.material.vertices_count,
            ibo.dtype,
            gl.ctypes.c_void_p(self.prev_vertices_pointer),
        )

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"Mesh draw_model Failure\n{error_code}")

        if self.texture and self.texture.valid:
            self.texture.unbind()

        if self.toon_texture and self.toon_texture.valid:
            self.toon_texture.unbind()

        if self.sphere_texture and self.sphere_texture.valid:
            self.sphere_texture.unbind()

        self.unbind_bone_matrixes()

    def draw_edge(
        self,
        bone_matrixes: np.ndarray,
        material_morphs: ShaderMaterial,
        shader: MShader,
        ibo: IBO,
    ):
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glCullFace(gl.GL_FRONT)

        # ボーンデフォームテクスチャ設定
        self.bind_bone_matrixes(bone_matrixes, shader, True)

        # ------------------
        # エッジ設定
        gl.glUniform4f(shader.edge_color_uniform[True], *material_morphs.edge_color.vector)
        gl.glUniform1f(shader.edge_size_uniform[True], material_morphs.edge_size)

        gl.glDrawElements(
            gl.GL_TRIANGLES,
            self.material.vertices_count,
            ibo.dtype,
            gl.ctypes.c_void_p(self.prev_vertices_pointer),
        )

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"Mesh draw_edge Failure\n{error_code}")

        self.unbind_bone_matrixes()

    def bind_bone_matrixes(
        self,
        mats: np.ndarray,
        shader: MShader,
        edge: bool,
    ):
        # テクスチャをアクティブにする
        gl.glActiveTexture(gl.GL_TEXTURE3)

        # テクスチャをバインドする
        gl.glBindTexture(gl.GL_TEXTURE_2D, shader.bone_matrix_texture_id[edge])

        # テクスチャのパラメーターの設定
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAX_LEVEL, 0)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        # テクスチャをシェーダーに渡す
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA32F,
            mats.shape[1],
            mats.shape[0],
            0,
            gl.GL_RGBA,
            gl.GL_FLOAT,
            mats.flatten(),
        )

        gl.glUniform1i(shader.bone_matrix_texture_uniform[edge], 3)

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"Mesh bind_bone_matrixes Failure\n{error_code}")

    def unbind_bone_matrixes(
        self,
    ):
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
