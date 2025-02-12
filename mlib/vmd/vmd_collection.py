import os
from bisect import bisect_left
from functools import lru_cache
from itertools import product
from math import acos, degrees
from typing import Iterable, Optional

import numpy as np
from numpy.linalg import inv

from mlib.core.collection import BaseHashModel, BaseIndexNameDictModel, BaseIndexNameDictWrapperModel
from mlib.core.interpolation import split_interpolation
from mlib.core.logger import MLogger
from mlib.core.math import MQuaternion, MVector3D, MVector4D, calc_list_by_ratio
from mlib.pmx.pmx_collection import PmxModel
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

logger = MLogger(os.path.basename(__file__))


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
        "_ik_indexes",
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

    def cache_clear(self) -> None:
        """キャッシュクリアとしてIK情報を削除"""
        super().cache_clear()

        for index in self.data.keys():
            self.data[index].ik_rotation = None
            self.data[index].corrected_position = None
            self.data[index].corrected_rotation = None

    def append(self, value: VmdBoneFrame, is_sort: bool = True, is_positive_index: bool = True) -> None:
        if value.ik_rotation is not None and value.index not in self._ik_indexes:
            self._ik_indexes.append(value.index)
            self._ik_indexes.sort()
        super().append(value, is_sort, is_positive_index)

    def insert(self, value: VmdBoneFrame, is_sort: bool = True, is_positive_index: bool = True) -> dict[int, int]:
        if value.ik_rotation is not None and value.index not in self._ik_indexes:
            self._ik_indexes.append(value.index)
            self._ik_indexes.sort()

        prev_index, middle_index, next_index = self.range_indexes(value.index)

        replaced_map: dict[int, int] = {}
        super().append(value, is_sort, is_positive_index)

        if next_index > value.index:
            # 次のキーフレが自身より後の場合、自身のキーフレがないので補間曲線を分割する
            for i, next_interpolation in enumerate(self.data[next_index].interpolations):
                split_target_interpolation, split_next_interpolation = split_interpolation(
                    next_interpolation, prev_index, middle_index, next_index
                )
                self.data[middle_index].interpolations[i] = split_target_interpolation
                self.data[next_index].interpolations[i] = split_next_interpolation

        return replaced_map

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
            next_bf = self.data[next_index]
            bf.position = next_bf.position.copy()
            bf.local_position = next_bf.local_position.copy()
            bf.rotation = next_bf.rotation.copy()
            bf.local_rotation = next_bf.local_rotation.copy()
            bf.scale = next_bf.scale.copy()
            bf.local_scale = next_bf.local_scale.copy()
            if next_bf.ik_rotation:
                bf.ik_rotation = next_bf.ik_rotation.copy()
            if next_bf.corrected_position:
                bf.corrected_position = next_bf.corrected_position.copy()
            if next_bf.corrected_rotation:
                bf.corrected_rotation = next_bf.corrected_rotation.copy()
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

        # ローカル回転
        bf.local_rotation = MQuaternion.slerp(prev_bf.local_rotation, next_bf.local_rotation, ry)

        # 移動・スケール・ローカル移動・ローカルスケール　は一括で計算
        bf.position.vector, bf.scale.vector, bf.local_position.vector, bf.local_scale.vector = calc_list_by_ratio(
            tuple(
                [
                    tuple(prev_bf.position.vector.tolist()),
                    tuple(prev_bf.scale.vector.tolist()),
                    tuple(prev_bf.local_position.vector.tolist()),
                    tuple(prev_bf.local_scale.vector.tolist()),
                ]
            ),
            tuple(
                [
                    tuple(next_bf.position.vector.tolist()),
                    tuple(next_bf.scale.vector.tolist()),
                    tuple(next_bf.local_position.vector.tolist()),
                    tuple(next_bf.local_scale.vector.tolist()),
                ]
            ),
            tuple([xy, yy, zy]),
        )

        return bf


