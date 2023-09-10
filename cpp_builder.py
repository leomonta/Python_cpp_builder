#!/usr/bin/env python3
# Building tool for compiling projects source files (maily c/c++)
# @Author Leonardo Montagner https://github.com/leomonta/Python_cpp_builder
#
# Done: compile and link files
# Done: check for newer version of source files
# Done: skip compilation or linking if there are no new or modified files
# Done: check for newer version of header files (check in every file if that header is included, if it has to be rebuilt)
# Done: if a config value is empty prevent double space in cmd agument
# Done: add a type config value for gcc | msvc so i can decide which cmd args to use -> -o | -Fo
# Done: add specific linker exec
# Done: use compiler exec if no linker exec is present
# Done: multithreaded compiling
# Done: error and warning coloring in the console
# Done: if error occurs stop compilation and return 1
# Done: if error occurs stop linking and return 1
# Done: retrive include dirs, libs and args from a file
# Done: retrive target directories for exe, objects, include and source files
# Done: support for debug and optimization compilation, compiler flag and libraries
# Done: support for pre and post script
# Done: support support for any names profile
# Done: implicit empty profile if none is specified
# Done: refactor out global variables (except constants)
# TODO: implicit empty configuration if no config file is foun
# TODO: better setting parsing

import subprocess # execute command on the cmd / bash / whatever
import os         # get directories file names
import json       # parse cpp_builder_config.json
import hashlib    # for calculating hashes
import threading  # for threading, duh
import time       #time.sleep
import sys        # for arguments parsing


CONFIG_FILENAME = "cpp_builder_config.json"
HASH_FILENAME = "files_hash"

DEFAULT_COMPILER = "gcc"

DEFAULT_PROFILE = {
    "libraries_names": [],
    "libraries_dirs": [],
    "compiler_args": "",
    "linker_args": ""
}

SPINNERS: list[str] = ["|", "/", "-", "\\"]

SOURCE_FILES_EXTENSIONS: list[str] = ["c", "cpp", "cxx", "c++", "cc", "C", "s", "rs"]

COMPILER_SPECIFIC_ARGS: list[dict[str]] = [
    {
        "compile_only": "-c",
        "output_compiler": "-o ",
        "output_linker": "-o ",
        "object_extension": "o",
        "include_path": "-I",
        "library_path": "-L",
        "library_name": "-l",
        "force_colors": "-fdiagnostics-color=always",
    }, {
        "compile_only": "/c",
        "output_compiler": "/Fo",
        "output_linker": "/OUT:",
        "object_extension": "obj",
        "include_path": "/I",
        "library_path": "/LIBPATH:",
        "library_name": "",
        "force_colors": "",
    }, {
        "compile_only": "--crate-name",
        "output_compiler": "-o ",
        "output_linker": "-o ",
        "object_extension": "o",
        "include_path": "",
        "library_path": "-L",
        "library_name": "-l",
        "force_colors": "",
    }
]

COMPILATION_STATUS_COMPILING = 0
COMPILATION_STATUS_DONE = 1
COMPILATION_STATUS_FAILED = 2


class COLS:

	FG_BLACK = "\033[30m"
	FG_RED = "\033[31m"
	FG_GREEN = "\033[32m"
	FG_YELLOW = "\033[33m"
	FG_BLUE = "\033[34m"
	FG_MAGENTA = "\033[35m"
	FG_CYAN = "\033[36m"
	FG_WHITE = "\033[37m"

	BG_BLACK = "\033[40m"
	BG_RED = "\033[41m"
	BG_GREEN = "\033[42m"
	BG_YELLOW = "\033[43m"
	BG_BLUE = "\033[44m"
	BG_MAGENTA = "\033[45m"
	BG_CYAN = "\033[46m"
	BG_WHITE = "\033[47m"

	FG_LIGHT_BLACK = "\033[90m"
	FG_LIGHT_RED = "\033[91m"
	FG_LIGHT_GREEN = "\033[92m"
	FG_LIGHT_YELLOW = "\033[93m"
	FG_LIGHT_BLUE = "\033[94m"
	FG_LIGHT_MAGENTA = "\033[95m"
	FG_LIGHT_CYAN = "\033[96m"
	FG_LIGHT_WHITE = "\033[97m"

	BG_LIGHT_BLACK = "\033[100m"
	BG_LIGHT_RED = "\033[101m"
	BG_LIGHT_GREEN = "\033[102m"
	BG_LIGHT_YELLOW = "\033[103m"
	BG_LIGHT_BLUE = "\033[104m"
	BG_LIGHT_MAGENTA = "\033[105m"
	BG_LIGHT_CYAN = "\033[106m"
	BG_LIGHT_WHITE = "\033[107m"

	RESET = "\033[0m"


