import os

bits_header_list = [
    ("bits", "c++config.h"),
]

include_header_list = [
    ("", "assert.h"),
    ("", "float.h"),
    ("", "math.h"),
    ("", "stdlib.h"),
]

bt_header_list = [
    ("LinearMath", "btScalar.h"),
    ("LinearMath", "btMinMax.h"),
    ("LinearMath", "btAlignedAllocator.h"),
    ("LinearMath", "btAlignedAllocator.cpp"),
    ("LinearMath", "btVector3.h"),
    ("LinearMath", "btQuadWord.h"),
    ("LinearMath", "btQuaternion.h"),
    ("LinearMath", "btMatrix3x3.h"),
    ("LinearMath", "btTransform.h"),
    ("LinearMath", "btMotionState.h"),
    ("LinearMath", "btDefaultMotionState.h"),
    ("LinearMath", "btAlignedObjectArray.h"),
    ("LinearMath", "btHashMap.h"),
    ("LinearMath", "btSerializer.h"),
    ("LinearMath", "btSerializer.cpp"),
    ("LinearMath", "btSerializer64.cpp"),
    ("LinearMath", "btAabbUtil2.h"),
    ("LinearMath", "btConvexHullComputer.h"),
    ("LinearMath", "btConvexHullComputer.cpp"),
    ("LinearMath", "btGeometryUtil.h"),
    ("BulletCollision/BroadphaseCollision", "btBroadphaseProxy.h"),
    ("BulletCollision/CollisionShapes", "btCollisionMargin.h"),
    ("BulletCollision/CollisionShapes", "btCollisionShape.h"),
    ("BulletCollision/CollisionShapes", "btCollisionShape.cpp"),
    ("BulletCollision/CollisionShapes", "btConvexShape.h"),
    ("BulletCollision/CollisionShapes", "btConvexInternalShape.h"),
    ("BulletCollision/CollisionShapes", "btConvexInternalShape.cpp"),
    ("BulletCollision/CollisionShapes", "btSphereShape.h"),
    ("BulletCollision/CollisionShapes", "btConvexPolyhedron.h"),
    ("BulletCollision/CollisionShapes", "btPolyhedralConvexAabbCachingShape.h"),
    ("BulletCollision/CollisionShapes", "btPolyhedralConvexAabbCachingShape.cpp"),
    ("BulletCollision/CollisionShapes", "btPolyhedralConvexShape.h"),
    ("BulletCollision/CollisionShapes", "btPolyhedralConvexShape.cpp"),
    ("BulletCollision/CollisionShapes", "btConvexHullShape.h"),
    ("BulletCollision/CollisionShapes", "btBoxShape.h"),
    ("BulletCollision/CollisionShapes", "btBoxShape.cpp"),
    ("BulletCollision/CollisionShapes", "btTriangleShape.h"),
    # ("BulletCollision/CollisionShapes", "btTriangleShape.cpp"),
    ("BulletCollision/CollisionShapes", "btCylinderShape.h"),
    # ("BulletCollision/CollisionShapes", "btCylinderShape.cpp"),
    ("BulletCollision/CollisionShapes", "btCylinderShapeX.h"),
    # ("BulletCollision/CollisionShapes", "btCylinderShapeX.cpp"),
    ("BulletCollision/CollisionShapes", "btCylinderShapeZ.h"),
    # ("BulletCollision/CollisionShapes", "btCylinderShapeZ.cpp"),
    ("BulletCollision/CollisionShapes", "btConeShape.h"),
    # ("BulletCollision/CollisionShapes", "btConeShape.cpp"),
    ("BulletCollision/CollisionShapes", "btConeShapeX.h"),
    # ("BulletCollision/CollisionShapes", "btConeShapeX.cpp"),
    ("BulletCollision/CollisionShapes", "btConeShapeZ.h"),
    # ("BulletCollision/CollisionShapes", "btConeShapeZ.cpp"),
    ("BulletCollision/CollisionShapes", "btCapsuleShape.h"),
    # ("BulletCollision/CollisionShapes", "btCapsuleShape.cpp"),
    ("BulletCollision/CollisionShapes", "btCapsuleShapeX.h"),
    # ("BulletCollision/CollisionShapes", "btCapsuleShapeX.cpp"),
    ("BulletCollision/CollisionShapes", "btCapsuleShapeZ.h"),
    # ("BulletCollision/CollisionShapes", "btCapsuleShapeZ.cpp"),
    ("BulletCollision/CollisionShapes", "btConvexPointCloudShape.h"),
    ("BulletCollision/CollisionShapes", "btConvexShape.cpp"),
    # ("BulletDynamics/Dynamics", "btRigidBody.h"),
    # ("BulletDynamics/Dynamics", "btDiscreteDynamicsWorld.h"),
]


