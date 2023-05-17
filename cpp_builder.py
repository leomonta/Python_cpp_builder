# Building tool for cpp and hpp files
# @Author Leonardo Montagner https://github.com/Vectoryx
#
# Build only the modified files on a cpp project
# Link and compile usign the appropriate library and include path
# Print out error and warning messages
# add the args for the link and the compile process
#
# Done compile and link files
# TODO check for newer version of source files
# TODO skip compilation or linking if there are no new or modified files
# TODO check for newer versione of header files (check in every file if that header is included, if it is rebuild)
# Done error and warning coloring in the console
# TODO if error occurs stop compilation and return 1
# Done retrive include dirs, libs and args from a file
# Done retrive target directories for exe, objects, include and source files
# TODO support for debug and optimization compilation

import subprocess  # execute command on the cmd / bash / whatever
import os  # get directories file names
import json  # parse cpp_builder_config.json
from colorama import Fore, init

def print_stdout(mex: tuple[str, str]):

	out = mex[1].split("\n")[0:-1]
	
	for i in range(len(out)):
		if "error" in out[i]:
			print(Fore.RED, out[i])
			return False
		elif "warning" in out[i]:
			print(Fore.BLUE, out[i])
		elif "note" in out[i]:
			print(Fore.CYAN, out[i])
		else:
			print(out[i])

	print(Fore.WHITE)

	return True


def exe_command(command: str):
	"""
	execute the given command and return the output -> [stdout, stderr]
	"""

	stream = subprocess.Popen(
		command.split(" "), stderr=subprocess.PIPE, universal_newlines=True)

	return stream.communicate()  # execute the command and get the result


# 0 -> compiler args, 1 -> linker args
args = ["", ""]
# 0 -> the library to link with (-l), 1 -> the libraries path (-L)
libraries = ["", ""]
includes = ""
srcDirs = []
projectDir = ""
# 0-> object target Directory, 1 -> exe target Directory, 2 -> exe name
targetDir = ["", "", ""]

source_files_extensions = ["c", "cpp", "cxx", "c++", "cc", "C"]

def parse_config_json():
	"""
	Set the global variables by reading the from cpp_builder_config.json
	"""
	global includes, projectDir, targetDir, args, libraries, srcDirs

	# load and parse the file
	config_file = json.load(open("cpp_builder_config.json"))

	# base directory for ALL the other directories and files
	projectDir = config_file["projectDir"]

	# --- Libraries path and names ---

	# create the library args -> -lsomelib -lsomelib2 -l...
	for lname in config_file["libraries"]:
		libraries[0] += " -l" + lname

	# create the libraries path args -> -Lsomelibrary/lib -L...
	for Lname in config_file["Directories"]["libraryDir"]:
		libraries[1] += " -L" + Lname
	libraries[1] = libraries[1][1:] #remove first whitespace

	# --- Include and Source Directories

	# create the includes args -> -Iinclude -Isomelibrary/include -I...
	for Idir in config_file["Directories"]["includeDir"]:
		includes += "-I" + Idir + " "
	includes = includes.removesuffix(" ") # remove trailing space

	# source dir where the source code file are located
	srcDirs = config_file["Directories"]["sourceDir"]

	targetDir[0] = config_file["Directories"]["objectsDir"]
	targetDir[1] = config_file["Directories"]["exeDir"]
	targetDir[2] = config_file["exeName"]

	# --- Compiling an linking arguments ---

	# compiler and linker argument
	args[0] = config_file["Arguments"]["Compiler"]
	args[1] = config_file["Arguments"]["Linker"]


def main():
	parse_config_json()

	os.chdir(projectDir)

	init()

	to_compile = [] # contains directory and filename

	# individuates the files that need to be compiled
	for source_directories in srcDirs: # loop trough all the source files directories
		for file in os.listdir(source_directories): # loop trough every file of each directory
			# i need to differentiate differen parts
			# extension: to decide if it has to be compiled or not and to name it 
			# filename: everything else of the file name ignoring the extension, useful for naming compilitation files
			# source dir: necessary for differentiate eventual same-named files on different dirs
			temp = file.split(".")
			ext = temp.pop(-1)
			file_name = "".join(temp)
			if (ext in source_files_extensions): # check if it is a source file
				to_compile.append([source_directories, file_name, ext])


	# --- Compiling ---

	print(Fore.GREEN, " --- Compiling ---", Fore.WHITE)

	errors = 0

	# compile each file and show the output
	for file in to_compile:
		command = f"g++ {args[0]} {includes} -c -o {targetDir[0]}/{file[0]}{file[1]}.o {file[0]}/{file[1]}.{file[2]}"
		print(command)
		errors += print_stdout(exe_command(command))



	# --- Linking ---

	if errors > 0:
		print(f"\n{Fore.RED} --- Linking skipped due to errors in compilation process! ---")
		return 1

	print(Fore.GREEN, " --- Linking ---", Fore.WHITE)

	Link_cmd = f"g++ {args[1]} -o {targetDir[1]}/{targetDir[2]} {libraries[1]}"


	for file in to_compile:
		Link_cmd += f" {targetDir[0]}/{file[0]}{file[1]}.o"
	
	Link_cmd += libraries[0]

	print(Link_cmd)
	print_stdout(exe_command(Link_cmd))


main()
