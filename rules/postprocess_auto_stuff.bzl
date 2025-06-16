def _postprocess_auto_stuff_impl(ctx):
    """Postprocess autoconf files."""
    args = ctx.actions.args()

    for postfix, binary in ctx.attr.bin_postfixes.items():
        args.add("--bin-postfix", "%s|%s" % (postfix, binary))

    for key, value in ctx.attr.replace_in_bin.items():
        args.add("--replace-in-bin", "%s|%s" % (key, value))

    output = ctx.actions.declare_directory(ctx.attr.output)

    for src in ctx.files.srcs:
        if src.is_directory:
            args.add("--dir", "%s/%s|%s" % (
                output.path,
                src.basename,
                src.path,
            ))
        else:
            args.add("--script", "%s/bin/%s|%s" % (
                output.path,
                src.basename,
                src.path,
            ))

    ctx.actions.run(
        inputs = ctx.files.srcs,
        outputs = [output],
        executable = ctx.executable._binary,
        arguments = [args],
    )

    return [DefaultInfo(files = depset([output]))]

postprocess_auto_stuff = rule(
    implementation = _postprocess_auto_stuff_impl,
    attrs = {
        "bin_postfixes": attr.string_dict(
            doc = "Binaries postfixes to search and replace with relative paths.",
        ),
        "replace_in_bin": attr.string_dict(
            doc = "Dict of key values to search and replace in binaries.",
        ),
        "srcs": attr.label(
            allow_files = True,
            doc = "The source files for autoconf.",
        ),
        "output": attr.string(
            mandatory = True,
            doc = "Output directory.",
        ),
        "_binary": attr.label(
            executable = True,
            default = ":postprocess_auto_stuff_bin",
            cfg = "exec",
            doc = "Postprocessing script",
        ),
    },
)
