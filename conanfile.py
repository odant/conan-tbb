# Intel TBB Conan package
# Dmitriy Vetutnev, Odant, 2018

from conans import ConanFile, CMake, tools
from conans.errors import ConanException
import os, glob


def get_safe(options, name):
    try:
        return getattr(options, name, None)
    except ConanException:
        return None


class TBBConan(ConanFile):
    name = "tbb"
    version = "2021.1.1+0"
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
        "ninja": [False, True],
        "shared": [True, False],
        "built_in_tests": [False, True]
    }
    default_options = "dll_sign=True", "ninja=True", "shared=True", "built_in_tests=False"
    generators = "cmake"
    exports_sources = "src/*", "CMakeLists.txt", \
                      "test_global_control-two-core.patch", \
                      "FindTBB.cmake"
    no_copy_source = True
    build_policy = "missing"
    
    def configure(self):
        # Only C++11
        if self.settings.compiler.get_safe("libcxx") == "libstdc++":
            raise ConanException("This package is only compatible with libstdc++11")
        # MT(d) static library
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            if self.settings.compiler.runtime == "MT" or self.settings.compiler.runtime == "MTd":
                self.options.shared=False
        # DLL sign, only Windows
        if self.settings.os != "Windows" or self.options.built_in_tests:
            del self.options.dll_sign

    def build_requirements(self):
        if self.options.get_safe("ninja"):
            self.build_requires("ninja/1.10.1")
        if get_safe(self.options, "dll_sign"):
            self.build_requires("windows_signtool/[~=1.1]@%s/stable" % self.user)

    def source(self):
        tools.patch(patch_file="test_global_control-two-core.patch")

    def build(self):
        build_type = "RelWithDebInfo" if self.settings.build_type == "Release" else "Debug"
        generator = "Ninja" if self.options.ninja == True else None
        cmake = CMake(self, build_type=build_type, generator=generator)
        cmake.verbose = False
        if not self.options.built_in_tests:
            cmake.definitions["TBB_TEST:BOOL"] = "OFF"
        cmake.configure()
        cmake.build()
        cmake.install()

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
            self.cpp_info.defines.append("__TBBMALLOC_NO_IMPLICIT_LINKAGE=1")
