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
#include <windows.h>
#include <psapi.h>
#include <stdint.h>
#include <stdio.h>

// A workaround APIs for Windows 5.x

DWORD _lastTickCount = 0;
int64_t _tickCount64 = 0;
int64_t WINAPI _GetTickCount64()
{
    DWORD current = GetTickCount();
    _tickCount64 += current - _lastTickCount;
    _lastTickCount = current;
    return _tickCount64;
}

#define BUFSIZE 512
DWORD WINAPI _GetFinalPathNameByHandleW(HANDLE hFile, LPWSTR lpszFilePath, DWORD cchFilePath, DWORD dwFlags)
{
    BOOL bSuccess = FALSE;
    HANDLE hFileMap;

    // Get the file size.
    DWORD dwFileSizeHi = 0;
    DWORD dwFileSizeLo = GetFileSize(hFile, &dwFileSizeHi);

    if( dwFileSizeLo == 0 && dwFileSizeHi == 0 )
    {
//        _tprintf(TEXT("Cannot map a file with a length of zero.\n"));
        return FALSE;
    }

    // Create a file mapping object.
    hFileMap = CreateFileMapping(hFile, NULL, PAGE_READONLY, 0, 1, NULL);

    if (hFileMap)
    {
        // Create a file mapping to get the file name.
        void* pMem = MapViewOfFile(hFileMap, FILE_MAP_READ, 0, 0, 1);

        if (pMem)
        {
            if (GetMappedFileNameW(GetCurrentProcess(), pMem, lpszFilePath, cchFilePath - 1))
            {

                // Translate path with device name to drive letters.
                WCHAR szTemp[BUFSIZE];
                szTemp[0] = '\0';

                if (GetLogicalDriveStringsW(BUFSIZE-1, szTemp))
                {
                    WCHAR szName[MAX_PATH];
                    WCHAR szDrive[3];
                    wcscpy(szDrive, L" :");
                    BOOL bFound = FALSE;
                    WCHAR* p = szTemp;

                    do
                    {
                        // Copy the drive letter to the template string
                        *szDrive = *p;

                        // Look up each device name
                        if (QueryDosDeviceW(szDrive, szName, MAX_PATH))
                        {
                            size_t uNameLen = wcslen(szName);

                            if (uNameLen < MAX_PATH)
                            {
                                bFound = wcsnicmp(lpszFilePath, szName, uNameLen) == 0 && *(lpszFilePath + uNameLen) == L'\\';

                                if (bFound)
                                {
                                    // Reconstruct pszFilename using szTempFile
                                    // Replace device path with DOS path
                                    WCHAR szTempFile[MAX_PATH];
                                    snwprintf(szTempFile, MAX_PATH, L"%s%s", szDrive, lpszFilePath+uNameLen);
                                    wcscpy(lpszFilePath, szTempFile);
                                }
                            }
                        }

                        // Go to the next NULL character.
                        while (*p++);
                    } while (!bFound && *p); // end of string
                }
            }
            bSuccess = TRUE;
            UnmapViewOfFile(pMem);
        }

        CloseHandle(hFileMap);
    }
//    _tprintf(TEXT("File name is %s\n"), lpszFilePath);
    return(bSuccess);
}
