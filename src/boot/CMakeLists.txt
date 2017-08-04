#
# MIT License
#
# Copyright 2017 Launchpad project contributors (see COPYRIGHT.md)
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
cmake_minimum_required(VERSION 3.7)
project(launchpad)
# This folder contains bootloaders for various platforms. Bootloader is application that loads python interpreter and
# executes client module.

set(CMAKE_CXX_STANDARD 11)

include(CMake/Utilities.cmake)

if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    set(ARCH_BITS 64)
    set(ARCH_NAME x64)
else ()
    set(ARCH_BITS 32)
    set(ARCH_NAME x86)
endif()

set(CMAKE_SHARED_LIBRARY_PREFIX lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/../../bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/../../bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)


if (${CMAKE_C_COMPILER_ID} STREQUAL GNU)
    add_linker_flags(-static -static-libgcc -static-libstdc++)
    add_linker_flags(
        -Wl,--nxcompat
        -Wl,--dynamicbase
        -Wl,--exclude-all-symbols
        -fvisibility=hidden
        EXE SHARED
    )
    if (RELEASE)
        add_compiler_flags(-Wl,--gc-sections)
    endif ()
endif()
if (RELEASE)
    add_linker_flags(-s -g -O3)
endif ()

add_compiler_flags(-fdata-sections -ffunction-sections -fomit-frame-pointer -fno-stack-protector -fno-unwind-tables)
add_compiler_flags(-std=c++14 -fno-rtti -fno-exceptions CXX)

add_subdirectory(common)

if (WIN32)
    # TODO: MingW crosscompiling support
    add_subdirectory(windows)
endif ()
