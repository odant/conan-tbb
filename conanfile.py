from conans import ConanFile, tools
from conans.errors import ConanException
import os


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
    exports_sources = "src/*", "Makefile.patch"
    no_copy_source = True
    build_policy = "missing"
    
    def source(self):
        tools.patch(patch_file="Makefile.patch")

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.build_requires("get_vcvars/1.0@odant/stable")
            self.build_requires("find_sdk_winxp/1.0@odant/stable")
            self.build_requires("gnu_make_installer/4.2.1@odant/stable")

    def configure(self):
        # Only C++11
        if self.settings.compiler.get_safe("libcxx") == "libstdc++":
            raise ConanException("This package is only compatible with libstdc++11")

    def build(self):
        build_type = str(self.settings.build_type).lower()
        arch = {
            "x86": "ia32",
            "x86_64": "intel64"
        }.get(str(self.settings.arch))
        if not arch:
            raise ConanException("Unsupported architecture %s" % self.settings.arch)
        #   
        build_env = self.get_build_environment()
        source_folder = os.path.join(self.source_folder, "src")
        with tools.chdir(source_folder), tools.environment_append(build_env):
            self.run("make tbb build_type=%s arch=%s tbb_build_dir=%s -j%s" % (build_type, arch, self.build_folder, tools.cpu_count()))

    def get_build_environment(self):
        env = {}
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            with tools.pythonpath(self):
                import get_vcvars
                env = get_vcvars.get_vcvars(self.settings)
                toolset = str(self.settings.compiler.get_safe("toolset"))
                if toolset.endswith("_xp"):
                    import find_sdk_winxp
                    env = find_sdk_winxp.dict_append(self.settings.arch, env=env)
        return env

    def package(self):
        self.copy("*.h", src="src/include", dst="include", keep_path=True)
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so*", dst="lib", keep_path=False, symlinks=True)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            # Disable auto link
            self.cpp_info.defines.append("__TBB_NO_IMPLICIT_LINKAGE=1")
