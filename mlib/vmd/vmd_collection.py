import os
from bisect import bisect_left
from functools import lru_cache
from math import acos, degrees
from typing import Optional

import numpy as np

from mlib.base.collection import BaseHashModel, BaseIndexNameDictModel, BaseIndexNameDictWrapperModel
from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MMatrix4x4List, MQuaternion, MVector3D, MVector4D
from mlib.pmx.pmx_collection import BoneTree, PmxModel
from mlib.pmx.pmx_part import (
    Bone,
    BoneMorphOffset,
    GroupMorphOffset,
    Material,
    MaterialMorphCalcMode,
    MaterialMorphOffset,
    MorphType,
    ShaderMaterial,
    UvMorphOffset,
    VertexMorphOffset,
)
from mlib.pmx.shader import MShader
from mlib.vmd.vmd_part import VmdBoneFrame, VmdCameraFrame, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame
from mlib.vmd.vmd_tree import VmdBoneFrameTrees

logger = MLogger(os.path.basename(__file__), level=1)


class VmdBoneNameFrames(BaseIndexNameDictModel[VmdBoneFrame]):
    """
    ボーン名別キーフレ辞書
    """

    __slots__ = (
        "data",
        "name",
        "cache",
        "_names",
        "_indexes",
        "_iter_index",
        "_ik_indexes",
        "_size",
    )

    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self._ik_indexes: list[int] = []

    def __getitem__(self, key: int | str) -> VmdBoneFrame:
        if isinstance(key, str):
            return VmdBoneFrame(name=key, index=0)

        if key in self.data:
            return self.get_by_index(key)

        # キーフレがない場合、生成したのを返す（保持はしない）
        prev_index, middle_index, next_index = self.range_indexes(key)

        # prevとnextの範囲内である場合、補間曲線ベースで求め直す
        return self.calc(
            prev_index,
            middle_index,
            next_index,
        )

    def append(self, value: VmdBoneFrame, is_sort: bool = True):
        if value.ik_rotation is not None and value.index not in self._ik_indexes:
            self._ik_indexes.append(value.index)
            self._ik_indexes.sort()
        super().append(value, is_sort)

    def calc(self, prev_index: int, index: int, next_index: int) -> VmdBoneFrame:
        if index in self.data:
            return self.data[index]

        if index in self.cache:
            bf = self.cache[index]
        else:
            bf = VmdBoneFrame(name=self.name, index=index)
            self.cache[index] = bf

        if prev_index == next_index:
            if next_index == index:
                # 全くキーフレがない場合、そのまま返す
                return bf

            # FKのprevと等しい場合、指定INDEX以前がないので、その次のをコピーして返す
            bf.position = self.data[next_index].position.copy()
            bf.local_position = self.data[next_index].local_position.copy()
            bf.rotation = self.data[next_index].rotation.copy()
            bf.position2 = self.data[next_index].position2.copy()
            bf.rotation2 = self.data[next_index].rotation2.copy()
            bf.scale2 = self.data[next_index].scale2.copy()
            bf.local_rotation = self.data[next_index].local_rotation.copy()
            bf.scale = self.data[next_index].scale.copy()
            bf.local_scale = self.data[next_index].local_scale.copy()
            return bf

        prev_bf = self.data[prev_index] if prev_index in self else VmdBoneFrame(name=self.name, index=prev_index)
        next_bf = self.data[next_index] if next_index in self else VmdBoneFrame(name=self.name, index=next_index)

        slice_idx = bisect_left(self._ik_indexes, index)
        prev_ik_indexes = self._ik_indexes[:slice_idx]
        next_ik_indexes = self._ik_indexes[slice_idx:]

        prev_ik_index = prev_ik_indexes[-1] if prev_ik_indexes else prev_index
        prev_ik_rotation = self.data[prev_ik_index].ik_rotation or MQuaternion() if prev_ik_index in self.data else MQuaternion()

        next_ik_index = next_ik_indexes[0] if next_ik_indexes else next_index
        next_ik_rotation = self.data[next_ik_index].ik_rotation or MQuaternion() if next_ik_index in self.data else prev_ik_rotation

        # 補間結果Yは、FKキーフレ内で計算する
        ry, xy, yy, zy = next_bf.interpolations.evaluate(prev_index, index, next_index)

        # IK用回転
        bf.ik_rotation = MQuaternion.slerp(prev_ik_rotation, next_ik_rotation, ry)

        # FK用回転
        bf.rotation = MQuaternion.slerp(prev_bf.rotation, next_bf.rotation, ry)

        # 移動
        bf.position = MVector3D.calc_by_ratio(prev_bf.position, next_bf.position, xy, yy, zy)

        # スケール
        bf.scale = MVector3D.calc_by_ratio(prev_bf.scale, next_bf.scale, xy, yy, zy)

        # 第二回転
        bf.rotation2 = MQuaternion.slerp(prev_bf.rotation2, next_bf.rotation2, ry)

        # 第二移動
        bf.position2 = MVector3D.calc_by_ratio(prev_bf.position2, next_bf.position2, xy, yy, zy)

        # 第二スケール
        bf.scale2 = MVector3D.calc_by_ratio(prev_bf.scale2, next_bf.scale2, xy, yy, zy)

        # ローカル回転
        bf.local_rotation = MQuaternion.slerp(prev_bf.local_rotation, next_bf.local_rotation, ry)

        # ローカル移動
        bf.local_position = MVector3D.calc_by_ratio(prev_bf.local_position, next_bf.local_position, xy, yy, zy)

        # ローカルスケール
        bf.local_scale = MVector3D.calc_by_ratio(prev_bf.local_scale, next_bf.local_scale, xy, yy, zy)

        return bf


