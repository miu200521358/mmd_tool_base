import argparse
import os
import sys
from winsound import SND_ALIAS, PlaySound

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mlib.domain.math import MVector3D, MVector4D  # noqa: E402
from mlib.pmx.bone_setting import BoneFlg  # noqa: E402
from mlib.pmx.pmx_collection import PmxModel  # noqa: E402
from mlib.pmx.pmx_part import (  # noqa: E402
    Bdef1,
    DisplaySlot,
    DisplaySlotReference,
    DrawFlg,
    Face,
    Material,
    Vertex,
)
from mlib.pmx.pmx_reader import PmxReader  # noqa: E402
from mlib.pmx.pmx_writer import PmxWriter  # noqa: E402
from mlib.utils import file_utils  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--path", default="", type=str)
parser.add_argument("--all", default=False, type=bool)
args, argv = parser.parse_known_args()

pmx_reader = PmxReader()
model: PmxModel = pmx_reader.read_by_filepath(
    args.path
    # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/025_一期一振/一期一振 peco式 20190316/一期一振_通常衣装_ver1.00.pmx"
    # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/112_膝丸/膝丸mkmk009b 刀剣乱舞/膝丸mkmk009b/膝丸mkmk009b_準標準.pmx"
    # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/ゲーム/原神/バーバラ/芭芭拉.pmx"
    # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/らぶ式ミク/らぶ式ミク_準標準_袖なし.pmx"
    # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/らぶ式ミク/sizing_らぶ式ミク_準標準_袖なし_青.pmx"
    # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Appearance Miku/Appearance Miku_準標準.pmx"
    # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式初音ミク・アペンドVer1.10/Tda式初音ミク・アペンド_Ver1.10.pmx"
)
model.setup()

OUTPUT_CENTER_NAMES = ["センター"]
OUTPUT_GROOVE_NAMES = ["グルーブ"]
OUTPUT_TRUNK_NAMES = [
    "下半身",
    "上半身",
    "上半身2",
    "上半身3",
]
OUTPUT_BONE_NAMES = [
    "左足",
    "左ひざ",
    "左足首",
    "右足",
    "右ひざ",
    "右足首",
    "左肩",
    "左腕",
    "左腕捩",
    "左ひじ",
    "左手捩",
    "左手首",
    "右肩",
    "右腕",
    "右腕捩",
    "右ひじ",
    "右手捩",
    "右手首",
    "首",
    "首根元",
    "頭",
    "左肩根元",
    "左親指０",
    "左親指１",
    "左親指２",
    "左親指先",
    "左人指１",
    "左人指２",
    "左人指３",
    "左人指先",
    "左中指１",
    "左中指２",
    "左中指３",
    "左中指先",
    "左薬指１",
    "左薬指２",
    "左薬指３",
    "左薬指先",
    "左小指１",
    "左小指２",
    "左小指３",
    "左小指先",
    "右肩根元",
    "右親指０",
    "右親指１",
    "右親指２",
    "右親指先",
    "右人指１",
    "右人指２",
    "右人指３",
    "右人指先",
    "右中指１",
    "右中指２",
    "右中指３",
    "右中指先",
    "右薬指１",
    "右薬指２",
    "右薬指３",
    "右薬指先",
    "右小指１",
    "右小指２",
    "右小指３",
    "右小指先",
    "腰キャンセル左",
    "腰キャンセル右",
]
OUTPUT_TWIST_NAMES = [
    "左腕捩",
    "左手捩",
    "右腕捩",
    "右手捩",
]

WIDTH = 0.1
NORMAL_VEC = MVector3D(0, 1, 0)

model_dir_path, model_file_name, model_ext = file_utils.separate_path(model.path)
if args.all:
    model_file_name += "_all"

stick_model = PmxModel(os.path.join(model_dir_path, f"bone_{model_file_name}.pmx"))
stick_model.model_name = "①" + model_file_name + "[Bone]"
stick_model.bones = model.bones.copy()
stick_model.initialize_display_slots()

# センターボーン材質作成
center_material = Material(name="センター材質")
center_material.diffuse = MVector4D(1, 1, 1, 1)
center_material.ambient = MVector3D(1, 0, 0)
center_material.draw_flg = DrawFlg.DOUBLE_SIDED_DRAWING
stick_model.materials.append(center_material)

# グルーブボーン材質作成
groove_material = Material(name="グルーブ材質")
groove_material.diffuse = MVector4D(1, 1, 1, 1)
groove_material.ambient = MVector3D(0, 0, 1)
groove_material.draw_flg = DrawFlg.DOUBLE_SIDED_DRAWING
stick_model.materials.append(groove_material)

