from typing import Optional

import numpy as np
import OpenGL.GL as gl

from mlib.base.exception import MViewerException
from mlib.base.part import BaseIndexModel
from mlib.pmx.pmx_part import DrawFlg, Material, ShaderMaterial, SphereMode, Texture
from mlib.pmx.shader import MShader, ProgramType, VsLayout


class VAO:
    """
    VAO（Vertex Array Object） ･･･ 頂点情報と状態を保持するオブジェクト
    """

    def __init__(self) -> None:
        try:
            self.vao_id = gl.glGenVertexArrays(1)
        except Exception as e:
            raise MViewerException(f"VBO glGenVertexArrays Failure\n{self.vao_id}", e)

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

        try:
            gl.glDeleteVertexArrays(1, [self.vao_id])
        except Exception as e:
            raise MViewerException(f"VBO glDeleteVertexArrays Failure\n{self.vao_id}", e)

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"VAO glDeleteVertexArrays Failure\n{self.vao_id}: {error_code}")


class VBO:
    """
    VBO（Vertex Buffer Object）･･･ 頂点バッファオブジェクト
    """

    def __init__(self, data: np.ndarray, components: dict[int, dict[str, int]]) -> None:
        try:
            self.vbo_id = gl.glGenBuffers(1)
        except Exception as e:
            raise MViewerException("VBO glGenBuffers Failure", e)

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

        try:
            gl.glDeleteBuffers(1, [self.vbo_id])
        except Exception as e:
            raise MViewerException(f"VBO glDeleteBuffers Failure\n{self.vbo_id}", e)

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

    def set_slot_by_value(self, slot_value: int) -> None:
        gl.glEnableVertexAttribArray(slot_value)
        gl.glVertexAttribPointer(
            slot_value,
            self.components[slot_value]["size"],
            gl.GL_FLOAT,
            gl.GL_FALSE,
            self.components[slot_value]["stride"],
            gl.ctypes.c_void_p(self.components[slot_value]["pointer"]),
        )


