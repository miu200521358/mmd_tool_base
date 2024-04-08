import os
from glob import glob

primitive_headers = []


def output_interface(header_path):
    # ヘッダーファイルの中身をすべて文字列リストとして読み込む
    with open(header_path, "r") as f:
        header_lines = f.readlines()

    dir_path = os.path.dirname(header_path)
    dir_path = dir_path.replace("\\", "/")
    dir_path = dir_path.replace("C:/MMD/mlib_go/pkg/mtex", "")
    if dir_path.startswith("/"):
        dir_path = dir_path[1:]
    header_file_name = os.path.basename(header_path)

    output_path = f"{header_path}.i"

    with open(output_path, "w") as of:
        of.write("////// %s/%s ----------------\n\n" % (dir_path, header_file_name))

        of.write("%include ")
        of.write('"%s/%s"\n\n' % (dir_path, header_file_name))

        of.write("%{\n")
        of.write("#include ")
        of.write('"%s/%s"' % (dir_path, header_file_name))
        of.write("\n%}\n")

        # of.write("%{\n\n")

        # for header_line in header_lines:
        #     if "#include " in header_line:
        #         # includeのパスを再設定する
        #         includes = header_line.split()
        #         if len(includes) >= 2:
        #             if "<" in includes[1]:
        #                 if includes[1] not in primitive_headers:
        #                     primitive_headers.append(includes[1])
        #                 of.write(header_line)
        #             else:
        #                 include_file = includes[1].replace('"', "")
        #                 include_dir_path = os.path.dirname(include_file)
        #                 if not include_dir_path:
        #                     include_dir_path = dir_path
        #                 include_file_name = os.path.basename(include_file)
        #                 # パスを書き直す
        #                 of.write(
        #                     # '#include "bullet/src/%s/%s"\n'
        #                     '#include "%s/%s"\n'
        #                     % (include_dir_path, include_file_name)
        #                 )
        #                 print(
        #                     '---- #include "%s" -> "%s/%s"'
        #                     % (header_line.strip(), include_dir_path, include_file_name)
        #                 )

        #     elif "#include " not in header_line:
        #         of.write(header_line)

        # of.write("\n\n%}\n")

    of.close()

    return None


if __name__ == "__main__":

    for root_dir_name in ["DDSTextureLoader", "WICTextureLoader"]:
        for header_path in glob(
            f"C:/MMD/mlib_go/pkg/mtex/{root_dir_name}/**/*.*", recursive=True
        ):
            if header_path.endswith(".h") or header_path.endswith(".cpp"):
                output_interface(header_path)

    for header in primitive_headers:
        print("#include %s" % header)
