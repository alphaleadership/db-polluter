

#!/usr/bin/env python3

# Allow direct execution
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import platform

from PyInstaller.__main__ import run as run_pyinstaller

from devscripts.utils import read_version

OS_NAME, MACHINE, ARCH = sys.platform, platform.machine().lower(), platform.architecture()[0][:2]
if MACHINE in ('x86', 'x86_64', 'amd64', 'i386', 'i686'):
    MACHINE = 'x86' if ARCH == '32' else ''


def main():
    opts, version = parse_options(), read_version()

    onedir = '--onedir' in opts or '-D' in opts
    if not onedir and '-F' not in opts and '--onefile' not in opts:
        opts.append('--onefile')

    name, final_file = exe(onedir)
    print(f'Building db_polluteur v{version} for {OS_NAME} {platform.machine()} with options {opts}')
    print('Remember to update the version using  "devscripts/update-version.py"')
    if not os.path.isfile('yt_dlp/extractor/lazy_extractors.py'):
        print('WARNING: Building without lazy_extractors. Run  '
              '"devscripts/make_lazy_extractors.py"  to build lazy extractors', file=sys.stderr)
    print(f'Destination: {final_file}\n')

    opts = [
        f'--name={name}',
        '--icon=devscripts/logo.ico',
        '--upx-exclude=vcruntime140.dll',
        '--noconfirm',
        *dependency_options(),
        *opts,
        'main.py',
    ]

    print(f'Running PyInstaller with {opts}')
    run_pyinstaller(opts)
    set_version_info(final_file, version)


def parse_options():
    # Compatibility with older arguments
    opts = sys.argv[1:]
    if opts[0:1] in (['32'], ['64']):
        if ARCH != opts[0]:
            raise Exception(f'{opts[0]}bit executable cannot be built on a {ARCH}bit system')
        opts = opts[1:]
    return opts


def exe(onedir):
    """@returns (name, path)"""
    name = '_'.join(filter(None, (
        'db_polluteur',
        {'win32': '', 'darwin': 'macos'}.get(OS_NAME, OS_NAME),
        MACHINE,
    )))
    return name, ''.join(filter(None, (
        'dist/',
        onedir and f'{name}/',
        name,
        OS_NAME == 'win32' and '.exe'
    )))


def version_to_list(version):
    version_list = version.split('.')
    return list(map(int, version_list)) + [0] * (4 - len(version_list))


def dependency_options():
    # Due to the current implementation, these are auto-detected, but explicitly add them just in case
    dependencies = [pycryptodome_module(), 'mutagen', 'brotli', 'certifi', 'websockets']
    excluded_modules = ('youtube_dl', 'youtube_dlc', 'test', 'ytdlp_plugins', 'devscripts')

    yield from (f'--hidden-import={module}' for module in dependencies)
    yield '--collect-submodules=websockets'
    yield from (f'--exclude-module={module}' for module in excluded_modules)


def pycryptodome_module():
    try:
        import Cryptodome  # noqa: F401
    except ImportError:
        try:
            import Crypto  # noqa: F401
            print('WARNING: Using Crypto since Cryptodome is not available. '
                  'Install with: pip install pycryptodomex', file=sys.stderr)
            return 'Crypto'
        except ImportError:
            pass
    return 'Cryptodome'


def set_version_info(exe, version):
    if OS_NAME == 'win32':
        windows_set_version(exe, version)


def windows_set_version(exe, version):
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        SetVersion,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

    version_list = version_to_list(version)
    suffix = MACHINE and f'_{MACHINE}'
    SetVersion(exe, VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=version_list,
            prodvers=version_list,
            mask=0x3F,
            flags=0x0,
            OS=0x4,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo([StringTable('040904B0', [
                StringStruct('Comments', 'db_polluteur%s Command Line Interface' % suffix),
                StringStruct('CompanyName', 'https://github.com/db_polluteur'),
                StringStruct('FileDescription', 'db_polluteur%s' % (MACHINE and f' ({MACHINE})')),
                StringStruct('FileVersion', version),
                StringStruct('InternalName', f'db_polluteur{suffix}'),
                StringStruct('LegalCopyright', 'pukkandan.ytdlp@gmail.com | UNLICENSE'),
                StringStruct('OriginalFilename', f'db_polluteur{suffix}.exe'),
                StringStruct('ProductName', f'db_polluteur{suffix}'),
                StringStruct(
                    'ProductVersion', f'{version}{suffix} on Python {platform.python_version()}'),
            ])]), VarFileInfo([VarStruct('Translation', [0, 1200])])
        ]
    ))


if __name__ == '__main__':
    main()
