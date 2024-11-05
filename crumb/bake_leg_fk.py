import os
import sys
import time
from winsound import SND_ALIAS, PlaySound

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mlib.domain.math import MQuaternion  # noqa: E402
from mlib.pmx.pmx_collection import PmxModel  # noqa: E402
from mlib.pmx.pmx_reader import PmxReader  # noqa: E402
from mlib.vmd.vmd_collection import VmdMotion  # noqa: E402
from mlib.vmd.vmd_part import VmdBoneFrame  # noqa: E402
from mlib.vmd.vmd_reader import VmdReader  # noqa: E402
from mlib.vmd.vmd_writer import VmdWriter  # noqa: E402

vmd_reader = VmdReader()
motion: VmdMotion = vmd_reader.read_by_filepath(
    "D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/運動/アラウンド・ザ・ワールド out 咲 枡/モデル ATW out IK補正4.vmd"
)

pmx_reader = PmxReader()
model: PmxModel = pmx_reader.read_by_filepath(
    "E:/MMD/Dressup/検証/20230819/AMikuSummerBody230819_Joint_20230819_211423.pmx"
)

bone_names = [
    "下半身",
    "左足D",
    "左ひざD",
    "左足首D",
    "右足D",
    "右ひざD",
    "右足首D",
    "左足ＩＫ",
    "右足ＩＫ",
    "左つま先ＩＫ",
    "右つま先ＩＫ",
]

fk_bone_names = [
    "左足",
    "左ひざ",
    "左足首",
    "右足",
    "右ひざ",
    "右足首",
]

# 時間計測開始
start_time = time.perf_counter()

new_motion = VmdMotion()

bone_matrixes = motion.animate_bone(
    list(range(145)), model, bone_names + fk_bone_names, out_fno_log=True
)

for fno in range(145):
    for bone_name in fk_bone_names:
        fk_rotation = motion.bones[bone_name][fno].rotation
        ik_rotation = motion.bones[bone_name][fno].ik_rotation or MQuaternion()
        d_rotation = motion.bones[f"{bone_name}D"][fno].rotation

        new_bf = VmdBoneFrame(fno, bone_name)
        new_bf.rotation = d_rotation * fk_rotation * ik_rotation
        new_motion.append_bone_frame(new_bf)

# 時間計測終了
end_time = time.perf_counter()

VmdWriter(
    new_motion,
    "D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/運動/アラウンド・ザ・ワールド out 咲 枡/モデル ATW out FK.vmd",
    "あぴミク足焼き込み",
).save()


PlaySound("SystemAsterisk", SND_ALIAS)