PROGRRESS_PREFIXES: list[str] = ["|", "+", "-"]
PROGRESS_STATUS: list[str] = [f"{COLS.FG_BLUE}Processing", f"{COLS.FG_GREEN}Done", f"{COLS.FG_RED}Failed"]


def get_value(dict: any, key: str, val="") -> dict | str:
	"""
	Tries to get the desired value from the dict, if fails returns val
	"""
	try:
		return dict[key]
	except:
		return val


def get_compilation_status(item: dict[str], tick: int = 0) -> str:

	# the first element is the spinner, takes up 1 char
	# the second is the name of the file being compiled, this should take at max 20 char
	# the last should be the textual status of compilation, it should start after the 20 chars of the name
	# / utils.cpp Compiling

	curr_spinner = SPINNERS[tick % len(SPINNERS)]

	print
	prefix: str = f" " + PROGRRESS_PREFIXES[item["result"]] + " "
	suffix: str = " " + PROGRESS_STATUS[item["result"]]

	if item["result"] == 0:                 # Still compiling
		prefix = f" {curr_spinner} "
		suffix += "." * ((tick % 12) // 4 + 1) # makes the dots progress 1/4 the speed of the spinner

	# fill the string with spaces until 20 and truncate the string if longer than that
	name = item["name"].ljust(20)[:20]

	return prefix + COLS.FG_LIGHT_BLACK + name + suffix + COLS.RESET


def print_progress(statuses: list[dict]) -> None:
	"""
	Wait for the given process status be completed and prints its status in the meantime
	Returns when all the processes are done or failed
	"""

	GO_UP = "\x1b[1A"
	CLEAR_LINE = "\x1b[2K"

	# Animation state
	tick = 0
	while True:
		# How many lines to print at the same time
		num_lines = len(statuses)

		# Check if every process is done
		all_done = True
		for item in statuses:

			print(get_compilation_status(item, tick))
			if item["result"] == 0:
				# If someone is still compiling keep looping
				all_done = False

		if all_done:
			break

		# Go up 1 line at the time and clear it
		for i in range(num_lines):
			print(GO_UP, end=CLEAR_LINE)

		# how quickly to refresh the printing
		time.sleep(0.15)
		tick += 1


def print_report(statuses: list[dict]) -> None:
	"""
	Prints the report for every status there is in statuses
	"""

	for item in statuses:
		cmd = item["command"]
		name = item["name"].ljust(20)[:20]
		print(f" {name}{COLS.FG_LIGHT_BLACK} {cmd}{COLS.RESET}\n")

		# print stdout and stderr only if there is something to print

		if item["output"] != "":
			print(COLS.FG_LIGHT_BLUE, "    out", COLS.RESET, ":\n", item["output"], sep="")

		if item["errors"] != "":
			print(COLS.FG_LIGHT_RED, "    err", COLS.RESET, ":\n", item["errors"], sep="")


def compile_and_command(compilation_targets: list[str], settings: dict) -> None:
	"""
	calls compile()

	print compilation status

	calls link() if compilation was fine
	"""

	# --- Compiling ---

	print("\n", COLS.FG_GREEN, " --- Compiling ---", COLS.RESET)

	# where the status of the different compilations is stored
	compilations: list[dict] = []
	# compile each file and show the output,
	# and check for errors
	compile(compilation_targets, settings, compilations)

	print_progress(compilations)
	print("")
	print_report(compilations)
 
	compilation_failed: bool = False

	for item in compilations:
		if item["result"] == COMPILATION_STATUS_FAILED: # Failure
			compilation_failed = True


	# all compilations done, linking
	if compilation_failed:
		print(f"\n{COLS.FG_RED} --- Linking skipped due to errors in compilation process! ---")
		sys.exit(2)

	# cleaning prev compilation data
	compilations.clear()

	# --- Linking ---

	print("\n", COLS.FG_GREEN, " --- Linking ---", COLS.RESET)

	link_status = {
	    "result": COMPILATION_STATUS_COMPILING,
	    "name": "",
	    "output": "",
	    "errors": "",
	    "command": ""
	}

	# Link starts a thread, no need to check anything from him
	link(compilation_targets, settings, link_status)

	print_progress([link_status])

	print("")

	# print
	print_report([link_status])

	if link_status["result"] == COMPILATION_STATUS_FAILED:
		print(f"\n{COLS.FG_RED} --- Errors in linking process! ---")
		sys.exit(3)


def get_profile(args: list[str]) -> str:
	try:
		return args[args.index("-p") + 1]
	except IndexError:
		# default profile
		return "empty"


def parse_file_path(filename: str) -> tuple[str, str, str] | None:
	# i need to differentiate different parts
	# extension: to decide if it has to be compiled or not and to name it
	# filename: everything else of the file name ignoring the extension, useful for naming compilitation files
	# source dir: necessary for differentiate eventual same-named files on different dirs

	# get file extension
	ext_pos = filename.rfind(".")
	filename_wo_extension = filename[:ext_pos]
	file_extension = filename[ext_pos + 1:]

	# get filename and relative source dir
	path: list[str] = filename_wo_extension.split("/")
	file_name: str = path[-1]
	full_directory: str = "/".join(path[:-1])

	return (full_directory, file_name, file_extension)


def get_includes(file: str) -> list[str]:

	founds: list[str] = []
	# org_path: str = parse_file_path(file)[0]
	with open(file, "r") as fp:
		line: str
		l_no: int
		for l_no, line in enumerate(fp):

			if "#include" in line:

				# first " delimiter
				first_deli = line.find("\"") + 1
				# second " delimiter
				second_deli = line[first_deli:].find("\"")

				if first_deli > 0:
					incl = line[first_deli:second_deli + first_deli]
					founds.append(incl)

	return founds


def exe_command(command: str, status: dict) -> int:
	"""
	execute the given command, set the ouput and return code to the correct structure
	"""

	stream = subprocess.Popen(command.split(" "), stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

	out, err = stream.communicate() # execute the command and get the result

	ret = COMPILATION_STATUS_DONE
	if stream.returncode != 0: # the actual program return code, 0 is ok
		ret = COMPILATION_STATUS_FAILED

	status["output"] = out
	status["errors"] = err
	status["result"] = ret

	return ret


def parse_config_json(profile: str) -> int:
	"""
	Set the global variables by reading the from cpp_builder_config.json
	the optimization argument decide if debug or release mode
	"""

	settings: dict[str, any] = {
	                              # name of the compiler and linker executable
	    "compiler": "gcc",
	    "linker": "gcc",

	                              # compiler and linker args
	    "cargs": "",
	    "largs": "",

	                              # output, includes, filenames swithces (/Fo -o) for msvc, clang, and gcc
	    "specifics": {},

	                              # path and name of the final executable
	    "exe_path_name": "",

	                              # base directory of the project
	    "project_path": "",

	                              # the string composed by the path of the includes -> "-I./include -I./ext/include -I..."
	    "includes": "",

	                              # list of all the includes as they appear in the config file
	    "raw_includes": [],

	                              # directory where to leave the compiled object files
	    "objects_path": "",

	                              # directories containing the names of the source directories
	    "source_files": [],

	                              # the string composed by the names of the libraries -> "-lpthread -lm ..."
	    "libraries_names": "",

	                              # the string composed by the path of the libraries -> "-L./path/to/lib -L..."
	    "libraries_paths": "",

	                              # name of the scripts to execute
	    "scripts": {}
	}

	# load and parse the file
	config_filename = "cpp_builder_config.json"
	if os.path.isfile(config_filename):
		config_file = json.load(open(config_filename))
	else:
		print(COLS.FG_YELLOW, f"[WARNING]{COLS.FG_LIGHT_RED} Config file \"{config_filename}\" not found", COLS.RESET)
		return dict

	del config_filename

	# --- Scripts settings ---
	settings["scripts"] = get_value(config_file, "scripts", {})

	# --- Compiler settings ---
	# get the compiler executable (gcc, g++, clang, rustc, etc)
	# and the linker executable, plus the type (needed for cli args)

	compiler_settings = get_value(config_file, "compiler")

	settings["compiler"] = get_value(compiler_settings, "compiler_exe", DEFAULT_COMPILER)

	temp = get_value(compiler_settings, "compiler_style", DEFAULT_COMPILER)

	# 0 gcc / clang
	# 1 msvc
	# 2 rust
	compiler_type: int = 0

	if temp == "gcc":
		compiler_type = 0
	elif temp == "clang":
		compiler_type = 0
	elif temp == "msvc":
		compiler_type = 1
	elif temp == "rustc":
		compiler_type = 2

	del temp

	settings["specifics"] = COMPILER_SPECIFIC_ARGS[compiler_type]

	del compiler_type

	# if no linker is specified use the compiler executable
	settings["linker"] = get_value(compiler_settings, "linker_exe", settings["compiler"])

	del compiler_settings

	#
	# --- Directories settings ---
	#
	# Where is the project
	# where are the source files and the include files

	directories_settings = get_value(config_file, "directories")

	# base directory for ALL the other directories and files
	settings["project_path"] = get_value(directories_settings, "project_dir", "./")

	# name of the final executable
	settings["exe_path_name"] = get_value(directories_settings, "exe_path_name", "a.out")

	targets: list[str] = []

	old_dir: str = os.getcwd()
	os.chdir(settings["project_path"])

	for sdir in get_value(directories_settings, "source_dirs", ["src"]):
		for path, subdirs, files in os.walk(sdir):
			for name in files:
				targets.append(f"{path}/{name}")

	os.chdir(old_dir)

	del old_dir, path, subdirs, files, name, sdir

	settings["source_files"] = targets

	del targets

	# create the includes args -> -IInclude -ISomelibrary/include -I...
	for Idir in get_value(directories_settings, "include_dirs", ["include"]):
		settings["raw_includes"].append(Idir)
		settings["includes"] += " " + settings["specifics"]["include_path"] + Idir

	del Idir

	settings["objects_path"] = get_value(directories_settings, ["temp_dir"], "obj")

	# ----- Profiles -----

	del directories_settings

	profile_settings = get_value(config_file, profile, DEFAULT_PROFILE)

	# --- Libs ---
	# create the library args -> -lSomelib -lSomelib2 -l...
	for lname in get_value(profile_settings, "libraries_names", DEFAULT_PROFILE["libraries_names"]):
		settings["libraries_names"] += " " + settings["specifics"]["library_name"] + lname

	# cant be sure if it has been created
	# del lname

	# create the libraries path args -> -LSomelibrary/lib -L...
	for ldname in get_value(profile_settings, "libraries_dirs", DEFAULT_PROFILE["libraries_dirs"]):
		settings["libraries_paths"] += " " + settings["specifics"]["library_path"] + ldname

	# cant be sure if it has been created
	# del ldname

	# --- Compiler an Linker arguments ---
	settings["cargs"] = get_value(profile_settings, "compiler_args", DEFAULT_PROFILE["compiler_args"])
	settings["largs"] = get_value(profile_settings, "linker_args", DEFAULT_PROFILE["linker_args"])

	# fix for empty args
	if settings["cargs"]:
		settings["cargs"] = " " + settings["cargs"]

	if settings["largs"]:
		settings["largs"] = " " + settings["largs"]

	return settings


def to_recompile(filename: str, old_hashes: dict, new_hashes: dict, env="") -> bool:
	"""
	Given a filename return if it needs to be recompiled
	A source file needs to be recompiled if it has been modified
	Or an include chain (God help me this shit is recursive) has been modified
	"""

	# collect all of the includes here
	includes: list[str]

	# I need to find the actual path of the file
	# try only the includes dirs given in the config file

	includes_directories = [".", ""]

	# have to do this cus cannot append([]) or extend(str)
	if isinstance(env, str):
		env = [env]

	includes_directories.extend(env)
	curr = filename

	for dir in includes_directories:
		fullname: str = dir + "/" + curr
		if os.path.isfile(fullname):
			curr = fullname
			break

	if curr in old_hashes:
		if old_hashes[curr] != new_hashes[curr]:
			return True
	else:
		new_hashes[curr] = make_new_file_hash(curr)
		return True

	# the file is known but not modified
	# check the includes

	for inc in get_includes(curr):
		add_incl = [parse_file_path(curr)[0]]
		add_incl.extend(env)

		if to_recompile(inc, old_hashes, new_hashes, add_incl):
			return True

	return False


def make_new_file_hash(file: str) -> str:
	"""
	Calculate the hash for the given file an puts it in the new_hashes file
	"""
	# i need to re-instantiate the object to empty it
	sha1 = hashlib.sha1()

	# sha1 hash calculation
	with open(file, "rb") as f:
		sha1.update(f.read())

	return sha1.hexdigest() # create the new hash


def calculate_new_hashes(old_hashes: dict, new_hashes: dict) -> None:
	"""
	Calculate the hashes for all the source files
	"""

	for file in old_hashes: # loop trough every file of each directory

		new_hashes[file] = make_new_file_hash(file)


def load_old_hashes() -> dict[str, str]:
	"""
	Load in old_hashes the hashes present in files_hash
	"""
	hashes: dict[str, str] = {}

	# read hashes from files and add them to old_hashes array
	with open(HASH_FILENAME, "r") as f:
		while True:
			data = f.readline()
			if not data:
				break
			temp = data.split(":")

			# remove trailing newline
			temp[1] = temp[1].replace("\n", "")
			hashes[temp[0]] = temp[1]

	return hashes


def get_to_compile(source_files: list[str], old_hashes: dict, new_hashes: dict, add_incl: list[str]) -> list[str]:
	"""
	return a list of files and their directories that need to be compiled
	"""

	to_compile: list[tuple[str, str, str]] = [] # contains directory and filename

	# checking which file need to be compiled
	file: str = ""
	for file in source_files: # loop trough every file of each directory

		if to_recompile(file, old_hashes, new_hashes, add_incl):
			to_compile.append(parse_file_path(file))

	return to_compile


def save_new_hashes(new_hashes: dict) -> None:
	"""
	Write all the hashes on files_hash.txt
	"""

	with open(HASH_FILENAME, "w") as f:
		for i in new_hashes.keys():
			f.write(i + ":")
			f.write(new_hashes[i] + "\n")


def compile(to_compile: list[str], settings: dict, compilations: list[dict]) -> None:
	"""
	Calls the compiler with the specified arguments
	"""

	cexe = settings["compiler"]
	includes = settings["includes"]
	cargs = settings["cargs"]
	obj_dir = settings["objects_path"]
	oargs = settings["specifics"]

	for file in to_compile:
		obj_name: str = "".join(file[0].split("/"))

		command = f'{cexe} {oargs["force_colors"]}{cargs}{includes} {oargs["compile_only"]} {oargs["output_compiler"]}{obj_dir}/{obj_name}{file[1]}.{oargs["object_extension"]} {file[0]}/{file[1]}.{file[2]}'

		result = {
		    "result": COMPILATION_STATUS_COMPILING,
		    "name": f"{file[1]}.{file[2]}",
		    "output": "",
		    "errors": "",
		    "command": command
		}
		compilations.append(result)
		threading.Thread(target=exe_command, args=(command, result)).start()


def link(to_compile: list[str], settings: dict, status: dict) -> None:
	"""
	Link together all the files that have been compiled with the specified libraries and arguments
	"""

	to_link: list[str] = []

	for file in settings["source_files"]: # loop trough every file of each directory

		to_link.append(parse_file_path(file))

	lexe = settings["linker"]
	largs = settings["largs"]
	epn = settings["exe_path_name"]
	libs = settings["libraries_paths"]
	obj_dir = settings["objects_path"]
	oargs = settings["specifics"]

	command = f'{lexe}{largs} {oargs["output_linker"]}{epn}{libs}'

	for file in to_link:
		obj_name: str = "".join(file[0].split("/"))

		command += f' {obj_dir}/{obj_name}{file[1]}.{oargs["object_extension"]}'

	command += settings["libraries_names"]

	status["name"] = epn
	status["command"] = command
	threading.Thread(target=exe_command, args=(command, status)).start()


def create_makefile():

	# TODO: use all possible profiles in the makefile
	# first debug options
	parse_config_json("empty")
	make_file = ""

	# variables

	make_file += f'CC={compilation_variables["compiler_exec"]}\n'
	make_file += f'BinName={compilation_variables["exe_path"]}/{compilation_variables["exe_name"]}\n'
	make_file += f'ObjsDir={compilation_variables["objects_path"]}\n'

	make_file += "\n# Debug variables\n"
	make_file += f'DCompilerArgs={compilation_variables["compiler_args"]}\n'
	make_file += f'DLinkerArgs={compilation_variables["linker_args"]}\n'
	make_file += f'DLibrariesPaths={compilation_variables["libraries_paths"]}\n'
	make_file += f'DLibrariesNames={compilation_variables["libraries_names"]}\n'

	# first debug options
	parse_config_json(True)

	make_file += "\n# Release variables\n"
	make_file += f'RCompilerArgs={compilation_variables["compiler_args"]}\n'
	make_file += f'RLinkerArgs={compilation_variables["linker_args"]}\n'
	make_file += f'RLibrariesPaths={compilation_variables["libraries_paths"]}\n'
	make_file += f'RLibrariesNames={compilation_variables["libraries_names"]}\n'

	make_file += "\n# includes\n"
	make_file += f'Includes={compilation_variables["includes_paths"]}\n'

	make_file += "\n\n"

	# targets

	os.chdir(compilation_variables["project_path"])

	# obtain new hashes
	calculate_new_hashes()

	# get the file needed to compile
	to_compile = get_to_compile()

	make_file += "debug: DCompile DLink\n\n"

	make_file += "release: RCompile RLink\n\n"

	# Debug commands

	make_file += "\nDCompile: \n"

	for file in to_compile:
		make_file += f"	$(CC) $(DCompilerArgs) $(Includes) -c -o $(ObjsDir)/{file[0]}{file[1]}.o {file[0]}/{file[1]}.{file[2]}\n"

	make_file += "\nDLink: \n"

	make_file += f"	$(CC) $(DLinkerArgs) -o $(BinName) $(DLibrariesPaths)"

	for file in to_compile:
		make_file += f"	$(ObjsDir)/{file[0]}{file[1]}.o"

	make_file += f" $(DLibrariesNames)\n"

	# Release commands

	make_file += "\nRCompile: \n"

	for file in to_compile:
		make_file += f"	$(CC) $(RCompilerArgs) $(Includes) -c -o $(ObjsDir)/{file[0]}{file[1]}.o {file[0]}/{file[1]}.{file[2]}\n"

	make_file += "\nRLink: \n"

	make_file += f"	$(CC) $(RLinkerArgs) -o $(BinName) $(RLibrariesPaths)"

	for file in to_compile:
		make_file += f" $(ObjsDir)/{file[0]}{file[1]}.o"

	make_file += f" $(RLibrariesNames)\n"

	make_file += "\nclean:\n"
	make_file += "	rm -r -f objs/*\n"
	make_file += "	rm -r -f $(BinName)\n"

	with open("Makefile", "w+") as mf:
		mf.write(make_file)


def main():

	# makefile option
	if "-e" in sys.argv:
		create_makefile()
		return

	# Release or debug mode
	compilation_profile = get_profile(sys.argv)

	# settings is garanteted to have all of the necessary values
	settings = parse_config_json(compilation_profile)

	# script are executed from the project path
	os.chdir(settings["project_path"])

	# TODO: progress spinner here
	if "pre" in settings["scripts"]:
		print(COLS.FG_GREEN, " --- Pre Script ---", COLS.RESET)
		nm = settings["scripts"]["pre"]
		result = {
		    "result": COMPILATION_STATUS_COMPILING,
		    "name": nm,
		    "output": "",
		    "errors": "",
		    "command": nm
		}
		threading.Thread(target=exe_command, args=(f'./{nm}', result)).start()
		print_progress([result])
		print("")
		print_report([result])

	# create file if it does not exist
	if not os.path.exists(HASH_FILENAME):
		f = open(HASH_FILENAME, "w")
		f.close()

	old_hashes: dict = {}

	# by not loading old hashes, all of the files results new
	if "-a" not in sys.argv:
		# load old hashes
		old_hashes = load_old_hashes()

	new_hashes: dict = {}
	# obtain new hashes
	calculate_new_hashes(old_hashes, new_hashes)

	# get the file needed to compile
	to_compile = get_to_compile(settings["source_files"], old_hashes, new_hashes, settings["raw_includes"])

	# if to_compile is empty, no need to do anything
	if not to_compile:
		print(f"{COLS.FG_YELLOW} --- Compilation and linking skipped due to no new or modified files ---{COLS.RESET}")
		return

	if not os.path.exists(settings["objects_path"]):
		os.makedirs(settings["objects_path"])

	# manages compilation and printing
	compile_and_command(to_compile, settings)

	if "post" in settings["scripts"]:
		print("\n", COLS.FG_GREEN, " --- Post Script ---", COLS.RESET)
		nm = settings["scripts"]["post"]
		result = {
		    "result": COMPILATION_STATUS_COMPILING,
		    "name": nm,
		    "output": "",
		    "errors": "",
		    "command": nm
		}
		threading.Thread(target=exe_command, args=(f'./{nm}', result)).start()
		print_progress([result])
		print("")
		print_report([result])

	# do not overwrite the old hashes
	if "-a" not in sys.argv:
		save_new_hashes(new_hashes)


if __name__ == "__main__":
	main()
