Launchpad
=========

⚠️ This is alpha-quality software. Contributions are welcome. If it breaks you get to keep both pieces. ⚠️

Launchpad is a post-exploitation agent / remote administration tool written Python 3.6. Project is inspired by 
[pupy](https://github.com/n1nj4sec/pupy).


### Supported operating systems

* Windows XP-10

### Features

* File-less execution (Windows/Powershell)
* Asynchronous: both dashboard and client are powered by greenlets (micro-threads)
* Communicates through json-rpc
* Supported protocols: Websockets

### Usage instructions

1. Clone repository: `git clone --recursive https://github.com/rokups/Launchpad`
2. Download binary files from [Launchpad-bin](https://github.com/rokups/Launchpad-bin/archive/master.zip) repository
or build them yourself as described below. Put them to `bin` directory.
3. Create or update database: `src/manage migrate`. Do this each time Launchpad is updated.
4. Run dashboard: `src/manage runserver <address>:<port>`
5. Navigate to `http://<address>:<port>` in your browser.

Please note that by default dashboard runs in debug mode and only allows localhost access. If you would like to use
Launchpad in a live environment make sure you configure it properly. At least set `launchpad.settings.DEBUG = False`, 
`launchpad.settings.SECRET_KEY = 'some very random string'` and add appropriate address or host name to 
`launchpad.settings.ALLOWED_HOSTS`. Failure to properly configure dashboard may leave you vulnerable to external 
threats.

### Building stdlib zip files

Launchpad requires pre-created zip files containing with python interpreter, standard library and other dependencies. 

1. Create virtual environment: `python3 -m venv /path/to/venv`
2. Activate created virtual environment:
   * Windows: `..\path\to\venv\Script\activate`
   * Linux: `. /path/to/venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Create zip file: `python3 src/tool/zip_python bin/windows-x64-3.6.zip`

### Building bootloader

Bootloader is executable that bootstraps python application on target machine. It is built using gcc on linux or
MingW-w64 on windows. Simply build `src/boot` CMake project as you normally would. Built executable will be put to `bin`
directory.
