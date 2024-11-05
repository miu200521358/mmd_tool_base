import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mlib.domain.math import MMatrix4x4, MQuaternion, MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_reader import PmxReader
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdBoneFrame
from mlib.vmd.vmd_reader import VmdReader
from mlib.vmd.vmd_writer import VmdWriter

vmd_reader = VmdReader()
motion: VmdMotion = vmd_reader.read_by_filepath("D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/ラビットホール mobiusP/ラビットホール_Z-1.vmd")

pmx_reader = PmxReader()
model: PmxModel = pmx_reader.read_by_filepath("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Sour式初音ミクVer.1.02/White.pmx")

fnos = list(range(0, motion.max_fno, 2))
offsets = [0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2, 1.35]
matrixes = motion.animate_bone(fnos, model, ["上半身"], out_fno_log=True)

out_motions: list[VmdMotion] = [VmdMotion() for _ in range(len(offsets))]
initial_qq = MQuaternion()

prev_y_qq = MQuaternion()
prev_fno = 0

for fidx, fno in enumerate(fnos):
    center_mat = matrixes[fno, "センター"].global_matrix
    center_pos = matrixes[fno, "センター"].position
    upper_mat = matrixes[fno, "上半身"].global_matrix
    x_qq, y_qq, z_qq, yz_qq = upper_mat.to_quaternion().separate_by_axis(MVector3D(1, 0, 0))
    y_dot = abs(y_qq.dot(prev_y_qq))

    if fidx > 0 and 0.999 > y_dot:
        print(f"SKIP fno[{fno}({y_dot:.5f})]")
        # 回転量が大きい場合は一旦スルー
        prev_y_qq = y_qq.copy()
        continue

    mat = MMatrix4x4()
    mat.translate(center_pos)
    mat.rotate(y_qq)
    dot = abs(1 - y_qq.dot(initial_qq))

    for n, offset in enumerate(offsets):
        center_original_pos = motion.bones["センター"][fno].position
        center_fixed_pos = mat * MVector3D(0, 0, offset * dot)
        center_offset_pos = center_mat.inverse() * center_fixed_pos

        bf = VmdBoneFrame(index=fno, name="グルーブ")
        bf.position = center_offset_pos
        out_motions[n].bones["グルーブ"].append(bf)

    print(f"fno[{fno}({offset:.2f})], original[{center_original_pos}] offset[{center_offset_pos}] y_dot[{y_dot:.5f}]")

    prev_fno = fno
    prev_y_qq = y_qq.copy()

for n, (offset, motion) in enumerate(zip(offsets, out_motions)):
    VmdWriter(motion, f"D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/ラビットホール mobiusP/ラビットホール_{offset:.2f}.vmd", model.name).save()

if os.name == "nt":
    try:
        from winsound import SND_ALIAS, PlaySound

        PlaySound("SystemAsterisk", SND_ALIAS)
    except Exception:
        pass
