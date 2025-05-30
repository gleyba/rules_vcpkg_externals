import os
import shutil
import argparse

def postprocess_autoconf(directories, scripts):
    for dst, src in directories.items():
        if not os.listdir(src):
            continue

        shutil.copytree(src, dst, dirs_exist_ok=True)

    build_tmpdir_str = "autoconf.build_tmpdir/autoconf"

    for dst, src in scripts.items():
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        # # Read the content of the source file
        with open(src, 'r') as file:
            content = []

            is_sh = False

            is_perl = False
            use_line_idx = None

            has_build_dir_usage = False
            need_file_basename = True
            need_abs_path = True
            
            for line_idx, line in enumerate(file.readlines()):
                if line_idx == 0:
                    if line.startswith("#! /bin/sh\n"):
                        is_sh = True
                        line = "#!/usr/bin/env sh\n"
                    elif line.startswith("#! /usr/bin/perl"):
                        is_perl = True
                        line = "#!/usr/bin/env perl\n"
                    else:
                        raise Exception("Unknown file type: %s" % src)
                else:
                    if is_perl and line.startswith("use "):
                        if use_line_idx == None:
                            use_line_idx = line_idx
                        
                        if line == "use File::Basename;\n":
                            need_file_basename = False
                        elif line == "use Cwd qw(abs_path);\n":
                            need_abs_path = False

                    build_dir_pos = line.find(build_tmpdir_str)
                    if build_dir_pos != -1:
                        root_start_pos = line.find("'/private")
                        if root_start_pos == -1:
                            raise Exception("Can't postprocess line: %s" % line)
                        if is_sh:
                            line = "".join([
                                line[:root_start_pos],
                                "$(dirname \"$(readlink -f \"$0\")\")'/..",
                                line[build_dir_pos + len(build_tmpdir_str):],
                            ])
                        elif is_perl:
                            has_build_dir_usage = True
                            next_apostrofe_pos = line.find("'", build_dir_pos)
                            if next_apostrofe_pos == -1:
                               raise Exception("Can't postprocess line: %s" % line)

                            line = "".join([
                                line[:root_start_pos],
                                "(abs_path(dirname(__FILE__) . \"/..\") . '",
                                line[build_dir_pos + len(build_tmpdir_str):next_apostrofe_pos + 1],
                                ")",
                                line[next_apostrofe_pos + 1:],
                            ])

                content.append(line)

            if has_build_dir_usage:
                if use_line_idx == None:
                    raise Exception("Can't find line idx for use injection file: %s" % src)

                if need_file_basename:
                    content.insert(use_line_idx, "use File::Basename;\n")

                if need_abs_path:
                    content.insert(use_line_idx, "use Cwd qw(abs_path);\n")

            with open(dst, 'w') as out_file:
                out_file.writelines(content)

def main():
    parser = argparse.ArgumentParser(description="Post-process autoconf output.")

    parser.add_argument(
        "--dir", 
        action="append",
        help="Directories to copy.",
    )
    parser.add_argument(
        "--script",
        action="append",
        help="Scripts to postprocess.",
    )
    arg = parser.parse_args()

    def to_dict(arg_list):
        return {
            k: v
            for k, v in 
            (x.split('=') for x in arg_list)
        }

    postprocess_autoconf(to_dict(arg.dir), to_dict(arg.script))

if __name__ == "__main__":
    main()