# def find_header(root_dir_path, dir_path, header_file_name):
#     header_path = os.path.join(root_dir_path, dir_path, header_file_name)

#     if not os.path.exists(header_path):
#         print("×not found: %s" % header_path)
#         return None

#     print("○found: %s" % header_path)

#     # ヘッダーファイルの中身をすべて文字列リストとして読み込む
#     with open(header_path, "r") as f:
#         header_lines = f.readlines()

#     # for header_line in header_lines:
#     #     if "#include " in header_line:
#     #         # include 文がある場合、その行のファイルを先に出力する
#     #         includes = header_line.split()
#     #         if len(includes) >= 2:
#     #             if "<" in includes[1]:
#     #                 if includes[1] not in primitive_headers:
#     #                     primitive_headers.append(includes[1])
#     #             else:
#     #                 include_file = includes[1].replace('"', "")
#     #                 include_dir_path = os.path.dirname(include_file)
#     #                 if not include_dir_path:
#     #                     include_dir_path = dir_path
#     #                 include_file_name = os.path.basename(include_file)
#     #                 find_header(root_dir_path, include_dir_path, include_file_name, of)
#     #     # else:
#     #     #     of.write(header_line)

#     # included_headers.append((dir_path, header_file_name))

#     output_path = os.path.join(root_dir_path, dir_path, f"{header_file_name}")

#     with open(output_path, "w") as of:
#         of.write("////// %s/%s ----------------\n\n" % (dir_path, header_file_name))

#         of.write('"')
#         of.write('%s/%s"\n\n' % (dir_path, header_file_name))

#         of.write("%{\n\n")

#         for header_line in header_lines:
#             if "#include " in header_line:
#                 # includeのパスを再設定する
#                 includes = header_line.split()
#                 if len(includes) >= 2:
#                     if "<" in includes[1]:
#                         if includes[1] not in primitive_headers:
#                             primitive_headers.append(includes[1])
#                     else:
#                         include_file = includes[1].replace('"', "")
#                         include_dir_path = os.path.dirname(include_file)
#                         if not include_dir_path:
#                             include_dir_path = dir_path
#                         include_file_name = os.path.basename(include_file)
#                         # of.write(
#                         #     '#include "bullet/src/%s/%s"\n'
#                         #     % (include_dir_path, include_file_name)
#                         # )
#                         print(
#                             '---- #include "%s" -> "%s/%s"'
#                             % (header_line.strip(), include_dir_path, include_file_name)
#                         )

#             elif "#include " not in header_line:
#                 of.write(header_line)

#         of.write("\n\n%}\n")

#     return None


# if __name__ == "__main__":
#     # 出力用テキストファイル
#     output_file = "C:/MMD/mmd_base/crumb/bullet_headers.txt"
#     with open(output_file, "w") as of:

#         # for header_dir_path, header_file_name in bits_header_list:
#         #     find_header(
#         #         "C:/development/TDM-GCC-64/lib/gcc/x86_64-w64-mingw32/10.3.0/include/c++/x86_64-w64-mingw32",
#         #         header_dir_path,
#         #         header_file_name,
#         #         of,
#         #     )

#         # for header_dir_path, header_file_name in include_header_list:
#         #     find_header(
#         #         "C:/development/TDM-GCC-64/x86_64-w64-mingw32/include",
#         #         header_dir_path,
#         #         header_file_name,
#         #         of,
#         #     )

#         for header_dir_path, header_file_name in bt_header_list:
#             find_header(
#                 "C:/MMD/mlib_go/pkg/mbt/bullet/src",
#                 header_dir_path,
#                 header_file_name,
#                 of,
#             )

#     of.close()

