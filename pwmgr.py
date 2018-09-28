# ~~~ Version 1.4 (Linux with xclip usage) ~~~
import getpass, secrets, string, subprocess
import logging, os, re, sys
logging.basicConfig(level=logging.WARNING, format='%(asctime)s:%(levelname)s: %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class PassManager:
	"""
	Class Variables
	---------------
	ALLOWED_OPTIONS : dictionary
		Each key is the full name of a possible command line option as: --key, and its value is the default for
		that option.
	ALLOWED_OPTIONS_WITH_PARAMETER : dictionary
		Each key is the full name of a possible command line option which must be followed by a single parameter as:
		--key parameter. Its value defines the default value of the parameter.
	CONFIG_FILE_NAME : string
		Name of configuration file (this must be in the same directory as this script.
	CONFIG_SETTINGS : dictionary
		Each key is the identifier (string) of a setting that may be set in CONFIG_FILE_NAME. Its value is the 
		default for that setting.
	HIDDEN_PRINT_COLOUR_ID : string
		Template ANSI escape sequence \u001b[38;5;{id}m' used to conceal passwords printed to the console.
		{id} runs from 0 to 255; 232-255 describes greys (black to white). Usage of this code is shell and/or
		terminal dependent.
	MIN_GENERATED_PWORD_LENGTH : int
		Minimum length of password that can be generated. It is not recommended to reduce this (see implementation in 
		self.generate_new_pword()). Note that there is no restriction on user entered passwords.
	MAX_GENERATED_PWORD_LENGTH : int
		Maximum length of password that can be generated.
	OPTION_ABBREVIATIONS : dictionary
		Each key is a possible short command line option; -key, and its value is the key of the option in 
		ALLOWED_OPTIONS or ALLOWED_OPTIONS_WITH_PARAMETER that key is an abbreviation of.
	PASSWORD_FILENAME : string
		Name of the password file in the archive.
	RESET_ANSI : string
		ANSI escape sequence used to reset all formatting (in particular, any foreground colour change).
	TIMEOUT : int
		Length of time to wait for 7z extraction and update commands to complete (None for no timeout).
	USAGE : string
		Message displayed with the --help option.
	VERSION : float
		Current version of this program.
	"""
	ALLOWED_OPTIONS = {'help':False, 'list':False, 'version': False}
	ALLOWED_OPTIONS_WITH_PARAMETER = {'set-archive':None, 'application_name':None, 'update':None, 'search':None,
		'new-archive':None}
	CONFIG_FILE_NAME = 'pwmgr_config'
	CONFIG_SETTINGS = {'archive_name':'', '7z_application':'7z', 'always_print':False, 'copy_to_selection':True,
	'logging_level':'WARNING', 'pvault_dir':'pvault', 'hidden_colour_visibility': 0.6, 'selection':'clipboard',
	'generated_password_length':15, 'check_new_password':True}
	HIDDEN_PRINT_COLOUR_ID = '\u001b[38;5;idm'
	MIN_GENERATED_PWORD_LENGTH = 8
	MAX_GENERATED_PWORD_LENGTH = 100
	OPTION_ABBREVIATIONS = {'h':'help','sa':'set-archive', 'u':'update', 's':'search', 'v':'version', 'n':'new-archive'}
	PASSWORD_FILENAME = 'passes'
	RESET_ANSI = '\u001b[0m'
	TIMEOUT = 5
	USAGE = """PWMGR

\u001b[1mNAME\u001b[21m
 	pwmgr - Store, access and generate passwords in a encrypted 7-Zip archive

\u001b[1mSYNOPSIS\u001b[21m
	pwmgr OPTION [ARGUMENT]

\u001b[1mOPTIONS\u001b[21m
	\x1B[3mapplication_name\x1B[23m
		Retrieves any passwords for \x1B[3mapplication_name\x1B[23m listed in the password file of the current archive.
		If the archive is password protected, a prompt will be given to enter the archive password. By default, the
		first password found is copied to the clipboard and, if multiple passwords are found, the user may choose
		to print them to the console. Relevant configuration settings include: \x1B[3mcopy_to_selection\x1B[23m, 
		\x1B[3mhidden_colour_visibility\x1B[23m and \x1B[3malways_print\x1B[23m.

	-h, --help
		Display this message and quit.

	-n, --new-archive \x1B[3marchive_name\x1B[23m
		Create a new archive with an empty password file inside the pvault directory. A prompt will be given to set
		a password for the archive (enter nothing for no password). If the archive_name setting is not already specified
		in pwmgr_config, it will be set to the newly created archive.

	-s, --search '\x1B[3mregular_expression\x1B[23m'
		Searches the list of application names in the password file using a pythonic regular expression (case insensitive).
		To avoid shell expansion, this should be placed in single quotes.

	-sa, --set-archive \x1B[3marchive_name\x1B[23m
		Choose which 7-Zip archive in the pvault directory to use. This sets the archive_name configuration setting
		in pwmgr_config.

	-u, --update \x1B[3mapplication_name\x1B[23m
		Update the password for \x1B[3mapplication_name\x1B[23m, or create a new entry if one does not already exist.
		A prompt will be given to enter the new password - enter nothing to have pwmgr generate a password for you
		(by default the generated password will be copied to the clipboard).

	-v, --version
		Print the version of the program and quit.

\u001b[1mSet-up\u001b[21m
	For initial set-up and additional information, please refer to https://github.com/piperfw/pwmgr/blob/master/README.md

\u001b[1mCONFIGURATION\u001b[21m
	Each line in pwmgr_config must have the following format (whitespace delimited):
	setting_name setting_value
	where setting_name is one of...
	archive_name
		The name of the encrypted 7-Zip archive in pvault_dir to be used by this program. This should contain a text
		file called \x1B[3mpasses\x1B[23m.
		Default: None (a prompt will be given to temporarily select one).

	7z_application
		The name or path to the 7z application.
		Default: 7z.

	always_print (True/False)
		If True, retrieved and generated passwords will always be printed to the console, without prompt.
		Default: False

	copy_to_selection (True/False)
		If True, xclip is used to copy the first password retrieved to the X selection specified by the selection setting
		(this also occurs when a new password is generated following use of the -u option).
		Default: True.

	logging_level
		The logging level used by the pwmgr.py script.
		Default: WARNING

	pvault_dir
		'pvault' if a directory called pvault is in the same directory as pwmgr.py. Otherwise, this should be the 
		\x1B[3mabsolute\x1B[23m path to the directory containing your encrypted archive(s).
		Default: pvault

	hidden_colour_visibility (0 - 1)
		How visible the text used to print retrieved passwords is. Varies from 0 (black) to 1 (white).
		Default: 0.6

	selection (primary/secondary/clipboard)
		The X selection to be used if copy_to_selection is True.
		Default: clipboard

	generated_password_length (int)
		The length of passwords generated by the program following use of the -u option. Must be at least 8 and no
		greater than 100.

	check_new_password (True/False)
		If True, when manually adding a new password you must enter it twice.
		Default: True."""
	VERSION = 1.4

	def __init__(self, options):
		# Options provided by command line arguments.
		self.options = options
		self.unset_options_to_defaults()
		# If help was passed as an argument, print the help message and exit.
		if self.options['help']:
			print(self.USAGE)
			return
		# Similarly for the version information (also archive creation below).
		if self.options['version']:
			print('pwmgr v{}.'.format(self.VERSION))
			return
		# self.config_dict holds settings loaded from config file (or their defaults).
		self.config_dict = {}
		self.config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), self.CONFIG_FILE_NAME))
		self.read_config_file()
		self.unset_config_settings_to_defaults()
		user_print_scale = float(self.config_dict['hidden_colour_visibility'])
		self.hidden_print_colour = self.HIDDEN_PRINT_COLOUR_ID.replace(
			'id', str(int(232+min(abs(23 * user_print_scale), 23))))
		# Set logging level according to setting in self.config_dict (default INFO).
		self.set_logging_level()
		if self.options['set-archive']:
			self.set_archive_save_to_config(self.options['set-archive'])
		# string to hold contents of self.PASSWORD_FILENAME extracted from the archive
		self.password_file_string = ''
		# Set to store names of all applications found in archive (repeats omitted)
		self.all_applications = set()
		# Empty list to store all passwords found for the parameter application_name (if not None).
		self.all_passes_retrieved = []
		# Initialise relevant absolute pathnames (7z, pvault_dir, archive and pvault_output_dir).
		self.abs_paths_init()
		# Create a new archive and exit, if requested.
		if self.options['new-archive']:
			self.make_new_archive()
			return
		# Check archive actually exists (gives user option to temporarily reassign archive_username if it doesn't)
		self.determine_archive()
		# Unless one of search, update or application_name options is set, functionality ends.
		if not any([self.options['search'], self.options['update'], self.options['application_name']]):
			return
		# Otherwise we must extract passwords from the archive, so get archive pword from user (empty if none).
		self.archive_pword = getpass.getpass(prompt='Enter password for {}: '.format(self.config_dict['archive_name']))
		# Extract self.PASSWORD_FILENAME in archive to self.password_file_string
		self.extract_archive_to_string()
		# Holds pattern (regex) compiled from command line parameter following the search option, if specified.
		self.user_regex_pattern = None
		# Set of application names for which self.user_regex_pattern produces a match. Remains empty if no pattern.
		self.search_results = set()
		if self.options['search']:
			self.set_user_regex_pattern()
		# Main functionality - handles password retrieval, regex searching and updating.
		self.parse_password_file_string()
		# Present passwords or (inclusive) search results according to user options.
		if self.options['application_name']:
			# Show passwords found for self.options['application_name'] in self.password_file_string
			self.present_passwords()
		if self.options['search']:
			self.present_search_results()

	def unset_options_to_defaults(self):
		"""Option values in self.options that were NOT provided by command line arguments are set to the default values
		given in self.ALLOWED_OPTIONS and self.ALLOWED_OPTIONS_WITH_PARAMTER.
		"""
		for option_name, default_value in self.ALLOWED_OPTIONS.items():
			if option_name not in self.options:
				self.options[option_name] = default_value
		for option_name, default_value in self.ALLOWED_OPTIONS_WITH_PARAMETER.items():
			if option_name not in self.options:
				self.options[option_name] = default_value

	def read_config_file(self):
		"""Read config file at self.config_file_path and store settings as key-value pairs in self.config_dict."""
		# If file doesn't exist, self.config_dict will be 'default initialised'	in self.unset_config_settings_to_defaults
		if not os.path.isfile(self.config_file_path):
			logger.info('{} not found in {}.'.format(self.CONFIG_FILE_NAME, os.path.dirname(self.config_file_path)))
			return
		with open(self.config_file_path, 'r') as cfg:
			for index, line in enumerate(cfg):
				line_num = index + 1
				stripped_line = line.strip()
				# Ignore empty lines
				if not stripped_line:
					continue
				try:
					# Split line on first whitespace (on Windows path names in settings may contain spaces)
					setting_id, setting_value = line.split(' ', 1)
					# setting_value is a string, which may or may not represent a boolean
					setting_value = setting_value.strip()
					# strings 'on'/'true' and 'off'/'false' (case insensitive) taken to mean True and False respectively
					if setting_value.lower() in {'on', 'true'}:
						setting_value = True
					elif setting_value.lower() in {'off', 'false'}:
						setting_value = False
					# Add setting to config_dict as key-value pair
					self.config_dict[setting_id] = setting_value
					# If ValueError on unpacking (< 2 elements after .split()), formatting is incorrect. Ignore line.
				except ValueError as err:
					logger.warning('Formatting error in line {} of {}. Ignoring line.'
						.format(line_num, self.CONFIG_FILE_NAME))
					continue

	def unset_config_settings_to_defaults(self):
		"""Keys present in self.CONFIG_SETTINGS but not self.config_dict are added to self.config_dict with values
		specified in self.CONFIG_SETTINGS."""
		for setting_id, setting_value in self.CONFIG_SETTINGS.items():
			if setting_id not in self.config_dict:
				self.config_dict[setting_id] = setting_value
				logger.debug('{} setting not found in {}. Assigning default value:{}.'.format(setting_id,
					self.CONFIG_FILE_NAME, setting_value))

	def set_logging_level(self):
		"""Set level according to self.config_dict['logging_level']. Prior, level as defined at top of this file."""
		try:
			lvl = getattr(logging, self.config_dict['logging_level'])
			logger.setLevel(lvl)
		except AttributeError as err:
			logger.warning('{} in {} is not a valid logging level. Setting logging level to logging.INFO'
				.format(self.config_dict['logging_level'], self.CONFIG_FILE_NAME))
			logger.setLevel(logging.INFO)

	def set_archive_save_to_config(self, new_archive_name):
		"""Save the parameter of the -sa option passed to the command line as the name of the archive for future
		retrievals, searches and updates."""
		self.config_dict['archive_name'] = new_archive_name
		self.write_config_file()
		print('Target archive set to {} (setting saved in {}).'.format(
			self.config_dict['archive_name'], self.config_file_path))

	def write_config_file(self):
		"""Write current contents of self.config_dict to self.config_file_path."""
		lines_to_write = []
		for setting_id, setting_value in self.config_dict.items():
			# Adhere to format of config file defined in the usage/help message.
			lines_to_write.append(' '.join([str(setting_id), str(setting_value)]))
		str_to_write = '\n'.join(lines_to_write)
		with open(self.config_file_path, 'w') as cfg:
			cfg.write(str_to_write)

	def make_new_archive(self):
		"""Create a new archive with an empty text file for use by this program. If self.config_dict['archive_name']
		is unset, set this to the new archive."""
		# If archive already exists, do not overwrite it
		new_archive_path = os.path.abspath(os.path.join(self.path_pvault_dir, self.options['new-archive']))
		if os.path.exists(new_archive_path):
			logger.error('{} already exists in {}. Please remove this or use a different archive name.'.format(
				self.options['new-archive'], self.path_pvault_dir))
			return
		# Get a master password for the new archive.
		new_archive_pword = self.get_new_pword(self.options['new-archive'])
		# 7z quirk - if archive name does not end in .7z this extension will be added.
		# End with . to ensure this does not occur.
		if not new_archive_path.endswith('.7z'):
			new_archive_path += '.'
		# Run a 7z process to create the new archive (cannot include this in self.subprocess_run_wrapper - see 
		# see note on subprocess usage in self.present_passwords).
		creation_args = ['7z', 'a', new_archive_path, '-si' + self.PASSWORD_FILENAME, '-mhe', '-p' + new_archive_pword]
		process = subprocess.Popen(creation_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			universal_newlines=True, stdin=subprocess.PIPE)
		try:
			# Immediately close stdin (7z waits for keyboard input ended by EOF).
			process.stdin.close() #7z now creates the archive
			# Wait for the process to terminate by itself for up to self.TIMEOUT seconds.
			process.wait(self.TIMEOUT)
			print('Archive {} created successfully.'.format(self.options['new-archive']))
		except subprocess.TimeoutExpired:
			error_message = '{} process failed to complete after {} seconds.'.format('Archive creation', self.TIMEOUT)
			if process.stderr:
				error_message += ' There were the following errors: {}'.format(process.stderr)
			error_message += 'Exiting.'
			logger.error(error_message)
		# self.config_dict['archive_name'] == '' by default
		if not self.config_dict['archive_name']:
			self.set_archive_save_to_config(self.options['new-archive'])
		else:
			logger.info('Did not set target archive to {} as \'archive_name\' setting already specified in {}.'.
				format(self.options['new-archive'], self.CONFIG_FILE_NAME))

	def abs_paths_init(self):
		"""Initialises a set of attributes corresponding to relevant path names for PassManager."""
		# Absolute paths to the 'pvault' directory and the contained (ensures script will work when run from anywhere 
		# in file system). N.B. If self.config_dict['pvault_dir'] == 'pvault', it is taken as a relative path
		# to this script
		if self.config_dict['pvault_dir'] == 'pvault':
			self.path_pvault_dir = os.path.join(os.path.dirname(__file__), self.config_dict['pvault_dir'])
		else:
			self.path_pvault_dir = os.path.abspath(self.config_dict['pvault_dir'])
		self.path_archive = os.path.abspath(os.path.join(self.path_pvault_dir, self.config_dict['archive_name']))
		# Do not use an absolute path for 7z, as this may simply be a name ('7z') on Unix systems.
		self.path_7z = self.config_dict['7z_application']

	def determine_archive(self):
		"""Check whether target archive exists. If not, prompt user to select from available archives or quit."""
		# Flag to indicate user has changed self.config_dict['archive_name'] (temporarily).
		# N.B. Current behaviour is to only assign the 'archive_name' temporarily (no call to self.write_config_file()).
		temp_change = False
		while True:
			# If archive exists no action is required.
			if os.path.exists(self.path_archive):
				logger.debug('Archive {} found.'.format(self.path_archive))
				if temp_change:
					logger.info('Make this choice permanent in ' + self.CONFIG_FILE_NAME + ' or using the -sa option.')
				return
			# Otherwise archive does not exist. 
			if not self.config_dict['archive_name']:
				# Archive doesn't exist because 'archive_setting' was not set in config.
				print('No archive set. Current files in pvault:')
			else:
				# 'archive_setting' set in config but not an actual archive.
				print('Archive {} not found. Current files in pvault:'.format(self.config_dict['archive_name']))
			# Print all .7z files in ./pvault/
			for filename in os.listdir(self.path_pvault_dir):
				# splitext[1] includes period ([0] gives filename).
				if os.path.splitext(filename)[1] == '.7z':
					print(filename)
			# Prompt user and set 'archive_name' setting to user's response unless the response is 'q'.
			print('Enter desired archive or q to quit:', end=' ')
			user_respose = input().strip()
			# Note: 'q' does not have a .7z extension so cannot be an archive.
			if user_respose == 'q':
				sys.exit(0)
			self.config_dict['archive_name'] = user_respose
			temp_change = True
			# Construct new path to be checked i next loop.
			self.path_archive = os.path.abspath(os.path.join(self.path_pvault_dir, self.config_dict['archive_name']))

	def extract_archive_to_string(self):
		"""Extract from the 7z archive self.path_archive the contents of the file self.PASSWORD_FILENAME and store in 
		self.password_file_string. The 7z application is used.
		N.B. The file itself is not extracted in the sense that a copy of the file is not created outside the archive.
		Removing self.PASSWORD_FILENAME would instead extract the contents of ALL files in the archive (possibly
		allow for this in the future).

		For the command line usage of the 7z program, see https://sevenzip.osdn.jp/chm/cmdline/
		"""
		# Arguments to be used in subprocess. Each element of list is passed to command line as its own string
		# Note, it is fine for self.archive_pword is an empty string (archive not password protected).
		extract_args = ['7z', 'e', self.path_archive, self.PASSWORD_FILENAME, '-so', '-p' + self.archive_pword]
		# Run a command described by extract_args assign output (the contents of self.PASSWORD_FILENAME) to 
		# self.password_file_string
		self.password_file_string = self.subprocess_run_wrapper(process_args=extract_args, process_name='Extraction')
		# If it is empty, then self.PASSWORD_FILENAME did not exist or was empty.
		if not self.password_file_string:
			logger.warning(
				'{} was empty or missing from {}.'.format(self.PASSWORD_FILENAME, self.config_dict['archive_name']))

	def subprocess_run_wrapper(self, process_args, process_input=None, process_name=''):
		"""Run a process described by process_args. Use process_input, if provided, capture any output and return 
		to caller. If there are errors or the process timesout (self.TIMEOUT), exit this program.

		For subprocess usage, see the official python docs and my subprocess_test.py testing script.
		"""
		try:
			# Run a command described by process_args and capture both stdout and stderr (not captured by default).
			# universal_newlines=True -> stdout and stderr will be text rather than bytes (this uses the io.TextIOWrapper 
			# default encoding). .run waits for the process to finish. timeout=self.TIMEOUT kills the process after 
			# self.TIMEOUT seconds and raises subprocess.TimeoutExpired.
			process = subprocess.run(process_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
				universal_newlines=True, timeout=self.TIMEOUT, input=process_input)
			# .run returns a subprocess.completed process object (see python docs on subprocess)
			logger.debug('{} process with arguments '.format(process_name) + '[' + ', '.join(process_args) + ']'
			+ ' completed with return code {}.'.format(process.returncode))
			# 7z will give error if password is incorrect.
			if process.stderr != '':
				print(process.stderr)
				sys.exit(1)
			return process.stdout
		except subprocess.TimeoutExpired:
			# Process was killed due to timeout expiring. Notify user and print any error.
			error_message = '{} process failed to complete after {} seconds.'.format(self.process_name, self.TIMEOUT)
			if process.stderr:
				error_message += ' There were the following errors: {}'.format(process.stderr)
			error_message += 'Exiting.'
			logger.error(error_message)
			sys.exit(1)

	def set_user_regex_pattern(self):
		"""Compile a regular expression pattern using the parameter passed to the command line following the -s
		option."""
		try:
			# Attempt to compile a pattern using user's query/expression
			self.user_regex_pattern = re.compile(self.options['search'].lower())
			# re.error is raised when a string passed to re.compile is not a valid regular expressions 
		except re.error as err:
			logger.error("{} is not a valid regular expression ({}). Exciting.".format(err.pattern, err.msg))
			sys.exit(1)

	def parse_password_file_string(self):
		"""Parse self.password_file_string, identifying application names and passwords in this string. In addition:

		if self.options['application_name'], store any passwords for self.options['application_name'] found in
		self.password_file_string in self.all_passes_retrieved. 

		if self.options['search'], store any matches for the regular expression pattern self.user_regex_pattern in
		self.search_results

		if self.options['update'], look for the appropriate line to which to insert a new password for the 
		application self.options['update']. When found, insert into a copy of self.password_file_string,
		and update the archive using this modified string via a call to self.update.

		See the usage message for the application_name pword syntax (i.e. format of selfPASSWORD_FILENAME).
		"""

		# Copy self.password_file_string and split this copy into a list of lines (i.e. split on '\n').
		# if self.options['update'], this list will be modified and used to update self.path_archive.
		# Slice is essential to perform a shallow copy (alternatively use .copy()), while keepends=True retains
		# any newline characters, so as to preserve any (arbitrary) formatting the user may have in the password file.
		self.lines_to_write = self.password_file_string[:].splitlines(keepends=True)
		# We only want to update the archive with a new password once, so keep track if it has been.
		# May be more appropriate to name this 'lines_to_write_modified' or similar.
		self.archive_updated = False
		# Strip leading/trailing whitespace characters from each line.
		stripped_lines = [line.strip() for line in self.password_file_string.splitlines(keepends=False)]
		# Iterate through stripped_lines, examining each line with non-whitespace characters
		for index, line in enumerate(stripped_lines):			
			line_num = index + 1  # Current line number is index plus 1
			# Ignore lines containing whitespace only (which are empty after .strip())
			# Note: Could alternatively have used stripped_lines = list(filter(None,stripped_lines)) 
			# (see https://stackoverflow.com/questions/3845423/remove-empty-strings-from-a-list-of-strings)
			if not line:
				# logger.debug('Line {} is blank.'.format(line_num))
				continue
			try:				
				# Split line on 1st whitespace for maximum of 2 strings. Note sep=None treats runs of consecutive 
				# whitespace are regarded as a single separator (assume pword does not begin with spaces).
				application_name, pword = line.split(sep=None, maxsplit=1) 
				# Update application set (use lowercase to avoid repeats with different case)
				self.all_applications.add(application_name.lower())
				# Strip trailing whitespace (inc. '\n') from pword - assumes that pword does not end with spaces,
				# spaces within pword allowed (due to sep=None in .split, we know there is no leading whitespace).
				pword = pword.strip()
				# If ValueError on unpack (fewer than 2 elements after .split()), the formatting of .txt is incorrect
			except ValueError as err:
				rel_path = os.path.relpath(os.path.join(self.config_dict['archive_name'], os.path.basename(file_to_search)))
				logger.warning('Formatting error in {}, line {}.'.format(rel_path, line_num))
				# Continue work with rest of file (the formatting of other lines may be fine
				continue 
			# Retrieval mode functionality
			if self.options['application_name']:				
				# See if application_name matches self.options['application_name']. Compare after .lower() to make
				# search case-insensitive. Could use re.fullmatch here.
				if application_name.lower() == self.options['application_name']:
					# Match found so append password to password list (now non-empty)
					self.all_passes_retrieved.append(pword)
					logger.debug('Password {} found for application {}.'.format(pword, application_name))
			# Search mode functionality
			if self.user_regex_pattern:
				# If match for self.user_regex_pattern found, add this application (lower case) to set self.search_results
				if re.search(self.user_regex_pattern, application_name.lower()):
					self.search_results.add(application_name.lower())
					logger.debug("Match for {} found in '{}'".format(self.user_regex_pattern, application_name.lower()))
			
			# Update mode functionality. 
			if self.options['update'] and not self.archive_updated:
				self.update_if_appropiate(index, application_name)

	def update_if_appropiate(self, index, application_name):
		"""Checks the alphabetical relation of self.options['update'] to application_name and inserts 
		an entry with self.options['update'] and a new password obtained from the user, if appropriate.
		
		If self.options['update'] should occur BEFORE application_name in an alphabetically ordered list,
		the new entry added one line above the entry for application name.
		If self.options['update'] matches application_name, the new entry replaces the old entry.
		In addition, if the final line has been reached, just append the new entry.

		N.B. It is essential that the archive is updated only once because a) Once we find the first application_name
		the new entry should appear before, the below if will be true for all application_names thereafter and b)
		once self.lines_to_write is modified, its indexing no longer matches that of stripped_lines in 
		self.parse_password_file_string().
		"""
		if application_name.lower() >= self.options['update'].lower() or index == len(self.lines_to_write) - 1:
			# Obtain new password from get_new_pword (which is also used to get archive pword)
			# self.options['update'] is used in the password prompt and the user may use the pword generator tool.
			new_pword = self.get_new_pword(self.options['update'], offer_to_generate_password=True)
			# Displayed to user to notify of success
			str_to_print = 'Password successfully added to archive'
			# Print and/or copy pword to X selection if appropriate.
			if self.config_dict['always_print'] and self.config_dict['copy_to_selection']:
				self.xclip_copy_to_selection(new_pword)
				str_to_print += '.\nYour new password for {} is:\n{}{}{}\nThis has been copied to {}.'.format(
					self.options['update'], self.hidden_print_colour, new_pword, self.RESET_ANSI, self.config_dict['selection'])
			elif self.config_dict['always_print']:
				str_to_print += '.\nYour new password for {} is:\n{}'.format(self.options['update'], new_pword)
			elif self.config_dict['copy_to_selection']:
				self.xclip_copy_to_selection(new_pword)
				str_to_print += ' (copied to {}).'.format(self.config_dict['selection'])
			# New entry to replace current application_name password (space delimited)
			new_entry = self.options['update'] + ' ' + new_pword + '\n'
			logger.debug('New entry to be added to {}: {}'.format(self.config_dict['archive_name'], new_entry.strip()))
			if application_name.lower() == self.options['update'].lower():
				self.lines_to_write[index] = new_entry
				logger.debug('Entry for {} overwritten with {} (line {}).'.format(application_name, new_entry[:-1], index + 1))
			elif application_name.lower() > self.options['update'].lower():
				self.lines_to_write.insert(index, new_entry)
			else:
				self.lines_to_write.append(new_entry)
			# Update the archive and notify user.
			self.update()
			print(str_to_print)
			# Set flag to ensure this function is never run again (see self.parse_password_file_string()).
			self.archive_updated = True

	def get_new_pword(self, name, offer_to_generate_password=False):
		"""Get new password from user for application self.to_update. Called by self.update_if_appropiate.

		Validation: Password must contain printable characters only and cannot begin or end with a space. 
		If self.config_dict['check_new_password'] is True, the user must enter the password twice.
		"""
		prompt_string = 'New password for {} '.format(name)
		if offer_to_generate_password:
			prompt_string += '(enter nothing to generate one): '
		else:
			prompt_string += '(q to quit): '
		new_pword = ''
		while True:
			user_response = getpass.getpass(prompt=prompt_string)
			if offer_to_generate_password and not user_response:
				return self.generate_new_pword()
			# Otherwise return prompt string to 'non-offer' mode and set offer_to_generate_password False so 
			# the user cannot accidentally generate a password on the next iteration with an empty input.
			offer_to_generate_password = False
			prompt_string = 'New password for {} (q to quit): '.format(name)

			user_response_stripped = user_response.strip()
			if user_response_stripped == 'q':
				sys.exit(0)
			# Check user input contains valid (printable) characters only (uses printable defined in the string module).
			if not all(char in string.printable for char in user_response_stripped):
				logger.debug('Password found to contain non-printable characters.')
				print('Password cannot contain non-printable characters.')
				continue
			# Don't allow user to enter password starting or ending with white-space
			if user_response != user_response_stripped:
				logger.debug('Leading or trailing spaces were stripped from user_input.')
				print('Password cannot begin or end with a space.')
				continue
			# User must enter the same password twice. This check is skipped when new_pword == '' (first iteration).
			if new_pword and self.config_dict['check_new_password'] and new_pword != user_response_stripped:
				print('Passwords do not match. Please retry.')
				# Possibly re-enable ability to generate password? (Would have to use a different flag/method).
				new_pword = ''
				continue
			# Update new_pword to be checked against the input in the next iteration.
			if not new_pword:
				new_pword = user_response_stripped
			else:
				# Finally, provide warning if password contains spaces (permissible for passwords in many applications)
				if ' ' in new_pword:
					logger.warning('Password found to contain one or more spaces (permitted).')
				return new_pword

	def generate_new_pword(self):
		"""Generate a password containing at least one uppercase character, lowercase character and digit. The length
		of the password is determined by self.config_dict['generated_password_length'], which must be between 
		self.MIN_GENERATED_PWORD_LENGTH and self.MAX_GENERATED_PWORD_LENGTH."""
		character_pool = string.ascii_letters + string.digits
		password_length = int(self.config_dict['generated_password_length'])
		# character_pool = string.ascii_letters + string.digits + string.ascii_lowercase # Skew slightly with lowercase (more readable).
		if not self.MIN_GENERATED_PWORD_LENGTH <= password_length <= self.MAX_GENERATED_PWORD_LENGTH:
			logger.warning('Value for \'generated_password_length\' is not permitted. ' 
				+ 'Using the default password length (15).')
			password_length = 15
		while True:
			# Taken from recipes on the page for the secrets module on the official docs
			# secrets is preferrable to using random (note: /dev/urandom is used as a seed).
		    password = ''.join(secrets.choice(character_pool) for i in range(password_length))
		    if (any(c.islower() for c in password)
		            and any(c.isupper() for c in password)
		            and sum(c.isdigit() for c in password) >= 3):
		        return password

	def update(self):
		"""Update password text file in user's archive with new password.

		Called by self.update_if_appropiate upon insert a new entry (application name + password) into
		self.lines_to_write (which was a copy of the content's of self.PASSWORD_FILENAME).
		The self.PASSWORD_FILENAME file is updated (or created) in the archive self.archive using the 7-zip program.

		This function should only be called once per running of this script (see N.B. in self.update_if_appropiate -
		the flag self.archive_updated is set to True here to enforce this).

		Before updating self.PASSWORD_FILENAME, a backup password file, self.PASSWORD_FILENAME + '.bak', is created
		using self.password_file_string. This is deleted if the update occurs successfully. Note that the 7z -u 
		switch does not appear to accommodate stdin (this can be used to update a file in the archive if it is 
		found to be older than file to be added, for example) (note the -ao overwrite switch applies during extraction
		[to file] only).
		"""
		# Quirk of 7z - if the file ending is not .7z or ., the .7z extension will be appended when updating.
		# (See note in self.make_new_archive()).
		if not self.path_archive.endswith('.7z'):
			# Do this AFTER extracting from the archive!
			self.path_archive += '.'
		# Create list of arguments to be used to call 7z from CL. Note -mhe encrypts file headers (i.e. name of files).
		stdin_arg = '-si' + self.PASSWORD_FILENAME
		update_args = [self.config_dict['7z_application'], 'u', self.path_archive, stdin_arg, '-mhe', '-p' + self.archive_pword]
		# String written to self.PASSWORD_FILENAME (self.lines_to_write is a list of strings)
		str_to_write = ''.join(self.lines_to_write)
		# Backup the password file.
		self.backup_password_file()
		# Process to update the archive (we don't need the output - there shouldn't be any).
		self.subprocess_run_wrapper(process_args=update_args, process_input=str_to_write, process_name='Update')
		# Update was successful (subprocess_run_wrapper sys.exit(1) otherwise), so remove the backup.
		self.remove_backup_password_file()

	def backup_password_file(self):
		"""Create a backup password file, self.PASSWORD_FILENAME + '.bak', using the original contents of 
		self.PASSWORD_FILENAME,	self.password_file_string. Note: Don't simply make a copy of the archive, in case
		it is very large."""
		stdin_arg = '-si' + self.PASSWORD_FILENAME + '.bak'
		backup_args = [self.config_dict['7z_application'], 'u', self.path_archive, stdin_arg, '-mhe', '-p' + self.archive_pword]
		self.subprocess_run_wrapper(
			process_args=backup_args, process_input=self.password_file_string, process_name='Backup')

	def remove_backup_password_file(self):
		"""Delete self.PASSWORD_FILENAME + '.bak' from the user's archive. Called if self.PASSWORD_FILENAME was
		successfully updated."""
		delete_args = [self.config_dict['7z_application'], 'd', self.path_archive, self.PASSWORD_FILENAME + '.bak', '-p' + self.archive_pword]
		self.subprocess_run_wrapper(
			process_args=delete_args, process_input=self.password_file_string, process_name='Removal of backup')

	def present_passwords(self):
		"""Present result of password search in archive to user.

		- If >=1 password is found, the first is copied to the clipboard if self.config_dict['copy_to_selection']
		- If >1 password is found, all found passwords may be printed to console with a hidden colouring.
		- If 1 password found and not self.config_dict['copy_to_selection'], the password is printed with a 
		'hidden' colouring.
		- If no passwords are found, the user is notified and asked if wants to view full list of applications.
		"""
		logger.debug('All passwords retrieved: {}.'.format(self.all_passes_retrieved))
		# If no passwords were found (self.all_passes_retrieved empty) notify user and offer to print application set
		if not self.all_passes_retrieved:
			print('No passwords found for {}.'.format(self.options['application_name']))
			self.print_all_applications()
			return
		if self.config_dict['copy_to_selection']:
			# Run xclip to copy first password found to X selection self.config_dict['selection']
			self.xclip_copy_to_selection(self.all_passes_retrieved[0])
		# If >1 password found, prompt user if they want them listed.
		if len(self.all_passes_retrieved) > 1:
			# Additional comment added to string if copy_to_selection setting on
			string_extension = (' (first one coped to {})'
				.format(self.config_dict['selection']) if self.config_dict['copy_to_selection'] else '')
			print('{} passwords found for {}{}.'
				.format(len(self.all_passes_retrieved), self.options['application_name'], string_extension))
			# if always_print toggle is on, print all passwords without prompting user
			if not self.config_dict['always_print']:				
				print('Hit Enter to display all passwords or enter anything to quit.', end=' ')
			# If user just hits Enter (i.e. Enters an empty string) then input() returns '' (falsy).
			# Note: This conditional short-circuits if self.config_dict['always_print'] is True.
			if self.config_dict['always_print'] or not input():
				print('Passwords found for {}:'.format(self.options['application_name']))
				# Print all found pwords to console
				for pword in self.all_passes_retrieved:
					print(self.hidden_print_colour + pword + self.RESET_ANSI)
		else:
			string_extension = ' and copied to {}'.format(self.config_dict['selection']) if self.config_dict['copy_to_selection'] else ''
			print('1 password found for {}{}.'.format(self.options['application_name'], string_extension))
			# Note: If not copying to clipboard must now print pword otherwise user has no means of accessing it!
			if self.config_dict['always_print'] or not self.config_dict['copy_to_selection']:
				print(self.hidden_print_colour + self.all_passes_retrieved[0] + self.RESET_ANSI)

	def xclip_copy_to_selection(self, string_to_copy):
		"""Run an xclip process to send string_to_copy to the X selection given by self.conf_dict['selection']."""
		# Verify self.config_dict['selection'] is a valid X selection & assign to 'primary' if it isn't.
		if self.config_dict['selection'] not in ['primary', 'secondary', 'clipboard']:
			# self.config_dict['selection'] is changed below (but not saved), so this warning will only appear once
			# per runtime
			logger.warning('{} is not a valid xclip selection - default (primary) will be used).'.format(
				self.config_dict['selection']) + ' Please change or remove the value in {}'.format(
				self.CONFIG_FILE_NAME))
			self.config_dict['selection'] = 'primary'
		xclip_args = ['xclip', '-sel', self.config_dict['selection']]
		# Have to use the Popen constructor directly (this is created by subprocess.run normally) as need to be
		# able to write directly to stdin AND close it: The 'input' parameter or subporocess.run is equivalent
		# to calling subprocess.Popen and then process.communicate(), which WAITs for the process to finish. 
		# However, xclip will hang until EOF, so the stdin needs to be closed after sending the input! 
		# Using .close() after .write seems the only and best way to do this, although the docs recommend using 
		# communicate() where possible. Possibly should just use Popen in self.subprocess_run_wrapper().
		# OR RENAME self.subprocess_run_wrapper to self.run_7z....
		process = subprocess.Popen(xclip_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
		universal_newlines=True, stdin=subprocess.PIPE)
		try:
			# Write string_to_copy to stdin and then immediately close the stream (xclip waits for EOF).
			process.stdin.write(string_to_copy)
			process.stdin.close() # xclip now copies stdin to clipboard
			# Wait for the process to terminate for up to self.TIMEOUT seconds. If it is still running after this,
			# raise TimeoutExpired. Note: If the process terminates before then (xclip should take a fraction of
			# a second), we do not have to wait for the timeout to finish!
			process.wait(self.TIMEOUT)
		except subprocess.TimeoutExpired:
			error_message = '{} process failed to complete after {} seconds.'.format('xclip', self.TIMEOUT)
			if process.stderr:
				error_message += ' There were the following errors: {}'.format(process.stderr)
			error_message += 'Exiting.'
			logger.error(error_message)

	def print_all_applications(self):
		"""Optionally print list of all applications found in self.PASSWORD_FILENAME of archive."""
		# Prompt user only if always_print toggle is False
		if not self.config_dict['always_print']:
			print('Hit Enter to display all application names for which passwords were found or enter anything to '
				'quit.', end=' ')
		if self.config_dict['always_print'] or not input():
			print('Applications with passwords in {}:'.format(self.config_dict['archive_name']))
			# sorted() returns an ordered list of the elements of an iterable (wish to print in alphabetical order)
			sorted_applications = sorted(self.all_applications) 
			for application_name in sorted_applications:
				print(application_name)

	def present_search_results(self):
		"""Present result of regular search of application names in archive. Passwords are not shown."""
		logger.debug('Search result set: {}.'.format(self.search_results))
		if not self.search_results:
			print("Case-insensitive search with regular expression '{}'' returned no matches in {}."
				.format(self.options['search'], self.config_dict['archive_name']))
			# Offer just to print all applications in consolation.
			self.print_all_applications()
			return
		print('Applications in {} returning a match in a case-insensitive search with regular expression \'{}\':'
			.format(self.config_dict['archive_name'], self.options['search']))
		for application_name in self.search_results:
			print(application_name)

