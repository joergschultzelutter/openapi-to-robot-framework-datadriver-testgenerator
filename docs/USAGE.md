# Usage and Known Issues

## Command Line Parameters

The following input parameter are supported:

- __inputfile__. OpenAPI V3 JSON / YAML input file. __Mandatory parameter__.
- __outputfile__. Output file name for both Robot Framework test file AND the Excel/Datadriver file. Default is 'export' which will result in ``export.robot`` and ``export.xlsx`` files. Existing files will always be overwritten.
- __jira_access_key__. Required if you want the program to create Jira tickets and associate them with the Robot tests. Contact your administrator if necessary. The access key may look like this: ``dGVu9Y3lfcm9ib3Q6M08lKADt9vTVhnchhaUnQ9``
- __output_dir__. Output file directory name. Default is ``output``, resulting in the output files ``output/export.robot`` and so on.
- __--add_example_data__. Default - false. If you set this switch, the program will try to prepopulate your Excel sheet with sample data from the OpenAPI file.

## Known issues and constraints

- The OpenAPI parser is VERY sensitive if you try to parse an OpenAPI file which deviates from the OpenAPI standards but may be accepted by other systems and software. The ``openapi-spec-validator`` [uses strict mode](https://github.com/RonnyPfannschmidt/prance#compatibility), meaning that e.g. no integer-based keys in the OpenAPI spec file are allowed. If the program crashes, then an error like this might be the reason.
- The Robot demo code (not the actual parser itself) cannot deal with multi-layered JSON request bodies in an automated manner. The current approach focuses on fields on a single layer

Example:

    {
      "field1": "value1",
      "field2:: "value2"
    }

However, a nested request body like this one cannot be generated __in an automated manner__ with the help of this program:

Example:

    {
      "field1": "value1",
	  "more_fields": {
          "field2":": "value2",
		  "field3": "value3"
	  }
    }

This does _not_ mean that you cannot use the program for the initial test generation - the program will still be able to extract all fields from the OpenAPI file, add them to the Excel file and generate the Robot code for you. However, nested structures are not automatically generated and you may be forced to apply some additional changes to the code in order to create a nested JSON object.

- Robot Framework test case names need to be unique. As there is a remote chance that an OpenAPI file _may_ contain test names which could result in dupes, the program tries to dodge these edge cases by forming a combination of the API call's internal name AND the HTTP method. This approach works for me but your miles may vary.

- The sample code assumes that your [robotframework-datadriver](https://github.com/Snooz82/robotframework-datadriver) version is 1.5.0 or later. The Robot demo template makes heavy usage of the Datadriver's [typed cells](https://github.com/Snooz82/robotframework-datadriver#ms-excel-and-typed-cells) option, meaning that you apply the desired target format for your input data directly to your respective Excel cell. For example, a cell containing the numeric value of 123 with an Excel _General_ format will be recognised as Integer value whereas the same value with an Excel _Text_ formatting will be treated as text. Booleans, Floats etc are supported. Some edge cases may not work out of the box and may require some manual magic, though.

## How does this program work?

The program consists of six possible steps:

- __Step 1__ will read the template files from your hard drive. Internally, these files' values are simply stored as strings, meaning that when it comes to creating the Robot Framework Datadriver test, the program will simply search-and-replace predefined strings.
- __Step 2__ will parse the OpenAPI YAML/JSON file and transfer its contents (variables, examples, return codes) into an internal dictionary.
  - The OpenAPI file's ``operationId`` field is considered to be the future test's name (excluding the HTTP operation code, e.g. PUT, GET etc). If an  API method is present in the file but misses the ``operationId``, the program will fail.
- __Step 3__ is disabled per default and will write the Jira tickets if the user has specified a ``jira_access_key``. Note that this step will communicate directly with the Jira server URLs for Jira and Jira XRay. You may want/need to test the program's config extensively prior to being able to use this optional step.
- __Step 4__ generates the DataDriver Excel file.
- __Step 5__ and __Step 6__ generate the Robot Framework Test files (the actual Robot test plus an Include file)

## How does the final Robot code work?

The Robot Framework Datadriver processes the Excel file on a per-line basis. Due to each API call's previously determined ``operationId``, the program knows if an API call requires a request body to be sent to the API and which fields are to be included in that request body. So if the program 'knows' that a request body needs to be sent, it checks if a field (read: Excel cell) which belongs to this body has been populated or not. If it contains a value, it will add this field and its value to an internal dictionary - which will then be converted to a plain JSON body that is then to be sent to the API.