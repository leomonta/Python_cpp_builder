#!/usr/bin/env python3
# Building tool for cpp and hpp files
# @Author Leonardo Montagner https://github.com/leomonta/Python_cpp_builder
#
# Build only the modified files on a cpp project
# Link and compile using the appropriate library and include path
# Print out error and warning messages
# add the args for the link and the compile process
#
# Done: compile and link files
# Done: check for newer version of source files
# Done: skip compilation or linking if there are no new or modified files
# TODO: check for newer version of header files (check in every file if that header is included, if it has to be rebuilt)
# TODO: identify each header and figure out which source file include which
# TODO: if a config value is empty prevent double space in cmd agument
# TODO: add a type config value for gcc | msvc so i can decide which cmd args to use -> -o | -Fo
# Done: added specific linker exec
# TODO: use compiler exec if no linker exec is present
# TODO: multithreaded compiling
## - main.cpp  Compiling
##   utils.cpp Done
## / other.cpp Compiling
# Done: error and warning coloring in the console
# Done: if error occurs stop compilation and return 1
# Done: if error occurs stop linking and return 1
# Done: retrive include dirs, libs and args from a file
# Done: retrive target directories for exe, objects, include and source files
# Done: support for debug and optimization compilation, compiler flag and libraries
# Done: support for pre and post script

import subprocess # execute command on the cmd / bash / whatever
import os         # get directories file names
import json       # parse cpp_builder_config.json
import hashlib    # for calculating hashes
import threading  # for threading, duh
import sys        # for arguments parsing


includes_variable: dict[str, list[str]] = {
                                            # names of all includes dir + name
    "all_includes": [],

                                            # file: list of references (indices) to include files
    "src_references": {}
}

settings: dict[str, any] = {
                             # name of the compiler and linker executable
    "compiler": "",
    "linker": "",

                             # compiler and linker args
    "cargs": "",
    "largs": "",

                             # misc args
                             # output, includes, filenames swithces (/Fo -o) for msvc, clang, and gcc
    "args": {},

                             # path and name of the final executable
    "exe_path_name": "",

                             # base directory of the project
    "project_path": "",

                             # the string composed by the path of the includes -> "-I./include -I./ext/include -I..."
    "includes": "",

                             # directory where to leave the compiled object files
    "objects_path": "",

                             # directories containing the names of the source directories
    "source_files": [],

                             # the string composed by the names of the libraries -> "-lpthread -lm ..."
    "libraries_names": "",

                             # the string composed by the path of the libraries -> "-L./path/to/lib -L..."
    "libraries_paths": "",
}

# for now use these, might add more in the future
compiler_includes: list[str] = ["./"]

sha1 = hashlib.sha1()
old_hashes: dict[str, str] = {}
new_hashes: dict[str, str] = {}

source_files_extensions: list[str] = ["c", "cpp", "cxx", "c++", "cc", "C", "s"]

