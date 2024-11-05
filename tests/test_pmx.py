from multiprocessing import freeze_support
from typing import cast

import pytest


def test_Bdef2_get_indexes():
    import numpy as np

    from mlib.pmx.pmx_part import Bdef2

    assert np.isclose(
        np.array([1, 2]),
        Bdef2(1, 2, 0.3).get_indexes(),
    ).all()

    assert np.isclose(
        np.array([2]),
        Bdef2(1, 2, 0.3).get_indexes(0.5),
    ).all()


def test_Bdef4_get_indexes():
    import numpy as np

    from mlib.pmx.pmx_part import Bdef4

    assert np.isclose(
        np.array([1, 2, 3, 4]),
        Bdef4(1, 2, 3, 4, 0.3, 0.2, 0.4, 0.1).get_indexes(),
    ).all()

    assert np.isclose(
        np.array([1, 3]),
        Bdef4(1, 2, 3, 4, 0.3, 0.2, 0.4, 0.1).get_indexes(0.3),
    ).all()


def test_Bdef4_normalized():
    import numpy as np

    from mlib.pmx.pmx_part import Bdef4

    d = Bdef4(1, 2, 3, 4, 5, 6, 7, 8)
    d.normalize()
    assert np.isclose(
        np.array([0.19230769, 0.23076923, 0.26923077, 0.30769231]),
        d.weights,
    ).all()


def test_Material_draw_flg():
    from mlib.pmx.pmx_part import DrawFlg, Material

    m = Material()
    m.draw_flg |= DrawFlg.DOUBLE_SIDED_DRAWING
    assert DrawFlg.DOUBLE_SIDED_DRAWING in m.draw_flg
    assert DrawFlg.DRAWING_EDGE not in m.draw_flg


def test_Bone_copy():
    from mlib.pmx.pmx_part import Bone

    b = Bone()
    assert b != b.copy()


def test_DisplaySlots_init() -> None:
    from mlib.pmx.pmx_collection import DisplaySlots
    from mlib.pmx.pmx_part import DisplaySlot, Switch

    dd = DisplaySlots()
    d01 = DisplaySlot(name="Root", english_name="Root")
    d01.special_flg = Switch.ON
    dd.append(d01)
    d02 = DisplaySlot(name="表情", english_name="Exp")
    d02.special_flg = Switch.ON
    dd.append(d02)

    d1: DisplaySlot = dd[0]
    assert 0 == d1.index
    assert "Root" == d1.name

    d2: DisplaySlot = dd[1]
    assert 1 == d2.index
    assert "表情" == d2.name

    d3: DisplaySlot = dd["表情"]
    assert 1 == d3.index
    assert "表情" == d3.name
    assert Switch.ON == d3.special_flg


def test_read_by_filepath_error():
    import os

    from mlib.domain.exception import MParseException
    from mlib.pmx.pmx_reader import PmxReader

    reader = PmxReader()
    with pytest.raises(MParseException):
        reader.read_by_filepath(os.path.join("tests", "resources", "サンプルモーション.vmd"))


