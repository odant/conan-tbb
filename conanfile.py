# Intel TBB Conan package
# Dmitriy Vetutnev, Odant, 2018

from conan import ConanFile, tools
from conan.errors import ConanInvalidConfiguration, ConanException
from datetime import datetime
import os, glob, shutil



class TBBConan(ConanFile):
    name = "tbb"
    version = "2022.1.0+0"
    license = "Apache License 2.0 - https://www.threadingbuildingblocks.org/faq/10"
    description = "Intel(R) Threading Building Blocks (Intel(R) TBB) lets you easily write parallel C++ programs that take full advantage of multicore performance, that are portable, composable and have future-proof scalability."
    url = "https://github.com/odant/conan-tbb"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "dll_sign": [False, True],
        "ninja": [False, True],
        "shared": [True, False],
        "atomic_wait": [True, False]
    }
    default_options = {
        "dll_sign":    True, 
        "ninja":       True,
        "shared":      True, 
        "atomic_wait": False
    }
    exports_sources = "src/*", "CMakeLists.txt", \
                      "test_global_control-two-core.patch", \
                      "dynamic_winapi.patch", \
                      "add_atomic_wait.patch"
    #no_copy_source = True
    build_policy = "missing"
    python_requires = "windows_signtool/[>=1.2]@odant/stable"
    
    def layout(self):
        tools.cmake.cmake_layout(self, src_folder="src")
            
    def configure(self):
        # Only C++11
        if self.settings.compiler.get_safe("libcxx") == "libstdc++":
            raise ConanException("This package is only compatible with libstdc++11")
        # MT(d) static library
        if self.settings.os == "Windows" and self.settings.compiler == "msvc" and self.settings.compiler.runtime == "static":
            self.options.shared = False
        # DLL sign, only Windows
        if self.settings.os != "Windows":
            self.options.rm_safe("dll_sign")

    def build_requirements(self):
        if self.options.get_safe("ninja"):
            self.tool_requires("ninja/[>=1.12.1]")

    def generate(self):
        benv = tools.env.VirtualBuildEnv(self)
        benv.generate()
        if tools.microsoft.is_msvc(self):
            vc = tools.microsoft.VCVars(self)
            vc.generate()
        generator = "Ninja" if self.options.ninja == True else None
        tc = tools.cmake.CMakeToolchain(self, generator=generator)
        tc.variables["TBB_TEST"] = "OFF"
        if self.settings.os == "Windows" and self.settings.arch == "x86":
            tc.variables["TBB_STRICT"] = "OFF"
        tc.generate()

    def _patch_sources(self):
        self.output.info(f"self.source_folder = {self.source_folder}")
        tools.files.patch(self, patch_file="test_global_control-two-core.patch")
        if self.options.get_safe("atomic_wait"):
            tools.files.patch(self, patch_file=os.path.join(self.source_folder,"add_atomic_wait.patch"))
        if self.settings.os == "Windows":
            tools.files.patch(self, patch_file="dynamic_winapi.patch")

    def build(self):
        self._patch_sources()
        cmake = tools.cmake.CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = tools.cmake.CMake(self)
        cmake.install()
        tools.files.rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        tools.files.rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.files.rm(self, "*tbbmalloc*", os.path.join(self.package_folder, "bin"))
        tools.files.rm(self, "*tbbmalloc*", os.path.join(self.package_folder, "lib"))
        if self.settings.os == "Windows":
            tools.files.rm(self, "*tbb.*", os.path.join(self.package_folder, "lib"))
            tools.files.rm(self, "*tbb_*", os.path.join(self.package_folder, "lib"))
            
        # Sign DLL
        if self.options.get_safe("dll_sign"):
            self.python_requires["windows_signtool"].module.sign(self, [os.path.join(self.package_folder, "bin", "*.dll")])

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "TBB")
        self.cpp_info.set_property("cmake_target_name", "TBB::tbb")
        self.cpp_info.libs = tools.files.collect_libs(self)
        # Disable auto link
        if self.settings.os == "Windows":
            self.cpp_info.defines.append("__TBB_NO_IMPLICIT_LINKAGE=1")
            self.cpp_info.defines.append("__TBBMALLOC_NO_IMPLICIT_LINKAGE=1")