class IBO:
    """
    IBO（Index Buffer Object） ･･･ インデックスバッファオブジェクト
    """

    def __init__(self, data: np.ndarray) -> None:
        try:
            self.ibo_id = gl.glGenBuffers(1)
        except Exception as e:
            raise MViewerException("IBO glGenBuffers Failure", e)

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"IBO glGenBuffers Failure\n{error_code}")

        match data.dtype:
            case np.uint8:
                self.dtype = gl.GL_UNSIGNED_BYTE
            case np.uint16:
                self.dtype = gl.GL_UNSIGNED_SHORT
            case np.uint32:
                self.dtype = gl.GL_UNSIGNED_INT
        self.dsize = np.dtype(data.dtype).itemsize

        self.bind()
        self.set_indices(data)
        self.unbind()

    def __del__(self) -> None:
        if not self.ibo_id:
            return

        try:
            gl.glDeleteBuffers(1, [self.ibo_id])
        except Exception as e:
            raise MViewerException(f"IBO glDeleteBuffers Failure\n{self.ibo_id}", e)

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
        self.bind_bone_matrixes(bone_matrixes, shader, ProgramType.MODEL)

        # ------------------
        # 材質色設定
        # full.fx の AmbientColor相当
        gl.glUniform4f(shader.diffuse_uniform[ProgramType.MODEL.value], *material_morphs.diffuse)
        gl.glUniform3f(shader.ambient_uniform[ProgramType.MODEL.value], *material_morphs.ambient)
        gl.glUniform4f(shader.specular_uniform[ProgramType.MODEL.value], *material_morphs.specular)

        # テクスチャ使用有無
        gl.glUniform1i(shader.use_texture_uniform[ProgramType.MODEL.value], self.texture is not None and self.texture.valid)
        if self.texture and self.texture.valid:
            self.texture.bind()
            gl.glUniform1i(shader.texture_uniform[ProgramType.MODEL.value], self.texture.texture_type.value)
            gl.glUniform4f(shader.texture_factor_uniform[ProgramType.MODEL.value], *material_morphs.texture_factor)

        # Toon使用有無
        gl.glUniform1i(shader.use_toon_uniform[ProgramType.MODEL.value], self.toon_texture is not None and self.toon_texture.valid)
        if self.toon_texture and self.toon_texture.valid:
            self.toon_texture.bind()
            gl.glUniform1i(shader.toon_uniform[ProgramType.MODEL.value], self.toon_texture.texture_type.value)
            gl.glUniform4f(shader.toon_factor_uniform[ProgramType.MODEL.value], *material_morphs.toon_texture_factor)

        # Sphere使用有無
        gl.glUniform1i(
            shader.use_sphere_uniform[ProgramType.MODEL.value],
            self.sphere_texture is not None and self.sphere_texture.valid and self.material.sphere_mode != SphereMode.INVALID,
        )
        if self.sphere_texture and self.sphere_texture.valid:
            self.sphere_texture.bind()
            gl.glUniform1i(shader.sphere_mode_uniform[ProgramType.MODEL.value], self.material.sphere_mode)
            gl.glUniform1i(shader.sphere_uniform[ProgramType.MODEL.value], self.sphere_texture.texture_type.value)
            gl.glUniform4f(shader.sphere_factor_uniform[ProgramType.MODEL.value], *material_morphs.sphere_texture_factor)

        try:
            gl.glDrawElements(
                gl.GL_TRIANGLES,
                self.material.vertices_count,
                ibo.dtype,
                gl.ctypes.c_void_p(self.prev_vertices_pointer),
            )
        except Exception as e:
            raise MViewerException("Mesh draw_model Failure", e)

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
        self.bind_bone_matrixes(bone_matrixes, shader, ProgramType.EDGE)

        # ------------------
        # エッジ設定
        gl.glUniform4f(shader.edge_color_uniform[ProgramType.EDGE.value], *material_morphs.edge_color)
        gl.glUniform1f(shader.edge_size_uniform[ProgramType.EDGE.value], material_morphs.edge_size)

        try:
            gl.glDrawElements(
                gl.GL_TRIANGLES,
                self.material.vertices_count,
                ibo.dtype,
                gl.ctypes.c_void_p(self.prev_vertices_pointer),
            )
        except Exception as e:
            raise MViewerException("Mesh draw_edge Failure", e)

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"Mesh draw_edge Failure\n{error_code}")

        self.unbind_bone_matrixes()

    def bind_bone_matrixes(
        self,
        matrixes: np.ndarray,
        shader: MShader,
        program_type: ProgramType,
    ):
        # テクスチャをアクティブにする
        gl.glActiveTexture(gl.GL_TEXTURE3)

        # テクスチャをバインドする
        gl.glBindTexture(gl.GL_TEXTURE_2D, shader.bone_matrix_texture_id[program_type.value])

        # テクスチャのパラメーターの設定
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAX_LEVEL, 0)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        # テクスチャのサイズを計算する
        num_bones = matrixes.shape[0]
        tex_size = int(np.ceil(np.sqrt(num_bones)))
        width = int(np.ceil(tex_size / 4) * 4 * 4)
        height = int(np.ceil((num_bones * 4) / width))

        padded_matrixes = np.zeros(height * width * 4)
        padded_matrixes[: matrixes.size] = matrixes.flatten()

        # テクスチャをシェーダーに渡す
        try:
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D,
                0,
                gl.GL_RGBA32F,
                width,
                height,
                0,
                gl.GL_RGBA,
                gl.GL_FLOAT,
                padded_matrixes.flatten(),
            )
        except Exception as e:
            raise MViewerException("Mesh bind_bone_matrixes Failure", e)

        gl.glUniform1i(shader.bone_matrix_texture_uniform[program_type.value], 3)
        gl.glUniform1i(shader.bone_matrix_texture_width[program_type.value], width)
        gl.glUniform1i(shader.bone_matrix_texture_height[program_type.value], height)

        error_code = gl.glGetError()
        if error_code != gl.GL_NO_ERROR:
            raise MViewerException(f"Mesh bind_bone_matrixes Failure\n{error_code}")

    def unbind_bone_matrixes(
        self,
    ):
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