class VmdBoneFrames(BaseIndexNameDictWrapperModel[VmdBoneNameFrames]):
    """
    ボーンキーフレ辞書
    """

    def __init__(self) -> None:
        super().__init__()

    def create(self, key: str) -> VmdBoneNameFrames:
        return VmdBoneNameFrames(name=key)

    @property
    def max_fno(self) -> int:
        return max([max(self[bname].indexes + [0]) for bname in self.names] + [0])

    def cache_clear(self) -> None:
        for bname in self.data.keys():
            self.data[bname].cache_clear()

    def animate_bone_matrixes(
        self,
        fnos: list[int],
        model: PmxModel,
        morph_bone_frames: Optional["VmdBoneFrames"] = None,
        bone_names: Iterable[str] = [],
        append_ik: bool = True,
        out_fno_log: bool = False,
    ) -> VmdBoneFrameTrees:
        if not bone_names:
            target_bone_names = model.bones.names
        else:
            target_bone_names = [
                model.bones[bone_index].name
                for bone_index in sorted(
                    set([bone_index for bone_name in bone_names for bone_index in model.bones[bone_name].relative_bone_indexes])
                )
            ]

        bone_offset_mats: list[tuple[int, np.ndarray]] = []
        bone_pos_mats = np.full((1, len(model.bones.indexes), 4, 4), np.eye(4))
        for bone_name in target_bone_names:
            bone = model.bones[bone_name]
            bone_pos_mats[0, bone.index, :3, 3] = bone.position.vector
            bone_offset_mats.append((bone.index, bone.offset_matrix))

        if out_fno_log:
            logger.info("ボーンモーフ計算")

        # モーフボーン操作
        if morph_bone_frames is not None:
            (
                morph_bone_poses,
                morph_bone_qqs,
                morph_bone_scales,
                morph_bone_local_poses,
                morph_bone_local_qqs,
                morph_bone_local_scales,
            ) = morph_bone_frames.get_bone_matrixes(fnos, model, target_bone_names, append_ik=False, out_fno_log=False)
        else:
            morph_row = len(fnos)
            morph_col = len(model.bones)
            morph_bone_poses = np.full((morph_row, morph_col, 4, 4), np.eye(4))
            morph_bone_qqs = np.full((morph_row, morph_col, 4, 4), np.eye(4))
            morph_bone_scales = np.full((morph_row, morph_col, 4, 4), np.eye(4))
            morph_bone_local_poses = np.full((morph_row, morph_col, 4, 4), np.eye(4))
            morph_bone_local_qqs = np.full((morph_row, morph_col, 4, 4), np.eye(4))
            morph_bone_local_scales = np.full((morph_row, morph_col, 4, 4), np.eye(4))

        if out_fno_log:
            logger.info("ボーンモーション計算")

        # モーションボーン操作
        (
            motion_bone_poses,
            motion_bone_qqs,
            motion_bone_scales,
            motion_bone_local_poses,
            motion_bone_local_qqs,
            motion_bone_local_scales,
        ) = self.get_bone_matrixes(fnos, model, target_bone_names, append_ik=append_ik, out_fno_log=out_fno_log)

        # ボーン変形行列
        matrixes = np.full(motion_bone_poses.shape, np.eye(4))
        eye_mat = np.eye(4)

        # モーフの適用
        if 0 < np.count_nonzero(morph_bone_poses - eye_mat):
            matrixes = matrixes @ morph_bone_poses
        if 0 < np.count_nonzero(morph_bone_local_poses - eye_mat):
            matrixes = matrixes @ morph_bone_local_poses
        if 0 < np.count_nonzero(morph_bone_qqs - eye_mat):
            matrixes = matrixes @ morph_bone_qqs
        if 0 < np.count_nonzero(morph_bone_local_qqs - eye_mat):
            matrixes = matrixes @ morph_bone_local_qqs
        if 0 < np.count_nonzero(morph_bone_scales - eye_mat):
            matrixes = matrixes @ morph_bone_scales
        if 0 < np.count_nonzero(morph_bone_local_scales - eye_mat):
            matrixes = matrixes @ morph_bone_local_scales

        # モーションの適用
        if 0 < np.count_nonzero(motion_bone_poses - eye_mat):
            matrixes = matrixes @ motion_bone_poses
        if 0 < np.count_nonzero(motion_bone_local_poses - eye_mat):
            matrixes = matrixes @ motion_bone_local_poses
        if 0 < np.count_nonzero(motion_bone_qqs - eye_mat):
            matrixes = matrixes @ motion_bone_qqs
        if 0 < np.count_nonzero(motion_bone_local_qqs - eye_mat):
            matrixes = matrixes @ motion_bone_local_qqs
        if 0 < np.count_nonzero(motion_bone_scales - eye_mat):
            matrixes = matrixes @ motion_bone_scales
        if 0 < np.count_nonzero(motion_bone_local_scales - eye_mat):
            matrixes = matrixes @ motion_bone_local_scales

        if out_fno_log:
            logger.info("ボーン行列計算")

        # 各ボーンごとのボーン変形行列結果と逆BOf行列(初期姿勢行列)の行列積
        relative_matrixes = model.bones.parent_revert_matrixes @ matrixes

        if out_fno_log:
            logger.info("ボーン変形行列リストアップ")

        # ボーンツリーINDEXリストごとのボーン変形行列リスト(子どもから親に遡る)
        tree_relative_matrixes = [
            [relative_matrixes[fidx, list(reversed(bone.tree_indexes))] for bone in model.bones] for fidx in range(len(fnos))
        ]

        # 行列積ボーン変形行列結果
        result_matrixes = np.full(motion_bone_poses.shape, np.eye(4))
        result_global_matrixes = np.full(motion_bone_poses.shape, np.eye(4))

        for i, (fidx, (bone_index, offset_matrix)) in enumerate(product(list(range(len(fnos))), bone_offset_mats)):
            if out_fno_log and 0 < i and 0 == i % 10000:
                logger.info("-- ボーン変形行列積 [{i}]", i=i)

            result_matrixes[fidx, bone_index] = offset_matrix.copy()
            for matrix in tree_relative_matrixes[fidx][bone_index]:
                result_matrixes[fidx, bone_index] = matrix @ result_matrixes[fidx, bone_index]

        # グローバル行列は最後にボーン位置に移動させる
        result_global_matrixes = result_matrixes @ bone_pos_mats

        bone_matrixes = VmdBoneFrameTrees()
        for fidx, fno in enumerate(fnos):
            if out_fno_log:
                logger.count("ボーン行列結果", index=fidx, total_index_count=len(fnos), display_block=100)

            for bone in model.bones:
                bone_matrixes.append(
                    fno, bone.index, bone.name, result_global_matrixes[fidx, bone.index], result_matrixes[fidx, bone.index]
                )

        return bone_matrixes

    def get_bone_matrixes(
        self,
        fnos: list[int],
        model: PmxModel,
        target_bone_names: list[str],
        append_ik: bool = True,
        out_fno_log: bool = False,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """ボーン変形行列を求める"""

        row = len(fnos)
        col = len(model.bones)
        poses = np.full((row, col, 4, 4), np.eye(4))
        qqs = np.full((row, col, 4, 4), np.eye(4))
        scales = np.full((row, col, 4, 4), np.eye(4))
        local_poses = np.full((row, col, 4, 4), np.eye(4))
        local_qqs = np.full((row, col, 4, 4), np.eye(4))
        local_scales = np.full((row, col, 4, 4), np.eye(4))

        if append_ik:
            # IK回転を事前に求めておく
            for fno in fnos:
                self.calc_ik_rotations(fno, model, target_bone_names)

        total_count = len(fnos) * len(target_bone_names)

        for fidx, fno in enumerate(fnos):
            fno_poses: dict[int, MVector3D] = {}
            fno_scales: dict[int, MVector3D] = {}
            fno_local_poses: dict[int, MVector3D] = {}
            fno_local_qqs: dict[int, MQuaternion] = {}
            fno_local_scales: dict[int, MVector3D] = {}

            is_valid_local_pos = False
            is_valid_local_rot = False
            is_valid_local_scale = False

            for bidx, bone_name in enumerate(target_bone_names):
                if out_fno_log:
                    logger.count(
                        "ボーン計算",
                        index=fidx * len(target_bone_names) + bidx,
                        total_index_count=total_count,
                        display_block=100,
                    )

                bone = model.bones[bone_name]
                if bone.index in fno_local_poses:
                    continue
                bf = self[bone.name][fno]
                fno_poses[bone.index] = bf.position
                fno_scales[bone.index] = bf.scale
                fno_local_poses[bone.index] = bf.local_position
                fno_local_qqs[bone.index] = bf.local_rotation
                fno_local_scales[bone.index] = bf.local_scale

                is_valid_local_pos = is_valid_local_pos or bool(bf.local_position)
                is_valid_local_rot = is_valid_local_rot or bool(bf.local_rotation)
                is_valid_local_scale = is_valid_local_scale or bool(bf.local_scale)

            for bone_name in target_bone_names:
                bone = model.bones[bone_name]

                is_parent_bone_not_local_cancels: list[bool] = []
                parent_local_poses: list[MVector3D] = []
                parent_local_qqs: list[MQuaternion] = []
                parent_local_scales: list[MVector3D] = []
                parent_local_axises: list[MVector3D] = []

                for parent_index in bone.tree_indexes[:-1]:
                    parent_bone = model.bones[parent_index]
                    if parent_bone.index not in fno_local_poses:
                        parent_bf = self[parent_bone.name][fno]
                        fno_local_poses[parent_bone.index] = parent_bf.local_position
                        fno_local_qqs[parent_bone.index] = parent_bf.local_rotation
                        fno_local_scales[parent_bone.index] = parent_bf.local_scale
                    is_parent_bone_not_local_cancels.append(model.bones.is_bone_not_local_cancels[parent_bone.index])
                    parent_local_axises.append(model.bones.local_axises[parent_bone.index])
                    parent_local_poses.append(fno_local_poses[parent_bone.index])
                    parent_local_qqs.append(fno_local_qqs[parent_bone.index])
                    parent_local_scales.append(fno_local_scales[parent_bone.index])

                poses[fidx, bone.index] = self.get_position(fno, model, bone, fno_poses[bone.index])

                # モーションによるローカル移動量
                if is_valid_local_pos:
                    local_pos_mat = self.get_local_position(
                        bone,
                        fno_local_poses,
                        is_parent_bone_not_local_cancels,
                        parent_local_poses,
                        parent_local_axises,
                    )
                    local_poses[fidx, bone.index] = local_pos_mat

                # FK(捩り) > IK(捩り) > 付与親(捩り)
                qq = self.get_rotation(fno, model, bone, append_ik=append_ik)
                qqs[fidx, bone.index] = qq.to_matrix4x4().vector

                # ローカル回転
                if is_valid_local_rot:
                    local_rot_mat = self.get_local_rotation(
                        bone,
                        fno_local_qqs,
                        is_parent_bone_not_local_cancels,
                        parent_local_qqs,
                        parent_local_axises,
                    )
                    local_qqs[fidx, bone.index] = local_rot_mat

                # モーションによるスケール変化
                scale_mat = self.get_scale(fno, model, bone, fno_scales[bone.index])
                scales[fidx, bone.index] = scale_mat

                # ローカルスケール
                if is_valid_local_scale:
                    local_scale_mat = self.get_local_scale(
                        bone,
                        fno_local_scales,
                        is_parent_bone_not_local_cancels,
                        parent_local_scales,
                        parent_local_axises,
                    )
                    local_scales[fidx, bone.index] = local_scale_mat

        return poses, qqs, scales, local_poses, local_qqs, local_scales

    def get_position(self, fno: int, model: PmxModel, bone: Bone, position: MVector3D, loop: int = 0) -> np.ndarray:
        """
        該当キーフレにおけるボーンの移動位置
        """
        # 自身の位置
        mat = np.eye(4)
        mat[:3, 3] = position.vector

        # 付与親を加味して返す
        return mat @ self.get_effect_position(fno, model, bone, loop=loop + 1)

    def get_effect_position(self, fno: int, model: PmxModel, bone: Bone, loop: int = 0) -> np.ndarray:
        """
        付与親を加味した移動を求める
        """
        if not (bone.is_external_translation and bone.effect_index in model.bones):
            return np.eye(4)

        if 0 == bone.effect_factor or 20 < loop:
            # 付与率が0の場合、常に0になる
            return np.eye(4)

        # 付与親の移動量を取得する（それが付与持ちなら更に遡る）
        effect_bone = model.bones[bone.effect_index]
        effect_bf = self[effect_bone.name][fno]
        effect_pos_mat = self.get_position(fno, model, effect_bone, effect_bf.position, loop=loop + 1)
        # 付与率を加味する
        effect_pos_mat[:3, 3] *= bone.effect_factor

        return effect_pos_mat

    def get_local_position(
        self,
        bone: Bone,
        fno_local_poses: dict[int, MVector3D],
        is_parent_bone_not_local_cancels: Iterable[bool],
        parent_local_poses: Iterable[MVector3D],
        parent_local_axises: Iterable[MVector3D],
    ) -> np.ndarray:
        """
        該当キーフレにおけるボーンのローカル位置
        """
        # 自身のローカル移動量
        local_pos = fno_local_poses[bone.index]

        return calc_local_position(
            local_pos,
            bone.is_not_local_cancel,
            bone.local_axis,
            tuple(is_parent_bone_not_local_cancels),
            tuple(parent_local_poses),
            tuple(parent_local_axises),
        )

    def calc_ik_rotations(self, fno: int, model: PmxModel, target_bone_names: Iterable[str]):
        """IK関連ボーンの事前計算"""
        ik_target_names = [
            model.bone_trees[target_bone_name].last_name for target_bone_name in target_bone_names if model.bones[target_bone_name].is_ik
        ]
        if not ik_target_names:
            # IK計算対象がない場合はそのまま終了
            return

        ik_relative_bone_names = [
            model.bones[bone_index].name
            for bone_index in sorted(
                set(
                    [
                        relative_bone_index
                        for ik_target_name in ik_target_names
                        for relative_bone_index in model.bones[ik_target_name].relative_bone_indexes
                    ]
                )
            )
        ]

        # モーション内のキーフレリストから前の変化キーフレと次の変化キーフレを抽出する
        prev_frame_indexes: set[int] = {0}
        next_frame_indexes: set[int] = {self.max_fno}
        for relative_bone_name in ik_relative_bone_names:
            if relative_bone_name not in self:
                continue
            (prev_fno, _, next_fno) = self[relative_bone_name].range_indexes(fno)
            if prev_fno != fno:
                prev_frame_indexes |= {prev_fno}
            if next_fno != fno:
                next_frame_indexes |= {next_fno}

        for fno in (max(prev_frame_indexes), min(next_frame_indexes)):
            fno_qqs: dict[int, MQuaternion] = {}
            fno_ik_qqs: dict[int, Optional[MQuaternion]] = {}

            for relative_bone_name in ik_relative_bone_names:
                bone = model.bones[relative_bone_name]
                bf = self[relative_bone_name][fno]
                fno_qqs[bone.index] = bf.rotation
                fno_ik_qqs[bone.index] = bf.ik_rotation

            for relative_bone_name in ik_relative_bone_names:
                self.get_rotation(fno, model, bone, append_ik=True)

    def get_scale(self, fno: int, model: PmxModel, bone: Bone, scale: MVector3D, loop: int = 0) -> np.ndarray:
        """
        該当キーフレにおけるボーンの縮尺
        """

        # 自身のスケール
        scale_mat = np.eye(4)
        scale_mat[:3, :3] += np.diag(np.where(scale.vector < -1, -1, scale.vector))

        # 付与親を加味して返す
        return self.get_effect_scale(fno, model, bone, scale_mat, loop=loop + 1)

    def get_effect_scale(self, fno: int, model: PmxModel, bone: Bone, scale_mat: np.ndarray, loop: int = 0) -> np.ndarray:
        """
        付与親を加味した縮尺を求める
        """
        if not (bone.is_external_translation and bone.effect_index in model.bones):
            return scale_mat

        if 0 == bone.effect_factor or 20 < loop:
            # 付与率が0の場合、常に1になる
            return np.eye(4)

        # 付与親の回転量を取得する（それが付与持ちなら更に遡る）
        effect_bone = model.bones[bone.effect_index]
        effect_bf = self[effect_bone.name][fno]
        effect_scale_mat = self.get_scale(fno, model, effect_bone, effect_bf.scale, loop=loop + 1)

        return scale_mat @ effect_scale_mat

    def get_local_scale(
        self,
        bone: Bone,
        fno_local_scales: dict[int, MVector3D],
        is_parent_bone_not_local_cancels: Iterable[bool],
        parent_local_scales: Iterable[MVector3D],
        parent_local_axises: Iterable[MVector3D],
    ) -> np.ndarray:
        """
        該当キーフレにおけるボーンのローカル縮尺
        """
        # 自身のローカルスケール
        local_scale = fno_local_scales[bone.index]

        return calc_local_scale(
            local_scale,
            bone.is_not_local_cancel,
            bone.local_axis,
            tuple(is_parent_bone_not_local_cancels),
            tuple(parent_local_scales),
            tuple(parent_local_axises),
        )

    def get_rotation(self, fno: int, model: PmxModel, bone: Bone, append_ik: bool = False, loop: int = 0) -> MQuaternion:
        """
        該当キーフレにおけるボーンの相対位置
        append_ik : IKを計算するか(循環してしまう場合があるので、デフォルトFalse)
        """

        # FK(捩り) > IK(捩り) > 付与親(捩り)
        bf = self[bone.name][fno]
        qq = bf.rotation.copy()

        if bf.ik_rotation is not None:
            # IK用回転を持っている場合、追加
            qq *= bf.ik_rotation

        fk_qq = self.get_fix_rotation(bone, qq)

        # IKを加味した回転
        ik_qq = self.get_ik_rotation(fno, model, bone, fk_qq) if append_ik else fk_qq

        # 付与親を加味した回転
        effect_qq = self.get_effect_rotation(fno, model, bone, ik_qq, loop=loop + 1)

        return effect_qq

    def get_effect_rotation(self, fno: int, model: PmxModel, bone: Bone, qq: MQuaternion, loop: int = 0) -> MQuaternion:
        """
        付与親を加味した回転を求める
        """
        if not (bone.is_external_rotation and bone.effect_index in model.bones):
            return qq

        if 0 == bone.effect_factor or loop > 20:
            # 付与率が0の場合、常に0になる
            # MMDエンジン対策で無限ループを避ける
            return MQuaternion()

        # 付与親の回転量を取得する（それが付与持ちなら更に遡る）
        effect_bone = model.bones[bone.effect_index]
        effect_qq = self.get_rotation(fno, model, effect_bone, loop=loop + 1)
        if 0 < bone.effect_factor:
            # 正の付与親
            qq *= effect_qq.multiply_factor(bone.effect_factor)
            qq.normalize()
        else:
            # 負の付与親の場合、逆回転
            qq *= (effect_qq.multiply_factor(abs(bone.effect_factor))).inverse()
            qq.normalize()

        return qq

    def get_ik_rotation(self, fno: int, model: PmxModel, bone: Bone, qq: MQuaternion) -> MQuaternion:
        """
        IKを加味した回転を求める
        """

        if not bone.ik_link_indexes:
            return qq

        for ik_target_bone_idx in bone.ik_link_indexes:
            # IKボーン自身の位置
            ik_bone = model.bones[ik_target_bone_idx]

            if ik_target_bone_idx not in model.bones or not ik_bone.ik:
                continue

            # IKターゲットボーン
            effector_bone = model.bones[ik_bone.ik.bone_index]

            is_break = False
            for loop in range(ik_bone.ik.loop_count):
                for ik_link in ik_bone.ik.links:
                    # ikLink は末端から並んでる
                    if ik_link.bone_index not in model.bones:
                        continue

                    # 処理対象IKボーン
                    link_bone = model.bones[ik_link.bone_index]

                    # IK関連の行列を一括計算
                    ik_matrixes = self.animate_bone_matrixes(
                        [fno], model, bone_names=[ik_bone.name, effector_bone.name, link_bone.name], append_ik=False
                    )

                    # IKボーンのグローバル位置
                    global_target_pos = ik_matrixes[fno, ik_bone.name].position

                    # 現在のIKターゲットボーンのグローバル位置を取得
                    global_effector_pos = ik_matrixes[fno, effector_bone.name].position

                    # 注目ノード（実際に動かすボーン）
                    link_matrix = ik_matrixes[fno, link_bone.name].global_matrix

                    # ワールド座標系から注目ノードの局所座標系への変換
                    link_inverse_matrix = link_matrix.inverse()

                    # 注目ノードを起点とした、エフェクタのローカル位置
                    local_effector_pos = link_inverse_matrix * global_effector_pos
                    # 注目ノードを起点とした、IK目標のローカル位置
                    local_target_pos = link_inverse_matrix * global_target_pos

                    if 1e-6 > (local_effector_pos - local_target_pos).length_squared():
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

                    logger.test(f"[{model.name}][{fno}][{bone.name}:{link_bone.name}][{loop:02d}][{1 - rotation_dot}]: IK計算")

                    if 1e-8 > 1 - rotation_dot:
                        # 変形角度がほぼ変わらない場合、スルー
                        is_break = True
                        break

                    # 回転角度
                    rotation_radian = acos(max(-1, min(1, rotation_dot)))

                    # 回転軸
                    rotation_axis = norm_effector_pos.cross(norm_target_pos).normalized()
                    # 回転角度
                    rotation_degree = degrees(rotation_radian)

                    # 制限角で最大変位量を制限する(システムボーンは制限角に準拠)
                    if 0 < loop and not ik_bone.is_system:
                        rotation_degree = min(rotation_degree, ik_bone.ik.unit_rotation.degrees.x)

                    # リンクボーンの角度を保持
                    link_bf = self[link_bone.name][fno]

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
        """
        if bone.has_fixed_axis:
            return qq.to_fixed_axis_quaternion(bone.corrected_fixed_axis)

        return qq

    def get_local_rotation(
        self,
        bone: Bone,
        fno_local_qqs: dict[int, MQuaternion],
        is_parent_bone_not_local_cancels: Iterable[bool],
        parent_local_qqs: Iterable[MQuaternion],
        parent_local_axises: Iterable[MVector3D],
    ) -> np.ndarray:
        """
        該当キーフレにおけるボーンのローカル回転
        """
        # 自身のローカル回転量
        local_qq = fno_local_qqs[bone.index]

        return calc_local_rotation(
            local_qq,
            bone.is_not_local_cancel,
            bone.local_axis,
            tuple(is_parent_bone_not_local_cancels),
            tuple(parent_local_qqs),
            tuple(parent_local_axises),
        )


@lru_cache(maxsize=None)
def calc_local_position(
    local_pos: MVector3D,
    is_bone_not_local_cancel: bool,
    local_axis: MVector3D,
    is_parent_bone_not_local_cancels: tuple[bool],
    parent_local_poses: tuple[MVector3D],
    parent_local_axises: tuple[MVector3D],
) -> np.ndarray:
    local_parent_matrix = np.eye(4)

    # 親を辿る
    if not is_bone_not_local_cancel:
        for n in range(1, len(parent_local_axises) + 1):
            local_parent_matrix = local_parent_matrix @ calc_local_position(
                parent_local_poses[-n],
                is_parent_bone_not_local_cancels[-n],
                parent_local_axises[-n],
                tuple(is_parent_bone_not_local_cancels[:-n]),
                tuple(parent_local_poses[:-n]),
                tuple(parent_local_axises[:-n]),
            )

    # ローカル軸に沿った回転行列
    rotation_matrix = local_axis.to_local_matrix4x4().vector

    local_pos_mat = np.eye(4)
    local_pos_mat[:3, 3] = local_pos.vector

    # ローカル軸に合わせた移動行列を作成する(親はキャンセルする)
    return inv(local_parent_matrix) @ inv(rotation_matrix) @ local_pos_mat @ rotation_matrix


@lru_cache(maxsize=None)
def calc_local_rotation(
    local_qq: MQuaternion,
    is_bone_not_local_cancel: bool,
    local_axis: MVector3D,
    is_parent_bone_not_local_cancels: tuple[bool],
    parent_local_qqs: tuple[MQuaternion],
    parent_local_axises: tuple[MVector3D],
) -> np.ndarray:
    local_parent_matrix = np.eye(4)

    # 親を辿る
    if not is_bone_not_local_cancel:
        for n in range(1, len(parent_local_axises) + 1):
            local_parent_matrix = local_parent_matrix @ calc_local_rotation(
                parent_local_qqs[-n],
                is_parent_bone_not_local_cancels[-n],
                parent_local_axises[-n],
                tuple(is_parent_bone_not_local_cancels[:-n]),
                tuple(parent_local_qqs[:-n]),
                tuple(parent_local_axises[:-n]),
            )

    # ローカル軸に沿った回転行列
    rotation_matrix = local_axis.to_local_matrix4x4().vector

    local_rot_mat = local_qq.to_matrix4x4().vector

    # ローカル軸に合わせた移動行列を作成する(親はキャンセルする)
    return inv(local_parent_matrix) @ inv(rotation_matrix) @ local_rot_mat @ rotation_matrix


@lru_cache(maxsize=None)
def calc_local_scale(
    local_scale: MVector3D,
    is_bone_not_local_cancel: bool,
    local_axis: MVector3D,
    is_parent_bone_not_local_cancels: tuple[bool],
    parent_local_scales: tuple[MVector3D],
    parent_local_axises: tuple[MVector3D],
) -> np.ndarray:
    local_parent_matrix = np.eye(4)

    # 親を辿る
    if not is_bone_not_local_cancel:
        for n in range(1, len(parent_local_axises) + 1):
            local_parent_matrix = local_parent_matrix @ calc_local_scale(
                parent_local_scales[-n],
                is_parent_bone_not_local_cancels[-n],
                parent_local_axises[-n],
                tuple(is_parent_bone_not_local_cancels[:-n]),
                tuple(parent_local_scales[:-n]),
                tuple(parent_local_axises[:-n]),
            )

    # ローカル軸に沿った回転行列
    rotation_matrix = local_axis.to_local_matrix4x4().vector

    # マイナス縮尺にはしない
    local_scale_mat = np.eye(4)
    local_scale_mat[:3, :3] += np.diag(np.where(local_scale.vector < -1, -1, local_scale.vector))

    # ローカル軸に合わせた移動行列を作成する(親はキャンセルする)
    return inv(local_parent_matrix) @ inv(rotation_matrix) @ local_scale_mat @ rotation_matrix


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
        mf.ratio = prev_mf.ratio + (next_mf.ratio - prev_mf.ratio) * ry

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

    def animate_vertex_morphs(self, fno: int, model: PmxModel, is_gl: bool = True) -> np.ndarray:
        """頂点モーフ変形量"""
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
                    ratio_pos: MVector3D = offset.position * mf.ratio
                    if is_gl:
                        poses[offset.vertex_index] += ratio_pos.gl.vector
                    else:
                        poses[offset.vertex_index] += ratio_pos.vector

        return np.array(poses)

    def animate_after_vertex_morphs(self, fno: int, model: PmxModel, is_gl: bool = True) -> np.ndarray:
        """ボーン変形後頂点モーフ変形量"""
        row = len(model.vertices)
        poses = np.full((row, 3), np.zeros(3))

        for morph in model.morphs.filter_by_type(MorphType.AFTER_VERTEX):
            if morph.name not in self.data:
                # モーフそのものの定義がなければスルー
                continue
            mf = self[morph.name][fno]
            if not mf.ratio:
                continue

            # モーションによる頂点モーフ変動量
            for offset in morph.offsets:
                if type(offset) is VertexMorphOffset and offset.vertex_index < row:
                    ratio_pos: MVector3D = offset.position * mf.ratio
                    if is_gl:
                        poses[offset.vertex_index] += ratio_pos.gl.vector
                    else:
                        poses[offset.vertex_index] += ratio_pos.vector

        return np.array(poses)

    def animate_uv_morphs(self, fno: int, model: PmxModel, uv_index: int, is_gl: bool = True) -> np.ndarray:
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

        if is_gl:
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
        bf.local_position += offset.local_position * ratio
        bf.rotation *= MQuaternion.from_euler_degrees(offset.rotation.degrees * ratio)
        bf.local_rotation *= MQuaternion.from_euler_degrees(offset.local_rotation.degrees * ratio)
        bf.scale += offset.scale * ratio
        bf.local_scale += offset.local_scale * ratio
        return bf

    def animate_group_morphs(
        self, fno: int, model: PmxModel, materials: list[ShaderMaterial], is_gl: bool = True
    ) -> tuple[np.ndarray, VmdBoneFrames, list[ShaderMaterial]]:
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
                            ratio_pos: MVector3D = offset.position * mf_factor
                            if is_gl:
                                group_vertex_poses[offset.vertex_index] += ratio_pos.gl.vector
                            else:
                                group_vertex_poses[offset.vertex_index] += ratio_pos.vector
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
        return int(np.sum([len(bfs.indexes) for bfs in self.bones]))

    @property
    def morph_count(self) -> int:
        return int(np.sum([len(mfs.indexes) for mfs in self.morphs]))

    @property
    def ik_count(self) -> int:
        return int(np.sum([len(ifs.iks) for ifs in self.show_iks]))

    @property
    def max_fno(self) -> int:
        return max(self.bones.max_fno, self.morphs.max_fno)

    @property
    def name(self) -> str:
        return self.model_name

    def cache_clear(self) -> None:
        self.bones.cache_clear()

    def append_bone_frame(self, bf: VmdBoneFrame) -> None:
        """ボーンキーフレ追加"""
        self.bones[bf.name].append(bf)

    def append_morph_frame(self, mf: VmdMorphFrame) -> None:
        """モーフキーフレ追加"""
        self.morphs[mf.name].append(mf)

    def insert_bone_frame(self, bf: VmdBoneFrame) -> None:
        """ボーンキーフレ挿入"""
        self.bones[bf.name].insert(bf)

    def insert_morph_frame(self, mf: VmdMorphFrame) -> None:
        """モーフキーフレ挿入"""
        self.morphs[mf.name].insert(mf)

    def animate(
        self, fno: int, model: PmxModel, is_gl: bool = True
    ) -> tuple[int, np.ndarray, VmdBoneFrameTrees, np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[ShaderMaterial]]:
        logger.debug(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: 開始")

        # 頂点モーフ
        vertex_morph_poses = self.morphs.animate_vertex_morphs(fno, model, is_gl)
        logger.test(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: 頂点モーフ")

        # ボーン変形後頂点モーフ
        after_vertex_morph_poses = self.morphs.animate_after_vertex_morphs(fno, model, is_gl)
        logger.test(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: ボーン変形後頂点モーフ")

        # UVモーフ
        uv_morph_poses = self.morphs.animate_uv_morphs(fno, model, 0, is_gl)
        logger.test(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: UVモーフ")

        # 追加UVモーフ1
        uv1_morph_poses = self.morphs.animate_uv_morphs(fno, model, 1, is_gl)
        logger.test(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: 追加UVモーフ1")

        # 追加UVモーフ2-4は無視

        # 材質モーフ
        material_morphs = self.morphs.animate_material_morphs(fno, model)
        logger.test(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: 材質モーフ")

        # グループモーフ
        group_vertex_morph_poses, group_morph_bone_frames, group_materials = self.morphs.animate_group_morphs(
            fno, model, material_morphs, is_gl
        )
        logger.test(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: グループモーフ")

        bone_matrixes = self.animate_bone([fno], model)

        # OpenGL座標系に変換

        gl_matrixes = np.array([bft.local_matrix_ary.T for bft in bone_matrixes])
        # gl_matrixes = np.array(bone_matrixes)

        gl_matrixes[..., 0, 1:3] *= -1
        gl_matrixes[..., 1:3, 0] *= -1
        gl_matrixes[..., 3, 0] *= -1

        logger.test(f"-- スキンメッシュアニメーション[{model.name}][{fno:04d}]: OpenGL座標系変換")

        return (
            fno,
            gl_matrixes,
            bone_matrixes,
            vertex_morph_poses + group_vertex_morph_poses,
            after_vertex_morph_poses,
            uv_morph_poses,
            uv1_morph_poses,
            group_materials,
        )

    def animate_bone(
        self,
        fnos: list[int],
        model: PmxModel,
        bone_names: Iterable[str] = [],
        append_ik: bool = True,
        clear_ik: bool = False,
        out_fno_log: bool = False,
    ) -> VmdBoneFrameTrees:
        all_morph_bone_frames = VmdBoneFrames()

        if clear_ik:
            self.cache_clear()

        for fidx, fno in enumerate(fnos):
            if out_fno_log:
                logger.count("キーフレ確認", index=fidx, total_index_count=len(fnos), display_block=100)

            logger.test(f"-- ボーンアニメーション[{model.name}][{fno:04d}]: 開始")

            # 材質モーフ
            material_morphs = self.morphs.animate_material_morphs(fno, model)
            logger.test(f"-- ボーンアニメーション[{model.name}][{fno:04d}]: 材質モーフ")

            # ボーンモーフ
            morph_bone_frames = self.morphs.animate_bone_morphs(fno, model)
            logger.test(f"-- ボーンアニメーション[{model.name}][{fno:04d}]: ボーンモーフ")

            for bfs in morph_bone_frames:
                bf = bfs[fno]

                if clear_ik:
                    # IK計算しない場合、IK計算結果を渡さない
                    bf.ik_rotation = None

                mbf = all_morph_bone_frames[bf.name][bf.index]
                all_morph_bone_frames[bf.name][bf.index] = mbf + bf

            # グループモーフ
            _, group_morph_bone_frames, _ = self.morphs.animate_group_morphs(fno, model, material_morphs)
            logger.test(f"-- ボーンアニメーション[{model.name}][{fno:04d}]: グループモーフ")

            for bfs in group_morph_bone_frames:
                bf = bfs[fno]
                mbf = all_morph_bone_frames[bf.name][bf.index]

                if clear_ik:
                    # IK計算しない場合、IK計算結果を渡さない
                    bf.ik_rotation = None
                    mbf.ik_rotation = None

                all_morph_bone_frames[bf.name][bf.index] = mbf + bf

            logger.test(f"-- ボーンアニメーション[{model.name}][{fno:04d}]: モーフキーフレ加算")

        # ボーン変形行列操作
        bone_matrixes = self.bones.animate_bone_matrixes(
            fnos, model, all_morph_bone_frames, bone_names, append_ik=append_ik, out_fno_log=out_fno_log
        )
        logger.test(f"-- ボーンアニメーション[{model.name}]: ボーン変形行列操作")

        return bone_matrixes
