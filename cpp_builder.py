# Building tool for cpp and hpp files 
# @Author Leonardo Montagner https://github.com/Vectoryx
# 
# Build only the modified files on a cpp project
# Link and compile usign the appropriate library and include path
# Print out error and warning messages
# add the args for the link and the compile process

"""
import subprocess
import os
import sys
import hashlib

sha1 = hashlib.sha1()
old_hashes = {}
new_hashes = {}
temp = []


def ismodified(filename):
	global new_hashes
	global old_hashes

	if filename in old_hashes.keys():
		if old_hashes[filename] == new_hashes[filename]:
			return False
	return True


# create file if it does not exist
if not os.path.exists("files_hash.txt"):
	f = open("files_hash.txt", "w")
	f.close()


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

# mi posiziono sulla cartella in cui ci sono i file da compilare e controllare
files = os.listdir("src")

# obtain new hashes
for i in files:
	with open("src\\" + i, "r+b") as f:
		sha1.update(f.read())

	# insert in the new_hashes dict the key filename eith the value hash
	new_hashes[i] = sha1.hexdigest()  # create the new hash

	# i need to re-instanciate the object to empty it
	sha1 = hashlib.sha1()

out = ["/", "/"]
errors = 0

print("--Compiling--")  # inizio la fase di compilazione
for i in files:
	temp = i.split(".")

	if temp[-1] == "cpp":  # distinguo eventuali file cpp o h

		if ismodified(i):  # controllo che non sia gia stato compilato / non modificato

			command = f"g++ -g3 -std=c++2a -Iinclude -Iext -c -Wconversion -Wshadow -Wextra -o .\\objs\\{temp[0]}.o .\\src\\{temp[0]}.cpp"

			print(command)  # stampo il comando per eventuale debug

			stream = subprocess.Popen(
				command.split(" "), stderr=subprocess.PIPE, universal_newlines=True)
			out = stream.communicate()  # eseguo il comando e mi faccio comunicare l'esito

			if len(out[1]) == 0:
				print(f"{i} compiled successfully")
			else:
				print(out[1])
				if (out[1].find("error:") != -1):
					errors +=1

# ora lavoro con gli oggetti

if errors != 0:
	print("skipped the linking process for presence of error in the compiling process")
	exit(1)

# if no compilation happened cause no file changed
if out[1] == "/":
	print("Linking skipped, no compilation happened")
else:
	files = os.listdir("objs")

	command = f"g++ -g3 -o exe/Game.exe -Lext/glfw/lib -Lext/glew/lib"

	for i in files:
		if [i.split(".")[-1] == "o"]:
			command += f" objs/{i}"
	command += " -lglfw3 -lopengl32 -lgdi32 -lwinmm -lglew32"

	print("\n--Linking--")
	print(command)

	stream = subprocess.Popen(command.split(
		" "), stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
	out = stream.communicate()

	if len(out[1]) == 0:
		print(f"Program linked successufully")
	else:
		print(out[1])
		exit(1)

with open("files_hash.txt", "w") as f:
	for i in new_hashes.keys():
		f.write(i + ":")
		f.write(new_hashes[i] + "\n")

"""