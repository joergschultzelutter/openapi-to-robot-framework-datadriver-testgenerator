
## Additional code which might be required by your test
## Remember - all of these are keywords and not tests!

Add Variable To Dict If Value Is Not None
	[Documentation]			Function: Internal helper method. Check a variable's data type and add key/value to dictionary if value is present and the data type is scalar
	...						| *Input/Output* | *optional* | *Parameter*     | *Description*                                                             | *Default value/variable for optional parameters*      |
	...						| Input          | no         | VARIABLE_NAME   | "key" part of the variable. We add this if the value is not None+scalar   | n/a; mandatory parameter                              |
	...						| Input          | no         | VARIABLE_VALUE  | "value" part of the variable. We add this if the value is not None+scalar | n/a; mandatory parameter                              |
	...						| Input          | no         | OUTPUT_DICT     | The output dictionary that we#re going to add the k/v pair to             | n/a; mandatory parameter                              |
	...						| Output         | no         | OUTPUT_DICT     | Out (potentially) modified output dictionary with the new key/value       | n/a; mandatory parameter                              |
	[arguments]		${VARIABLE_NAME}	${VARIABLE_VALUE}	${OUTPUT_DICT}

	${data_type}=    	                Check Variable Type         ${VARIABLE_VALUE}
	Return From Keyword If				'${data_type}' == 'None'	${OUTPUT_DICT}

	Set To Dictionary					${OUTPUT_DICT}	${VARIABLE_NAME}	${VARIABLE_VALUE}
	[Return]							${OUTPUT_DICT}

Check Variable Type
 	[Documentation]			Function: Check a variable's data type and return data type and value to the user. Non-Scalar data types or empty values are returned as 'NONE' data type
	...						| *Input/Output* | *optional* | *Parameter* | *Description*                                                   | *Default value/variable for optional parameters*      |
	...						| Input          | no         | object      | Variable value that we are going to examine                     | n/a; mandatory parameter                              |
	...						| Output         | no         | data type   | The data type. Can be NONE, NUMBER, INTEGER, BOOLEAN or STRING  | n/a; mandatory parameter                              |
	...						| Output         | no         | data value  | The (transformed) value, e.g. a float value if data type=NUMBER | n/a; mandatory parameter                              |
   [Arguments]    ${object}
 
    Return From Keyword If		    not "${object}"    None

    ${VARTYPE}=                     Evaluate     type($object).__name__
	[Return]                        ${VARTYPE}


Get The Expected Status Code From Excel
	[Documentation]			Function: Internal helper method. Checks if a numeric HTTP status is present (und uses this one) - otherwise, http200 will be used as default
	...						| *Input/Output* | *optional*                     | *Parameter*               | *Description*                                                             | *Default value/variable for optional parameters*      |
	...						| Input          | no                             | EXPECTED_STATUS_CODE      | Status Code variable. If empty, we will use (http)200 as default          | n/a; mandatory parameter                              |
	...						| Output         | no                             | EXPECTED_STATUS_CODE      | (Potentially) transformed HTTP status code                                | n/a; mandatory parameter                              |
	[Arguments]    ${EXPECTED_STATUS_CODE}

	# Convert status code to numeric value. If not populated, use (HTTP)200 as default - otherwise, use the value that the user has provided us with
	${data_type}= 	Check Variable Type    ${EXPECTED_STATUS_CODE}
	${EXPECTED_STATUS_CODE} = 		       Set Variable If            '${data_type}' == 'int'    ${EXPECTED_STATUS_CODE}    200
	[return]	                           ${EXPECTED_STATUS_CODE}

 Validate Robot Environment
	[Documentation]			Function: Validate the $ENVIRONMENT parameter and convert its value to lower case
	...						| *Input/Output* | *optional*  | *Parameter* | *Description*                                                   | *Default value/variable for optional parameters* |
	...						| Input          | no          | ENVIRONMENT | Environment variable. Valid values: "Development","Production"  | n/a; mandatory parameter                         |
	...						| Output         | no          | ENVIRONMENT | Validated $ENVIRONMENT variable, converted to lower case        | n/a                                              |
	...
	[arguments]				${ENVIRONMENT}	

	# This parameter represents the list of all valid environment names
	@{T_VALID_ENVIRONMENTS}=					Create List		production	development
	
	# convert environment parameter to lowercase. Check if it is present in the list of valid environments
	${ENVIRONMENT} =							Convert To Lower Case	${ENVIRONMENT}
	List Should Contain Value					${T_VALID_ENVIRONMENTS}	${ENVIRONMENT}	msg=Invalid environment parameter; received: '${ENVIRONMENT}'; supported: ${T_VALID_ENVIRONMENTS}
	
	[return]				${ENVIRONMENT}

