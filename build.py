# Build Conan package
# Dmitriy Vetutnev, ODANT, 2020


from cpt.packager import ConanMultiPackager


if __name__ == "__main__":
    builder = ConanMultiPackager(
        exclude_vcvars_precommand=True
    )
    builder.add_common_builds()
    builder.remove_build_if(
        lambda build: build.settings.get("compiler.libcxx") == "libstdc++"
    )
    builder.run()