#     for header in primitive_headers:
#         print("#include %s" % header)


# def output_interface(header_path):
#     # ヘッダーファイルの中身をすべて文字列リストとして読み込む
#     with open(header_path, "r") as f:
#         header_lines = f.readlines()

#     dir_path = os.path.dirname(header_path)
#     dir_path = dir_path.replace("\\", "/")
#     dir_path = dir_path.replace("C:/MMD/mlib_go/pkg/mbt", "")
#     if dir_path.startswith("/"):
#         dir_path = dir_path[1:]
#     header_file_name = os.path.basename(header_path)

#     output_path = f"{header_path}"

#     with open(output_path, "w") as of:
#         of.write("////// %s/%s ----------------\n\n" % (dir_path, header_file_name))

#         of.write('"')
#         of.write('%s/%s"\n\n' % (dir_path, header_file_name))

#         of.write("%{\n\n")

#         for header_line in header_lines:
#             if "#include " in header_line:
#                 # includeのパスを再設定する
#                 includes = header_line.split()
#                 if len(includes) >= 2:
#                     if "<" in includes[1]:
#                         if includes[1] not in primitive_headers:
#                             primitive_headers.append(includes[1])
#                     else:
#                         include_file = includes[1].replace('"', "")
#                         include_dir_path = os.path.dirname(include_file)
#                         if not include_dir_path:
#                             include_dir_path = dir_path
#                         include_file_name = os.path.basename(include_file)
#                         of.write(
#                             # '#include "bullet/src/%s/%s"\n'
#                             '#include "%s/%s"\n'
#                             % (include_dir_path, include_file_name)
#                         )
#                         print(
#                             '---- #include "%s" -> "%s/%s"'
#                             % (header_line.strip(), include_dir_path, include_file_name)
#                         )

#             elif "#include " not in header_line:
#                 of.write(header_line)

#         of.write("\n\n%}\n")

#     return None


# if __name__ == "__main__":

#     for root_dir_name in ["LinearMath", "BulletCollision", "BulletDynamics"]:
#         for header_path in glob(
#             f"C:/MMD/mlib_go/pkg/mbt/{root_dir_name}/**/*.*", recursive=True
#         ):
#             if header_path.endswith(".h") or header_path.endswith(".cpp"):
#                 output_interface(header_path)

#     for header in primitive_headers:
#         print("#include %s" % header)