def test_read_by_filepath_ok() -> None:
    import os

    import numpy as np

    from mlib.pmx.pmx_collection import PmxModel
    from mlib.pmx.pmx_part import (
        BoneFlg,
        DeformType,
        DisplayType,
        DrawFlg,
        MorphPanel,
        MorphType,
        RigidBodyCollisionGroup,
        RigidBodyMode,
        RigidBodyShape,
        VertexMorphOffset,
    )
    from mlib.pmx.pmx_reader import PmxReader

    system_bone_cnt = 4

    reader = PmxReader()
    model: PmxModel = reader.read_by_filepath(os.path.join("tests", "resources", "サンプルモデル.pmx"))
    assert b"PMX " == model.signature
    assert 2.0 == model.version
    assert 2 == model.vertex_count
    assert 1 == model.material_count
    assert 2 == model.bone_count
    assert 2 == model.morph_count
    assert 1 == model.rigidbody_count
    assert "v2配布用素体03" == model.name
    assert "sample model" == model.english_name
    # 頂点
    assert np.isclose(
        np.array([0.3187934, 10.7431, -0.6637576]),
        model.vertices[0].position.vector,
    ).all()
    assert np.isclose(
        np.array([-0.4265585, -0.2953186, -0.8548887]),
        model.vertices[0].normal.vector,
    ).all()
    assert np.isclose(
        np.array([0.5220807, 0.552156]),
        model.vertices[0].uv.vector,
    ).all()
    assert DeformType.BDEF2 == model.vertices[0].deform_type
    assert np.isclose(
        np.array([4, 108 + system_bone_cnt]),
        model.vertices[0].deform.get_indexes(),
    ).all()
    assert np.isclose(
        np.array([0.7978904, 0.2021096]),
        model.vertices[0].deform.get_weights(),
    ).all()
    assert 1 == model.vertices[0].edge_factor
    # 面
    assert [2, 1, 0] == model.faces[0].vertices
    # cSpell:disable
    # テクスチャ
    assert "tex\\_09.png" == model.textures[16].name
    assert "tex\\MatcapWarp_01.png" == model.textures[1].name
    # 材質
    assert "00_FaceEyeline" == model.materials[7].name
    assert "N00_000_00_FaceEyeline_00_FACE (Instance)" == model.materials[7].english_name
    # cSpell:enable
    assert np.isclose(
        np.array([1, 1, 1, 1]),
        model.materials[7].diffuse.vector,
    ).all()
    assert np.isclose(
        np.array([0, 0, 0]),
        model.materials[7].specular.vector,
    ).all()
    assert 0 == model.materials[7].specular_factor
    assert np.isclose(
        np.array([0.5, 0.5, 0.5]),
        model.materials[7].ambient.vector,
    ).all()
    assert DrawFlg.DOUBLE_SIDED_DRAWING in model.materials[7].draw_flg
    assert DrawFlg.GROUND_SHADOW in model.materials[7].draw_flg
    assert DrawFlg.DRAWING_ON_SELF_SHADOW_MAPS in model.materials[7].draw_flg
    assert DrawFlg.DRAWING_SELF_SHADOWS in model.materials[7].draw_flg
    assert DrawFlg.DRAWING_EDGE not in model.materials[7].draw_flg
    assert np.isclose(
        np.array([0.2745098, 0.09019607, 0.1254902, 1]),
        model.materials[7].edge_color.vector,
    ).all()
    assert 1 == model.materials[7].edge_size
    assert 16 == model.materials[7].texture_index
    assert 1 == model.materials[7].sphere_texture_index
    # 下半身ボーン
    lower_bone = model.bones[4]
    assert "下半身" == lower_bone.name
    assert "J_Bip_C_Spine" == lower_bone.english_name
    assert np.isclose(
        np.array([0, 12.39097, -0.2011687]),
        lower_bone.position.vector,
    ).all()
    assert 3 == lower_bone.parent_index
    assert BoneFlg.TAIL_IS_BONE not in lower_bone.bone_flg
    assert BoneFlg.CAN_ROTATE in lower_bone.bone_flg
    assert BoneFlg.CAN_TRANSLATE not in lower_bone.bone_flg
    assert BoneFlg.IS_VISIBLE in lower_bone.bone_flg
    assert BoneFlg.CAN_MANIPULATE in lower_bone.bone_flg
    assert BoneFlg.IS_IK not in lower_bone.bone_flg
    assert BoneFlg.IS_EXTERNAL_LOCAL not in lower_bone.bone_flg
    assert BoneFlg.IS_EXTERNAL_ROTATION not in lower_bone.bone_flg
    assert BoneFlg.IS_EXTERNAL_TRANSLATION not in lower_bone.bone_flg
    assert BoneFlg.HAS_FIXED_AXIS not in lower_bone.bone_flg
    assert BoneFlg.HAS_LOCAL_COORDINATE not in lower_bone.bone_flg
    assert BoneFlg.IS_AFTER_PHYSICS_DEFORM not in lower_bone.bone_flg
    assert BoneFlg.IS_EXTERNAL_PARENT_DEFORM not in lower_bone.bone_flg
    assert np.isclose(
        np.array([8.003151e-31, -0.6508856, 0.1564678]),
        lower_bone.tail_position.vector,
    ).all()
    # 左足IKボーン
    left_leg_ik_bone = model.bones[98 + system_bone_cnt]
    assert "左足ＩＫ" == left_leg_ik_bone.name
    assert "leg_IK_L" == left_leg_ik_bone.english_name
    assert np.isclose(
        np.array([0.9644502, 1.647273, 0.4050385]),
        left_leg_ik_bone.position.vector,
    ).all()
    assert 97 + system_bone_cnt == left_leg_ik_bone.parent_index
    assert BoneFlg.TAIL_IS_BONE not in left_leg_ik_bone.bone_flg
    assert BoneFlg.CAN_ROTATE in left_leg_ik_bone.bone_flg
    assert BoneFlg.CAN_TRANSLATE in left_leg_ik_bone.bone_flg
    assert BoneFlg.IS_VISIBLE in left_leg_ik_bone.bone_flg
    assert BoneFlg.CAN_MANIPULATE in left_leg_ik_bone.bone_flg
    assert BoneFlg.IS_IK in left_leg_ik_bone.bone_flg
    assert BoneFlg.IS_EXTERNAL_LOCAL not in left_leg_ik_bone.bone_flg
    assert BoneFlg.IS_EXTERNAL_ROTATION not in left_leg_ik_bone.bone_flg
    assert BoneFlg.IS_EXTERNAL_TRANSLATION not in left_leg_ik_bone.bone_flg
    assert BoneFlg.HAS_FIXED_AXIS not in left_leg_ik_bone.bone_flg
    assert BoneFlg.HAS_LOCAL_COORDINATE not in left_leg_ik_bone.bone_flg
    assert BoneFlg.IS_AFTER_PHYSICS_DEFORM not in left_leg_ik_bone.bone_flg
    assert BoneFlg.IS_EXTERNAL_PARENT_DEFORM not in left_leg_ik_bone.bone_flg
    assert np.isclose(
        np.array([0, 0, 1]),
        left_leg_ik_bone.tail_position.vector,
    ).all()
    if left_leg_ik_bone.ik:
        assert 95 + system_bone_cnt == left_leg_ik_bone.ik.bone_index
        assert 40 == left_leg_ik_bone.ik.loop_count
        assert np.isclose(
            np.array([57.29578, 0, 0]),
            left_leg_ik_bone.ik.unit_rotation.degrees.vector,
        ).all()
        assert 94 + system_bone_cnt == left_leg_ik_bone.ik.links[0].bone_index
        assert left_leg_ik_bone.ik.links[0].angle_limit
        assert np.isclose(
            np.array([-180, 0, 0]),
            left_leg_ik_bone.ik.links[0].min_angle_limit.degrees.vector,
        ).all()
        assert np.isclose(
            np.array([-0.5, 0, 0]),
            left_leg_ik_bone.ik.links[0].max_angle_limit.degrees.vector,
        ).all()
    # 頂点モーフ
    surprised_morph = model.morphs[27]
    assert "びっくり" == surprised_morph.name
    assert "Fcl_EYE_Surprised" == surprised_morph.english_name
    assert MorphPanel.EYE_UPPER_LEFT == surprised_morph.panel
    assert MorphType.VERTEX == surprised_morph.morph_type
    vertex_offset = cast(VertexMorphOffset, surprised_morph.offsets[29])
    assert 8185 == vertex_offset.vertex_index
    assert np.isclose(
        np.array([-0.0001545548, 0.002120972, -4.768372e-07]),
        vertex_offset.position.vector,
    ).all()
    # 表示枠
    right_hand_display_slot = model.display_slots[9]
    assert "右指" == right_hand_display_slot.name
    assert "right hand" == right_hand_display_slot.english_name
    assert DisplayType.BONE == right_hand_display_slot.references[7].display_type
    assert 81 + system_bone_cnt == right_hand_display_slot.references[7].display_index
    # 剛体
    left_knee_rigidbody = model.rigidbodies[20]
    assert "左ひざ" == left_knee_rigidbody.name
    assert "J_Bip_L_LowerLegUpper" == left_knee_rigidbody.english_name
    assert 94 + system_bone_cnt == left_knee_rigidbody.bone_index
    assert RigidBodyMode.STATIC == left_knee_rigidbody.mode
    assert 1 == left_knee_rigidbody.collision_group
    assert RigidBodyCollisionGroup.GROUP01 not in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP02 not in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP03 not in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP04 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP05 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP06 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP07 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP08 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP09 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP10 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP11 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP12 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP13 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP14 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP15 in left_knee_rigidbody.no_collision_group
    assert RigidBodyCollisionGroup.GROUP16 in left_knee_rigidbody.no_collision_group
    assert RigidBodyShape.CAPSULE == left_knee_rigidbody.shape_type
    assert np.isclose(
        np.array([0.6404971, 2.494654, 0]),
        left_knee_rigidbody.shape_size.vector,
    ).all()
    assert np.isclose(
        np.array([0.9472712, 5.526337, 0.4232892]),
        left_knee_rigidbody.shape_position.vector,
    ).all()
    assert np.isclose(
        np.array([-4.5407, 0.00, 0.00]),
        left_knee_rigidbody.shape_rotation.degrees.vector,
    ).all()
    assert 1 == left_knee_rigidbody.param.mass
    assert 0.5 == left_knee_rigidbody.param.linear_damping
    assert 0.5 == left_knee_rigidbody.param.angular_damping
    assert 0 == left_knee_rigidbody.param.restitution
    assert 0 == left_knee_rigidbody.param.friction
    # ジョイント
    left_bust_joint = model.joints[7]
    assert "Bst|左胸接続|左胸下" == left_bust_joint.name
    assert "Bst|LeftBustConnect|LeftBustLower" == left_bust_joint.english_name
    assert 34 == left_bust_joint.rigidbody_index_a
    assert 33 == left_bust_joint.rigidbody_index_b
    assert np.isclose(
        np.array([0.9984654, 14.25822, -1.298016]),
        left_bust_joint.position.vector,
    ).all()
    assert np.isclose(
        np.array([0, 0, 0]),
        left_bust_joint.rotation.degrees.vector,
    ).all()
    assert np.isclose(
        np.array([0, 0, 0]),
        left_bust_joint.param.translation_limit_min.vector,
    ).all()
    assert np.isclose(
        np.array([0, 0, 0]),
        left_bust_joint.param.translation_limit_max.vector,
    ).all()
    assert np.isclose(
        np.array([-15.1515, 0, 0]),
        left_bust_joint.param.rotation_limit_min.degrees.vector,
    ).all()
    assert np.isclose(
        np.array([15.1515, 0, 0]),
        left_bust_joint.param.rotation_limit_max.degrees.vector,
    ).all()
    assert np.isclose(
        np.array([0, 0, 0]),
        left_bust_joint.param.spring_constant_translation.vector,
    ).all()
    assert np.isclose(
        np.array([66.6667, 33.3333, 0]),
        left_bust_joint.param.spring_constant_rotation.vector,
    ).all()
    # ボーンツリー
    bone_tree = model.bone_trees["左手首"]
    ["全ての親", "センター", "グルーブ", "腰", "上半身", "上半身2", "上半身3", "左肩P", "左肩", "左肩C", "左腕", "左腕捩", "左ひじ", "左手捩", "左手首"] == bone_tree.names


