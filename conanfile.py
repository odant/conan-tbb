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
    version = "2018.2"
    license = "Apache License 2.0 - https://www.threadingbuildingblocks.org/faq/10"
    description = "Intel(R) Threading Building Blocks (Intel(R) TBB) lets you easily write parallel C++ programs that take full advantage of multicore performance, that are portable, composable and have future-proof scalability."
    url = "https://github.com/odant/conan-tbb"
    settings = {
        "os": ["Windows", "Linux"],
        "compiler": ["Visual Studio", "gcc"],
        "build_type": ["Debug", "Release"],
        "arch": ["x86_64", "x86"]
    }
    options = {
        "dll_sign": [False, True]
    }
    default_options = "dll_sign=True"
    exports_sources = "src/*", "Makefile.patch", "windows.tbb_output_name.patch", "linux.tbb_output_name.patch", "FindTBB.cmake"
    no_copy_source = True
    build_policy = "missing"
    
    def configure(self):
        # Only C++11
        if self.settings.compiler.get_safe("libcxx") == "libstdc++":
            raise ConanException("This package is only compatible with libstdc++11")
        # DLL sign, only Windows
        if self.settings.os != "Windows":
            del self.options.dll_sign

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.build_requires("find_sdk_winxp/1.0@%s/stable" % self.user)
            self.build_requires("gnu_make_installer/4.2.1@%s/stable" % self.user)
        if get_safe(self.options, "dll_sign"):
            self.build_requires("windows_signtool/[~=1.0]@%s/stable" % self.user)

    def source(self):
        tools.patch(patch_file="Makefile.patch")
        tools.patch(patch_file="windows.tbb_output_name.patch")
        tools.patch(patch_file="linux.tbb_output_name.patch")

    def build(self):
        output_name = "tbb"
        if self.settings.os == "Windows":
            output_name += {
                            "x86": "32",
                            "x86_64": "64"
                        }.get(str(self.settings.arch))
            if self.settings.build_type == "Debug":
                output_name += "d"
        #
        build_env = self.get_build_environment()
        source_folder = os.path.join(self.source_folder, "src")
        build_args = [
            "SDL_FLAGS=-DTBB_NO_LEGACY",
            "tbb_output_name=%s" % output_name,
            "build_type=%s" % str(self.settings.build_type).lower(),
            "arch=%s" % {
                        "x86": "ia32",
                        "x86_64": "intel64"
                    }.get(str(self.settings.arch)),
            "tbb_root=%s" % source_folder,
            "tbb_build_dir=%s" % self.build_folder
        ]
        with tools.environment_append(build_env):
            self.output.info("Current directory: %s" % os.getcwd())
            self.run("make -f %s tbb %s -j%s" % (os.path.join(source_folder, "Makefile"), " ".join(build_args), tools.cpu_count()))

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

