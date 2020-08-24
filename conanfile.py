# Intel TBB Conan package
# Dmitriy Vetutnev, Odant, 2018


from conans import ConanFile, tools
from conans.errors import ConanException
import os, glob


def get_safe(options, name):
    try:
        return getattr(options, name, None)
    except ConanException:
        return None


class TBBConan(ConanFile):
    name = "tbb"
    version = "2020.3+0"
    license = "Apache License 2.0 - https://www.threadingbuildingblocks.org/faq/10"
    description = "Intel(R) Threading Building Blocks (Intel(R) TBB) lets you easily write parallel C++ programs that take full advantage of multicore performance, that are portable, composable and have future-proof scalability."
    url = "https://github.com/odant/conan-tbb"
    settings = {
        "os": ["Windows", "Linux"],
        "compiler": ["Visual Studio", "gcc"],
        "build_type": ["Debug", "Release"],
        "arch": ["x86_64", "x86", "mips", "armv7"]
    }
    options = {
        "dll_sign": [False, True],
        "built_in_tests": [False, True]
    }
    default_options = "dll_sign=True", "built_in_tests=False"
    exports_sources = "src/*", \
                      "Makefile.patch", \
                      "windows.tbb_output_name.patch", \
                      "linux.tbb_output_name.patch", \
                      "fixup-mips-harness.patch", \
                      "test_parallel_for-two-core.patch", \
                      "test_task_scheduler_init-two-core.patch", \
                      "FindTBB.cmake"
    no_copy_source = True
    build_policy = "missing"
    
    def configure(self):
        # Only C++11
        if self.settings.compiler.get_safe("libcxx") == "libstdc++":
            raise ConanException("This package is only compatible with libstdc++11")
        # DLL sign, only Windows
        if self.settings.os != "Windows" or self.options.built_in_tests:
            del self.options.dll_sign

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.build_requires("gnu_make_installer/[~=4.2.1]@%s/stable" % self.user)
            toolset = str(self.settings.compiler.get_safe("toolset"))
            if toolset.endswith("_xp"):
                self.build_requires("find_sdk_winxp/[~=1.0]@%s/stable" % self.user)
        if get_safe(self.options, "dll_sign"):
            self.build_requires("windows_signtool/[~=1.1]@%s/stable" % self.user)

    def source(self):
        tools.patch(patch_file="Makefile.patch")
        tools.patch(patch_file="windows.tbb_output_name.patch")
        tools.patch(patch_file="linux.tbb_output_name.patch")
        tools.patch(patch_file="fixup-mips-harness.patch")
        tools.patch(patch_file="test_parallel_for-two-core.patch")
        tools.patch(patch_file="test_task_scheduler_init-two-core.patch")

    def build(self):
        output_name = "tbb"
        if self.settings.os == "Windows":
            if self.settings.build_type == "Debug":
                output_name += "d"
        #
        source_folder = os.path.join(self.source_folder, "src")
        #
        flags = ["-DTBB_NO_LEGACY=1"]
        if self.settings.arch == "mips":
            flags += [
                "-D__TBB_64BIT_ATOMICS=0"
            ]
        build_args = [
            "CXXFLAGS=\"%s\"" % " ".join(flags),
            "tbb_output_name=%s" % output_name,
            "build_type=%s" % str(self.settings.build_type).lower(),
            "arch=%s" % {
                        "x86": "ia32",
                        "x86_64": "intel64",
                        "mips": "mips",
                        "armv7": "arm"
                    }.get(str(self.settings.arch)),
            "tbb_root=%s" % source_folder,
            "tbb_build_dir=%s" % self.build_folder
        ]
        target = "tbb"
        #
        if self.options.built_in_tests:
            build_args.insert(0, "NO_LEGACY_TESTS=1")
            target = "test"
        #
        build_env = self.get_build_environment()
        with tools.environment_append(build_env):
            self.output.info("Current directory: %s" % os.getcwd())
            self.run("make -f %s %s %s -j%s" % (os.path.join(source_folder, "Makefile"), " ".join(build_args), target, tools.cpu_count()))

    def get_build_environment(self):
        env = {}
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            env = tools.vcvars_dict(self.settings, filter_known_paths=False)
            toolset = str(self.settings.compiler.get_safe("toolset"))
            if toolset.endswith("_xp"):
                import find_sdk_winxp
                env = find_sdk_winxp.dict_append(self.settings.arch, env=env)
        return env

    def package(self):
        # Don`t pack if testing
        if self.options.built_in_tests:
            return
        self.copy("FindTBB.cmake", src=".", dst=".")
        self.copy("*.h", src="src/include", dst="include", keep_path=True)
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so.*", dst="lib", keep_path=False, symlinks=True)
        self.copy("*.a", dst="lib", keep_path=False)
        self.copy("*tbb*.pdb", dst="bin", keep_path=False)
        # Symlink
        if self.settings.os == "Linux":
            lib_folder = os.path.join(self.package_folder, "lib")
            if not os.path.isdir(lib_folder):
                return
            with tools.chdir(lib_folder):
                for fname in os.listdir("."):
                    extension = ".so"
                    symlink = fname[0:fname.rfind(extension) + len(extension)]
                    self.run("ln -s \"%s\" \"%s\"" % (fname, symlink))
        # Sign DLL
        if get_safe(self.options, "dll_sign"):
            import windows_signtool
            pattern = os.path.join(self.package_folder, "bin", "*.dll")
            for fpath in glob.glob(pattern):
                fpath = fpath.replace("\\", "/")
                for alg in ["sha1", "sha256"]:
                    is_timestamp = True if self.settings.build_type == "Release" else False
                    cmd = windows_signtool.get_sign_command(fpath, digest_algorithm=alg, timestamp=is_timestamp)
                    self.output.info("Sign %s" % fpath)
                    self.run(cmd)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        # Disable auto link
        if self.settings.os == "Windows":
            self.cpp_info.defines.append("__TBB_NO_IMPLICIT_LINKAGE=1")