def test_get_vertices_by_material() -> None:
    import os

    from mlib.pmx.pmx_collection import PmxModel
    from mlib.pmx.pmx_reader import PmxReader

    reader = PmxReader()
    model: PmxModel = reader.read_by_filepath(os.path.join("tests", "resources", "サンプルモデル.pmx"))
    model.update_vertices_by_material()
    assert model.vertices_by_materials


def test_read_by_filepath_ok_tree() -> None:
    import os

    from mlib.pmx.pmx_collection import PmxModel
    from mlib.pmx.pmx_reader import PmxReader

    reader = PmxReader()
    model: PmxModel = reader.read_by_filepath(os.path.join("tests", "resources", "ボーンツリーテストモデル.pmx"))
    # ボーンツリー
    bone_tree = model.bone_trees["左人指先"]
    [
        "全ての親",
        "センター",
        "グルーブ",
        "腰",
        "上半身",
        "上半身2",
        "首根元",
        "左肩根元",
        "左肩P",
        "左肩",
        "左腕YZ",
        "左腕捩YZ",
        "左腕捩X",
        "左ひじYZ",
        "左手捩YZ",
        "左手捩X",
        "左手捩6",
        "左手首R",
        "左手首2",
        "左人指１",
        "左人指２",
        "左人指３",
        "左人指先",
    ] == bone_tree.names

    new_bone_trees = model.bone_trees.filter("左人指先", "右人指先")
    assert "全ての親" == new_bone_trees["左人指先"][0].name
    assert "左人指先" == new_bone_trees["左人指先"][-1].name
    assert "全ての親" == new_bone_trees["右人指先"][0].name
    assert "右人指先" == new_bone_trees["右人指先"][-1].name

    range_bone_tree = model.bone_trees["右手首"].filter("上半身", "右手首")
    assert [
        "上半身",
        "上半身2",
        "首根元",
        "右肩根元",
        "右肩P",
        "右肩",
        "右肩C",
        "右腕",
        "右腕捩",
        "右ひじ",
        "右手捩",
        "右手首",
    ] == range_bone_tree.names

    slice1_bone_tree = range_bone_tree.range(4, 6)
    assert 2 == len(slice1_bone_tree)
    assert ["右肩P", "右肩"] == [b.name for b in slice1_bone_tree]

    slice2_bone_tree = range_bone_tree.range(9)
    assert 3 == len(slice2_bone_tree)
    assert ["右ひじ", "右手捩", "右手首"] == [b.name for b in slice2_bone_tree]

    assert model.bone_trees.is_in_standard("右腕")
    assert model.bone_trees.is_in_standard("左腕捩YZ")
    assert model.bone_trees.is_in_standard("右薬指先")
    assert not model.bone_trees.is_in_standard("左エリIK")
    assert not model.bone_trees.is_in_standard("左ひざ2先")