def main():
	# Remove first sys.argv, which is always pwmgr.py.
	del sys.argv[0]
	# List to hold options (command line arguments) provided by user.
	options = {}
	# Default behaviour (no option) is --help
	if len(sys.argv) == 0:
		sys.argv.append('--help')
		# If no hyphen (switch prefix), first parameter is the name of the application for which a password is wanted.
	if not sys.argv[0].startswith('-'): # Could use regex
		options['application_name'] = sys.argv[0]
		# Remove from list so not encountered in following loop
		del sys.argv[0]
	while sys.argv:
		arg = sys.argv.pop(0)
		# No problem with .startswith() or slice if string is empty (arg[0] would fail though)
		stripped_arg = arg.strip('-')
		if arg.startswith('-') and stripped_arg in PassManager.OPTION_ABBREVIATIONS:
			arg = '-' + arg
			stripped_arg = PassManager.OPTION_ABBREVIATIONS[stripped_arg]
		if arg.startswith('--') and stripped_arg in PassManager.ALLOWED_OPTIONS:
			options[stripped_arg] = True
		elif arg.startswith('--') and stripped_arg in PassManager.ALLOWED_OPTIONS_WITH_PARAMETER:
			try:
				# Next argument should be a 'parameter' for the option
				options[stripped_arg] = sys.argv.pop(0)
			except IndexError:
				print('The {} option requires a parameter.'.format(arg.strip('-')))
				sys.exit(1)
		else:
			print('Invalid argument. See -h or --help for usage.')
			sys.exit(1)
	# Create anonymous PassManager object. All functionality is dictated by options and occurs from __init__().
	PassManager(options)

if __name__ == '__main__':
	main()
