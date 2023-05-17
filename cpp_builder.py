#!/usr/bin/env python3.9
# Building tool for cpp and hpp files
# @Author Leonardo Montagner https://github.com/Vectoryx
#
# Build only the modified files on a cpp project
# Link and compile usign the appropriate library and include path
# Print out error and warning messages
# add the args for the link and the compile process
#
# Done: compile and link files
# Done: check for newer version of source files
# Done: skip compilation or linking if there are no new or modified files
# TODO: check for newer versione of header files (check in every file if that header is included, if it is rebuild)
# Done: error and warning coloring in the console
# Done: if error occurs stop compilation and return 1
# Done: if error occurs stop linking and return 1
# Done: retrive include dirs, libs and args from a file
# Done: retrive target directories for exe, objects, include and source files
# TODO: support for debug and optimization compilation

import subprocess  # execute command on the cmd / bash / whatever
import os  # get directories file names
import json  # parse cpp_builder_config.json
from colorama import Fore, init
import hashlib # for calculating hashes
import sys # for arguments parsing


# 0 -> compiler args, 1 -> linker args
args = ["", ""]
# 0 -> the library to link with (-l), 1 -> the libraries path (-L)
libraries = ["", ""]
includes = ""
srcDirs = []
projectDir = ""
# 0-> object target Directory, 1 -> exe target Directory, 2 -> exe name
targetDir = ["", "", ""]

sha1 = hashlib.sha1()
old_hashes = {}
new_hashes = {}

source_files_extensions = ["c", "cpp", "cxx", "c++", "cc", "C"]


def print_stdout(mexage: tuple) -> bool:

	out = mexage[1].split("\n")[0:-1]
	
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


def exe_command(command: str) -> tuple:
	"""
	execute the given command and return the output -> [stdout, stderr]
	"""

	stream = subprocess.Popen(command.split(" "), stderr=subprocess.PIPE, universal_newlines=True)

	return stream.communicate()  # execute the command and get the result


def parse_config_json() -> None:
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


def ismodified(filename: str) -> bool:
	global new_hashes
	global old_hashes

	if filename in old_hashes.keys():
		if old_hashes[filename] == new_hashes[filename]:
			return False
	return True


def calculate_new_hashes() -> None:
	global new_hashes, sha1, srcDirs
	for source_directory in srcDirs: # loop trough all the source files directories
		for file in os.listdir(source_directory): # loop trough every file of each directory

			# sha1 hash calculation

			with open(f"{source_directory}/{file}", "r+b") as f:
				sha1.update(f.read())

			# insert in the new_hashes dict the key filename eith the value hash
			new_hashes[source_directory + file] = sha1.hexdigest()  # create the new hash

			# i need to re-instanciate the object to empty it
			sha1 = hashlib.sha1()


def load_old_hashes() -> None:
	global old_hashes
	if "-a" not in sys.argv:
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


def get_to_compile() -> list:
	to_compile = [] # contains directory and filename
	# checking which file need to be compiled
	for source_directory in srcDirs: # loop trough all the source files directories
		for file in os.listdir(source_directory): # loop trough every file of each directory
			# i need to differentiate differen parts
			# extension: to decide if it has to be compiled or not and to name it 
			# filename: everything else of the file name ignoring the extension, useful for naming compilitation files
			# source dir: necessary for differentiate eventual same-named files on different dirs

			if ismodified(source_directory + file):

				temp = file.split(".")
				ext = temp.pop(-1)
				file_name = "".join(temp)
				if (ext in source_files_extensions): # check if it is a source file
					to_compile.append([source_directory, file_name, ext])
	return to_compile


def save_new_hashes() -> None:
	global new_hashes
	with open("files_hash.txt", "w") as f:
		for i in new_hashes.keys():
			f.write(i + ":")
			f.write(new_hashes[i] + "\n")


def compile(to_compile: list) -> bool:
	global args, includes, targetDir
	errors = 0

	for file in to_compile:
		command = f"g++ {args[0]} {includes} -c -o {targetDir[0]}/{file[0]}{file[1]}.o {file[0]}/{file[1]}.{file[2]}"
		print(command)
		errors += not print_stdout(exe_command(command))

	return errors > 0


def link() -> bool:

	global args, targetDir, libraries

	to_link = [] # contains directory and filename
	# checking which file need to be compiled
	for source_directory in srcDirs: # loop trough all the source files directories
		for file in os.listdir(source_directory): # loop trough every file of each directory
			# i need to differentiate differen parts
			# extension: to decide if it has to be compiled or not and to name it 
			# filename: everything else of the file name ignoring the extension, useful for naming compilitation files
			# source dir: necessary for differentiate eventual same-named files on different dirs

			temp = file.split(".")
			ext = temp.pop(-1)
			file_name = "".join(temp)
			if (ext in source_files_extensions): # check if it is a source file
				to_link.append([source_directory, file_name, ext])


	Link_cmd = f"g++ {args[1]} -o {targetDir[1]}/{targetDir[2]} {libraries[1]}"

	for file in to_link:
		Link_cmd += f" {targetDir[0]}/{file[0]}{file[1]}.o"
	
	Link_cmd += libraries[0]

	print(Link_cmd)
	return print_stdout(exe_command(Link_cmd))


def main():
	parse_config_json()

	os.chdir(projectDir)

	#init colorama
	init()

	# create file if it does not exist
	if not os.path.exists("files_hash.txt"):
		f = open("files_hash.txt", "w")
		f.close()


	# load old hashes
	load_old_hashes()

	# obtain new hashes
	calculate_new_hashes()

	# get the file needed to compile
	to_compile = get_to_compile()

	# --- Compiling ---

	print(Fore.GREEN, " --- Compiling ---", Fore.WHITE)

	if not to_compile:
		print(" --- Compilation skipped due to no new or modified files ---")


	# compile each file and show the output,
	# and check for errors
	if compile(to_compile):
		print(f"\n{Fore.RED} --- Linking skipped due to errors in compilation process! ---")
		sys.exit(1)

	# --- Linking ---

	print(Fore.GREEN, " --- Linking ---", Fore.WHITE)

	if not link():
		print(f"\n{Fore.RED} --- Errors in linking process! ---")
		sys.exit(1)

	save_new_hashes()


main()
