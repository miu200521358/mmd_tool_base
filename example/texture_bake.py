import os
import sys
from itertools import product

import numpy as np
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mlib.domain.logger import MLogger
from mlib.domain.math import MVectorDict
from mlib.pmx.pmx_reader import PmxReader

model_path = "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/073_燭台切光忠/燭台切光忠 sam式 Ver1.5/sam式燭台切光忠（Tシャツ）Ver1.5/ギャルソン服(袖捲り)0.10/黄sam式燭台切光忠（Tシャツ）_20230708_114549.pmx"
dress_path = "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/073_燭台切光忠/燭台切光忠 sam式 Ver1.5/sam式燭台切光忠（Tシャツ）Ver1.5/ギャルソン服(袖捲り)0.10/キッチンカーギャルソン服(袖捲り)_20230708_114554.pmx"

model_texture_path = (
    "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/073_燭台切光忠/燭台切光忠 sam式 Ver1.5/sam式燭台切光忠（Tシャツ）Ver1.5/ギャルソン服(袖捲り)0.10/燭台切　体2.bmp"
)
dress_texture_path = "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/073_燭台切光忠/燭台切光忠 sam式 Ver1.5/sam式燭台切光忠（Tシャツ）Ver1.5/ギャルソン服(袖捲り)0.10/Costume/tex/body.png"
correct_dress_texture_path = "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/073_燭台切光忠/燭台切光忠 sam式 Ver1.5/sam式燭台切光忠（Tシャツ）Ver1.5/ギャルソン服(袖捲り)0.10/Costume/tex/body_correct.png"
fill_dress_texture_path = "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/073_燭台切光忠/燭台切光忠 sam式 Ver1.5/sam式燭台切光忠（Tシャツ）Ver1.5/ギャルソン服(袖捲り)0.10/Costume/tex/body_fill.png"

model_material_name = "体"
dress_material_name = "体"

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text

model = PmxReader().read_by_filepath(model_path)
dress = PmxReader().read_by_filepath(dress_path)

model.update_vertices_by_material()
dress.update_vertices_by_material()

model_material = model.materials[model_material_name]
dress_material = dress.materials[dress_material_name]

model_texture = np.array(Image.open(model_texture_path))
dress_texture = np.array(Image.open(dress_texture_path))

# 補正衣装テクスチャ
corrected_dress_texture = np.asarray(np.copy(dress_texture), np.float64)

# 人物の指定材質に割り当てられた頂点INDEXリスト
model_vertex_indexes = model.vertices_by_materials[model_material.index]
# 衣装の指定材質に割り当てられた頂点INDEXリスト
dress_vertex_indexes = dress.vertices_by_materials[dress_material.index]

# 人物の指定材質に割り当てられた面INDEXリスト
model_face_indexes = model.faces_by_materials[model_material.index]
# 衣装の指定材質に割り当てられた面INDEXリスト
dress_face_indexes = dress.faces_by_materials[dress_material.index]

# 人物の頂点に紐付く面の構成頂点INDEXがmodel_vertex_indexesの何番目に存在しているかのリスト
model_near_vertices: dict[int, list[int]] = {}
for model_face_index in model_face_indexes:
    for vertex_index in model.faces[model_face_index].vertices:
        if vertex_index not in model_near_vertices:
            model_near_vertices[vertex_index] = []
        for near_vertex_index in model.faces[model_face_index].vertices:
            if near_vertex_index in model_vertex_indexes:
                model_near_vertices[vertex_index].append(
                    [vi for (vi, vidx) in enumerate(model_vertex_indexes) if vidx == near_vertex_index][0]
                )

# 衣装の頂点に紐付く面の構成頂点INDEXがdress_vertex_indexesの何番目に存在しているかのリスト
dress_near_vertices: dict[int, list[int]] = {}
for dress_face_index in dress_face_indexes:
    for vertex_index in dress.faces[dress_face_index].vertices:
        if vertex_index not in dress_near_vertices:
            dress_near_vertices[vertex_index] = []
        for near_vertex_index in dress.faces[dress_face_index].vertices:
            if near_vertex_index in dress_vertex_indexes:
                dress_near_vertices[vertex_index].append(
                    [vi for (vi, vidx) in enumerate(dress_vertex_indexes) if vidx == near_vertex_index][0]
                )

# 人物の指定材質に割り当てられた頂点INDEXが配置されている3次元頂点の位置
model_vertex_positions = MVectorDict()
for model_vertex_index in model_vertex_indexes:
    model_vertex_positions.append(model_vertex_index, model.vertices[model_vertex_index].position)

# 衣装の指定材質に割り当てられた頂点INDEXが配置されている3次元頂点の位置
dress_vertex_positions = MVectorDict()
for dress_vertex_index in dress_vertex_indexes:
    dress_vertex_positions.append(dress_vertex_index, dress.vertices[dress_vertex_index].position)