# 体幹ボーン材質作成
trunk_material = Material(name="体幹ボーン材質")
trunk_material.diffuse = MVector4D(1, 1, 1, 1)
trunk_material.ambient = MVector3D(0, 1, 1)
trunk_material.draw_flg = DrawFlg.DOUBLE_SIDED_DRAWING
stick_model.materials.append(trunk_material)

# 四肢ボーン材質作成
bone_material = Material(name="四肢ボーン材質")
bone_material.diffuse = MVector4D(1, 1, 1, 1)
bone_material.ambient = MVector3D(1, 1, 0)
bone_material.draw_flg = DrawFlg.DOUBLE_SIDED_DRAWING
stick_model.materials.append(bone_material)

# 捩りボーン材質作成
twist_material = Material(name="捩り材質")
twist_material.diffuse = MVector4D(1, 1, 1, 1)
twist_material.ambient = MVector3D(0, 1, 0)
twist_material.draw_flg = DrawFlg.DOUBLE_SIDED_DRAWING
stick_model.materials.append(twist_material)

# その他ボーン材質作成
other_material = Material(name="その他材質")
other_material.diffuse = MVector4D(1, 1, 1, 1)
other_material.ambient = MVector3D(1, 0, 1)
other_material.draw_flg = DrawFlg.DOUBLE_SIDED_DRAWING
stick_model.materials.append(other_material)

stick_model.display_slots["Root"].references.append(
    DisplaySlotReference(display_index=stick_model.bones["全ての親"].index)
)

for ds in model.display_slots:
    if ds.name in ("表情", "Root"):
        continue
    stick_ds = DisplaySlot(name=ds.name)
    stick_model.display_slots.append(stick_ds)
    for r in ds.references:
        stick_ds.references.append(
            DisplaySlotReference(
                display_index=stick_model.bones[model.bones[r.display_index].name].index
            )
        )

target_bone_names = (
    [
        bone.name
        for bone in model.bones
        if True
        not in [
            exclude_name in bone.name
            for exclude_name in [
                "エッジ",
                "帽子",
                "リボン",
                "眼鏡",
                "耳",
                "髪",
                "ER",
                "鼻",
                "目",
                "帯",
                "fs",
                "袖B",
                "袖C",
                "袖D",
                "袖E",
                "靴",
                "skirt",
                "掴",
            ]
        ]
    ]
    if args.all
    else (
        OUTPUT_CENTER_NAMES
        + OUTPUT_GROOVE_NAMES
        + OUTPUT_TRUNK_NAMES
        + OUTPUT_BONE_NAMES
        + OUTPUT_TWIST_NAMES
    )
)

print(target_bone_names)

