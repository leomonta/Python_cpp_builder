# CPP python building tool
## Compile and link cpp projects 

### Options:
	-a	rebuild the entire project
	-o	utilize optimization options arguments and libraries, default is debug 
	-e	do not compile and export the cpp_builder_config as a Makefile with debug and release steps

### the cpp_builder_config.json structure

<pre>
{
	"projectDir": "Base directory of the entire project"
	"exeName": "Name of th executable produced",
	"compilerExe" : "Path to the compiler executable",
	"Directories": { 
		"includeDir": [
			"include directories (h, hpp files)"
		],
		"sourceDir": [
			"source file directories (c, cpp files)"
		],
		"libraryDir": [
			"every library directory"
		],
		"objectsDir": "directory where the .o files will be saved",
		"exeDir": "directory where the exe file will be saved"
	},
	"libraries": {
		"Debug" : [
			"name of the debug libraries used, without the heading -l",
		],
		"Release" : [
			"name of the release libraries used, without the heading -l",
		]
	}
	"Arguments": {
		"Debug" : {
			"Compiler": "additional arguments for the compiler, like c standard or warnings, for the debug mode"
			"Linker": "additiona arguments for the linker, for the debug mode"
		}, 
		"Release" : {
			"Compiler": "additional arguments for the compiler, like c standard or warnings, for the release mode"
			"Linker": "additiona arguments for the linker, for the release mode"
		}
	}
}
</pre>
