# Intel TBB Conan package
# Dmitriy Vetutnev, Odant, 2018, 2020


find_path(TBB_INCLUDE_DIR
    NAMES tbb/tbb_stddef.h
    PATHS ${CONAN_INCLUDE_DIRS_TBB}
    NO_DEFAULT_PATH
)

find_library(TBB_LIBRARY
    NAMES tbb tbbd tbb32 tbb32d tbb64 tbb64d
    PATHS ${CONAN_LIB_DIRS_TBB}
    NO_DEFAULT_PATH
)

if(TBB_INCLUDE_DIR)

    file(STRINGS ${TBB_INCLUDE_DIR}/tbb/tbb_stddef.h define_major
         REGEX "^#define[\t ]+TBB_VERSION_MAJOR[\t ]+[0-9]+"
    )
    string(REGEX REPLACE "^#define[\t ]+TBB_VERSION_MAJOR[\t ]+([0-9]+)"
           "\\1" TBB_VERSION_MAJOR ${define_major}
    )
    unset(define_major)

    file(STRINGS ${TBB_INCLUDE_DIR}/tbb/tbb_stddef.h define_minor
         REGEX "^#define[\t ]+TBB_VERSION_MINOR[\t ]+[0-9]+"
    )
    string(REGEX REPLACE "^#define[\t ]+TBB_VERSION_MINOR[\t ]+([0-9]+)"
           "\\1" TBB_VERSION_MINOR ${define_minor}
    )
    unset(define_minor)

    set(TBB_VERSION_STRING "${TBB_VERSION_MAJOR}.${TBB_VERSION_MINOR}")
    set(TBB_VERSION_COUNT 2)

endif()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(TBB
    REQUIRED_VARS TBB_INCLUDE_DIR TBB_LIBRARY
    VERSION_VAR TBB_VERSION_STRING
)

if(TBB_FOUND AND NOT TARGET TBB::tbb)

    add_library(TBB::tbb UNKNOWN IMPORTED)

    set_target_properties(TBB::tbb PROPERTIES
        IMPORTED_LOCATION "${TBB_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${TBB_INCLUDE_DIR}"
        INTERFACE_COMPILE_DEFINITIONS "${CONAN_COMPILE_DEFINITIONS_TBB}"
    )

    mark_as_advanced(TBB_INCLUDE_DIR TBB_LIBRARY)

    set(TBB_INCLUDE_DIRS ${TBB_INCLUDE_DIR})
    set(TBB_LIBRARIES ${TBB_LIBRARY})
    set(TBB_DEFINITIONS ${CONAN_COMPILE_DEFINITIONS_TBB})

endif()

