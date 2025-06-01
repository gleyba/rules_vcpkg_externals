import os
import shutil
import argparse

def postprocess_search_prefixes(line, search_prefixes, is_sh, is_perl):
    changed = False
    for search_prefix, addition in search_prefixes.items():
        build_dir_pos = line.find(search_prefix)
        if build_dir_pos == -1:
            continue

        changed = True
        root_start_pos = line.find("'/private")
        if root_start_pos == -1:
            raise Exception("Can't postprocess line: %s" % line)

        if is_sh:
            line = "".join([
                line[:root_start_pos],
                "$(dirname \"$(readlink -f \"$0\")\")'/..",
                addition,
                line[build_dir_pos + len(search_prefix):],
            ])
        elif is_perl:
            next_apostrofe_pos = line.find("'", build_dir_pos)
            if next_apostrofe_pos == -1:
                raise Exception("Can't postprocess line: %s" % line)

            line = "".join([
                line[:root_start_pos],
                "(abs_path(dirname(abs_path(__FILE__)) . \"/..",
                addition,
                "\") . '",
                line[build_dir_pos + len(search_prefix):next_apostrofe_pos + 1],
                ")",
                line[next_apostrofe_pos + 1:],
            ])

    return line, changed

def postprocess_auto_stuff(prefix, bin_postfixes, directories, scripts):
    for dst, src in directories.items():
        if not os.listdir(src):
            continue

        shutil.copytree(src, dst, dirs_exist_ok=True)

    build_tmpdir_str = "{prefix}.build_tmpdir/{prefix}".format(prefix=prefix)

    search_prefixes = {
        build_tmpdir_str: "",
    } | bin_postfixes

    for dst, src in scripts.items():
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        # # Read the content of the source file
        with open(src, 'r') as file:
            content = []

            is_sh = False

            is_perl = False
            use_line_idx = None

            need_file_basename = False
            need_abs_path = False
            
            for line_idx, line in enumerate(file.readlines()):
                if line_idx == 0:
                    if line.startswith("#! /bin/sh\n") or line.startswith("#!/bin/sh\n"):
                        is_sh = True
                        line = "#!/usr/bin/env sh\n"
                    elif line.startswith("#! /usr/bin/perl") or line.startswith("#!/usr/bin/perl"):
                        is_perl = True
                        line = "#!/usr/bin/env perl\n"
                    else:
                        raise Exception("Unknown file type: %s" % src)
                elif "/usr/bin/" in line:
                    line = line.replace("/usr/bin/", "/usr/bin/env ")

                if is_perl and line.startswith("use "):
                    if use_line_idx == None:
                        use_line_idx = line_idx
                    
                    if line == "use File::Basename;\n":
                        need_file_basename = True
                        continue
                    elif line == "use Cwd qw(abs_path);\n":
                        need_abs_path = True
                        continue

                line, is_modified = postprocess_search_prefixes(
                    line, 
                    search_prefixes, 
                    is_sh, 
                    is_perl,
                )

                need_file_basename |= is_modified
                need_abs_path |= is_modified

                content.append(line)

            if is_perl and (need_file_basename or need_abs_path):
                if use_line_idx == None:
                    raise Exception("Can't find line idx for use injection file: %s" % src)
    
                if need_file_basename:
                    content.insert(use_line_idx, "use File::Basename;\n")
                if need_abs_path:
                    content.insert(use_line_idx, "use Cwd qw(abs_path);\n")

            with open(dst, 'w') as out_file:
                out_file.writelines(content)

def main():
    parser = argparse.ArgumentParser(description="Post-process auto* output.")

    parser.add_argument(
        "--prefix", 
        type=str,
        help="`build_tmpdir` prefix to search and replace with relative paths.",
    )
    parser.add_argument(
        "--bin-postfix", 
        action="append",
        help="Binaries postfixes to search and replace with relative paths.",
    )
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
        if not arg_list:
            return {}

        return {
            k: v
            for k, v in 
            (x.split('=') for x in arg_list)
        }

    postprocess_auto_stuff(
        arg.prefix,
        to_dict(arg.bin_postfix),
        to_dict(arg.dir),
        to_dict(arg.script),
    )

if __name__ == "__main__":
    main()