compilers_common_args: list[dict[str]] = [
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

# should be a reference to compilers_common_args
compiler_specific_args: dict[str] = {}


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


def print_stdout(mexage: tuple) -> bool:

	out = mexage[1].split("\n")[0:-1]

	res = True

	for i in range(len(out)):
		if "error:" in out[i]:
			res = False
		print(out[i])

	return res


def exe_command(command: str) -> tuple[str, str]:
	"""
	execute the given command and return the output -> [stdout, stderr]
	"""

	stream = subprocess.Popen(command.split(" "), stderr=subprocess.PIPE, universal_newlines=True)

	return stream.communicate() # execute the command and get the result


def parse_config_json(profile: str) -> int:
	"""
	Set the global variables by reading the from cpp_builder_config.json
	the optimization argument decide if debug or release mode
	"""

	global settings

	# load and parse the file
	config_filename = "cpp_builder_config.json"
	if os.path.isfile(config_filename):
		config_file = json.load(open(config_filename))
	else:
		print(COLS.FG_RED, f"[ERROR]{COLS.FG_LIGHT_RED} Config file \"{config_filename}\" not found", COLS.RESET)
		return 0

	# --- Scripts settings ---
	settings["scripts"] = config_file["scripts"]

	# --- Compiler settings ---
	# get the compiler executable (gcc, g++, clang, rustc, etc)
	# and the linker executable, plus the type (needed for cli args)

	settings["compiler"] = config_file["compiler"]["compiler_exe"]

	cstyle: str = config_file["compiler"]["compiler_style"]

	# 0 gcc / clang
	# 1 msvc
	# 2 rust
	compiler_type: int = 0

	if cstyle == "gcc":
		compiler_type = 0
	elif cstyle == "clang":
		compiler_type = 0
	elif cstyle == "msvc":
		compiler_type = 1
	elif cstyle == "rustc":
		compiler_type = 2

	settings["args"] = compilers_common_args[compiler_type]

	settings["linker"] = config_file["compiler"]["linker_exe"]

	# --- Directories settings ---
	# Where is the project
	# where are the source files and the include files

	# base directory for ALL the other directories and files
	settings["project_path"] = config_file["directories"]["project_dir"]

	# name of the final executable
	settings["exe_path_name"] = config_file["directories"]["exe_path_name"]

	targets: list[str] = []

	old_dir: str = os.getcwd()

	os.chdir(settings["project_path"])
	for sdir in config_file["directories"]["source_dirs"]:
		for path, subdirs, files in os.walk(sdir):
			for name in files:
				targets.append(f"{path}/{name}")

	os.chdir(old_dir)

	settings["source_files"] = targets

	# create the includes args -> -IInclude -ISomelibrary/include -I...
	for Idir in config_file["directories"]["include_dirs"]:
		compiler_includes.insert(1, Idir)
		settings["includes"] += " " + settings["args"]["include_path"] + Idir

	settings["objects_path"] = config_file["directories"]["temp_dir"]

	# ----- Profiles -----

	# set the default empty profile
	config_file["empty"] = {}
	config_file["empty"]["libraries_names"] = []
	config_file["empty"]["libraries_dirs"] = []
	config_file["empty"]["compiler_args"] = ""
	config_file["empty"]["linker_args"] = ""

	print(profile)

	# --- Libs ---
	# if the current optimization section has no libs, default to debug
	# if not config_file[optimization]["libraries_names"]:
	# opt = "debug"

	# create the library args -> -lSomelib -lSomelib2 -l...
	for lname in config_file[profile]["libraries_names"]:
		settings["libraries_names"] += " " + settings["args"]["library_name"] + lname

	# if the current optimization section has no libs, default to debug
	# if not config_file[optimization]["libraries_dirs"]:
	# opt = "debug"
	# else:
	# opt = optimization

	# create the libraries path args -> -LSomelibrary/lib -L...
	for Lname in config_file[profile]["libraries_dirs"]:
		settings["libraries_paths"] += " " + settings["args"]["library_path"] + Lname

	# --- Compiler an Linker arguments ---

	# if not config_file[optimization]["compiler_args"]:
	# opt = "debug"
	# else:
	# opt = optimization
	settings["cargs"] = config_file[profile]["compiler_args"]
	settings["largs"] = config_file[profile]["linker_args"]

	# fix for empty args
	if settings["cargs"]:
		settings["cargs"] = " " + settings["cargs"]

	if settings["largs"]:
		settings["largs"] = " " + settings["largs"]

	return 1


def to_recompile(filename: str, env="") -> bool:
	"""
	Given a filename return if it needs to be recompiled
	A source file needs to be recompiled if it has been modified
	Or an include chain (God help me this shit is recursive) has been modified
	"""

	global new_hashes
	global old_hashes
	"""
	if filename not in old_hashes.keys():
		return True

	# this means that filename is in old_hashses
	if old_hashes[filename] != new_hashes[filename]:
		# For the same file the new and the old hashes are different, this means that the file has been modified
		return True
	"""

	# now check if an include has been modified

	# collect all of the includes here
	includes: list[str]

	# while len(includes) > 0:

	# I need to find the actual path of the file
	# try /usr/include (or the compiler default includes)
	# try the INCLUDE_PATH environment variable (should be available also in windows)
	# try also the includes dirs given in the config file

	includes_directories = compiler_includes.copy()
	if isinstance(env, str):
		includes_directories.append(env)
	else:
		includes_directories.extend(env)

	curr = filename #includes[0]

	# print(includes_directories)

	for dir in includes_directories:
		fullname: str = dir + "/" + curr
		# print(dir, "-", fullname)
		if os.path.isfile(fullname):
			# everythin fine
			curr = fullname
			# print(COLS.FG_GREEN, "Found", curr, COLS.RESET)
			break

	# print(COLS.FG_RED, "Not Found", curr, COLS.RESET, "\n")

	if curr in old_hashes:
		if old_hashes[curr] != new_hashes[curr]:
			return True
	else:
		make_new_file_hash(curr)
		return True

	for inc in get_includes(curr):
		add_incl = parse_file_path(curr)[0] + "/"
		# print("Add incl ->", add_incl)
		if to_recompile(inc, add_incl):
			return True
	# incl = get_includes(curr)
	# if incl != None:
	# includes.extend(incl)
	# includes.pop(0)

	return False


def make_new_file_hash(file: str) -> str:
	"""
	Calculate the hash for the given file an puts it in the new_hashes file
	"""

	global sha1

	# sha1 hash calculation

	# print("Opening", file)
	with open(file, "rb") as f:
		sha1.update(f.read())

	# insert in the new_hashes dict the key filename with the value hash
	new_hashes[file] = sha1.hexdigest() # create the new hash

	# i need to re-instantiate the object to empty it
	sha1 = hashlib.sha1()


def calculate_new_hashes() -> None:
	"""
	Calculate the hashes for all the source files
	"""

	global settings

	for file in old_hashes: # loop trough every file of each directory

		make_new_file_hash(file)


def load_old_hashes() -> None:
	"""
	Load in old_hashes the hashes present in files_hash.txt
	"""

	global old_hashes

	# read hashes from files and add them to old_hashes array
	with open("files_hash.txt", "r") as f:
		while True:
			data = f.readline()
			if not data:
				break
			temp = data.split(":")

			# remove trailing newline
			temp[1] = temp[1].replace("\n", "")
			old_hashes[temp[0]] = temp[1]


def get_to_compile() -> list[str]:
	"""
	return a list of files and their directories that need to be compiled
	"""

	global settings

	to_compile: list[tuple[str, str, str]] = [] # contains directory and filename

	# checking which file need to be compiled
	file: str = ""
	for file in settings["source_files"]: # loop trough every file of each directory

		if to_recompile(file):
			print(COLS.FG_YELLOW, f"{file} needs to be compiled due to it or one of its headers being new or modified", COLS.RESET)

			to_compile.append(parse_file_path(file))

	return to_compile


def save_new_hashes() -> None:
	"""
	Write all the hashes on files_hash.txt
	"""

	global new_hashes

	with open("files_hash.txt", "w") as f:
		for i in new_hashes.keys():
			f.write(i + ":")
			f.write(new_hashes[i] + "\n")


def compile(to_compile: list[str]) -> bool:
	"""
	Compile all correct files with the specified arguments
	"""

	global settings

	errors = 0

	cexe = settings["compiler"]
	includes = settings["includes"]
	cargs = settings["cargs"]
	obj_dir = settings["objects_path"]
	oargs = settings["args"]

	for file in to_compile:
		obj_name: str = "".join(file[0].split("/"))

		command = f'{cexe} {oargs["force_colors"]}{cargs}{includes} {oargs["compile_only"]} {oargs["output_compiler"]}{obj_dir}/{obj_name}{file[1]}.{oargs["object_extension"]} {file[0]}/{file[1]}.{file[2]}'
		print(command)
		errors += not print_stdout(exe_command(command))
		print("\n")

	return errors > 0


def link(to_compile: list[str]) -> bool:
	"""
	Link together all the files that have been compiled with the specified libraries and arguments
	"""

	global settings

	to_link: list[str] = []

	for file in settings["source_files"]: # loop trough every file of each directory

		to_link.append(parse_file_path(file))

	lexe = settings["linker"]
	largs = settings["largs"]
	epn = settings["exe_path_name"]
	Libs = settings["libraries_paths"]
	obj_dir = settings["objects_path"]
	oargs = settings["args"]

	Link_cmd = f'{lexe}{largs} {oargs["output_linker"]}{epn}{Libs}'

	for file in to_link:
		obj_name: str = "".join(file[0].split("/"))

		Link_cmd += f' {obj_dir}/{obj_name}{file[1]}.{oargs["object_extension"]}'

	Link_cmd += settings["libraries_names"]

	print(Link_cmd)
	return print_stdout(exe_command(Link_cmd))


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

	global settings

	# makefile option
	if "-e" in sys.argv:
		create_makefile()
		return

	# Release or debug mode
	compilation_profile: str = "empty"
	if "-p" in sys.argv:
		compilation_profile = get_profile(sys.argv)

	if not parse_config_json(compilation_profile):
		sys.exit(1)

	# go to the project dir
	os.chdir(settings["project_path"])

	# Execute pre-script
	if "pre" in settings["scripts"]:
		print(COLS.FG_GREEN, " --- Pre Script ---", COLS.RESET)
		print(exe_command(f'./{settings["scripts"]["pre"]}')[1])

	# create file if it does not exist
	if not os.path.exists("files_hash.txt"):
		f = open("files_hash.txt", "w")
		f.close()

	# by not loading old hashes they all look new
	if "-a" not in sys.argv:
		# load old hashes
		load_old_hashes()

	# obtain new hashes
	calculate_new_hashes()

	# get the file needed to compile
	to_compile = get_to_compile()

	# --- Compiling ---

	print(COLS.FG_GREEN, " --- Compiling ---", COLS.RESET)

	# if to_compile is empty, no need to do anything
	if not to_compile:
		print("  --- Compilation and linking skipped due to no new or modified files ---")
		return

	if not os.path.exists(settings["objects_path"]):
		os.makedirs(settings["objects_path"])

	# compile each file and show the output,
	# and check for errors
	if compile(to_compile):
		print(f"\n{COLS.FG_RED} --- Linking skipped due to errors in compilation process! ---")
		sys.exit(2)

	# --- Linking ---

	print(COLS.FG_GREEN, " --- Linking ---", COLS.RESET)

	if not link(to_compile):
		print(f"\n{COLS.FG_RED} --- Errors in linking process! ---")
		sys.exit(3)

	if "post" in settings["scripts"]:
		print(COLS.FG_GREEN, " --- Post Script ---", COLS.RESET)
		print(exe_command(f'./{settings["scripts"]["post"]}')[1])

	# do not overwrite the old hashes
	if "-a" not in sys.argv:
		save_new_hashes()


if __name__ == "__main__":
	main()
