# CPP python building tool
## Compile and link cpp projects 

### Options:
	-a	rebuild the entire project
	-o	utilize optimization options arguments and libraries, default is debug 
	-e	do not compile and export the cpp_builder_config as a Makefile with debug and release steps

### the cpp_builder_config.json structure

```json
{
	"scripts" : {
		"pre" : "script to execute before the compilation begin",
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

	"debug": {
		"compiler_args": "additional debug compiler args",
		"linker_args": "additional debug linker args",
		"libraries_dirs": [
			"additional libraries directories"
		],
		"libraries_names": [
			"additional libraries names"
		]
	},

	"release": {
		"compiler_args": "additional release compiler args",
		"linker_args": "additional release linker args",
		"libraries_dirs": [
			"additional libraries directories"
		],
		"libraries_names": [
			"additional libraries names"
		]
	},
}
```