exclude_header_list = [
    "LinearMath/btScalar.h",
    "LinearMath/btMinMax.h",
    "LinearMath/btAlignedAllocator.h",
    "LinearMath/btAlignedAllocator.cpp",
    "LinearMath/btVector3.h",
    "LinearMath/btVector3.h",
    "LinearMath/btQuadWord.h",
    "LinearMath/btQuaternion.h",
    "LinearMath/btMatrix3x3.h",
    "LinearMath/btTransform.h",
    "LinearMath/btMotionState.h",
    "LinearMath/btDefaultMotionState.h",
    "BulletCollision/BroadphaseCollision/btBroadphaseProxy.h",
    "BulletCollision/CollisionShapes/btCollisionShape.h",
    "BulletCollision/CollisionShapes/btCollisionShape.cpp",
    "BulletCollision/CollisionShapes/btCollisionMargin.h",
    "BulletCollision/CollisionShapes/btConvexShape.h",
    "BulletCollision/CollisionShapes/btConvexShape.cpp",
    "LinearMath/btAabbUtil2.h",
    "BulletCollision/CollisionShapes/btConvexInternalShape.h",
    "BulletCollision/CollisionShapes/btConvexInternalShape.cpp",
    "BulletCollision/CollisionShapes/btSphereShape.h",
    "BulletCollision/CollisionShapes/btSphereShape.cpp",
    "BulletCollision/CollisionShapes/btPolyhedralConvexShape.h",
    "LinearMath/btAlignedObjectArray.h",
    "BulletCollision/CollisionShapes/btConvexPolyhedron.h",
    "BulletCollision/CollisionShapes/btConvexPolyhedron.cpp",
    "LinearMath/btConvexHullComputer.h",
    "LinearMath/btConvexHullComputer.cpp",
    "LinearMath/btGeometryUtil.h",
    "LinearMath/btGeometryUtil.cpp",
    "LinearMath/btGrahamScan2dConvexHull.h",
    "BulletCollision/CollisionShapes/btPolyhedralConvexShape.cpp",
    "BulletCollision/CollisionShapes/btBoxShape.h",
    "BulletCollision/CollisionShapes/btBoxShape.cpp",
    "BulletCollision/CollisionShapes/btCapsuleShape.h",
    "BulletCollision/CollisionShapes/btCapsuleShape.cpp",
    "BulletCollision/CollisionDispatch/btCollisionObject.h",
    "BulletCollision/CollisionDispatch/btCollisionObject.cpp",
    "BulletDynamics/Dynamics/btRigidBody.h",
    "LinearMath/btTransformUtil.h",
    "BulletDynamics/ConstraintSolver/btJacobianEntry.h",
    "BulletDynamics/ConstraintSolver/btSolverBody.h",
    "BulletDynamics/ConstraintSolver/btSolverConstraint.h",
    "BulletDynamics/ConstraintSolver/btTypedConstraint.h",
    "BulletDynamics/ConstraintSolver/btTypedConstraint.cpp",
    "LinearMath/btHashMap.h",
    "LinearMath/btSerializer.h",
    "LinearMath/btSerializer.cpp",
    "LinearMath/btSerializer64.cpp",
    "BulletDynamics/Dynamics/btRigidBody.cpp",
    "BulletCollision/BroadphaseCollision/btDbvt.h",
    "BulletCollision/BroadphaseCollision/btDbvt.cpp",
    "BulletCollision/BroadphaseCollision/btBroadphaseInterface.h",
    "BulletCollision/BroadphaseCollision/btOverlappingPairCallback.h",
    "BulletCollision/BroadphaseCollision/btOverlappingPairCache.h",
    "BulletCollision/BroadphaseCollision/btOverlappingPairCache.cpp",
    "BulletCollision/BroadphaseCollision/btDbvtBroadphase.h",
    "LinearMath/btThreads.h",
    "LinearMath/btThreads.cpp",
    "BulletCollision/BroadphaseCollision/btDbvtBroadphase.cpp",
    "BulletCollision/BroadphaseCollision/btDispatcher.h",
    "BulletCollision/BroadphaseCollision/btDispatcher.cpp",
    "BulletCollision/NarrowPhaseCollision/btManifoldPoint.h",
    "BulletCollision/NarrowPhaseCollision/btPersistentManifold.h",
    "BulletCollision/NarrowPhaseCollision/btPersistentManifold.cpp",
    "BulletCollision/NarrowPhaseCollision/btDiscreteCollisionDetectorInterface.h",
    "BulletCollision/CollisionDispatch/btCollisionObjectWrapper.h",
    "BulletCollision/CollisionDispatch/btManifoldResult.h",
    "BulletCollision/CollisionDispatch/btManifoldResult.cpp",
    "BulletCollision/CollisionDispatch/btCollisionCreateFunc.h",
    "BulletCollision/CollisionDispatch/btCollisionDispatcher.h",
    "BulletCollision/CollisionDispatch/btCollisionDispatcher.cpp",
    "BulletCollision/CollisionDispatch/btCollisionWorld.h",
    "BulletCollision/NarrowPhaseCollision/btVoronoiSimplexSolver.h",
    "BulletCollision/NarrowPhaseCollision/btSimplexSolverInterface.h",
    "BulletCollision/NarrowPhaseCollision/btGjkEpaPenetrationDepthSolver.h",
    "BulletCollision/CollisionShapes/btTriangleCallback.h",
    "BulletCollision/CollisionShapes/btConcaveShape.h",
    "BulletCollision/CollisionShapes/btStridingMeshInterface.h",
    "BulletCollision/CollisionShapes/btTriangleMeshShape.h",
    "BulletCollision/BroadphaseCollision/btQuantizedBvh.h",
    "BulletCollision/CollisionShapes/btOptimizedBvh.h",
    "BulletCollision/CollisionShapes/btTriangleInfoMap.h",
    "BulletCollision/CollisionShapes/btBvhTriangleMeshShape.h",
    "BulletCollision/CollisionShapes/btHeightfieldTerrainShape.h",
    "BulletCollision/NarrowPhaseCollision/btRaycastCallback.h",
    "LinearMath/btIDebugDraw.h",
    "BulletCollision/NarrowPhaseCollision/btConvexCast.h",
    "BulletCollision/NarrowPhaseCollision/btSubSimplexConvexCast.h",
    "BulletCollision/NarrowPhaseCollision/btGjkConvexCast.h",
    "BulletCollision/NarrowPhaseCollision/btGjkConvexCast.cpp",
    "BulletCollision/NarrowPhaseCollision/btContinuousConvexCollision.h",
    "BulletCollision/CollisionDispatch/btCollisionWorld.cpp",
    "BulletDynamics/ConstraintSolver/btContactSolverInfo.h",
    "BulletDynamics/Dynamics/btDynamicsWorld.h",
    "BulletDynamics/Dynamics/btDiscreteDynamicsWorld.h",
    "BulletCollision/CollisionDispatch/btUnionFind.h",
    "BulletCollision/CollisionDispatch/btSimulationIslandManager.h",
    "BulletDynamics/ConstraintSolver/btConstraintSolver.h",
    "BulletDynamics/ConstraintSolver/btSequentialImpulseConstraintSolver.h",
    "BulletDynamics/ConstraintSolver/btSequentialImpulseConstraintSolver.cpp",
    "BulletDynamics/ConstraintSolver/btConeTwistConstraint.h",
    "BulletDynamics/ConstraintSolver/btGeneric6DofConstraint.h",
    "BulletDynamics/Dynamics/btDiscreteDynamicsWorld.cpp",
    "BulletCollision/CollisionShapes/btTriangleCallback.cpp",
    "BulletCollision/NarrowPhaseCollision/btRaycastCallback.cpp",
    "BulletDynamics/ConstraintSolver/btGeneric6DofConstraint.cpp",
    "BulletDynamics/ConstraintSolver/btConeTwistConstraint.cpp",
    "BulletCollision/CollisionDispatch/btUnionFind.cpp",
    "BulletCollision/CollisionDispatch/btSimulationIslandManager.cpp",
    "BulletCollision/NarrowPhaseCollision/btConvexCast.cpp",
    "BulletCollision/NarrowPhaseCollision/btVoronoiSimplexSolver.cpp",
    "BulletCollision/NarrowPhaseCollision/btGjkPairDetector.h",
    "BulletCollision/NarrowPhaseCollision/btContinuousConvexCollision.cpp",
    "BulletCollision/CollisionShapes/btConcaveShape.cpp",
    "BulletCollision/CollisionShapes/btTriangleMeshShape.cpp",
    "BulletCollision/BroadphaseCollision/btQuantizedBvh.cpp",
    "BulletCollision/CollisionShapes/btOptimizedBvh.cpp",
    "BulletCollision/CollisionShapes/btBvhTriangleMeshShape.cpp",
    "BulletCollision/NarrowPhaseCollision/btGjkPairDetector.cpp",
    "BulletCollision/NarrowPhaseCollision/btSubSimplexConvexCast.cpp",
    "BulletCollision/CollisionShapes/btStridingMeshInterface.cpp",
    "BulletCollision/CollisionShapes/btHeightfieldTerrainShape.cpp",
    "BulletCollision/NarrowPhaseCollision/btGjkEpa2.h",
    "BulletCollision/NarrowPhaseCollision/btGjkEpaPenetrationDepthSolver.cpp",
    "BulletCollision/NarrowPhaseCollision/btGjkEpa2.cpp",
    "BulletCollision/BroadphaseCollision/btBroadphaseProxy.cpp",
    "BulletCollision/CollisionDispatch/btCollisionConfiguration.h",
    "BulletCollision/CollisionDispatch/btDefaultCollisionConfiguration.h",
    "BulletCollision/BroadphaseCollision/btCollisionAlgorithm.h",
    "BulletCollision/BroadphaseCollision/btCollisionAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btActivatingCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btActivatingCollisionAlgorithm.cpp",
    "BulletCollision/NarrowPhaseCollision/btPolyhedralContactClipping.h",
    "BulletCollision/NarrowPhaseCollision/btPolyhedralContactClipping.cpp",
    "BulletCollision/CollisionDispatch/btConvexConvexAlgorithm.h",
    "BulletCollision/CollisionDispatch/btConvexConvexAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btEmptyCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btEmptyCollisionAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btConvexConcaveCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btConvexConcaveCollisionAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btCompoundCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btCompoundCollisionAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btHashedSimplePairCache.h",
    "BulletCollision/CollisionDispatch/btHashedSimplePairCache.cpp",
    "BulletCollision/CollisionDispatch/btCompoundCompoundCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btCompoundCompoundCollisionAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btConvexPlaneCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btConvexPlaneCollisionAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btBoxBoxCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btBoxBoxCollisionAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btSphereSphereCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btSphereSphereCollisionAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btSphereBoxCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btSphereBoxCollisionAlgorithm.cpp",
    "BulletCollision/CollisionDispatch/btSphereTriangleCollisionAlgorithm.h",
    "BulletCollision/CollisionDispatch/btSphereTriangleCollisionAlgorithm.cpp",
    "BulletCollision/NarrowPhaseCollision/btConvexPenetrationDepthSolver.h",
    "BulletCollision/NarrowPhaseCollision/btMinkowskiPenetrationDepthSolver.h",
    "BulletCollision/NarrowPhaseCollision/btMinkowskiPenetrationDepthSolver.cpp",
    "LinearMath/btPoolAllocator.h",
    "BulletCollision/CollisionDispatch/btDefaultCollisionConfiguration.cpp",
    "BulletCollision/CollisionShapes/btMiniSDF.h",
    "BulletCollision/CollisionShapes/btMiniSDF.cpp",
    "BulletCollision/CollisionDispatch/btBoxBoxDetector.h",
    "BulletCollision/CollisionDispatch/btBoxBoxDetector.cpp",
    "BulletCollision/CollisionShapes/btSdfCollisionShape.h",
    "BulletCollision/CollisionShapes/btSdfCollisionShape.cpp",
    "BulletCollision/CollisionDispatch/SphereTriangleDetector.h",
    "BulletCollision/CollisionDispatch/SphereTriangleDetector.cpp",
    "BulletCollision/CollisionShapes/btStaticPlaneShape.h",
    "BulletCollision/CollisionShapes/btStaticPlaneShape.cpp",
]


