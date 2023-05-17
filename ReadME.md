# CPP python building tool
## Compile and link cpp projects 

#### the cpp_builderconfig.json structure

<pre>
{
    "projectDir": "Base directory of the entire project"
    "exeName": "Name of th executable produced",
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
        "objectsDir": "directory where the .o files will be saved"
        "exeDir": "directory where the exe file will be saved"
    },
    "libraries": [
        "name of the libraries used, without the heading -l"
    ],
    "Arguments": {
        "Compiler": "additional arguments for the compiler, like c standard or warnings
        "Linker": "additiona arguments for the linker"
    }
}
</pre>