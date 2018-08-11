# pwmgr
Simple password manager using the 7-Zip program

### Description
`pwmgr.py` manages an encrypted `.7z` archive containing a text file. Passwords are stored in and retrieved from this file. A master password must be entered to access the archive.

### Requirements
- 7-Zip Command Line Version
- python3 (3.6+)
- xclip (for X selection use)

### Set-up
- Ensure `pwmgr.py` and `pwmgr_config` are in the same directory, and that the (empty) `pvault` directory exists somewhere on your filesystem with read and write permissions.
- (Optional): Create a bash alias such as `pwmgr="python full_path_to_pwmgr.py"` to easily invoke the script from any shell with `pwmgr...` (otherwise replace `pwmgr` with `python full_path_to_pwmgr.py` in any code below).


