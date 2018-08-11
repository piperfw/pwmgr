# pwmgr
Simple password manager based on the 7-Zip program

### Description
`pwmgr.py` manages an encrypted `.7z` archive containing a text file. Passwords are stored in and retrieved from this file. A master password must be entered to access the archive.

### Requirements
- 7-Zip Command Line Version
- python3 (3.6+)
- xclip (for X selection use)

### Set-up
- Place `pwmgr.py` and the empty `pvault` directory in the same directory.
- (Optional): Create a bash alias such as `pwmgr="python full_path_to_pwmgr.py"` to easily invoke the script from any bash shell with `pwmgr...` (otherwise replace `pwmgr` with `python full_path_to_pwmgr.py` in the following code).
- Create a _new_ 'user' with `pwmgr -n username`. This invokes the 7-Zip executable to create a `.7z` archive called `username` in the `pvault` directory. You will be prompted to enter a password for the archive, which acts as the master password for the manager. A default configuration file is also created ([Configuration](#configuration "Goto: Configuration")).
- For those wishing to transfer passwords from another manager or listing, see [Manually creating an archive](#manually-creating-an-archive "Goto: Manually creating an archive").

### Usage
Add or update a password for an application with the `-u` switch:
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
During set-up, there are two main settings in `pwmgr_config` that you may wish to change. The format for each line of this file is `setting_name setting_value` (whitespace delimited).

1. `7z_application` (Default: `7z`). This is the name of the 7-Zip executable on your system, typically `7z`. The path to the executable may also be used if it is not on your path (e.g. `/usr/bin/7z`).
2. `pvault_dir` (Default: `pvault`). If you wish to place the `pvault` directory anywhere other than alongside `pwmgr.py`, or use a different directory name, change this to the _absolute path_ to the directory.

For a description of all available settings, view `pwmgr --help`.

### Manually creating an archive
`pwmgr` works by writing passwords to a text file called `passes` stored within the encrypted archive. Similar to the configuration file, the format of each line `passes` is a pair of fields separated by whitespace, this time describing an application's name and the associated password:
```
application_name application_password
```
The line is split on the first whitespace, so `application_name` cannot contain spaces.

In order to create an archive that can be used by `pwmgr` containing existing password, simply create a file called `passes` with this syntax and add it to a password protected `.7z` archive using the 7-Zip program using, for example,
```
7z a archive_name. passes -parchive_password -mhe
```
(the period trailing `archive_name` prevents `7z` from appending the `.7z` extension which you may or may not want).

This archive must be placed in the `pvault` directory (or whichever directory is specified in `pwmgr_config`).

In order to get `pwmgr` to point to your new archive, use
```
pwmgr -sa archive_name
```
Equivalently, change the value the `archive_name` setting in `pwmgr_config`.


### Planned features
- Option to use xsel instead of xclip
- Windows port using the pyclip python package

##### Disclaimer
This program was written for fun. I cannot advise using it to store passwords for accounts other than those that are absolutely expendable. In particular, please do _not_ rely on the password generator tool included with the script to create a secure password (its randomness is only as good as your system's `os.urandom()` implementation).


