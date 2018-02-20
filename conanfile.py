from conans import ConanFile, tools


class TBBConan(ConanFile):
    name = "tbb"
    version = "4.4.4"
    license = "Apache License 2.0 - https://www.threadingbuildingblocks.org/faq/10"
    description = "Intel(R) Threading Building Blocks (Intel(R) TBB) lets you easily write parallel C++ programs that take full advantage of multicore performance, that are portable, composable and have future-proof scalability."
    url = "https://github.com/odant/conan-tbb"
    settings = {
        "os": ["Windows", "Linux"],
        "compiler": ["Visual Studio", "gcc"],
        "build_type": ["Debug", "Release"],
        "arch": ["x86_64", "x86"]
    }
    exports_sources = "src/*"
    no_copy_source = True
    build_policy = "missing"

    def configure(self):
        # Only C++11
        if "libcxx" in self.settings.compiler.fields:
            if self.settings.compiler.libcxx == "libstdc++":
                raise Exception("This package is only compatible with libstdc++11")

    def build(self):
        pass

    def package(self):
        pass

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