tail_header_list = [
    "DDSTextureLoader/DDSTextureLoader12.h",
    "DDSTextureLoader/DDSTextureLoader12.cpp",
    "WICTextureLoader/WICTextureLoader12.h",
    "WICTextureLoader/WICTextureLoader12.cpp",
    # "BulletDynamics/ConstraintSolver/btGeneric6DofSpringConstraint.h",
    # "BulletDynamics/ConstraintSolver/btGeneric6DofSpringConstraint.cpp",
    # "BulletCollision/CollisionDispatch/btDefaultCollisionConfiguration.h",
    # "BulletCollision/CollisionDispatch/btDefaultCollisionConfiguration.cpp",
    # "BulletCollision/CollisionDispatch/btEmptyCollisionAlgorithm.h",
    # "BulletCollision/CollisionDispatch/btBoxBoxDetector.h",
    # "BulletCollision/CollisionShapes/btSdfCollisionShape.h",
    # "BulletCollision/CollisionDispatch/SphereTriangleDetector.h",
    # "BulletCollision/CollisionShapes/btSphereShape.h",
    # "BulletCollision/CollisionShapes/btPolyhedralConvexShape.h",
    # "BulletCollision/CollisionShapes/btPolyhedralConvexShape.cpp",
    # "BulletCollision/CollisionShapes/btBoxShape.h",
    # "BulletCollision/CollisionShapes/btBoxShape.cpp",
    # "BulletCollision/CollisionShapes/btCapsuleShape.h",
    # "BulletDynamics/Dynamics/btRigidBody.h",
    # "BulletDynamics/Dynamics/btRigidBody.cpp",
    # "BulletCollision/BroadphaseCollision/btDbvtBroadphase.h",
    # "BulletCollision/BroadphaseCollision/btDbvtBroadphase.cpp",
    # "BulletDynamics/Dynamics/btDiscreteDynamicsWorld.h",
    # "BulletDynamics/Dynamics/btDiscreteDynamicsWorld.cpp",
    # "BulletCollision/BroadphaseCollision/btDispatcher.h",
    # "BulletCollision/BroadphaseCollision/btDispatcher.cpp",
    # "BulletCollision/NarrowPhaseCollision/btManifoldPoint.h",
    # "BulletCollision/NarrowPhaseCollision/btPersistentManifold.h",
    # "BulletCollision/NarrowPhaseCollision/btPersistentManifold.cpp",
    # "BulletCollision/NarrowPhaseCollision/btDiscreteCollisionDetectorInterface.h",
    # "BulletCollision/CollisionDispatch/btCollisionObjectWrapper.h",
    # "BulletCollision/CollisionDispatch/btManifoldResult.h",
    # "BulletCollision/CollisionDispatch/btManifoldResult.cpp",
    # "BulletCollision/CollisionDispatch/btCollisionCreateFunc.h",
    # "BulletCollision/CollisionDispatch/btCollisionDispatcher.h",
    # "BulletCollision/CollisionDispatch/btCollisionDispatcher.cpp",
    # "BulletCollision/BroadphaseCollision/btBroadphaseInterface.h",
    # "BulletCollision/BroadphaseCollision/btOverlappingPairCallback.h",
    # "BulletCollision/BroadphaseCollision/btOverlappingPairCache.h",
    # "BulletCollision/BroadphaseCollision/btOverlappingPairCache.cpp",
    # "BulletCollision/CollisionDispatch/btCollisionWorld.h",
    # "BulletCollision/CollisionDispatch/btCollisionWorld.cpp",
    # "BulletDynamics/ConstraintSolver/btContactSolverInfo.h",
    # "BulletDynamics/Dynamics/btDynamicsWorld.h",
    # "LinearMath/btThreads.h",
    # "LinearMath/btThreads.cpp",
    # "BulletDynamics/Dynamics/btDiscreteDynamicsWorld.h",
    # "BulletDynamics/Dynamics/btDiscreteDynamicsWorld.cpp",
    # "BulletCollision/CollisionShapes/btTriangleCallback.h",
    # "BulletCollision/CollisionShapes/btTriangleCallback.cpp",
    # "BulletCollision/NarrowPhaseCollision/btRaycastCallback.h",
    # "BulletCollision/NarrowPhaseCollision/btRaycastCallback.cpp",
    # "BulletDynamics/ConstraintSolver/btGeneric6DofConstraint.h",
    # "BulletDynamics/ConstraintSolver/btGeneric6DofConstraint.cpp",
    # "BulletDynamics/ConstraintSolver/btConeTwistConstraint.h",
    # "BulletDynamics/ConstraintSolver/btConeTwistConstraint.cpp",
    # "BulletCollision/CollisionDispatch/btUnionFind.h",
    # "BulletCollision/CollisionDispatch/btUnionFind.cpp",
    # "BulletCollision/CollisionDispatch/btSimulationIslandManager.h",
    # "BulletCollision/CollisionDispatch/btSimulationIslandManager.cpp",
    # "BulletDynamics/ConstraintSolver/btConstraintSolver.h",
    # "BulletDynamics/ConstraintSolver/btSequentialImpulseConstraintSolver.h",
    # "BulletDynamics/ConstraintSolver/btSequentialImpulseConstraintSolver.cpp",
    # "LinearMath/btIDebugDraw.h",
    # "BulletCollision/NarrowPhaseCollision/btConvexCast.h",
    # "BulletCollision/NarrowPhaseCollision/btConvexCast.cpp",
    # "BulletCollision/NarrowPhaseCollision/btVoronoiSimplexSolver.h",
    # "BulletCollision/NarrowPhaseCollision/btVoronoiSimplexSolver.cpp",
    # "BulletCollision/NarrowPhaseCollision/btSimplexSolverInterface.h",
    # "BulletCollision/NarrowPhaseCollision/btContinuousConvexCollision.h",
    # "BulletCollision/NarrowPhaseCollision/btContinuousConvexCollision.cpp",
    # "BulletCollision/CollisionShapes/btConcaveShape.h",
    # "BulletCollision/CollisionShapes/btConcaveShape.cpp",
    # "BulletCollision/CollisionShapes/btStridingMeshInterface.h",
    # "BulletCollision/CollisionShapes/btTriangleMeshShape.h",
    # "BulletCollision/CollisionShapes/btTriangleMeshShape.cpp",
    # "BulletCollision/BroadphaseCollision/btQuantizedBvh.h",
    # "BulletCollision/BroadphaseCollision/btQuantizedBvh.cpp",
    # "BulletCollision/CollisionShapes/btOptimizedBvh.h",
    # "BulletCollision/CollisionShapes/btOptimizedBvh.cpp",
    # "BulletCollision/CollisionShapes/btTriangleInfoMap.h",
    # "BulletCollision/CollisionShapes/btBvhTriangleMeshShape.h",
    # "BulletCollision/CollisionShapes/btBvhTriangleMeshShape.cpp",
    # "BulletCollision/NarrowPhaseCollision/btGjkPairDetector.h",
    # "BulletCollision/NarrowPhaseCollision/btGjkPairDetector.cpp",
    # "BulletCollision/NarrowPhaseCollision/btSubSimplexConvexCast.h",
    # "BulletCollision/NarrowPhaseCollision/btSubSimplexConvexCast.cpp",
    # "BulletCollision/CollisionShapes/btStridingMeshInterface.h",
    # "BulletCollision/CollisionShapes/btStridingMeshInterface.cpp",
    # "BulletCollision/CollisionShapes/btHeightfieldTerrainShape.h",
    # "BulletCollision/CollisionShapes/btHeightfieldTerrainShape.cpp",
    # "BulletCollision/NarrowPhaseCollision/btGjkEpaPenetrationDepthSolver.h",
    # "BulletCollision/NarrowPhaseCollision/btGjkEpaPenetrationDepthSolver.cpp",
    # "BulletCollision/NarrowPhaseCollision/btGjkEpa2.h",
    # "BulletCollision/NarrowPhaseCollision/btGjkEpa2.cpp",
]


