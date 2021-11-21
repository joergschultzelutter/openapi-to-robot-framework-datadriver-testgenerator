# Installation and first program run

## Installation

- clone repository
- ``pip install --upgrade -r dependencies.txt``

This will install the following external dependencies:

- [prance](https://github.com/RonnyPfannschmidt/prance)
- [openspec-api-validator](https://github.com/p1c2u/openapi-spec-validator)
- [xlsxwriter](https://github.com/jmcnamara/XlsxWriter)
- [robotframework-datadriver](https://github.com/Snooz82/robotframework-datadriver) with Excel support module.


This program may or may not work with other OpenAPI validator modules supported by ``prance``  - see [Compatibility](https://github.com/RonnyPfannschmidt/prance#compatibility). It has only been tested in combination with ``openspec-api-validator`` library and OpenAPI ``V3`` files. See [comments](https://github.com/p1c2u/openapi-spec-validator#examples) on how to enable ``V2`` support if necessary.

## First run

Assuming that you have installed all pip packages, you don't need to apply ANY basic config changes - the program should already work out of the box. Do the following in order to check if the installation was successful:

- open up a command line
- go to the ``src`` directory
- run ``python s2rdd.py ../demo_schema_files/petstorev3.json``. This file was downloaded from [https://petstore3.swagger.io/](https://petstore3.swagger.io/).
- The program will detect that the ``output`` directory is missing and will create it. Finally, it will write two Robot files plus one Excel file to that directory.

Sample output:

    /Users/jsl/git/openapi-to-robot-framework-datadriver-testgenerator/venv/bin/python /Users/jsl/git/openapi-to-robot-framework-datadriver-testgenerator/src/s2rdd.py ../demo_schema_files/petstorev3.json
    2021-11-20 20:33:02,514 s2rdd -INFO- PASS 1 - Read Test Generator output templates
    2021-11-20 20:33:02,514 s2rdd -INFO- Output directory output does not exist, creating it ...
    2021-11-20 20:33:02,515 s2rdd -INFO- PASS 2 - Parse OpenAPI file ../demo_schema_files/petstorev3.json
    2021-11-20 20:33:03,417 s2rdd -INFO- skipping PASS 3 - no Jira access credentials provided
    2021-11-20 20:33:03,417 s2rdd -INFO- PASS 4 - Generate Excel file 'output/export.xlsx'
    2021-11-20 20:33:03,443 s2rdd -INFO- PASS 5 - Generate Robot Framework 'includes' file 'output/includes.resource'
    2021-11-20 20:33:03,444 s2rdd -INFO- PASS 6 - Generate Robot Framework test case file 'output/export.robot'
    2021-11-20 20:33:03,444 s2rdd -INFO- True

    Process finished with exit code 0

If you receive this output, then the program has been properly configured. 

Now have a look at the [Program Configuration](CONFIGURATION.md) documentation for customization and (Jira) configuration steps.

