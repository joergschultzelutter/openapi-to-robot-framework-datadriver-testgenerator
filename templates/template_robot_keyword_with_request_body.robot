Data_Driver_REPLACE_OPERATION_REPLACE_REPLACE_OPERATIONID_REPLACE
    [Documentation]    REPLACE_DOCUMENTATION_REPLACE
    [arguments]    REPLACE_DATA_DRIVER_ARGUMENTS_REPLACE
REPLACE_URL_PARAMETERS_REPLACE
    ${JsonDictionary}=          Create Dictionary

REPLACE_SCHEMA_GENERATOR_STRING_REPLACE
    ${JSON_BODY}=               Evaluate    json.dumps(${JsonDictionary})    json

    ${response_status}          ${response_body}    ${response_header} =     Send API Request    HTTP_METHOD=REPLACE_HTTP_OPERATION_REPLACE    URL_PATH=${ROBOT_BASE_URL}REPLACE_API_PATH_REPLACE    BODY=${JSON_BODY}    EXPECTED_STATUS_CODE=${EXPECTED_STATUS_CODE}
    Log To Console              ${response_body}