def test_read_by_filepath_complicated() -> None:
    from mlib.pmx.pmx_collection import PmxModel
    from mlib.pmx.pmx_reader import PmxReader

    reader = PmxReader()
    # cSpell:disable
    model: PmxModel = reader.read_by_filepath(
        "D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\刀剣乱舞\\025_一期一振\\一期一振 ちゃむ式 20211211\\01_10_極_一期_ちゃむ20211211.pmx",
    )
    assert "極 一期 ちゃむ" == model.name
    # cSpell:enable


def test_save_pmx01() -> None:
    import os

    from mlib.pmx.pmx_collection import PmxModel
    from mlib.pmx.pmx_reader import PmxReader
    from mlib.pmx.pmx_writer import PmxWriter

    input_path = os.path.join("tests", "resources", "柱.pmx")
    model: PmxModel = PmxReader().read_by_filepath(input_path)
    output_path = os.path.join("tests", "resources", "result.pmx")
    PmxWriter(model, output_path).save()

    with open(input_path, "rb") as f:
        input_model = f.read()

    with open(output_path, "rb") as f:
        output_model = f.read()

    assert input_model == output_model


def test_save_pmx02() -> None:
    import os

    from mlib.pmx.pmx_collection import PmxModel
    from mlib.pmx.pmx_reader import PmxReader
    from mlib.pmx.pmx_writer import PmxWriter

    input_path = os.path.join("tests", "resources", "曲げ柱tex.pmx")
    model: PmxModel = PmxReader().read_by_filepath(input_path)
    output_path = os.path.join("tests", "resources", "result.pmx")
    PmxWriter(model, output_path).save()

    with open(input_path, "rb") as f:
        input_model = f.read()

    with open(output_path, "rb") as f:
        output_model = f.read()

    assert input_model == output_model


