//
// MIT License
//
// Copyright 2017 Launchpad project contributors (see COPYRIGHT.md)
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the "Software"),
// to deal in the Software without restriction, including without limitation
// the rights to use, copy, modify, merge, publish, distribute, sublicense,
// and/or sell copies of the Software, and to permit persons to whom the
// Software is furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
// THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
// DEALINGS IN THE SOFTWARE.
//
// Portions of this file are licensed to "PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2", see
// https://github.com/python/cpython/blob/master/LICENSE
//
/*
 * Windows bootloader uses reflective loader package to load native dlls shipped in the interpreter zip file. It also
 * properly initializes native python extensions. Interpreter zip file is expected to be embedded into bootloader
 * executable by adding a new section and naming it ".py".
 */
#include <winsock2.h>           // Even though we do not use this MingW likes to complain if it is not included.
#include <windows.h>
#include <stdint.h>
#include <cmath>                // \_ Solves some odd build errors on mingw.
#define _hypot hypot
#undef Py_ENABLE_SHARED         // Prevent Python.h from defining API with external linkage. Required by PY_R_IMPORT macros.
#include <Python.h>
#include <miniz.h>
#include <locale.h>
#include <vector>
#include <string>
#include <winnt.h>

#include "ReflectiveLdr.h"

inline void CLIENT_LOG(const char* format, ...)
{
#if 0
    va_list ap;
    va_start(ap, format);
    vfprintf(stderr, format, ap);
    fprintf(stderr, "\n");
    fflush(stderr);
#endif
}

extern "C"
{
/// Replacements for new windows API that is not available on older OS versions.
int64_t WINAPI _GetTickCount64();
DWORD WINAPI _GetFinalPathNameByHandleW(HANDLE hFile, LPWSTR lpszFilePath, DWORD cchFilePath, DWORD dwFlags);
/// Python context magic.
void _LoadActCtxPointers();
void _UnloadActCtx();
ULONG_PTR _Py_ActivateActCtx();
void _Py_DeactivateActCtx(ULONG_PTR cookie);
/// A quick way to obtain base of current image. Works with even if image is loaded reflectively.
extern IMAGE_DOS_HEADER __ImageBase;
};

/// Macros used for reflectively importing python API from interpreter dll that was loaded from memory.
#define PY_R_IMPORT_STR(name) #name
#define PY_R_IMPORT_FN(name) auto name = (decltype(&::name))(ldr.GetProcAddressR(hPython, PY_R_IMPORT_STR(name)));
#define PY_R_IMPORT_DT(name) auto& name = *(decltype(&::name))(ldr.GetProcAddressR(hPython, PY_R_IMPORT_STR(name)));

/* Python interpreter main program for frozen scripts */

//#ifdef MS_WINDOWS
//extern void PyWinFreeze_ExeInit(void);
//extern void PyWinFreeze_ExeTerm(void);
//extern int PyInitFrozenExtensions(void);
//#endif

std::string replace(std::string subject, const std::string& search, const std::string& replacement)
{
    size_t pos = 0;
    for (; pos < subject.size();)
    {
        pos = subject.find(search, pos);
        if (pos == std::string::npos)
            break;
        subject.replace(pos, search.size(), replacement);
        pos += replacement.size();
    }
    return subject;
}

/* Main program */

