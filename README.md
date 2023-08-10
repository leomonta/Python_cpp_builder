# CPP python building tool

## Why:

When I started making stuff in c/c++ without an IDE (that compiles for you, VSCode does not) I encountered Makefile, and honestly, I hate it
There are some cool stuff that you can do with it but is too complex and with way too many hidden and implicit rules that are just stupid (e.g. `.c.o`)

So my brain had the brillian Idea of making an entire python script to compile projects the way i organize them. Cuz it was "Easier and Fun, Trust me"

I keep my source orginized in different directories, I keep the source files in `src/`, my includ files in `include/`, object files (`.o`) in `obj/` and so on, Makefile make this hard somehow, but with some variations from project to project, some times i use the `ext/` folder to keep libraries source files and includes, and often i use different libraries.

Also, I would like to use this same framework for other OSes (Windows), and compilers (Rust)

## Modus Operandis: (?)

A config file (`cpp_builder_config.json`) is always needed, even though i might add a simple empty config file in the builder if none is found,
The config file i a json because the key helps explain the what the requested info is, and i easily edited by people, + widely used for everything

It only compiles files that have been modifies from the previous call to the builder, to know which files have been modified it computes an hash of the file itself and compares it to a saved copy of the previous compilation (the hashes are stored unceremoniously in files_hash.txt)
This check is also performed recursively for every include the file contain, if the include name is enclosed int double quptes `"`, since those are usually the one that the programmer writes
If an header file has been modified all of the source files that include that header will be recompilated
And finally writes the new hashes to file

Profiles are just free floating keys, that can be used via `-p profileName`, in the config file if not profile is specify an empty profile, with all of the param empty, is used
Sometimes all of the params empty is fine

### Process

Checks for cli switches and respects them

Loads the files hashes in an array (if the `-a` is not specified)

Parse the config files and saves the useful data in an internal dict and the requested profile
> The builder `cd`s in the `project_dir` so all the other dirs should be relative to that one

If the `pre` key is present in `scripts` execute the given script

Lists of of the files that are in the `source_dirs` and select only the one that can be compiled (e.g. .c, .cpp. .h) and have been modified
> Early exit if no files to compile are found

Create a thread that calls the given compiler with all of the correct arguments and prints the waiting with a cool animation on the stdout

When all the threads are done prints all of the compiler output
> Early exit if there is an error

Call the given compiler on all of the compiled object files and prints the linker output

If the `post` key is present in `scripts` execute the given script

Saves the new hashes that have been generated

## Known problems

NONE

Next..
jkjk

### Modified files are not identified properly

Yes they are, but not immediatly

When checking if a has been modified or not the search stops at the first one that has been, in fact modified.
This means when `files_hash.txt` is empty, or simply a minimally complex amout of headers have been added, many calls to the builder are needed to reach the 'top' of the include chain

This is fixable but I'm probably not going to since it's not that big of a problem

### The Makefile export fails miserably

The Makefile "exporter" i quite old and needs an update as of know it misses compatibility for
- Different profiles
- New setting structure
- Pre and post scripts
- Use of implicit rules (that i don't like though)

## Options:
```
	-a              rebuild the entire project
	-p profile name	utilize the given profile specifies in the config file
	-e              do not compile and export the cpp_builder_config as a Makefile
```

## the cpp_builder_config.json structure

```json
{
	"scripts": {
		"pre": "script to execute before the compilation begin",
		"post": "script to execute after the compilation end"
	},
	"compiler" :{
		"compiler_style": "what kind of compiler is being used (gcc, clang, msvc, rustc)",
		"compiler_exe": "path to the compiler executable",
		"linker_exe": "path to the linker executable"
	},

	"directories" : {

		"project_dir": "project root directory relative to where the cpp_builder is being called",
		"exe_path_name": "path and name where to put the final executable",
		"include_dirs": [
			"additional include directories to pass to the compiler"
		],
		"source_dirs": [
			"directories where to search source files"
		],
		"temp_dir": "name of the temporary directory where to put object files"
	},

	"profile name": {
		"compiler_args": "additional compiler args",
		"linker_args": "additional linker args",
		"libraries_dirs": [
			"additional libraries directories"
		],
		"libraries_names": [
			"additional libraries names"
		]
	}

}
```
