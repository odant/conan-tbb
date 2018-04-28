# Test for Intel TBB Conan package
# Dmitriy Vetutnev, Odant, 2018


from conans import ConanFile, CMake


class PackageTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        if self.options["tbb"].built_in_tests:
            return
        cmake = CMake(self)
        cmake.verbose = True
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy("*.pdb", dst="bin", src="bin")
        self.copy("*.dll", dst="bin", src="bin")
        self.copy("*.so.*", dst="bin", src="lib")

    def test(self):
        if self.options["tbb"].built_in_tests:
            return
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.run("ctest --verbose --build-config %s" % self.settings.build_type)
        else:
            self.run("ctest --verbose")
