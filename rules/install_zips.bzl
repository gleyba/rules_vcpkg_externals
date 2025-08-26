load("@bazel_skylib//lib:paths.bzl", "paths")

def _install_zips_impl(ctx):
    """Install zip files into the specified target directory."""
    output = ctx.actions.declare_file(ctx.label.name)

    ctx.actions.write(
        output = output,
        content = "\n".join([
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "mkdir -p $1",
        ] + [
            "install %s $1/%s.%s.zip" % (
                zip_file.basename,
                paths.replace_extension(zip_file.basename, ""),
                ctx.attr.file_postfix,
            )
            for zip_file in ctx.files.zips
        ]),
    )

    # Return the output file to indicate completion
    return DefaultInfo(
        executable = output,
        runfiles = ctx.runfiles(files = ctx.files.zips),
    )

install_zips = rule(
    implementation = _install_zips_impl,
    executable = True,
    attrs = {
        "zips": attr.label_list(
            mandatory = True,
            allow_files = True,
            doc = "List of zip files to install.",
        ),
        "file_postfix": attr.string(
            mandatory = True,
        ),
    },
)