def test_save_pmx03() -> None:
    import os

    from mlib.pmx.pmx_collection import PmxModel
    from mlib.pmx.pmx_reader import PmxReader
    from mlib.pmx.pmx_writer import PmxWriter

    input_path = os.path.join("tests", "resources", "サンプルモデル.pmx")
    model: PmxModel = PmxReader().read_by_filepath(input_path)
    output_path = os.path.join("tests", "resources", "result.pmx")
    PmxWriter(model, output_path).save()

    with open(input_path, "rb") as f:
        input_model = f.read()

    with open(output_path, "rb") as f:
        output_model = f.read()

    assert input_model == output_model


def test_insert_bone() -> None:
    import os

    from mlib.pmx.pmx_collection import PmxModel
    from mlib.pmx.pmx_part import Bone, BoneMorphOffset
    from mlib.pmx.pmx_reader import PmxReader
    from mlib.pmx.pmx_writer import PmxWriter

    input_path = os.path.join("tests", "resources", "サンプルモデル.pmx")
    model: PmxModel = PmxReader().read_by_filepath(input_path)

    insert_bone = Bone(name="追加ボーン", index=model.bones["上半身"].index + 1)
    insert_bone.parent_index = model.bones["上半身"].index
    model.insert_bone(insert_bone)
    system_bone_cnt = 4

    v = model.vertices[15724]
    assert 10 + system_bone_cnt == v.deform.indexes[0]
    assert 135 + system_bone_cnt == v.deform.indexes[1]

    lower_bone = model.bones["下半身"]
    assert 4 == lower_bone.index
    assert 3 == lower_bone.parent_index

    upper_bone = model.bones["上半身"]
    assert 5 + 1 == upper_bone.index
    assert 3 == upper_bone.parent_index

    inserted_bone = model.bones["追加ボーン"]
    assert 6 + 1 == inserted_bone.index
    assert 5 + 1 == inserted_bone.parent_index

    upper2_bone = model.bones["上半身2"]
    assert 7 + 1 == upper2_bone.index
    assert 6 + 1 == upper2_bone.parent_index
    assert 8 + 1 == upper2_bone.tail_index

    left_eye_bone = model.bones["左目"]
    assert 12 + system_bone_cnt == left_eye_bone.index
    assert 10 + system_bone_cnt == left_eye_bone.parent_index
    assert -1 == left_eye_bone.tail_index

    left_leg_ik_bone = model.bones["左足ＩＫ"]
    assert 99 + system_bone_cnt == left_leg_ik_bone.index
    assert 98 + system_bone_cnt == left_leg_ik_bone.parent_index
    assert left_leg_ik_bone.ik
    assert 96 + system_bone_cnt == left_leg_ik_bone.ik.bone_index
    assert 95 + system_bone_cnt == left_leg_ik_bone.ik.links[0].bone_index
    assert 94 + system_bone_cnt == left_leg_ik_bone.ik.links[1].bone_index

    e_morph = model.morphs["えボーン"]
    assert isinstance(e_morph.offsets[0], BoneMorphOffset)
    assert 17 + system_bone_cnt == e_morph.offsets[0].bone_index
    assert isinstance(e_morph.offsets[1], BoneMorphOffset)
    assert 18 + system_bone_cnt == e_morph.offsets[1].bone_index
    assert isinstance(e_morph.offsets[2], BoneMorphOffset)
    assert 19 + system_bone_cnt == e_morph.offsets[2].bone_index

    trunk_display_slot = model.display_slots["体幹"]
    assert 3 == trunk_display_slot.references[0].display_index
    assert 4 == trunk_display_slot.references[1].display_index
    assert 5 + 1 == trunk_display_slot.references[2].display_index
    assert 7 + 1 == trunk_display_slot.references[3].display_index
    assert 8 + 1 == trunk_display_slot.references[4].display_index
    assert 9 + system_bone_cnt == trunk_display_slot.references[5].display_index
    assert 10 + system_bone_cnt == trunk_display_slot.references[6].display_index

    upper_rigidbody = model.rigidbodies["上半身"]
    assert 5 + 1 == upper_rigidbody.bone_index

    head_rigidbody = model.rigidbodies["頭"]
    assert 10 + system_bone_cnt == head_rigidbody.bone_index

    output_path = os.path.join("tests", "resources", "result.pmx")
    PmxWriter(model, output_path).save()