int Py_FrozenMain(Reflective::Ldr& ldr, int argc, char** argv, HMODULE hPython, std::vector<_inittab>& frozen_native)
{
    PY_R_IMPORT_FN(PyMem_RawMalloc);
    PY_R_IMPORT_FN(Py_FatalError);
    PY_R_IMPORT_FN(Py_GetPath);
    PY_R_IMPORT_FN(Py_Initialize);
    PY_R_IMPORT_FN(PyRun_AnyFileExFlags);
    PY_R_IMPORT_FN(PyRun_SimpleStringFlags);
    PY_R_IMPORT_FN(Py_FinalizeEx);
    PY_R_IMPORT_FN(_PyMem_RawStrdup);
    PY_R_IMPORT_FN(Py_DecodeLocale);
    PY_R_IMPORT_FN(PyMem_RawFree);
    PY_R_IMPORT_FN(Py_SetProgramName);
    PY_R_IMPORT_FN(PySys_SetArgv);
    PY_R_IMPORT_FN(PyImport_ImportFrozenModule);
    PY_R_IMPORT_FN(PyImport_ExtendInittab);
    PY_R_IMPORT_FN(PySys_SetObject);
    PY_R_IMPORT_FN(PyBool_FromLong);
    PY_R_IMPORT_FN(PyEval_InitThreads);
    PY_R_IMPORT_FN(PyGILState_Ensure);
    PY_R_IMPORT_FN(PyGILState_Release);

    PY_R_IMPORT_DT(Py_IgnoreEnvironmentFlag);
    PY_R_IMPORT_DT(Py_NoSiteFlag);
    PY_R_IMPORT_DT(Py_NoUserSiteDirectory);
    PY_R_IMPORT_DT(Py_FrozenFlag);

    // Kill any possible PYTHONPATH setting, avoid mixing this interpreter with system-wide installations.
    *Py_GetPath() = 0;

    PyGILState_STATE gil_state;
    int i, n, sts = 1;
    char* oldloc = NULL;
    wchar_t** argv_copy = NULL;
    /* We need a second copies, as Python might modify the first one. */
    wchar_t** argv_copy2 = NULL;

    if (argc > 0)
    {
        argv_copy = (wchar_t**)PyMem_RawMalloc(sizeof(wchar_t*) * argc);
        argv_copy2 = (wchar_t**)PyMem_RawMalloc(sizeof(wchar_t*) * argc);
        if (!argv_copy || !argv_copy2)
        {
            CLIENT_LOG("out of memory");
            goto error;
        }
    }

    Py_FrozenFlag = 1; /* Suppress errors from getpath.c */

    oldloc = _PyMem_RawStrdup(setlocale(LC_ALL, NULL));
    if (!oldloc)
    {
        CLIENT_LOG("out of memory");
        goto error;
    }

    setlocale(LC_ALL, "");
    for (i = 0; i < argc; i++)
    {
        argv_copy[i] = Py_DecodeLocale(argv[i], NULL);
        argv_copy2[i] = argv_copy[i];
        if (!argv_copy[i])
        {
            CLIENT_LOG("Unable to decode the command line argument #%i", i + 1);
            argc = i;
            goto error;
        }
    }
    setlocale(LC_ALL, oldloc);
    PyMem_RawFree(oldloc);
    oldloc = NULL;

//#ifdef MS_WINDOWS
//    PyInitFrozenExtensions();
//#endif /* MS_WINDOWS */
    PyImport_ExtendInittab(&frozen_native.front());
    if (argc >= 1)
        Py_SetProgramName(argv_copy[0]);

    Py_Initialize();
    PyEval_InitThreads();

    PySys_SetObject("frozen", PyBool_FromLong(1));
    PySys_SetArgv(argc, argv_copy);

// This calls DllMain(DLL_PROCESS_ATTACH), already done by reflective module loader.
//#ifdef MS_WINDOWS
//    PyWinFreeze_ExeInit();
//#endif

    gil_state = PyGILState_Ensure();

    n = PyImport_ImportFrozenModule("__main__");

    if (n == 0)
        Py_FatalError("__main__ not frozen");
    if (n < 0)
    {
        // Causes crash on x64 for some reason.
        // PyErr_Print();
        sts = 1;
    }
    else
        sts = 0;

    PyGILState_Release(gil_state);

    if (Py_FinalizeEx() < 0)
        sts = 120;

error:
    PyMem_RawFree(argv_copy);
    if (argv_copy2)
    {
        for (i = 0; i < argc; i++)
            PyMem_RawFree(argv_copy2[i]);
        PyMem_RawFree(argv_copy2);
    }
    PyMem_RawFree(oldloc);
    return sts;
}