for bone_name in target_bone_names:
    if bone_name not in stick_model.bones:
        continue

    bone = stick_model.bones[bone_name]
    parent_bone_index = (
        stick_model.bones[bone.parent_index].index
        if bone.parent_index >= 0
        else bone.index
    )
    if BoneFlg.IS_VISIBLE not in bone.bone_flg:
        # 非表示ボーンの場合、表示する
        bone.bone_flg |= BoneFlg.IS_VISIBLE | BoneFlg.CAN_MANIPULATE

    from_pos = bone.position
    if bone.name in OUTPUT_CENTER_NAMES:
        tail_pos = MVector3D(0, 1.5, 0) + bone.position
        parent_bone_index = bone.index
    elif bone.name in OUTPUT_GROOVE_NAMES:
        tail_pos = MVector3D(0, -1.5, 0) + bone.position
        parent_bone_index = bone.index
    elif bone.name in OUTPUT_TWIST_NAMES:
        local_y_vector = MVector3D(0, 0.5, 0)
        local_x_vector = (
            bone.position - stick_model.bones[bone.parent_index].position
        ).normalized()
        local_z_vector = local_y_vector.cross(bone.local_x_vector).normalized()

        tail_pos = local_z_vector + bone.position
        parent_bone_index = bone.index
    elif bone.name == "下半身":
        if args.all:
            tail_pos = MVector3D(0, -1, 0) + bone.position
            parent_bone_index = bone.index
        else:
            tail_pos = model.bones["足中心"].position
    elif "腰キャンセル" in bone.name:
        if args.all:
            tail_pos = bone.position
            parent_bone_index = bone.index
        else:
            tail_pos = model.bones["足中心"].position
    elif bone.name in ("右腕", "左腕"):
        tail_pos = model.bones[f"{bone.name[0]}ひじ"].position
        parent_bone_index = model.bones[f"{bone.name[0]}ひじ"].index
    elif bone.name in ("右ひじ", "左ひじ"):
        tail_pos = model.bones[f"{bone.name[0]}手首"].position
        parent_bone_index = model.bones[f"{bone.name[0]}手首"].index
    else:
        tail_pos = bone.tail_relative_position + bone.position

    # FROMからTOまで面を生成
    v1 = Vertex()
    v1.position = from_pos
    v1.normal = NORMAL_VEC
    v1.deform = Bdef1(bone.index)
    stick_model.vertices.append(v1)

    v2 = Vertex()
    v2.position = tail_pos
    v2.normal = NORMAL_VEC
    v2.deform = Bdef1(parent_bone_index)
    stick_model.vertices.append(v2)

    v3 = Vertex()
    v3.position = from_pos + MVector3D(WIDTH, 0, 0)
    v3.normal = NORMAL_VEC
    v3.deform = Bdef1(bone.index)
    stick_model.vertices.append(v3)

    v4 = Vertex()
    v4.position = tail_pos + MVector3D(WIDTH, 0, 0)
    v4.normal = NORMAL_VEC
    v4.deform = Bdef1(parent_bone_index)
    stick_model.vertices.append(v4)

    v5 = Vertex()
    v5.position = from_pos + MVector3D(WIDTH, WIDTH, 0)
    v5.normal = NORMAL_VEC
    v5.deform = Bdef1(bone.index)
    stick_model.vertices.append(v5)

    v6 = Vertex()
    v6.position = tail_pos + MVector3D(WIDTH, WIDTH, 0)
    v6.normal = NORMAL_VEC
    v6.deform = Bdef1(parent_bone_index)
    stick_model.vertices.append(v6)

    v7 = Vertex()
    v7.position = from_pos + MVector3D(0, 0, WIDTH)
    v7.normal = NORMAL_VEC
    v7.deform = Bdef1(bone.index)
    stick_model.vertices.append(v7)

    v8 = Vertex()
    v8.position = tail_pos + MVector3D(0, 0, WIDTH)
    v8.normal = NORMAL_VEC
    v8.deform = Bdef1(parent_bone_index)
    stick_model.vertices.append(v8)

    stick_model.faces.append(
        Face(vertex_index0=v1.index, vertex_index1=v2.index, vertex_index2=v3.index)
    )
    stick_model.faces.append(
        Face(vertex_index0=v3.index, vertex_index1=v2.index, vertex_index2=v4.index)
    )
    stick_model.faces.append(
        Face(vertex_index0=v3.index, vertex_index1=v4.index, vertex_index2=v5.index)
    )
    stick_model.faces.append(
        Face(vertex_index0=v5.index, vertex_index1=v4.index, vertex_index2=v6.index)
    )
    stick_model.faces.append(
        Face(vertex_index0=v5.index, vertex_index1=v6.index, vertex_index2=v7.index)
    )
    stick_model.faces.append(
        Face(vertex_index0=v7.index, vertex_index1=v6.index, vertex_index2=v8.index)
    )
    stick_model.faces.append(
        Face(vertex_index0=v7.index, vertex_index1=v8.index, vertex_index2=v1.index)
    )
    stick_model.faces.append(
        Face(vertex_index0=v1.index, vertex_index1=v8.index, vertex_index2=v2.index)
    )

    if bone.name in OUTPUT_CENTER_NAMES:
        center_material.vertices_count += 24
    elif bone.name in OUTPUT_GROOVE_NAMES:
        groove_material.vertices_count += 24
    elif bone.name in OUTPUT_TWIST_NAMES:
        twist_material.vertices_count += 24
    elif bone.name in OUTPUT_TRUNK_NAMES:
        trunk_material.vertices_count += 24
    elif bone.name in OUTPUT_BONE_NAMES:
        bone_material.vertices_count += 24
    else:
        other_material.vertices_count += 24

PmxWriter(stick_model, stick_model.path, include_system=True).save()

stick_model.path = os.path.join(model_dir_path, f"bone_{model_file_name}_2.pmx")
stick_model.model_name = "②" + model_file_name + "[Bone]"
trunk_material.ambient = MVector3D(1, 0, 0)
bone_material.ambient = MVector3D(0, 1, 0)
PmxWriter(stick_model, stick_model.path, include_system=True).save()

stick_model.path = os.path.join(model_dir_path, f"bone_{model_file_name}_3.pmx")
stick_model.model_name = "③" + model_file_name + "[Bone]"
trunk_material.ambient = MVector3D(0, 0, 1)
bone_material.ambient = MVector3D(1, 0, 0)
PmxWriter(stick_model, stick_model.path, include_system=True).save()

PlaySound("SystemAsterisk", SND_ALIAS)