def find_tree_header(
    tail_header_path: str,
    included_headers: list[str] = [],
    primitive_headers: list[str] = [],
    depth=0,
) -> tuple[list[str], list[str]]:
    root_dir_path = "C:/MMD/DirectXTex"

    if depth > 50:
        return included_headers, primitive_headers

    if not os.path.exists(f"{root_dir_path}/{tail_header_path}"):
        print("×not found: %s" % tail_header_path)
        return included_headers, primitive_headers

    if tail_header_path in included_headers or tail_header_path in exclude_header_list:
        return included_headers, primitive_headers

    # ヘッダーファイルの中身をすべて文字列リストとして読み込む
    with open(f"{root_dir_path}/{tail_header_path}", "r") as f:
        header_lines = f.readlines()

    dir_path, file_name = os.path.split(tail_header_path)

    for header_line in header_lines:
        if "#include " in header_line:
            # include 文がある場合、その行のファイルを先に出力する
            includes = header_line.split()
            if len(includes) >= 2:
                if "<" in includes[1]:
                    if includes[1] not in primitive_headers:
                        primitive_headers.append(includes[1])
                else:
                    include_file = includes[1].replace('"', "")
                    include_dir_path = os.path.dirname(include_file)
                    if not include_dir_path:
                        include_file = f"{dir_path}/{include_file}"
                    find_tree_header(
                        include_file, included_headers, primitive_headers, depth + 1
                    )

    included_headers.append(tail_header_path)

    return included_headers, primitive_headers


if __name__ == "__main__":

    all_included_headers = []
    for tail_header_path in tail_header_list:
        included_headers, primitive_headers = find_tree_header(tail_header_path)

        for n in range(len(included_headers)):
            now_included_header = included_headers[n]

            if now_included_header in all_included_headers:
                continue

            if n > 0:
                prev_included_header = included_headers[n - 1]
            else:
                if not all_included_headers:
                    all_included_headers.append(now_included_header)
                    continue
                else:
                    prev_included_header = included_headers[n]

            try:
                prev_index = all_included_headers.index(prev_included_header)
                all_included_headers.insert(prev_index + 1, now_included_header)
            except ValueError:
                # prev が見つからない場合、nowを最初に入れる
                all_included_headers.insert(0, now_included_header)

    for header in all_included_headers:
        print(f'%include "{header}.i"')
