import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mlib.domain.interpolation import split_interpolation
from mlib.domain.math import MMatrix4x4
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_reader import PmxReader
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_reader import VmdReader
from mlib.vmd.vmd_writer import VmdWriter

vmd_reader = VmdReader()
motion: VmdMotion = vmd_reader.read_by_filepath(
    "D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/カミサマネジマキ 粉ふきスティック/sora_guiter1_2016.vmd"
)

pmx_reader = PmxReader()
model: PmxModel = pmx_reader.read_by_filepath(
    # "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/弱音ハク/Tda式改変弱音ハクccvセット1.05 coa/Tda式改変弱音ハクccv_nc 1.05/ギター用/Tda式改変弱音ハクccv_nc ver1.05_ギター.pmx"
    "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/他/天羽ソラ_set ISAO/天羽ソラpony/ギター/天羽ソラPony_ギター.pmx"
)

bone_names = (
    "センター",
    "上半身",
    "上半身2",
    "左肩",
    "左腕",
    "左腕捩",
    "左ひじ",
    "左手捩",
    "左手首",
    "左親指０",
    "左親指１",
    "左親指２",
    "左人指１",
    "左人指２",
    "左人指３",
    "左中指１",
    "左中指２",
    "左中指３",
    "左薬指１",
    "左薬指２",
    "左薬指３",
    "左小指１",
    "左小指２",
    "左小指３",
    "右肩",
    "右腕",
    "右腕捩",
    "右ひじ",
    "右手捩",
    "右手首",
    "右親指０",
    "右親指１",
    "右親指２",
    "右人指１",
    "右人指２",
    "右人指３",
    "右中指１",
    "右中指２",
    "右中指３",
    "右薬指１",
    "右薬指２",
    "右薬指３",
    "右小指１",
    "右小指２",
    "右小指３",
    "下半身",
    "左足",
    "左ひざ",
    "左足首",
    "右足",
    "右ひざ",
    "右足首",
    "左足ＩＫ",
    "右足ＩＫ",
    "左つま先ＩＫ",
    "右つま先ＩＫ",
)

# 時間計測開始
start_time = time.perf_counter()

all_fnos = {0}
for bone_name in ("左手首", "右手首"):
    all_fnos |= set(motion.bones[bone_name].indexes)

new_motion = VmdMotion()

for n in range(1, 5):
    fnos = sorted(set(range((n - 1) * 100, n * 100)) & set(all_fnos))
    poses, qqs, _, _, _, _ = motion.bones.get_bone_matrixes(
        fnos, model, model.bones.names
    )
    for fidx, fno in enumerate(fnos):
        for bone_name in bone_names:
            new_bf = new_motion.bones[bone_name][fno]
            new_bf.position = motion.bones[bone_name][fno].position
            new_bf.rotation = MMatrix4x4(
                qqs[fidx, model.bones[bone_name].index]
            ).to_quaternion()

            prev_fno, now_fno, next_fno = motion.bones[bone_name].range_indexes(
                fno, indexes=motion.bones[bone_name].register_indexes
            )
            if now_fno < next_fno:
                next_bf = motion.bones[bone_name].data[next_fno]
                now_rot_ip, next_rot_ip = split_interpolation(
                    next_bf.interpolations.rotation, prev_fno, now_fno, next_fno
                )
                now_mov_x_ip, next_mov_x_ip = split_interpolation(
                    next_bf.interpolations.translation_x, prev_fno, now_fno, next_fno
                )
                now_mov_y_ip, next_mov_y_ip = split_interpolation(
                    next_bf.interpolations.translation_y, prev_fno, now_fno, next_fno
                )
                now_mov_z_ip, next_mov_z_ip = split_interpolation(
                    next_bf.interpolations.translation_z, prev_fno, now_fno, next_fno
                )

                new_bf.interpolations.rotation = now_rot_ip
                new_bf.interpolations.translation_x = now_mov_x_ip
                new_bf.interpolations.translation_y = now_mov_y_ip
                new_bf.interpolations.translation_z = now_mov_z_ip

                new_next_bf = new_motion.bones[bone_name][next_fno]
                new_next_bf.interpolations.rotation = next_rot_ip
                new_next_bf.interpolations.translation_x = next_mov_x_ip
                new_next_bf.interpolations.translation_y = next_mov_y_ip
                new_next_bf.interpolations.translation_z = next_mov_z_ip

                new_motion.bones[bone_name].append(new_bf)
                new_motion.bones[bone_name].append(new_next_bf)

    # 時間計測終了
    end_time = time.perf_counter()

    print(f"{n:02d}: {len(fnos):03d} ({((end_time - start_time) / 60):.4f})")

VmdWriter(
    new_motion,
    "D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/カミサマネジマキ 粉ふきスティック/sora_guiter1_2016_焼き込み2.vmd",
    "ハク腕焼き込み",
).save()
