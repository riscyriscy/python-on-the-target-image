cmake_minimum_required(VERSION 3.21)
project(frametool LANGUAGES C)

# Development.Module = headers for building extension modules (no libpython link needed).
# scikit-build-core sets SKBUILD_SABI_COMPONENT when the build asks for the stable ABI
# (uv build -C wheel.py-api=cp312), and the variable is empty in every other build
find_package(Python 3.12 REQUIRED COMPONENTS Interpreter Development.Module ${SKBUILD_SABI_COMPONENT})

# The firmware's own crc16.c compiled into a CPython extension: _crc16.cpython-3XX-<platform>.so
if(SKBUILD_SABI_COMPONENT)
  set(sabi USE_SABI 3.12)
endif()
python_add_library(_crc16 MODULE WITH_SOABI ${sabi}
  native/crc16.c
  native/crc16_module.c)        # the CPython binding
target_include_directories(_crc16 PRIVATE native)
set_target_properties(_crc16 PROPERTIES C_VISIBILITY_PRESET hidden)

if(SKBUILD)
  # Building a wheel (pip install / uv build): scikit-build-core packs this into frametool/
  install(TARGETS _crc16 LIBRARY DESTINATION frametool)
else()
  # Plain CMake developer build: drop the module beside the sources (gitignored) and let
  # CTest run the pytest suite against it
  set_target_properties(_crc16 PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/src/frametool)
  enable_testing()
  add_test(NAME pytest
           COMMAND ${Python_EXECUTABLE} -m pytest -q ${CMAKE_CURRENT_SOURCE_DIR}/tests)
  set_tests_properties(pytest PROPERTIES
    ENVIRONMENT PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/src)
endif()