class VmdBoneFrames(BaseIndexNameDictWrapperModel[VmdBoneNameFrames]):
    """
    ボーンキーフレ辞書
    """

    __slots__ = (
        "data",
        "cache",
        "cache_poses",
        "cache_qqs",
        "cache_scales",
        "cache_poses2",
        "cache_qqs2",
        "cache_scales2",
        "cache_local_poses",
        "cache_local_qqs",
        "cache_local_scales",
        "_names",
        "_iter_index",
        "_size",
    )

    def __init__(self) -> None:
        super().__init__()
        self.cache_poses: dict[tuple[int, str, int], MVector3D] = {}
        self.cache_qqs: dict[tuple[int, str, int], MQuaternion] = {}
        self.cache_scales: dict[tuple[int, str, int], MVector3D] = {}
        self.cache_poses2: dict[tuple[int, str, int], np.ndarray] = {}
        self.cache_qqs2: dict[tuple[int, str, int], np.ndarray] = {}
        self.cache_scales2: dict[tuple[int, str, int], np.ndarray] = {}
        self.cache_local_poses: dict[tuple[int, str, int], np.ndarray] = {}
        self.cache_local_qqs: dict[tuple[int, str, int], np.ndarray] = {}
        self.cache_local_scales: dict[tuple[int, str, int], np.ndarray] = {}

    def create(self, key: str) -> VmdBoneNameFrames:
        return VmdBoneNameFrames(name=key)

    def clear(self) -> None:
        self.cache_poses = {}
        self.cache_qqs = {}
        self.cache_scales = {}
        self.cache_poses2 = {}
        self.cache_qqs2 = {}
        self.cache_scales2 = {}
        self.cache_local_poses = {}
        self.cache_local_qqs = {}
        self.cache_local_scales = {}

    @property
    def max_fno(self) -> int:
        return max([max(self[bname].indexes + [0]) for bname in self.names] + [0])

    def get_matrix_by_indexes(
        self,
        fnos: list[int],
        bone_names: list[str],
        model: PmxModel,
        append_ik: bool = True,
        morph_motion: Optional["VmdMotion"] = None,
    ) -> VmdBoneFrameTrees:
        """
        指定されたキーフレ番号の行列計算結果を返す

        Parameters
        ----------
        fnos : list[int]
            キーフレ番号のリスト
        bone_names: list[str]
            取得ボーン名リスト
        model: PmxModel
            モデルデータ
        append_ik: bool
            IK計算を行うか否か
        morph_motion: VmdMotion
            モーフモーション

        Returns
        -------
        行列辞書（キー: fno,ボーン名、値：行列リスト）
        """

        if append_ik:
            # IK回転を事前に求めておく
            for fno in fnos:
                self.calc_ik_rotations(fno, model, bone_names)

        bone_trees = model.bone_trees.filter(*bone_names)
        bone_matrixes = VmdBoneFrameTrees()

        for bone_tree in bone_trees.values():
            row = len(fnos)
            col = len(bone_tree) + 1
            bone_poses = np.full((row, col, 3), np.zeros(3))
            poses = np.full((row, col, 3), np.zeros(3))
            qqs = np.full((row, col, 4, 4), np.eye(4))
            scales = np.full((row, col, 3), np.ones(3))
            poses2 = np.full((row, col, 4, 4), np.eye(4))
            qqs2 = np.full((row, col, 4, 4), np.eye(4))
            scales2 = np.full((row, col, 4, 4), np.eye(4))
            local_poses = np.full((row, col, 4, 4), np.eye(4))
            local_qqs = np.full((row, col, 4, 4), np.eye(4))
            local_scales = np.full((row, col, 4, 4), np.eye(4))

            morph_poses = np.full((row, col, 3), np.zeros(3))
            morph_qqs = np.full((row, col, 4, 4), np.eye(4))
            morph_scales = np.full((row, col, 3), np.ones(3))
            morph_poses2 = np.full((row, col, 4, 4), np.eye(4))
            morph_qqs2 = np.full((row, col, 4, 4), np.eye(4))
            morph_scales2 = np.full((row, col, 4, 4), np.eye(4))
            morph_local_poses = np.full((row, col, 4, 4), np.eye(4))
            morph_local_qqs = np.full((row, col, 4, 4), np.eye(4))
            morph_local_scales = np.full((row, col, 4, 4), np.eye(4))

            for n, fno in enumerate(fnos):
                if morph_motion is not None:
                    morph_bone_frames = morph_motion.morphs.animate_bone_morphs(fno, model)
                    (
                        morph_all_bone_poses,
                        morph_all_bone_qqs,
                        morph_all_bone_scales,
                        morph_all_bone_poses2,
                        morph_all_bone_qqs2,
                        morph_all_bone_scales2,
                        morph_all_bone_local_poses,
                        morph_all_bone_local_qqs,
                        morph_all_bone_local_scales,
                    ) = morph_bone_frames.animate_bone_matrixes(fno, model, append_ik=False)
                else:
                    morph_col = len(model.bones)
                    morph_all_bone_poses = np.full((1, morph_col, 3), np.zeros(3))
                    morph_all_bone_qqs = np.full((1, morph_col, 4, 4), np.eye(4))
                    morph_all_bone_scales = np.full((1, morph_col, 3), np.ones(3))
                    morph_all_bone_poses2 = np.full((1, morph_col, 4, 4), np.eye(4))
                    morph_all_bone_qqs2 = np.full((1, morph_col, 4, 4), np.eye(4))
                    morph_all_bone_scales2 = np.full((1, morph_col, 4, 4), np.eye(4))
                    morph_all_bone_local_poses = np.full((1, morph_col, 4, 4), np.eye(4))
                    morph_all_bone_local_qqs = np.full((1, morph_col, 4, 4), np.eye(4))
                    morph_all_bone_local_scales = np.full((1, morph_col, 4, 4), np.eye(4))

                for m, bone in enumerate(bone_tree):
                    # ボーンの親から見た相対位置
                    bone_poses[n, m] = (bone.position - (MVector3D() if m == 0 else bone_tree[bone_tree.names[m - 1]].position)).vector

                    # 移動量
                    if (fno, model.digest, bone.index) in self.cache_poses:
                        poses[n, m] = self.cache_poses[(fno, model.digest, bone.index)].vector
                    else:
                        pos = self.get_position(bone, fno, model)
                        self.cache_poses[(fno, model.digest, bone.index)] = pos
                        poses[n, m] = pos.vector

                    # 第二移動量
                    if (fno, model.digest, bone.index) in self.cache_poses2:
                        poses2[n, m] = self.cache_poses2[(fno, model.digest, bone.index)]
                    else:
                        pos = self.get_position2(bone, fno, model)
                        self.cache_poses2[(fno, model.digest, bone.index)] = pos
                        poses2[n, m] = pos

                    # ローカル移動量
                    if (fno, model.digest, bone.index) in self.cache_local_poses:
                        local_poses[n, m] = self.cache_local_poses[(fno, model.digest, bone.index)]
                    else:
                        local_pos = self.get_local_position(bone, fno, model)
                        self.cache_local_poses[(fno, model.digest, bone.index)] = local_pos
                        local_poses[n, m] = local_pos

                    # FK(捩り) > IK(捩り) > 付与親(捩り)
                    if (fno, model.digest, bone.index) in self.cache_qqs:
                        qqs[n, m] = self.cache_qqs[(fno, model.digest, bone.index)].to_matrix4x4().vector
                    else:
                        qq = self.get_rotation(bone, fno, model, append_ik=append_ik)
                        self.cache_qqs[(fno, model.digest, bone.index)] = qq
                        qqs[n, m] = qq.to_matrix4x4().vector

                    # 第二回転量
                    if (fno, model.digest, bone.index) in self.cache_qqs2:
                        qqs2[n, m] = self.cache_qqs2[(fno, model.digest, bone.index)]
                    else:
                        qq = self.get_rotation2(bone, fno, model)
                        self.cache_qqs2[(fno, model.digest, bone.index)] = qq
                        qqs2[n, m] = qq

                    # ローカル回転
                    if (fno, model.digest, bone.index) in self.cache_local_qqs:
                        local_qqs[n, m] = self.cache_local_qqs[(fno, model.digest, bone.index)]
                    else:
                        local_qq = self.get_local_rotation(bone, fno, model)
                        self.cache_local_qqs[(fno, model.digest, bone.index)] = local_qq
                        local_qqs[n, m] = local_qq

                    # モーションによるスケール変化
                    if (fno, model.digest, bone.index) in self.cache_scales:
                        scales[n, m] = self.cache_scales[(fno, model.digest, bone.index)].vector
                    else:
                        scale = self.get_scale(bone, fno, model)
                        self.cache_scales[(fno, model.digest, bone.index)] = scale
                        scales[n, m] = scale.vector

                    # モーションによるスケール変化
                    if (fno, model.digest, bone.index) in self.cache_scales2:
                        scales2[n, m] = self.cache_scales2[(fno, model.digest, bone.index)]
                    else:
                        scale = self.get_scale2(bone, fno, model)
                        self.cache_scales2[(fno, model.digest, bone.index)] = scale
                        scales2[n, m] = scale

                    # モーションによるローカルスケール変化
                    if (fno, model.digest, bone.index) in self.cache_local_scales:
                        local_scales[n, m] = self.cache_local_scales[(fno, model.digest, bone.index)]
                    else:
                        local_scale = self.get_local_scale(bone, fno, model)
                        self.cache_local_scales[(fno, model.digest, bone.index)] = local_scale
                        local_scales[n, m] = local_scale

                # 末端ボーン表示先の位置を計算
                bone_poses[n, -1] = np.zeros(3)
                poses[n, -1] = bone_tree[-1].tail_relative_position.vector
                local_poses[n, -1] = np.eye(4)
                qqs[n, -1] = np.eye(4)
                local_qqs[n, -1] = np.eye(4)
                scales[n, -1] = np.ones(3)
                local_scales[n, -1] = np.eye(4)

                # モーフの該当項目を設定
                morph_poses[n, : (col - 1)] = morph_all_bone_poses[0, bone_tree.indexes]
                morph_qqs[n, : (col - 1)] = morph_all_bone_qqs[0, bone_tree.indexes]
                morph_scales[n, : (col - 1)] = morph_all_bone_scales[0, bone_tree.indexes]
                morph_poses2[n, : (col - 1)] = morph_all_bone_poses2[0, bone_tree.indexes]
                morph_qqs2[n, : (col - 1)] = morph_all_bone_qqs2[0, bone_tree.indexes]
                morph_scales2[n, : (col - 1)] = morph_all_bone_scales2[0, bone_tree.indexes]
                morph_local_poses[n, : (col - 1)] = morph_all_bone_local_poses[0, bone_tree.indexes]
                morph_local_qqs[n, : (col - 1)] = morph_all_bone_local_qqs[0, bone_tree.indexes]
                morph_local_scales[n, : (col - 1)] = morph_all_bone_local_scales[0, bone_tree.indexes]
            # 親ボーンから見たローカル座標行列
            matrixes = MMatrix4x4List(row, col)
            matrixes.translate(bone_poses.tolist())

            # モーフ変化量
            matrixes.translate(morph_poses.tolist())
            matrixes.matmul(morph_local_poses)
            matrixes.rotate(morph_qqs.tolist())
            matrixes.matmul(morph_local_qqs)
            matrixes.scale(morph_scales.tolist())
            matrixes.matmul(morph_local_scales)
            matrixes.matmul(morph_poses2)
            matrixes.matmul(morph_qqs2)
            matrixes.matmul(morph_scales2)

            # ボーンモーション変化量
            matrixes.translate(poses.tolist())
            matrixes.matmul(local_poses)
            matrixes.rotate(qqs.tolist())
            matrixes.matmul(local_qqs)
            matrixes.scale(scales.tolist())
            matrixes.matmul(local_scales)
            matrixes.matmul(poses2)
            matrixes.matmul(qqs2)
            matrixes.matmul(scales2)
            # グローバル座標行列
            global_mats = matrixes.matmul_cols()
            # グローバル位置
            positions = global_mats.to_positions()

            for i, fno in enumerate(fnos):
                for j, bone in enumerate(bone_tree):
                    bone_matrixes.append(
                        fno,
                        bone.name,
                        MMatrix4x4(*global_mats.vector[i, j].flatten()),
                        MVector3D(*positions[i, j]),
                        MVector3D(*positions[i, j + 1]),
                    )

        return bone_matrixes

    def animate_bone_matrixes(
        self,
        fno: int,
        model: PmxModel,
        bone_names: list[str] = [],
        append_ik: bool = True,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        row = 1
        col = len(model.bones)
        poses = np.full((row, col, 3), np.zeros(3))
        qqs = np.full((row, col, 4, 4), np.eye(4))
        scales = np.full((row, col, 3), np.ones(3))
        poses2 = np.full((row, col, 4, 4), np.eye(4))
        qqs2 = np.full((row, col, 4, 4), np.eye(4))
        scales2 = np.full((row, col, 4, 4), np.eye(4))
        local_poses = np.full((row, col, 4, 4), np.eye(4))
        local_qqs = np.full((row, col, 4, 4), np.eye(4))
        local_scales = np.full((row, col, 4, 4), np.eye(4))

        if not bone_names:
            bone_names = model.bones.tail_bone_names

        if append_ik:
            # IK回転を事前に求めておく
            self.calc_ik_rotations(fno, model)

        for bone_name in bone_names:
            for bone in model.bone_trees[bone_name]:
                # モーションによる移動量
                if (fno, model.digest, bone.index) not in self.cache_poses:
                    pos = self.get_position(bone, fno, model)
                    poses[0, bone.index] = pos.vector
                    self.cache_poses[(fno, model.digest, bone.index)] = pos

                # モーションによる第二移動量
                if (fno, model.digest, bone.index) not in self.cache_poses2:
                    pos = self.get_position2(bone, fno, model)
                    poses2[0, bone.index] = pos
                    self.cache_poses2[(fno, model.digest, bone.index)] = pos

                # モーションによるローカル移動量
                if (fno, model.digest, bone.index) not in self.cache_local_poses:
                    local_pos = self.get_local_position(bone, fno, model)
                    local_poses[0, bone.index] = local_pos
                    self.cache_local_poses[(fno, model.digest, bone.index)] = local_pos

                # FK(捩り) > IK(捩り) > 付与親(捩り)
                if (fno, model.digest, bone.index) not in self.cache_qqs:
                    qq = self.get_rotation(bone, fno, model, append_ik=append_ik)
                    self.cache_qqs[(fno, model.digest, bone.index)] = qq
                    qqs[0, bone.index] = qq.to_matrix4x4().vector

                # 第二回転量
                if (fno, model.digest, bone.index) not in self.cache_qqs2:
                    qq = self.get_rotation2(bone, fno, model)
                    self.cache_qqs2[(fno, model.digest, bone.index)] = qq
                    qqs2[0, bone.index] = qq

                # ローカル回転
                if (fno, model.digest, bone.index) not in self.cache_local_qqs:
                    local_qq = self.get_local_rotation(bone, fno, model)
                    self.cache_local_qqs[(fno, model.digest, bone.index)] = local_qq
                    local_qqs[0, bone.index] = local_qq

                # モーションによるスケール変化
                if (fno, model.digest, bone.index) not in self.cache_scales:
                    scale = self.get_scale(bone, fno, model)
                    scales[0, bone.index] = scale.vector
                    self.cache_scales[(fno, model.digest, bone.index)] = scale

                # モーションによる第二スケール変化
                if (fno, model.digest, bone.index) not in self.cache_scales2:
                    scale = self.get_scale2(bone, fno, model)
                    scales2[0, bone.index] = scale
                    self.cache_scales2[(fno, model.digest, bone.index)] = scale

                # モーションによるローカルスケール変化
                if (fno, model.digest, bone.index) not in self.cache_local_scales:
                    local_scale = self.get_local_scale(bone, fno, model)
                    local_scales[0, bone.index] = local_scale
                    self.cache_local_scales[(fno, model.digest, bone.index)] = local_scale

        return poses, qqs, scales, poses2, qqs2, scales2, local_poses, local_qqs, local_scales

    def calc_ik_rotations(self, fno: int, model: PmxModel, bone_names: Optional[list[str]] = []):
        # IK関係の末端ボーン名
        ik_last_bone_names: set[str] = {model.bones[0].name}
        if bone_names:
            target_last_bone_names = {model.bone_trees[bname].last_name for bname in bone_names}
        else:
            target_last_bone_names = set(model.bones.names)
        for bone in model.bones:
            if bone.is_ik and bone.ik:
                # IKリンクボーン・ターゲットボーンのボーンツリーをすべてチェック対象とする
                ik_last_bone_names |= {model.bone_trees[bone.name].last_name}
                ik_last_bone_names |= {model.bone_trees[model.bones[bone.ik.bone_index].name].last_name}
                for link_bone in bone.ik.links:
                    ik_last_bone_names |= {model.bone_trees[model.bones[link_bone.bone_index].name].last_name}
        ik_last_bone_names &= target_last_bone_names
        if not ik_last_bone_names:
            # IK計算対象がない場合はそのまま終了
            return
        # モーション内のキーフレリストから前の変化キーフレと次の変化キーフレを抽出する
        prev_frame_indexes: set[int] = {0}
        next_frame_indexes: set[int] = {self.max_fno}
        for ik_last_bone_name in [bone.name for bone in model.bones if bone.name in ik_last_bone_names]:
            if ik_last_bone_name in self:
                prev_frame_indexes |= {i for i in self[ik_last_bone_name].indexes if fno > i}
                next_frame_indexes |= {i for i in self[ik_last_bone_name].indexes if fno < i}
                prev_fno = max(list(prev_frame_indexes))
                next_fno = min(list(next_frame_indexes))

                is_calc_prev = False
                is_calc_next = False
                for bone in model.bone_trees[ik_last_bone_name]:
                    if bone.ik_link_indexes or bone.ik_target_indexes:
                        if prev_fno not in self[bone.name] or not self[bone.name][prev_fno].ik_rotation:
                            is_calc_prev = True
                        if next_fno not in self[bone.name] or not self[bone.name][next_fno].ik_rotation:
                            is_calc_next = True
                if is_calc_prev and (prev_fno, model.digest, ik_last_bone_name) not in self.cache_qqs:
                    self.get_rotation(model.bones[ik_last_bone_name], prev_fno, model, append_ik=True)
                if is_calc_next and (next_fno, model.digest, ik_last_bone_name) not in self.cache_qqs:
                    self.get_rotation(model.bones[ik_last_bone_name], next_fno, model, append_ik=True)

    def get_position(self, bone: Bone, fno: int, model: PmxModel) -> MVector3D:
        """
        該当キーフレにおけるボーンの移動位置

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        model : PmxModel
            計算対象モデル

        Returns
        -------
        MVector3D
            相対位置
        """
        # 自身の位置
        pos = self[bone.name][fno].position.copy()

        # 付与親を加味して返す
        return self.get_effect_position(bone, fno, pos, model)

    def get_effect_position(
        self,
        bone: Bone,
        fno: int,
        pos: MVector3D,
        model: PmxModel,
    ) -> MVector3D:
        """
        付与親を加味した移動を求める

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        pos : MVector3D
            計算対象移動
        model : PmxModel
            計算対象モデル

        Returns
        -------
        MVector3D
            計算結果
        """
        if not (bone.is_external_translation and bone.effect_index in model.bones):
            return pos

        if 0 == bone.effect_factor:
            # 付与率が0の場合、常に0になる
            return MVector3D()

        # 付与親の回転量を取得する（それが付与持ちなら更に遡る）
        effect_bone = model.bones[bone.effect_index]
        # effect_pos = model.bones.get_parent_relative_position(bone.effect_index)
        effect_pos = self.get_position(effect_bone, fno, model)
        pos *= effect_pos

        return pos

    def get_position2(self, bone: Bone, fno: int, model: PmxModel) -> np.ndarray:
        """
        該当キーフレにおけるボーンの移動位置

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        model : PmxModel
            計算対象モデル

        Returns
        -------
        np.ndarray
            移動行列
        """
        # 自身の位置
        pos_matrix = np.eye(4)
        pos_matrix[:3, 3] = self[bone.name][fno].position2.vector

        return pos_matrix

    def get_local_position(self, bone: Bone, fno: int, model: PmxModel) -> np.ndarray:
        """
        該当キーフレにおけるボーンのローカル位置

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        model : PmxModel
            計算対象モデル

        Returns
        -------
        np.ndarray
            ローカル軸を加味した移動行列
        """
        # 自身のローカル移動量
        local_pos = self[bone.name][fno].local_position
        local_parent_matrix = np.eye(4)

        if not bone.is_twist:
            for parent_name in model.bone_trees[bone.name].names[:-1]:
                # 親のキャンセルローカル移動
                parent_bone = model.bones[parent_name]
                local_parent_matrix = local_parent_matrix @ self.cache_local_poses.get((fno, model.digest, parent_bone.index), np.eye(4))

        if not local_pos and np.all(np.isclose(local_parent_matrix, np.eye(4))):
            return np.eye(4)

        # 3D移動は、ローカル軸に沿う
        pos_matrix = np.eye(4)
        pos_matrix[:3, 3] = local_pos.vector

        # ローカル軸に沿った回転行列
        rotation_matrix = bone.tail_relative_position.to_local_matrix4x4().vector

        # ローカル軸に合わせた移動行列を作成する
        return np.linalg.inv(local_parent_matrix) @ np.linalg.inv(rotation_matrix) @ pos_matrix @ rotation_matrix

    def get_scale(self, bone: Bone, fno: int, model: PmxModel) -> MVector3D:
        """
        該当キーフレにおけるボーンの縮尺

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        model : PmxModel
            計算対象モデル

        Returns
        -------
        MVector3D
            相対スケール
        """
        # 自身のスケール
        scale = self[bone.name][fno].scale.copy() + MVector3D(1, 1, 1)

        # 付与親を加味して返す
        return self.get_effect_scale(bone, fno, scale, model)

    def get_effect_scale(
        self,
        bone: Bone,
        fno: int,
        scale: MVector3D,
        model: PmxModel,
    ) -> MVector3D:
        """
        付与親を加味した縮尺を求める

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        scale : MVector3D
            計算対象縮尺
        model : PmxModel
            計算対象モデル

        Returns
        -------
        MVector3D
            計算結果
        """
        if not (bone.is_external_translation and bone.effect_index in model.bones):
            return scale

        if 0 == bone.effect_factor:
            # 付与率が0の場合、常に1になる
            return MVector3D(1, 1, 1)

        # 付与親の回転量を取得する（それが付与持ちなら更に遡る）
        effect_bone = model.bones[bone.effect_index]
        effect_scale = self.get_scale(effect_bone, fno, model)
        scale *= effect_scale

        return scale

    def get_scale2(self, bone: Bone, fno: int, model: PmxModel) -> np.ndarray:
        """
        該当キーフレにおけるボーンの第二縮尺

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        model : PmxModel
            計算対象モデル

        Returns
        -------
        MVector3D
            相対スケール
        """
        # 自身のスケール

        scale2 = self[bone.name][fno].scale2 + MVector3D(1, 1, 1)

        scale_matrix = np.eye(4)
        scale_matrix[:3, :3] = np.diag(scale2.vector)

        return scale_matrix

    def get_local_scale(self, bone: Bone, fno: int, model: PmxModel) -> np.ndarray:
        """
        該当キーフレにおけるボーンのローカル縮尺

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        model : PmxModel
            計算対象モデル

        Returns
        -------
        np.ndarray
            ローカル軸を加味したスケーリング行列
        """
        # return self.calc_locale_scale(bone.index, fno, model)
        # 自身のローカルスケール
        local_scale = self[bone.name][fno].local_scale
        local_parent_matrix = np.eye(4)

        if not bone.is_twist:
            for parent_name in model.bone_trees[bone.name].names[:-1]:
                # 親のキャンセルローカルスケール
                parent_bone = model.bones[parent_name]
                local_parent_matrix = local_parent_matrix @ self.cache_local_scales.get((fno, model.digest, parent_bone.index), np.eye(4))

        if not local_scale and np.all(np.isclose(local_parent_matrix, np.eye(4))):
            return np.eye(4)

        scale_matrix = np.eye(4)
        scale_matrix[:3, :3] += np.diag(local_scale.vector)

        # ローカル軸に沿った回転行列
        rotation_matrix = bone.tail_relative_position.to_local_matrix4x4().vector

        # ローカル軸に合わせたスケーリング行列を作成する(親はキャンセルする)
        return np.linalg.inv(local_parent_matrix) @ np.linalg.inv(rotation_matrix) @ scale_matrix @ rotation_matrix

    # def calc_locale_scale(self, bone_index: int, fno: int, model: PmxModel) -> np.ndarray:
    #     """ローカル軸に沿ったスケーリング行列"""
    #     if 0 > bone_index:
    #         return np.eye(4)

    #     # 自身のローカルスケール
    #     bone = model.bones[bone_index]
    #     local_scale = self[bone.name][fno].local_scale
    #     local_parent_matrix = self.calc_locale_scale(bone.parent_index, fno, model)

    #     if not local_scale and np.all(np.isclose(local_parent_matrix, np.eye(4))):
    #         return np.eye(4)

    #     if bone.is_twist:
    #         return np.eye(4)

    #     scale_matrix = np.eye(4)
    #     scale_matrix[:3, :3] += np.diag(local_scale.vector)

    #     # ローカル軸に沿った回転行列
    #     rotation_matrix = bone.tail_relative_position.to_local_matrix4x4().vector

    #     # ローカル軸に合わせたスケーリング行列を作成する(親はキャンセルする)
    #     return np.linalg.inv(local_parent_matrix) @ np.linalg.inv(rotation_matrix) @ scale_matrix @ rotation_matrix

    def get_rotation(self, bone: Bone, fno: int, model: PmxModel, append_ik: bool = False) -> MQuaternion:
        """
        該当キーフレにおけるボーンの相対位置

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        model : PmxModel
            計算対象モデル
        append_ik : bool
            IKを計算するか(循環してしまう場合があるので、デフォルトFalse)

        Returns
        -------
        MQuaternion
            該当キーフレにおけるボーンの回転量
        """

        # FK(捩り) > IK(捩り) > 付与親(捩り)
        bf = self[bone.name][fno]
        qq = bf.rotation.copy()

        if bf.ik_rotation is not None:
            # IK用回転を持っている場合、追加
            qq *= bf.ik_rotation

        fk_qq = self.get_fix_rotation(bone, qq)

        # IKを加味した回転
        ik_qq = self.get_ik_rotation(bone, fno, fk_qq, model) if append_ik else fk_qq

        # 付与親を加味した回転
        effect_qq = self.get_effect_rotation(bone, fno, ik_qq, model, append_ik)

        return effect_qq

    def get_effect_rotation(
        self,
        bone: Bone,
        fno: int,
        qq: MQuaternion,
        model: PmxModel,
        append_ik: bool,
    ) -> MQuaternion:
        """
        付与親を加味した回転を求める

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        qq : MQuaternion
            計算対象クォータニオン
        model : PmxModel
            計算対象モデル

        Returns
        -------
        MQuaternion
            計算結果
        """
        if not (bone.is_external_rotation and bone.effect_index in model.bones):
            return qq

        if 0 == bone.effect_factor:
            # 付与率が0の場合、常に0になる
            return MQuaternion()

        # 付与親の回転量を取得する（それが付与持ちなら更に遡る）
        effect_bone = model.bones[bone.effect_index]
        effect_qq = self.get_rotation(effect_bone, fno, model, append_ik=append_ik)
        if 0 < bone.effect_factor:
            # 正の付与親
            qq *= effect_qq.multiply_factor(bone.effect_factor)
        else:
            # 負の付与親の場合、逆回転
            qq *= (effect_qq.multiply_factor(abs(bone.effect_factor))).inverse()

        return qq.normalized()

    def get_ik_rotation(
        self,
        bone: Bone,
        fno: int,
        qq: MQuaternion,
        model: PmxModel,
    ) -> MQuaternion:
        """
        IKを加味した回転を求める

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        qq : MQuaternion
            計算対象クォータニオン
        model : PmxModel
            計算対象モデル
        ik_bones : PmxModel
            IK計算用キーフレ

        Returns
        -------
        MQuaternion
            計算結果
        """

        if not bone.ik_link_indexes:
            return qq

        # 影響ボーン移動辞書
        bone_positions: dict[int, MVector3D] = {}

        for ik_target_bone_idx in bone.ik_link_indexes:
            # IKボーン自身の位置
            ik_bone = model.bones[ik_target_bone_idx]

            if ik_target_bone_idx not in model.bones or not ik_bone.ik:
                continue

            ik_matrixes = self.get_matrix_by_indexes([fno], [ik_bone.name], model, append_ik=False)
            global_target_pos = ik_matrixes[fno, ik_bone.name].position

            # IKターゲットボーンツリー
            effector_bone = model.bones[ik_bone.ik.bone_index]
            effector_bone_tree = model.bone_trees[effector_bone.name]

            # IKリンクボーンツリー
            ik_link_bone_trees: dict[int, BoneTree] = {ik_bone.index: model.bone_trees[ik_bone.name]}
            for ik_link in ik_bone.ik.links:
                if ik_link.bone_index not in model.bones:
                    continue
                ik_link_bone_trees[ik_link.bone_index] = model.bone_trees[model.bones[ik_link.bone_index].name]

            is_break = False
            for loop in range(ik_bone.ik.loop_count):
                for ik_link in ik_bone.ik.links:
                    # ikLink は末端から並んでる
                    if ik_link.bone_index not in model.bones:
                        continue

                    # 現在のIKターゲットボーンのグローバル位置を取得
                    col = len(effector_bone_tree)
                    poses = np.full((1, col, 3), np.zeros(3))
                    qqs = np.full((1, col, 4, 4), np.eye(4))
                    scales = np.full((1, col, 3), np.ones(3))
                    for m, it_bone in enumerate(effector_bone_tree):
                        # ボーンの親から見た相対位置を求める
                        if it_bone.index not in bone_positions:
                            bone_positions[it_bone.index] = it_bone.position - (
                                MVector3D() if m == 0 else effector_bone_tree[effector_bone_tree.names[m - 1]].position
                            )
                            bone_positions[it_bone.index] += self.get_position(it_bone, fno, model)
                        poses[0, m] = bone_positions[it_bone.index].vector
                        # ボーンの回転
                        qqs[0, m] = self.get_rotation(it_bone, fno, model, append_ik=False).to_matrix4x4().vector
                        # ボーンのスケール
                        scales[0, m] = self.get_scale(it_bone, fno, model).vector
                    matrixes = MMatrix4x4List(1, col)
                    matrixes.translate(poses.tolist())
                    matrixes.rotate(qqs.tolist())
                    matrixes.scale(scales.tolist())
                    effector_result_mats = matrixes.matmul_cols()
                    global_effector_pos = MVector3D(*effector_result_mats.to_positions()[0, -1])

                    # 処理対象IKボーン
                    link_bone = model.bones[ik_link.bone_index]
                    link_bone_tree = ik_link_bone_trees[link_bone.index]

                    # リンクボーンの角度を保持
                    link_bf = self[link_bone.name][fno]

                    # 処理対象IKボーンのグローバル位置と行列を取得
                    col = len(link_bone_tree)
                    poses = np.full((1, col, 3), np.zeros(3))
                    qqs = np.full((1, col, 4, 4), np.eye(4))
                    scales = np.full((1, col, 3), np.ones(3))
                    for m, it_bone in enumerate(link_bone_tree):
                        # ボーンの親から見た相対位置を求める
                        if it_bone.index not in bone_positions:
                            bone_positions[it_bone.index] = it_bone.position - (MVector3D() if m == 0 else link_bone_tree[link_bone_tree.names[m - 1]].position)
                            bone_positions[it_bone.index] += self.get_position(it_bone, fno, model)
                        poses[0, m] = bone_positions[it_bone.index].vector
                        # ボーンの回転
                        qqs[0, m] = self.get_rotation(it_bone, fno, model, append_ik=False).to_matrix4x4().vector
                        # ボーンのスケール
                        scales[0, m] = self.get_scale(it_bone, fno, model).vector
                    matrixes = MMatrix4x4List(1, col)
                    matrixes.translate(poses.tolist())
                    matrixes.rotate(qqs.tolist())
                    matrixes.scale(scales.tolist())
                    link_target_mats = matrixes.matmul_cols()

                    # 注目ノード（実際に動かすボーン）
                    link_matrix = MMatrix4x4(*link_target_mats.vector[0, -1].flatten())

                    # ワールド座標系から注目ノードの局所座標系への変換
                    link_inverse_matrix = link_matrix.inverse()

                    # 注目ノードを起点とした、エフェクタのローカル位置
                    local_effector_pos = link_inverse_matrix * global_effector_pos
                    # 注目ノードを起点とした、IK目標のローカル位置
                    local_target_pos = link_inverse_matrix * global_target_pos

                    if 1e-5 > (local_effector_pos - local_target_pos).length_squared():
                        # 位置の差がほとんどない場合、スルー
                        is_break = True
                        break

                    #  (1) 基準関節→エフェクタ位置への方向ベクトル
                    norm_effector_pos = local_effector_pos.normalized()
                    #  (2) 基準関節→目標位置への方向ベクトル
                    norm_target_pos = local_target_pos.normalized()

                    # ベクトル (1) を (2) に一致させるための最短回転量（Axis-Angle）
                    # 回転角
                    rotation_dot = norm_effector_pos.dot(norm_target_pos)
                    # 回転角度
                    rotation_radian = acos(max(-1, min(1, rotation_dot)))

                    # 回転軸
                    rotation_axis = norm_effector_pos.cross(norm_target_pos)
                    # 回転角度
                    rotation_degree = degrees(rotation_radian)

                    # 制限角で最大変位量を制限する
                    if 0 < loop:
                        rotation_degree = min(rotation_degree, ik_bone.ik.unit_rotation.degrees.x)

                    # 補正関節回転量
                    correct_qq = MQuaternion.from_axis_angles(rotation_axis, rotation_degree)
                    ik_qq = (link_bf.ik_rotation or MQuaternion()) * correct_qq

                    if ik_link.angle_limit:
                        # 角度制限が入ってる場合、オイラー角度に分解する
                        euler_degrees = ik_qq.separate_euler_degrees()

                        euler_degrees.x = max(
                            min(
                                euler_degrees.x,
                                ik_link.max_angle_limit.degrees.x,
                            ),
                            ik_link.min_angle_limit.degrees.x,
                        )
                        euler_degrees.y = max(
                            min(
                                euler_degrees.y,
                                ik_link.max_angle_limit.degrees.y,
                            ),
                            ik_link.min_angle_limit.degrees.y,
                        )
                        euler_degrees.z = max(
                            min(
                                euler_degrees.z,
                                ik_link.max_angle_limit.degrees.z,
                            ),
                            ik_link.min_angle_limit.degrees.z,
                        )
                        ik_qq = MQuaternion.from_euler_degrees(euler_degrees)

                    link_bf.ik_rotation = ik_qq
                    self[link_bf.name].append(link_bf)

                if is_break:
                    break
            if is_break:
                break

        # IKの計算結果の回転を加味して返す
        bf = self[bone.name][fno]
        return bf.rotation * (bf.ik_rotation or MQuaternion())

    def get_fix_rotation(self, bone: Bone, qq: MQuaternion) -> MQuaternion:
        """
        軸制限回転を求める

        Parameters
        ----------
        bone : Bone
            対象ボーン
        qq : MQuaternion
            計算対象回転

        Returns
        -------
        MQuaternion
            軸制限された回転
        """
        if bone.has_fixed_axis:
            return qq.to_fixed_axis_quaternion(bone.corrected_fixed_axis)

        return qq

    def get_rotation2(self, bone: Bone, fno: int, model: PmxModel) -> np.ndarray:
        """
        該当キーフレにおけるボーンの相対位置

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        model : PmxModel
            計算対象モデル

        Returns
        -------
        MQuaternion
            該当キーフレにおけるボーンの回転量
        """

        return self[bone.name][fno].rotation2.to_matrix4x4().vector

    def get_local_rotation(self, bone: Bone, fno: int, model: PmxModel) -> np.ndarray:
        """
        該当キーフレにおけるボーンのローカル回転

        Parameters
        ----------
        bone : Bone
            計算対象ボーン
        fno : int
            計算対象キーフレ
        model : PmxModel
            計算対象モデル

        Returns
        -------
        np.ndarray
            ローカル軸を加味した回転行列
        """
        # 自身のローカル回転量
        qq_matrix = self[bone.name][fno].local_rotation.to_matrix4x4().vector

        local_parent_matrix = np.eye(4)

        if not bone.is_twist:
            for parent_name in model.bone_trees[bone.name].names[:-1]:
                # 親のキャンセルローカル移動
                parent_bone = model.bones[parent_name]
                local_parent_matrix = local_parent_matrix @ self.cache_local_qqs.get((fno, model.digest, parent_bone.index), np.eye(4))

        if np.all(np.isclose(qq_matrix, np.eye(4))) and np.all(np.isclose(local_parent_matrix, np.eye(4))):
            return np.eye(4)

        # ローカル軸に沿った回転行列
        rotation_matrix = bone.tail_relative_position.to_local_matrix4x4().vector

        # ローカル軸に合わせた回転行列を作成する(親はキャンセルする)
        return np.linalg.inv(local_parent_matrix) @ np.linalg.inv(rotation_matrix) @ qq_matrix @ rotation_matrix


@lru_cache(maxsize=None)
def calc_morph_ratio(prev: float, next: float, ratio: float) -> float:
    return prev + (next - prev) * ratio


class VmdMorphNameFrames(BaseIndexNameDictModel[VmdMorphFrame]):
    """
    モーフ名別キーフレ辞書
    """

    def __getitem__(self, key: int | str) -> VmdMorphFrame:
        if isinstance(key, str):
            return VmdMorphFrame(name=key, index=0)

        if key in self.data:
            return self.get_by_index(key)

        # キーフレがない場合、生成したのを返す（保持はしない）
        prev_index, middle_index, next_index = self.range_indexes(key)

        # prevとnextの範囲内である場合、補間曲線ベースで求め直す
        return self.calc(
            prev_index,
            middle_index,
            next_index,
        )

    def calc(self, prev_index: int, index: int, next_index: int) -> VmdMorphFrame:
        if index in self.data:
            return self.data[index]

        if index in self.cache:
            mf = self.cache[index]
        else:
            mf = VmdMorphFrame(name=self.name, index=index)
            self.cache[index] = mf

        if prev_index == next_index:
            if next_index == index:
                # 全くキーフレがない場合、そのまま返す
                return mf

            # FKのprevと等しい場合、指定INDEX以前がないので、その次のをコピーして返す
            mf.ratio = self.data[next_index].ratio
            return mf

        prev_mf = self.data[prev_index] if prev_index in self else VmdMorphFrame(name=self.name, index=prev_index)
        next_mf = self.data[next_index] if next_index in self else VmdMorphFrame(name=self.name, index=next_index)

        # モーフは補間なし
        ry = (index - prev_index) / (next_index - prev_index)
        mf.ratio = calc_morph_ratio(prev_mf.ratio, next_mf.ratio, ry)

        return mf


class VmdMorphFrames(BaseIndexNameDictWrapperModel[VmdMorphNameFrames]):
    """
    モーフキーフレ辞書
    """

    def __init__(self) -> None:
        super().__init__()

    def create(self, key: str) -> VmdMorphNameFrames:
        return VmdMorphNameFrames(name=key)

    @property
    def max_fno(self) -> int:
        return max([max(self[fname].indexes + [0]) for fname in self.names] + [0])

    def animate_vertex_morphs(self, fno: int, model: PmxModel) -> np.ndarray:
        row = len(model.vertices)
        poses = np.full((row, 3), np.zeros(3))

        for morph in model.morphs.filter_by_type(MorphType.VERTEX):
            if morph.name not in self.data:
                # モーフそのものの定義がなければスルー
                continue
            mf = self[morph.name][fno]
            if not mf.ratio:
                continue

            # モーションによる頂点モーフ変動量
            for offset in morph.offsets:
                if type(offset) is VertexMorphOffset and offset.vertex_index < row:
                    ratio_pos: MVector3D = offset.position_offset * mf.ratio
                    poses[offset.vertex_index] += ratio_pos.gl.vector

        return np.array(poses)

    def animate_uv_morphs(self, fno: int, model: PmxModel, uv_index: int) -> np.ndarray:
        row = len(model.vertices)
        poses = np.full((row, 4), np.zeros(4))

        target_uv_type = MorphType.UV if 0 == uv_index else MorphType.EXTENDED_UV1
        for morph in model.morphs.filter_by_type(target_uv_type):
            if morph.name not in self.data:
                # モーフそのものの定義がなければスルー
                continue
            mf = self[morph.name][fno]
            if not mf.ratio:
                continue

            # モーションによるUVモーフ変動量
            for offset in morph.offsets:
                if type(offset) is UvMorphOffset and offset.vertex_index < row:
                    ratio_pos: MVector4D = offset.uv * mf.ratio
                    poses[offset.vertex_index] += ratio_pos.vector

        # UVのYは 1 - y で求め直しておく
        poses[:, 1] = 1 - poses[:, 1]

        return np.array(poses)

    def animate_bone_morphs(self, fno: int, model: PmxModel) -> VmdBoneFrames:
        bone_frames = VmdBoneFrames()
        for morph in model.morphs.filter_by_type(MorphType.BONE):
            if morph.name not in self.data:
                # モーフそのものの定義がなければスルー
                continue
            mf = self[morph.name][fno]
            if not mf.ratio:
                continue

            # モーションによるボーンモーフ変動量
            for offset in morph.offsets:
                if type(offset) is BoneMorphOffset and offset.bone_index in model.bones:
                    bf = bone_frames[model.bones[offset.bone_index].name][fno]
                    bf = self.animate_bone_morph_frame(fno, model, bf, offset, mf.ratio)
                    bone_frames[bf.name][fno] = bf

        return bone_frames

    def animate_bone_morph_frame(self, fno: int, model: PmxModel, bf: VmdBoneFrame, offset: BoneMorphOffset, ratio: float) -> VmdBoneFrame:
        bf.position += offset.position * ratio
        bf.position2 += offset.position2 * ratio
        bf.local_position += offset.local_position * ratio
        bf.rotation *= MQuaternion.from_euler_degrees(offset.rotation.degrees * ratio)
        bf.rotation2 *= MQuaternion.from_euler_degrees(offset.rotation2.degrees * ratio)
        bf.local_rotation *= MQuaternion.from_euler_degrees(offset.local_rotation.degrees * ratio)
        bf.scale += offset.scale * ratio
        bf.scale2 += offset.scale2 * ratio
        bf.local_scale += offset.local_scale * ratio
        return bf

    def animate_group_morphs(self, fno: int, model: PmxModel, materials: list[ShaderMaterial]) -> tuple[np.ndarray, VmdBoneFrames, list[ShaderMaterial]]:
        group_vertex_poses = np.full((len(model.vertices), 3), np.zeros(3))
        bone_frames = VmdBoneFrames()

        # デフォルトの材質情報を保持（シェーダーに合わせて一部入れ替え）
        for morph in model.morphs.filter_by_type(MorphType.GROUP):
            if morph.name not in self.data:
                # モーフそのものの定義がなければスルー
                continue
            mf = self[morph.name][fno]
            if not mf.ratio:
                continue

            # モーションによるボーンモーフ変動量
            for group_offset in morph.offsets:
                if type(group_offset) is GroupMorphOffset and group_offset.morph_index in model.morphs:
                    part_morph = model.morphs[group_offset.morph_index]
                    mf_factor = mf.ratio * group_offset.morph_factor
                    if not mf_factor:
                        continue

                    for offset in part_morph.offsets:
                        if type(offset) is VertexMorphOffset and offset.vertex_index < group_vertex_poses.shape[0]:
                            ratio_pos: MVector3D = offset.position_offset * mf_factor
                            group_vertex_poses[offset.vertex_index] += ratio_pos.gl.vector
                        elif type(offset) is BoneMorphOffset and offset.bone_index in model.bones:
                            bf = bone_frames[model.bones[offset.bone_index].name][fno]
                            bf = self.animate_bone_morph_frame(fno, model, bf, offset, mf_factor)
                            bone_frames[bf.name][fno] = bf
                        elif type(offset) is MaterialMorphOffset and offset.material_index in model.materials:
                            materials = self.animate_material_morph_frame(model, offset, mf_factor, materials, MShader.LIGHT_AMBIENT4)

        return group_vertex_poses, bone_frames, materials

    def animate_material_morph_frame(
        self, model: PmxModel, offset: MaterialMorphOffset, ratio: float, materials: list[ShaderMaterial], light_ambient: MVector4D
    ) -> list[ShaderMaterial]:
        if 0 > offset.material_index:
            # 0の場合、全材質を対象とする
            material_indexes = model.materials.indexes
        else:
            # 特定材質の場合、材質固定
            material_indexes = [offset.material_index]
        # 指定材質を対象として変動量を割り当てる
        for target_calc_mode in [MaterialMorphCalcMode.MULTIPLICATION, MaterialMorphCalcMode.ADDITION]:
            # 先に乗算を計算した後に加算を加味する
            for material_index in material_indexes:
                # 元々の材質情報をコピー
                mat = model.materials[material_index]

                # オフセットに合わせた材質情報
                material = Material(
                    mat.index,
                    mat.name,
                    mat.english_name,
                )
                material.diffuse = offset.diffuse
                material.ambient = offset.ambient
                material.specular = offset.specular
                material.edge_color = offset.edge_color
                material.edge_size = offset.edge_size

                material_offset = ShaderMaterial(
                    material,
                    light_ambient,
                    offset.texture_factor,
                    offset.toon_texture_factor,
                    offset.sphere_texture_factor,
                )

                # オフセットに合わせた材質情報
                material_offset *= ratio
                if offset.calc_mode == target_calc_mode:
                    if offset.calc_mode == MaterialMorphCalcMode.ADDITION:
                        # 加算
                        materials[material_index] += material_offset
                    else:
                        # 乗算
                        materials[material_index] *= material_offset

        return materials

    def animate_material_morphs(self, fno: int, model: PmxModel) -> list[ShaderMaterial]:
        # デフォルトの材質情報を保持（シェーダーに合わせて一部入れ替え）
        materials = [ShaderMaterial(m, MShader.LIGHT_AMBIENT4) for m in model.materials]

        for morph in model.morphs.filter_by_type(MorphType.MATERIAL):
            if morph.name not in self.data:
                # モーフそのものの定義がなければスルー
                continue
            mf = self[morph.name][fno]
            if not mf.ratio:
                continue

            # モーションによる材質モーフ変動量
            for offset in morph.offsets:
                if type(offset) is MaterialMorphOffset and (offset.material_index in model.materials or 0 > offset.material_index):
                    materials = self.animate_material_morph_frame(model, offset, mf.ratio, materials, MShader.LIGHT_AMBIENT4)

        return materials


class VmdCameraFrames(BaseIndexNameDictModel[VmdCameraFrame]):
    """
    カメラキーフレリスト
    """

    def __init__(self) -> None:
        super().__init__()


class VmdLightFrames(BaseIndexNameDictModel[VmdLightFrame]):
    """
    照明キーフレリスト
    """

    def __init__(self) -> None:
        super().__init__()


class VmdShadowFrames(BaseIndexNameDictModel[VmdShadowFrame]):
    """
    照明キーフレリスト
    """

    def __init__(self) -> None:
        super().__init__()


class VmdShowIkFrames(BaseIndexNameDictModel[VmdShowIkFrame]):
    """
    IKキーフレリスト
    """

    def __init__(self) -> None:
        super().__init__()


class VmdMotion(BaseHashModel):
    """
    VMDモーション

    Parameters
    ----------
    path : str, optional
        パス, by default None
    signature : str, optional
        パス, by default None
    model_name : str, optional
        パス, by default None
    bones : VmdBoneFrames
        ボーンキーフレリスト, by default []
    morphs : VmdMorphFrames
        モーフキーフレリスト, by default []
    morphs : VmdMorphFrames
        モーフキーフレリスト, by default []
    cameras : VmdCameraFrames
        カメラキーフレリスト, by default []
    lights : VmdLightFrames
        照明キーフレリスト, by default []
    shadows : VmdShadowFrames
        セルフ影キーフレリスト, by default []
    show_iks : VmdShowIkFrames
        IKキーフレリスト, by default []
    """

    __slots__ = (
        "path",
        "digest",
        "signature",
        "model_name",
        "bones",
        "morphs",
        "cameras",
        "lights",
        "shadows",
        "show_iks",
    )

    def __init__(
        self,
        path: Optional[str] = None,
    ):
        super().__init__(path=path or "")
        self.signature: str = ""
        self.model_name: str = ""
        self.bones: VmdBoneFrames = VmdBoneFrames()
        self.morphs: VmdMorphFrames = VmdMorphFrames()
        self.cameras: VmdCameraFrames = VmdCameraFrames()
        self.lights: VmdLightFrames = VmdLightFrames()
        self.shadows: VmdShadowFrames = VmdShadowFrames()
        self.show_iks: VmdShowIkFrames = VmdShowIkFrames()

    @property
    def bone_count(self) -> int:
        return int(np.sum([len(bfs) for bfs in self.bones]))

    @property
    def max_fno(self) -> int:
        return max(self.bones.max_fno, self.morphs.max_fno)

    @property
    def name(self) -> str:
        return self.model_name

    def animate(self, fno: int, model: PmxModel, is_gl: bool = True) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[ShaderMaterial]]:
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: 開始")

        # 頂点モーフ
        vertex_morph_poses = self.morphs.animate_vertex_morphs(fno, model)
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: 頂点モーフ")

        # UVモーフ
        uv_morph_poses = self.morphs.animate_uv_morphs(fno, model, 0)
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: UVモーフ")

        # 追加UVモーフ1
        uv1_morph_poses = self.morphs.animate_uv_morphs(fno, model, 1)
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: 追加UVモーフ1")

        # 追加UVモーフ2-4は無視

        # 材質モーフ
        material_morphs = self.morphs.animate_material_morphs(fno, model)
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: 材質モーフ")

        # ボーンモーフ
        morph_bone_frames = self.morphs.animate_bone_morphs(fno, model)
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: ボーンモーフ")

        # グループモーフ
        group_vertex_morph_poses, group_morph_bone_frames, group_materials = self.morphs.animate_group_morphs(fno, model, material_morphs)
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: グループモーフ")

        for bfs in group_morph_bone_frames:
            bf = bfs[fno]
            mbf = morph_bone_frames[bf.name][bf.index]
            morph_bone_frames[bf.name][bf.index] = mbf + bf

        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: モーフキーフレ加算")

        # モーフボーン操作
        (
            morph_bone_poses,
            morph_bone_qqs,
            morph_bone_scales,
            morph_bone_poses2,
            morph_bone_qqs2,
            morph_bone_scales2,
            morph_bone_local_poses,
            morph_bone_local_qqs,
            morph_bone_local_scales,
        ) = morph_bone_frames.animate_bone_matrixes(fno, model, append_ik=False)
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: モーフボーン操作")

        # モーションボーン操作
        self.bones.clear()
        (
            motion_bone_poses,
            motion_bone_qqs,
            motion_bone_scales,
            motion_bone_poses2,
            motion_bone_qqs2,
            motion_bone_scales2,
            motion_bone_local_poses,
            motion_bone_local_qqs,
            motion_bone_local_scales,
        ) = self.bones.animate_bone_matrixes(fno, model)
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: モーションボーン操作")

        # ボーン変形行列
        matrixes = MMatrix4x4List(morph_bone_poses.shape[0], morph_bone_poses.shape[1])
        # モーフの適用
        matrixes.translate(morph_bone_poses.tolist())
        matrixes.matmul(morph_bone_local_poses)
        matrixes.rotate(morph_bone_qqs.tolist())
        matrixes.matmul(morph_bone_local_qqs)
        matrixes.scale(morph_bone_scales.tolist())
        matrixes.matmul(morph_bone_local_scales)
        matrixes.matmul(morph_bone_poses2)
        matrixes.matmul(morph_bone_qqs2)
        matrixes.matmul(morph_bone_scales2)
        # モーションの適用
        matrixes.translate(motion_bone_poses.tolist())
        matrixes.matmul(motion_bone_local_poses)
        matrixes.rotate(motion_bone_qqs.tolist())
        matrixes.matmul(motion_bone_local_qqs)
        matrixes.scale(motion_bone_scales.tolist())
        matrixes.matmul(motion_bone_local_scales)
        matrixes.matmul(motion_bone_poses2)
        matrixes.matmul(motion_bone_qqs2)
        matrixes.matmul(motion_bone_scales2)

        bone_matrixes: list[np.ndarray] = []
        for bone_index in model.bones.indexes:
            if 0 > bone_index:
                continue

            bone = model.bones[bone_index]

            # BOf行列: 自身のボーンのボーンオフセット行列
            matrix = bone.offset_matrix.copy().vector

            # 全体のボーン変形行列を求める
            matrix = model.bones.get_mesh_matrix(matrixes, bone.index, matrix)

            if is_gl:
                bone_matrixes.append(matrix.T)
            else:
                bone_matrixes.append(matrix)
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: ボーン変形行列")

        if not is_gl:
            return np.array(bone_matrixes), vertex_morph_poses + group_vertex_morph_poses, uv_morph_poses, uv1_morph_poses, group_materials

        # OpenGL座標系に変換
        gl_matrixes = np.array(bone_matrixes)
        gl_matrixes[..., 0, 1:3] *= -1
        gl_matrixes[..., 1:3, 0] *= -1
        gl_matrixes[..., 3, 0] *= -1

        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: OpenGL座標系変換")

        return gl_matrixes, vertex_morph_poses + group_vertex_morph_poses, uv_morph_poses, uv1_morph_poses, group_materials