# 衣装の指定材質に割り当てられた頂点INDEXが配置されている3次元頂点の位置に最も近い人物頂点を見つける
model_vertex_uv_list: list[np.ndarray] = []
dress_vertex_uv_list: list[np.ndarray] = []

# 面を構成している頂点（近似頂点）のリスト
model_vertices_by_face: list[list[int]] = []
dress_vertices_by_face: list[list[int]] = []

# 材質に割り当てられたテクスチャの色のRGBだけを取り出す
model_texture_colors = np.copy(model_texture[..., :3])
dress_texture_colors = np.copy(dress_texture[..., :3])

for dress_vertex_index in dress_vertex_indexes:
    nearest_model_vertex_index = model_vertex_positions.nearest_key(dress.vertices[dress_vertex_index].position)
    nearest_model_vertex = model.vertices[nearest_model_vertex_index]
    # 人物の指定頂点に割り当てられたテクスチャとUVから、テクスチャの該当位置を取得する
    model_vertex_uv_list.append(
        np.array([int(nearest_model_vertex.uv.x * model_texture.shape[0]), int(nearest_model_vertex.uv.y * model_texture.shape[1])])
    )
    # 面を構成している頂点（近似頂点）を求めておく
    model_vertices_by_face.append(model_near_vertices[nearest_model_vertex_index])

    # 衣装の指定頂点に割り当てられたテクスチャとUVから、テクスチャの該当位置を取得する
    dress_vertex = dress.vertices[dress_vertex_index]
    dress_vertex_uv_list.append(
        np.array([int(dress_vertex.uv.x * dress_texture.shape[0]), int(dress_vertex.uv.y * dress_texture.shape[1])])
    )
    dress_vertices_by_face.append(dress_near_vertices[dress_vertex_index])

model_vertex_uvs = np.array(model_vertex_uv_list)
dress_vertex_uvs = np.array(dress_vertex_uv_list)

# テクスチャの該当位置にある色の値
model_vertex_colors = model_texture_colors[model_vertex_uvs[:, 0], model_vertex_uvs[:, 1], :]
dress_vertex_colors = dress_texture_colors[dress_vertex_uvs[:, 0], dress_vertex_uvs[:, 1], :]

# 人物と衣装の該当UV位置にある色の差分を取得する
color_difference = dress_vertex_colors - model_vertex_colors

filled_dress_texture = np.zeros(dress_texture.shape)

for fidx, (model_near_vertices_by_face, dress_near_vertices_by_face) in enumerate(zip(model_vertices_by_face, dress_vertices_by_face)):
    model_near_vertex_uvs = model_vertex_uvs[np.array(model_near_vertices_by_face)]
    model_vertex_mean_color = np.mean(model_texture_colors[model_near_vertex_uvs[:, 0], model_near_vertex_uvs[:, 1], :], axis=0)

    dress_near_vertex_uvs = dress_vertex_uvs[np.array(dress_near_vertices_by_face)]
    dress_vertex_mean_color = np.mean(dress_texture_colors[dress_near_vertex_uvs[:, 0], dress_near_vertex_uvs[:, 1], :], axis=0)

    dress_min_uv = np.min(dress_near_vertex_uvs, axis=0)
    dress_max_uv = np.max(dress_near_vertex_uvs, axis=0)

    diff_color = model_vertex_mean_color - dress_vertex_mean_color

    # テクスチャの処理対象領域内でまだ補正されていない箇所だけ補正する
    for u, v in product(
        [u for u in range(dress_min_uv[1], (dress_max_uv[1] + 1))], [v for v in range(dress_min_uv[0], (dress_max_uv[0] + 1))]
    ):
        if np.sum(filled_dress_texture[u, v]) == 0:
            corrected_dress_texture[u, v, :3] += diff_color
            filled_dress_texture[u, v, :3] = np.where(diff_color == 0, 1, diff_color)

# 補正後の色が0未満または255を超える場合、範囲内にクリップする
corrected_dress_texture = np.clip(corrected_dress_texture, 0, 255)

# 補正後のテクスチャを保存する
corrected_dress_texture_image = Image.fromarray(corrected_dress_texture.astype(np.uint8))
corrected_dress_texture_image.save(correct_dress_texture_path)

logger.info(correct_dress_texture_path)

filled_dress_texture[..., 3] = 255
filled_dress_texture = np.clip(filled_dress_texture, 0, 255)
filled_dress_texture_image = Image.fromarray(filled_dress_texture.astype(np.uint8))
filled_dress_texture_image.save(fill_dress_texture_path)

logger.info(fill_dress_texture_path)
