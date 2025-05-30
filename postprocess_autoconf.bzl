
def _postprocess_autoconf_impl(ctx):
    """Postprocess autoconf files."""
    args = ctx.actions.args()

    outputs = []

    scripts = set(ctx.attr.scripts)
    for src in ctx.files.srcs:
        if src.is_directory:
            out = ctx.actions.declare_directory("%s/%s" %(
                ctx.attr.prefix, 
                src.basename,
            ))
            args.add("--dir", "%s=%s" % (
                out.path,
                src.path,
            ))
            outputs.append(out)
        elif src.basename in scripts:
            out = ctx.actions.declare_file("%s/bin/%s" %(
                ctx.attr.prefix, 
                src.basename,
            ))
            args.add("--script", "%s=%s" % (
                out.path,
                src.path,
            ))
            outputs.append(out)
        else:
            fail("Unknown script: {}".format(src.basename))

    ctx.actions.run(
        inputs = ctx.files.srcs,
        outputs = outputs,
        executable = ctx.executable._binary,
        arguments = [args],
    )

    return [DefaultInfo(files = depset(outputs))]

postprocess_autoconf = rule(
    implementation = _postprocess_autoconf_impl,
    attrs = {
        "srcs": attr.label(
            allow_files = True,
            doc = "The source files for autoconf.",
        ),
        "prefix": attr.string(
            mandatory = True,
            doc = "Output directory prefix.",
        ),
        "scripts": attr.string_list(
            mandatory = True,
            doc = "List of scripts to postprocess.",
        ),
        "_binary": attr.label(
            executable = True,
            default = "//:postprocess_autoconf_bin",
            cfg = "exec",
            doc = "Postprocessing script",
        ),
    },
)

select_binary = rule(
    implementation = lambda ctx: DefaultInfo(
        files = depset([
            src for src 
            in ctx.files.srcs
            if src.path.endswith(ctx.attr.postfix)
        ]),
    ),
    attrs = {
        "postfix": attr.string(
            mandatory = True,
            doc = "Postfix to filter srcs with.",
        ),
        "srcs": attr.label(
            allow_files = True,
            mandatory = True,
            doc = "The source files to filter.",
        ),
    },
)
