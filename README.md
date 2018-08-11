# pwmgr
Simple password manager using the 7-Zip program

### Description
`pwmgr.py` manages an encrypted `.7z` archive containing a text file. Passwords are stored in and retrieved from this file. A master password must be entered to access the archive.

### Requirements
- 7-Zip Command Line Version
- python3 (3.6+)
- xclip (for X selection use)

### Set-up
- Place `pwmgr.py` and the empty `pvault` directory in the same directory.
- (Optional): Create a bash alias such as `pwmgr="python full_path_to_pwmgr.py"` to easily invoke the script from any bash shell with `pwmgr...` (otherwise replace `pwmgr` with `python full_path_to_pwmgr.py` in the following code).
- Create a _new_ 'user' with `pwmgr -n username`. This invokes the 7-Zip executable to create a `.7z` archive called `username` in the `pvault` directory. You will be prompted to enter a password for the archive, which acts as the master password for the manager. A default configuration file is alsoc created ([Configuration](#configuration "Goto: Configuration")).
- For those wishing to transfer passwords from another manager or listing, see [Manually creating an archive](#manually-creating-an-archive "Goto: Manually creating an archive").

### Usage
Add or update a password for an apllication with the `-u` switch:
```
pwmgr -u application_name
```
A prompt will be given to enter the new password (just hit enter to have a password generated and copied to the clipboard).

To retrieve a password for an application, just use the application's name as an argument:
```
pwmgr application_name
```
By default, the first password found for that application will be copied to the clipboard.

Refer to  `pwmgr --help` for further options and usage notes.


### Configuration
During set-up, there are two main settings in `pwmgr_config` that you may wish to change. The format for each line of this file is
```
setting_name setting_value
```
(whitespace delimited).

1. `7z_application`. This is the name of the 7-Zip executable on your system, typically `7z`. The path to the executable may also be used if it is not on your path (e.g. `/usr/bin/7z`).
2. `pvault_dir` 

There mainl settings that you may wish to adjust during the initial 
- Add the full path to the `pvault` directory in `pwmgr_config`

### Manually creating an archive

#### Disclaimer

