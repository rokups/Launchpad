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
import io
import os
import zipfile

import math
from django.conf import settings
import pefile
from common.utilities import enumerate_files, compile_file


def pe_add_section(pe, data: bytes, name):
    file_alignment = pe.OPTIONAL_HEADER.FileAlignment
    section_alignment = pe.OPTIONAL_HEADER.SectionAlignment

    def align(value, alignment):
        return int(math.ceil(float(value) / alignment)) * alignment

    section_size = pe.sections[0].sizeof()
    section_offset = pe.OPTIONAL_HEADER.get_file_offset() + pe.FILE_HEADER.SizeOfOptionalHeader     # First section
    section_offset += pe.FILE_HEADER.NumberOfSections * section_size                                # New section

    if (section_offset + section_size) >= pe.OPTIONAL_HEADER.SizeOfHeaders:
        raise ValueError('There is not enough free space for new section.')

    section = pefile.SectionStructure(pe.__IMAGE_SECTION_HEADER_format__, pe=pe)
    section.Name = name.encode()
    section.VirtualAddress = align(pe.sections[-1].Misc_VirtualSize + pe.sections[-1].VirtualAddress, section_alignment)
    section.Misc = section.Misc_VirtualSize = len(data)

    # Pad data to be aligned to FileAlignment.
    data += b'\0' * (align(len(data), file_alignment) - len(data))

    # section.RawSize = len(data)
    section.PointerToRawData = pe.sections[-1].PointerToRawData + pe.sections[-1].SizeOfRawData
    section.SizeOfRawData = len(data)
    section.Characteristics = 0x40000040    # Readable | Initialized
    section.PointerToRelocations = 0
    section.PointerToLinenumbers = 0
    section.NumberOfRelocations = 0
    section.NumberOfLinenumbers = 0

    header_data = section.__pack__()

    # Add new section to PE header.
    pe.__data__ = pe.__data__[:section_offset] + header_data + pe.__data__[section_offset + len(header_data):]

    # Add section data to the end of file.
    pe.__data__ = pe.__data__[:section.PointerToRawData] + data + pe.__data__[section.PointerToRawData:]
    # pe.merge_modified_section_data()

    pe.sections.append(section)
    pe.FILE_HEADER.NumberOfSections += 1
    pe.OPTIONAL_HEADER.SizeOfImage = align(
        pe.OPTIONAL_HEADER.SizeOfHeaders + pe.sections[-1].VirtualAddress + pe.sections[-1].Misc_VirtualSize,
        section_alignment
    )
    pe.OPTIONAL_HEADER.SizeOfCode = 0
    pe.OPTIONAL_HEADER.SizeOfInitializedData = 0
    pe.OPTIONAL_HEADER.SizeOfUninitializedData = 0

    # Recalculating the sizes by iterating over every section and checking if
    # the appropriate characteristics are set.
    for section in pe.sections:
        if section.Characteristics & 0x00000020:    # Code
            pe.OPTIONAL_HEADER.SizeOfCode += section.SizeOfRawData
        elif section.Characteristics & 0x00000040:  # Initialized data
            pe.OPTIONAL_HEADER.SizeOfInitializedData += section.SizeOfRawData
        elif section.Characteristics & 0x00000080:  # Uninitialized data
            pe.OPTIONAL_HEADER.SizeOfUninitializedData += section.SizeOfRawData


def create_bootloader_win(interpreter_zip, executable, argv):
    """
    Prepares executable for execution on target machine. Appends client code to `interpreter_zip` archive. Embeds new
    archive into `executable`.
    :param interpreter_zip: Zip file containing python runtime, stdlib and essential dependencies.
    :param executable: Loader executable.
    :param argv: list of arguments passed to client.
    :return: binary string containing payload ready for execution.
    """
    with open(interpreter_zip, 'rb') as fp:
        zip_data = io.BytesIO(fp.read())

    with zipfile.ZipFile(zip_data, 'a', zipfile.ZIP_DEFLATED, False) as fp:
        fp.writestr('argv.txt', '\n'.join(argv))

        base_path = settings.SOURCE_DIR / 'common'
        for archive_path in enumerate_files(base_path, '.py'):
            file_path = base_path / archive_path
            archive_path = 'common/' + archive_path
            code = compile_file(file_path, archive_path)
            fp.writestr(archive_path + 'c', code)

        base_path = settings.SOURCE_DIR / 'client'
        for archive_path in enumerate_files(base_path, '.py'):
            file_path = base_path / archive_path

            if archive_path == 'main.py':
                archive_path = '__main__.py'
            else:
                archive_path = 'client/' + archive_path

            code = compile_file(file_path, archive_path)
            fp.writestr(archive_path + 'c', code)

    zip_data.seek(0, os.SEEK_SET)
    zip_data = zip_data.read()

    pe = pefile.PE(executable)
    pe_add_section(pe, zip_data, '.py')

    return pe.write()
