#
# Robot Framework Data Driver Test Case
# Auto-generated test case from OpenAPI file 'REPLACE_OPENAPI_FILENAME_REPLACE' at 'REPLACE_DATETIME_CREATION_REPLACE'
#

*** Settings ***
Library             DataDriver   .xlsx    preserve_xls_types=True
Library             OperatingSystem
Library             Collections

# generic Includes
Resource            includes.resource

# This is the test case's single point of entry
Test Template       Data Driver Main

*** Variables ***
# JSON request body (if supported by the respective service method)
${JSON_BODY}        ${EMPTY}

*** Test Cases ***
# This test case is never going to be executed. 
# It only exists because without a test case present in the file,
# the Robot Framework will refrain from executing the data driver test cases.
Robot Framework Action Keyword '${API_CALL}'
    [Documentation]	Run the test cases for method ${API_CALL}

*** Keywords ***
Data Driver Main
    [Documentation]                 This is the datadriver's single point of entry which takes all data from the Excel sheet and calls the target keyword
    [arguments]                     REPLACE_DATA_DRIVER_ARGUMENTS_REPLACE

    ${ROBOT_ENVIRONMENT} =          Validate Robot Environment                  ENVIRONMENT=${ROBOT_ENVIRONMENT}
    ${EXPECTED_STATUS_CODE} =       Get The Expected Status Code From Excel	    EXPECTED_STATUS_CODE=${EXPECTED_STATUS_CODE}

    Run Keyword                     Data_Driver_${API_OPERATION}_${API_CALL}  REPLACE_DATA_DRIVER_ARGUMENTS_REPLACE