def test_insert_standard_bone() -> None:
    import os

    from mlib.pmx.pmx_collection import PmxModel
    from mlib.pmx.pmx_reader import PmxReader
    from mlib.pmx.pmx_writer import PmxWriter
    from mlib.vmd.vmd_collection import VmdMotion

    input_path = os.path.join("tests", "resources", "サンプル標準モデル.pmx")
    model: PmxModel = PmxReader().read_by_filepath(input_path)

    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("全ての親", bone_matrixes)

    assert 0 == model.bones["全ての親"].index
    assert -1 == model.bones["全ての親"].parent_index

    for b in model.bones:
        if b.name in ["センター", "左足ＩＫ", "右足ＩＫ"]:
            assert model.bones["全ての親"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name
        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("グルーブ", bone_matrixes)

    for b in model.bones:
        if b.name in ["上半身", "下半身", "ﾈｸﾀｲＩＫ", "左髪ＩＫ", "右髪ＩＫ"]:
            assert model.bones["グルーブ"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("腰", bone_matrixes)

    for b in model.bones:
        if b.name in ["上半身", "下半身", "ﾈｸﾀｲＩＫ", "左髪ＩＫ", "右髪ＩＫ"]:
            assert model.bones["腰"].index == b.parent_index
        elif b.name in ["左足", "左足D"]:
            assert model.bones["腰キャンセル左"].index == b.parent_index
        elif b.name in ["右足", "右足D"]:
            assert model.bones["腰キャンセル右"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("上半身2", bone_matrixes)

    # output_path = os.path.join("tests", "resources", "result.pmx")
    # PmxWriter(model, output_path, include_system=True).save()

    for b in model.bones:
        if b.name in ["首根元"]:
            assert model.bones["上半身2"].index == b.parent_index
        elif b.name in ["首", "ﾈｸﾀｲ１", "左肩根元", "右肩根元"]:
            assert model.bones["首根元"].index == b.parent_index
        elif b.name in ["左肩"]:
            assert model.bones["左肩根元"].index == b.parent_index
        elif b.name in ["右肩"]:
            assert model.bones["右肩根元"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in ["上半身"]:
            assert model.bones["上半身2"].index == b.tail_index
        elif b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("右肩P", bone_matrixes)

    for b in model.bones:
        if b.name in ["右肩"]:
            assert model.bones["右肩P"].index == b.parent_index
        elif b.name in ["右腕"]:
            assert model.bones["右肩C"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("左肩P", bone_matrixes)

    for b in model.bones:
        if b.name in ["左肩"]:
            assert model.bones["左肩P"].index == b.parent_index
        elif b.name in ["左腕"]:
            assert model.bones["左肩C"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("左腕捩", bone_matrixes)

    for b in model.bones:
        if b.name in ["左ひじ"]:
            assert model.bones["左腕捩"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("右腕捩", bone_matrixes)

    for b in model.bones:
        if b.name in ["右ひじ"]:
            assert model.bones["右腕捩"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("右手捩", bone_matrixes)

    for b in model.bones:
        if b.name in ["右手首", "右袖"]:
            assert model.bones["右手捩"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("左手捩", bone_matrixes)

    for b in model.bones:
        if b.name in ["左手首", "左袖"]:
            assert model.bones["左手捩"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("左足IK親", bone_matrixes)

    for b in model.bones:
        if b.name in ["左足ＩＫ"]:
            assert model.bones["左足IK親"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("右足IK親", bone_matrixes)

    for b in model.bones:
        if b.name in ["右足ＩＫ"]:
            assert model.bones["右足IK親"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("右親指０", bone_matrixes)

    for b in model.bones:
        if b.name in ["右親指１"]:
            assert model.bones["右親指０"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    parent_names = dict(
        [
            (b.name, (model.bones[b.parent_index].name if b.parent_index >= 0 else None))
            for b in model.bones
            if b.index >= 0 and b.name != "全ての親"
        ]
    )
    tail_names = dict([(b.name, model.bones[b.tail_index].name) for b in model.bones if b.tail_index >= 0])
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("左親指０", bone_matrixes)

    for b in model.bones:
        if b.name in ["左親指１"]:
            assert model.bones["左親指０"].index == b.parent_index
        elif b.name in parent_names:
            assert parent_names[b.name] == model.bones[b.parent_index].name

        if b.name in tail_names and b.tail_index >= 0:
            assert tail_names[b.name] == model.bones[b.tail_index].name

    model.setup()
    model.update_vertices_by_bone()
    # -------
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("右足D", bone_matrixes)
    assert model.bones["右足D"].layer == 1
    assert model.bones["右足D"].parent_index == model.bones["腰キャンセル右"].index
    assert model.bones["右足D"].effect_index == model.bones["右足"].index
    assert model.bones["右足"].parent_index == model.bones["腰キャンセル右"].index

    model.setup()
    model.update_vertices_by_bone()
    # -------
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("右ひざD", bone_matrixes)
    assert model.bones["右ひざD"].layer == 1
    assert model.bones["右ひざD"].parent_index == model.bones["右足D"].index
    assert model.bones["右ひざD"].effect_index == model.bones["右ひざ"].index
    assert model.bones["右ひざ"].parent_index == model.bones["右足"].index

    model.setup()
    model.update_vertices_by_bone()
    # -------
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("右足首D", bone_matrixes)
    assert model.bones["右足首D"].layer == 1
    assert model.bones["右足首D"].parent_index == model.bones["右ひざD"].index
    assert model.bones["右足首D"].effect_index == model.bones["右足首"].index
    assert model.bones["右足首"].parent_index == model.bones["右ひざ"].index

    model.setup()
    model.update_vertices_by_bone()
    # -------
    bone_matrixes = VmdMotion().animate_bone([0], model, model.bones.tail_bone_names)
    model.insert_standard_bone("右足先EX", bone_matrixes)
    assert model.bones["右足先EX"].layer == 1
    assert model.bones["右足先EX"].parent_index == model.bones["右足首D"].index

    # ウェイト置き換え
    model.replace_standard_weights(["右足D", "右ひざD", "右足首D", "上半身2", "右足先EX", "右親指０", "右腕捩", "右手捩"])

    output_path = os.path.join("tests", "resources", "result.pmx")
    PmxWriter(model, output_path).save()


if __name__ == "__main__":
    freeze_support()
    pytest.main()