void insert_module(_frozen* dest, const char* name, const void* code, int csize, bool is_package)
{
    dest->name = strdup(name);
    dest->code = (const unsigned char*)malloc(csize);
    dest->size = is_package ? -csize : csize;
    memcpy((void*)dest->code, code, csize);
}

int main(int argc, char** argv)
{
    uint8_t* packed_bundle = 0;
    size_t file_size = 0;

    _LoadActCtxPointers();

    PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)(PCHAR(&__ImageBase) + (__ImageBase.e_lfanew));
    PIMAGE_SECTION_HEADER section = (PIMAGE_SECTION_HEADER)(PCHAR(&nt->OptionalHeader) + nt->FileHeader.SizeOfOptionalHeader);
    section = section + nt->FileHeader.NumberOfSections - 1;
#if DEBUG
    if (stricmp((const char*)&section->Name, ".py") != 0)
    {
        FILE* fp = fopen("test.zip", "rb");
        fseek(fp, 0, SEEK_END);
        file_size = ftell(fp);
        rewind(fp);
        packed_bundle = (uint8_t*)malloc(file_size);
        fread(packed_bundle, 1, file_size, fp);
        fclose(fp);
    }
    else
#endif
    {
        packed_bundle = (uint8_t*)(PCHAR(&__ImageBase) + section->VirtualAddress);
        file_size = section->Misc.VirtualSize;
    }

    mz_zip_archive zip = {};
    if (!mz_zip_reader_init_mem(&zip, packed_bundle, file_size, MZ_ZIP_FLAG_DO_NOT_SORT_CENTRAL_DIRECTORY))
        return -1;

    HMODULE hPython = 0;
    Reflective::Ldr ldr;
    auto file_count = mz_zip_reader_get_num_files(&zip);
    mz_uint index = 0;
    size_t module_index = 0;
    size_t frozen_index = 0;
    std::vector<_inittab> frozen_native;
    std::vector<_frozen> _PyImport_FrozenModules;
    std::vector<char*> embedded_argv;
    _PyImport_FrozenModules.resize(file_count + 1);
    frozen_native.resize(1);

    OSVERSIONINFO info;
    GetVersionEx(&info);

    // Python 3.5+ no longer supports windows XP and uses these two new APIs. Let loader provide fake imports and make
    // latest python work on XP.
    ldr.SetImportAlternative("kernel32.dll", "GetTickCount64", (FARPROC)&_GetTickCount64);
    ldr.SetImportAlternative("kernel32.dll", "GetFinalPathNameByHandleW", (FARPROC)&_GetFinalPathNameByHandleW);

    for (; index < file_count; index++)
    {
        char file_name[512];
        size_t extracted_size = 0;
        mz_zip_reader_get_filename(&zip, index, file_name, sizeof(file_name));
        void* extracted_data = mz_zip_reader_extract_file_to_heap(&zip, file_name, &extracted_size, 0);
        if (!extracted_data || !extracted_size)
            return -1;
        if (strstr(file_name, ".dll\0"))
        {
            ULONG_PTR cookie = _Py_ActivateActCtx();
            HMODULE hModule = 0;

            // Load from memory if not present in OS.
            hModule = (HMODULE)ldr.MapImageAndExecute(extracted_data, 0);
            if (hModule)
                CLIENT_LOG("memory-loaded %s", file_name);

            if (hModule == 0)
                CLIENT_LOG("Failed to load %s", file_name);

            _Py_DeactivateActCtx(cookie);
            if (strnicmp(file_name, "python", 6) == 0)
                hPython = hModule;
        }
        else if (strstr(file_name, ".pyd\0"))
        {
            std::string init_name = "PyInit_";
            std::string module_name = file_name;
            module_name = replace(module_name, ".pyd", "");

            // Name of native module includes full package path, eg. package.subpackage.pyd. Look for first dot going
            // from end of the string and use only last package name for deriving init function.
            auto last_dot_index = module_name.rfind('.');
            if (last_dot_index != std::string::npos)
                last_dot_index++;
            else
                last_dot_index = 0;
            init_name += module_name.substr(last_dot_index);

            // Replace all dots with __dot__ marker to create proper top level package name.
            module_name = replace(module_name, ".", "__dot__");

            ULONG_PTR cookie = _Py_ActivateActCtx();
            HMODULE hModule = (HMODULE)ldr.MapImageAndExecute(extracted_data, 0);
            if (hModule != 0)
            {
                CLIENT_LOG("memory-loaded %s", file_name);

                // Prepend all modified package names with __native__ so client knows which packages to redirect.
                if (module_name.find("__dot__", 0) != std::string::npos)
                    module_name = "__native__" + module_name;

                frozen_native[frozen_index].name = strdup(module_name.c_str());
                frozen_native[frozen_index].initfunc =
                    (PyObject* (*)(void))ldr.GetProcAddressR(hModule, init_name.c_str());

                if (frozen_native[frozen_index].initfunc == 0)
                    CLIENT_LOG("Could not load %s.%s export.", file_name, init_name.c_str());

                frozen_index++;
                frozen_native.resize(frozen_index + 1);
            }
            else
                CLIENT_LOG("Failed to load %s", file_name);
            _Py_DeactivateActCtx(cookie);
        }
        else if (strcmp(file_name, "argv.txt") == 0)
        {
            embedded_argv.push_back(strdup("__client__"));

            // Text is being processed but miniz does not put terminating \0 at the end.
            extracted_data = realloc(extracted_data, extracted_size + 1);
            ((uint8_t*)extracted_data)[extracted_size] = 0;

            char* tok = strtok((char*)extracted_data, "\n");
            while (tok)
            {
                embedded_argv.push_back(strdup(tok));
                tok = strtok(nullptr, "\n");
            }
        }
        else
        {
            auto name_len = strlen(file_name);
            bool is_package = false;
            if (strstr(file_name, "__init__.pyc\0"))
            {
                // Remove "__init__.pyc" from filename. Package __init__ file is referred to by it's directory name.
                file_name[name_len - 13] = 0;
                is_package = true;
            }
            else
                file_name[name_len - 4] = 0;    // Remove .pyc

            // Replace directory separators with dots. This results in full python package path.
            for (auto i = 0; i < name_len; i++)
            {
                if (file_name[i] == '/' || file_name[i] == '\\')
                    file_name[i] = '.';
            }
            insert_module(&_PyImport_FrozenModules[module_index], file_name, extracted_data, extracted_size, is_package);
            module_index++;
        }
        free(extracted_data);
    }
    _PyImport_FrozenModules[module_index].name = 0;
    _PyImport_FrozenModules[module_index].code = 0;
    _PyImport_FrozenModules[module_index].size = 0;

    frozen_native[frozen_index].name = 0;
    frozen_native[frozen_index].initfunc = 0;

    mz_zip_reader_end(&zip);
    packed_bundle = 0;
    file_size = 0;

    PY_R_IMPORT_FN(Py_IsInitialized);
    if (Py_IsInitialized() == 0)
    {
        PY_R_IMPORT_DT(PyImport_FrozenModules);
        PyImport_FrozenModules = &_PyImport_FrozenModules.front();

        argc = embedded_argv.size();
        argv = &embedded_argv.front();

        Py_FrozenMain(ldr, argc, argv, hPython, frozen_native);
    }

    _UnloadActCtx();

    for (auto& frozen: _PyImport_FrozenModules)
    {
        free((void*)frozen.name);
        free((void*)frozen.code);
    }

    for (auto& native: frozen_native)
        free((void*)native.name);

    for (auto argv_val: embedded_argv)
        free(argv_val);

    return TRUE;
}
