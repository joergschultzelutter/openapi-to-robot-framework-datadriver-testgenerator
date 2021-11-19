#!/opt/local/bin/python3
#
# OpenAPI-to-Robot-Framework-Data-Driver generator
# Author: Joerg Schultze-Lutter, 2021
#
# Read an OpenAPI V2/V3 spec file and create Robot Framework tests out of it
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# Sample OpenAPI V3 file for testing: https://petstore3.swagger.io/

import re
import json
import os.path
import logging
import xlsxwriter
from pprint import pformat
from datetime import datetime
import argparse
from prance import ResolvingParser
import sys
import requests

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

# Codes for the Excel sheet's cells
test_variables_color_code = "#bbbbbb"
test_cases_color_code = "f9e4b7"
optional_variable_color_code = "#99ee99"
required_variable_color_code = "ee9999"

# This is our Excel generator's start columm
# We will start adding the test's variable columns at this position
# Note that -as always- this index is zero-based which means that the
# first column that we add our data to is column 7 / "G"
start_column = 6

#
# You need to configure this setting in case you want this program to generate
# Jira/XRay test & test execution tickets. Replace this value with your correct
# Jira server URL and the path as shown here. Note that there are two occurrences
# in the code where this URL is being used. Your XRay server URL might need to
# get amended.
JIRA_SERVER_URL = "https://jira.acme.com:443"
#
# Additional mandatoryone-time Jira config changes which need to be applied to the templates:
# - Configure the Jira Project ID in both Jira template files
# - For the Jira "Test Execution" template, you must configure the correct "customfield" setting
#   for your Jira/XRay instance. This field references to XRay's "Test Environments" settings.
#   Unfortunately, neither Jira nor XRay provide you with a fixed field name. Keep in mind that you
#   are required to configure this per Jira instance; that field's name can/WILL differ per instance.


def check_and_create_data_directory(
    directory_name: str,
):
    """
    Check if the (output) directory is present and create it, if necessary

    Parameters
    ==========
    directory_name: 'str'
        target directory name (relative or absolute)

    Returns
    =======
    success: bool
        False in case of error
    """
    success = True
    if not os.path.exists(directory_name):
        logger.info(
            msg=f"Output directory {directory_name} does not exist, creating it ..."
        )
        try:
            os.mkdir(path=directory_name)
        except OSError:
            logger.info(
                msg=f"Cannot create data directory {directory_name}, aborting ..."
            )
            success = False
    else:
        if not os.path.isdir(directory_name):
            logger.info(msg=f"{directory_name} is not a directory, aborting ...")
            success = False
    return success


def check_if_file_exists(filename: str):
    """
    Simple wrapper for whether a file exists or not

    Parameters
    ==========
    filename: 'str'
        file whose presence we want to check

    Returns
    =======
    _: 'bool'
        True if file exists
    """

    return os.path.isfile(filename)


def read_template_file_from_disk(filename: str):
    """
    Checks if a file exists, reads its content and
    returns the content back to the user

    Parameters
    ==========
    filename: 'str'
        file whose presence we want to check

    Returns
    =======
    success: 'bool'
        True if the operation was successful
    file_content: 'str'
        'None' if file could not be read. Otherwise,
        variable holds the file content as string
    """

    success = False
    file_content = None

    if not check_if_file_exists(filename):
        logger.info(msg=f"Template {filename} does not exist")
        return success, file_content

    try:
        with open(filename, "r") as f:
            file_content = f.read()
            f.close()
            success = True
    except:
        success = False
        logger.info(msg=f"Cannot read template file {filename}")
        file_content = None
    return success, file_content


def read_template_files(
    template_directory: str = "templates",
    include: str = "template_robot_generic_includes.robot",
    footer: str = "template_robot_footer.robot",
    header: str = "template_robot_header.robot",
    keyword_body: str = "template_robot_keyword_with_request_body.robot",
    keyword_no_body: str = "template_robot_keyword_without_request_body.robot",
):
    """
    Tries to pre-load the template files for the
    robot header, robot footer and the keyword template(s)

    Parameters
    ==========
    template_directory: 'str'
        source directory in which the files are stored
    include: 'str'
        File name for a generic "includes" template
    footer: 'str'
        File name for the Robot Framework "footer" template
    header: 'str'
        File name for the Robot Framework "header" template
    keyword_body: 'str'
        File name for the Robot Framework "keyword_body" template
    keyword_no_body: 'str'
        File name for the Robot Framework "keyword_no_body" template

    Returns
    =======
    success: 'bool'
        True if the operation was successful
    includes_string: 'str'
        Content from the "includes" template
    footer_string: 'str'
        Content from  the Robot Framework "footer" template
        Footer can be 'None'
    header_string: 'str'
        Content from for the Robot Framework "header" template
    keyword_body_string: 'str'
        Content from the Robot Framework "keyword_body" template
    keyword_no_body_string: 'str'
        Content from the Robot Framework "keyword_no_body" template
    """

    success = False

    footer_string = None
    header_string = None
    keyword_body_string = None
    keyword_no_body_string = None
    includes_string = None

    includes_filename = os.path.join(template_directory, include)
    footer_filename = os.path.join(template_directory, footer)
    header_filename = os.path.join(template_directory, header)
    keyword_body_filename = os.path.join(template_directory, keyword_body)
    keyword_no_body_filename = os.path.join(template_directory, keyword_no_body)

    success, includes_string = read_template_file_from_disk(includes_filename)
    if not success:
        return False, None, None, None, None, None

    success, header_string = read_template_file_from_disk(header_filename)
    if not success:
        return False, None, None, None, None, None

    success, keyword_body_string = read_template_file_from_disk(keyword_body_filename)
    if not success:
        return False, None, None, None, None, None

    success, keyword_no_body_string = read_template_file_from_disk(
        keyword_no_body_filename
    )
    if not success:
        return False, None, None, None, None, None

    # our footer can be empty - this is desired behavior
    success, footer_string = read_template_file_from_disk(footer_filename)

    return (
        True,
        includes_string,
        header_string,
        footer_string,
        keyword_body_string,
        keyword_no_body_string,
    )


def create_jira_tickets(
    jira_access_key: str,
    test_cases: dict,
    openapi_filename: str,
    template_directory: str = "templates",
    jira_test: str = "template_jira_test_case",
    jira_test_execution: str = "template_jira_test_execution",
):

    """
    Creates the Jira tickets for our test cases

    Parameters
    ==========
    jira_access_key: 'str'
        'None' if no Jira tickets are supposed to be generated
        Otherwise, this field needs to contain the base64-encoded
        user:auth combination
    test_cases: 'dict'
        nested dictionary, containing all test cases with their
        associated optional and required variables
    openapi_filename: 'str'
        JSON or yaml schema
    template_directory: 'str'
        source directory in which the files are stored
    jira_test: 'str'
        predefined default template name for the Jira
        "Test" ticket template
    jira_test_execution: 'str'
        predefined default template name for the Jira
        "Test Execution" ticket template

    Returns
    =======
    success: 'bool'
        True if the operation was successful
    """
    assert jira_access_key is not None

    # Create the file names for the "Test" and "Test Execution" Jira request body templates
    jira_test_filename = os.path.join(template_directory, jira_test)
    jira_test_execution_filename = os.path.join(template_directory, jira_test_execution)

    # Read the template for the Jira 'Test' ticket type's request body
    success, jira_test_template = read_template_file_from_disk(
        filename=jira_test_filename
    )
    if not success:
        return success

    # Read the template for the Jira 'Test Execution' ticket type's request body
    success, jira_test_execution_template = read_template_file_from_disk(
        filename=jira_test_execution_filename
    )
    if not success:
        return success

    # This list contains all the Jira "Test" tickets that we will create in the next step
    jira_test_tickets = []

    # This is our default request header. It will be used
    # for both Jira REST and XRay REST requests
    jira_request_header = {
        "Authorization": f"Basic {jira_access_key}",
        "Content-Type": "application/json",
    }

    # Create 1..n Jira Test tickets
    for test_case in test_cases:
        # The test template will be used 1..n times so let's create a copy
        test_string = jira_test_template
        (test_case_name, test_case_operation, test_case_endpoint) = test_case

        # Extract the description. Note: As this field may contain quotation
        # marks, we need to get rid of them before we send the string to Jira
        description = test_cases[test_case]["description"]
        description = description.replace('"', '\\"').replace("'", "\\'")

        # Replace the placeholder data in our Jira "Test" ticket template
        test_string = test_string.replace("REPLACE_DESCRIPTION_REPLACE", description)
        test_string = test_string.replace(
            "REPLACE_TEST_CASE_NAME_REPLACE", test_case_name
        )

        jira_request_body = json.loads(test_string)

        # Jira expects a STRING for the request body - and on directory
        # so we need to send the JSON string to the rest API
        logger.debug(msg=f"Create Test ticket for {test_case_name}")
        success, jira_ticket_id = create_jira_item(
            request_header=jira_request_header,
            request_body=test_string,
            url=f"{JIRA_SERVER_URL}/jira/rest/api/2/issue/",
        )
        if success:
            logger.info(msg=f"Created Jira Test ticket {jira_ticket_id}")

            # Add the "Test" ticket ID to the list of tickets that will later
            # be referenced to the "Test Execution" ticket
            jira_test_tickets.append(jira_ticket_id)

            # Finally, add the Jira ticket ID as Tag to the list of
            # existing tags so that it will be automatically picked up
            # by the Excel / Robot generator
            #
            # Note that the following implementation assumes that we do have
            # at least one tag present - which might not always be the case
            if "tags" in test_cases[test_case]:
                if type(test_cases[test_case]["tags"] == list):
                    test_cases[test_case]["tags"].append(jira_ticket_id)

    # Have we created at least one "Test" ticket?
    if len(jira_test_tickets) > 0:
        # Replace some content in the Jira Test Execution Template ...
        jira_test_execution_template = jira_test_execution_template.replace(
            "REPLACE_API_NAME_REPLACE", openapi_filename
        )

        # ... and create the ticket
        logger.debug("Create Test Execution ticket")
        success, jira_ticket_id = create_jira_item(
            request_header=jira_request_header,
            request_body=jira_test_execution_template,
            url=f"{JIRA_SERVER_URL}/jira/rest/api/2/issue/",
        )
        if success:
            logger.info(msg=f"Created Jira Test Execution ticket {jira_ticket_id}")

            # Now we need to create the link between the test execution ticket and the tests
            # Create the dictionary which links the test cases to the test execution
            jira_execution_relation = {
                "add": jira_test_tickets,
            }

            # As usual, Jira requires this info as a string so let's dump the dict
            jira_execution_relation_string = json.dumps(jira_execution_relation)

            # This time, we need to access the XRay REST API so
            # we need to provide the XRay URL which differs from the Jira URL
            url = f"{JIRA_SERVER_URL}/jira/rest/raven/1.0/api/testexec/{jira_ticket_id}/test"

            logger.info(
                msg="Create relation between Jira Test(s) and the Jira Execution"
            )
            # For now, we don't care about the REST API's response and simply send the request to the XRay API
            # Note that the XRay API returns http200 for a successful response (Jira uses http201)
            success, _ = create_jira_item(
                request_body=jira_execution_relation_string,
                request_header=jira_request_header,
                url=url,
                expected_http_response=200,
                extract_ticket_id=False,
            )
            if not success:
                logger.info(
                    msg=f"Cannot create relationship between Jira Test Execution Ticket {jira_ticket_id} and its sub tickets {jira_test_tickets}"
                )
    else:
        logger.info(
            msg="Did not create any tickets - does your OpenAPI file contain any service methods at all?"
        )
        success = False

    return success


def create_jira_item(
    request_body: str,
    request_header: dict,
    url: str,
    expected_http_response: int = 201,
    extract_ticket_id: bool = True,
):
    """
    Contacts the Jira REST API and creates our ticket

    Parameters
    ==========
    request_body: 'str'
        JSON request body. Needs to be a JSON string and no dict
    request_header: 'dict'
        JSON request header (e.g. basic auth and content type)
    url: 'str'
        Jira REST URL
    expected_http_response: 'int'
        expected HTTP respponse code (XRay uses http200 vs. Jira uses http201
        for a successful operation)
    extract_ticket_id: 'bool'
        If False then the Jira ticket ID will not be extracted
        from the response (this is used for the XRay response - its
        response body is empty and holds no information whatsoever)

    Returns
    =======
    success: 'bool'
        True if the operation was successful
    jira_ticket_id: 'str'
        ID of the ticket that we have created (or 'None')

    """
    try:
        resp = requests.post(url=url, data=request_body, headers=request_header)
    except:
        resp = None

    # Request successful?
    if resp:
        if resp.status_code != expected_http_response:
            logger.debug(msg=f"Failed to create Jira ticket via url {url}, aborting")
            return False, None
    else:
        logger.debug(msg=f"Unable to access {url}, aborting")
        return False, None

    # If there is nothing to extract we can skip the remainder of the function
    if not extract_ticket_id:
        return True, None

    # Yep; parse the response item and convert it to JSON
    try:
        json_response = resp.json()
    except:
        json_response = None

    if not json_response:
        logger.debug(msg="Failed to convert response to json")
        return False, None

    # If there is a key in the response, then we were able to create our ticket
    if "key" in json_response:
        jira_ticket_key = json_response["key"]
        success = True
    else:
        jira_ticket_key = None
        success = False

    return success, jira_ticket_key


def parse_openapi_spec(openapi_filename: str):
    """
    Parse the given OpenAPI schema (can either be OpenAPI V3 or YAML)
    and return all relevant variables

    Parameters
    ==========
    openapi_filename: 'str'
        JSON or yaml schema

    Returns
    =======
    success: bool
        False in case of error
    servers: str
        list of servers that is associated with this API
    service_dictionary: dict
        nested dict which contains all variables (including the required ones)
        per url/operation/operationid
    all_service_variables: list
        list, containing the unique and sorted set of variables for this
    """

    _service_dictionary = {}
    _all_service_variables = []
    parser = None
    _success = False
    _servers = {}

    # Try to parse the file. If the parse process fails, check if your 
    # OpenAPI file is compliant. See
    # https://github.com/RonnyPfannschmidt/prance#compatibility for further 
    # information on this topic.
    try:
        parser = ResolvingParser(openapi_filename)
    except:
        parser = None
        logger.info(sys.exc_info()[0])

    if parser:
        if "servers" in parser.specification:
            _servers = parser.specification["servers"]

        _service_dictionary = {}
        varset = set()

        # fmt: off
        # Parse the OpenAPI spec
        for path in parser.specification["paths"]:
            operations = parser.specification["paths"][path]
            for operation in operations:
                if "tags" in parser.specification["paths"][path][operation]:
                    tags = parser.specification["paths"][path][operation]["tags"]
                else:
                    tags = ""
                if "summary" in parser.specification["paths"][path][operation]:
                    summary = parser.specification["paths"][path][operation]["summary"]
                else:
                    summary = ""
                if "description" in parser.specification["paths"][path][operation]:
                    description = parser.specification["paths"][path][operation]["description"]
                else:
                    description = ""

                # This is the test's identifying element - which should always be present
                if "operationId" in parser.specification["paths"][path][operation]:
                    operationid = parser.specification["paths"][path][operation]["operationId"]
                else:
                    logger.info(msg=pformat(parser.specification["paths"][path][operation]))
                    logger.info(msg="ERROR - no operationId present in OpenAPI file, cannot continue")
                    raise ValueError("No operationId present in OpenAPI file, cannot continue")

                required = properties = example = None
                if "requestBody" in parser.specification["paths"][path][operation]:
                    requestbody = parser.specification["paths"][path][operation]["requestBody"]
                    if "content" in requestbody:
                        if "application/json" in requestbody["content"]:
                            if "schema" in requestbody["content"]["application/json"]:
                                schema = requestbody["content"]["application/json"]["schema"]
                                if "required" in requestbody["content"]["application/json"]["schema"]:
                                    required = requestbody["content"]["application/json"]["schema"]["required"]
                                if "properties" in requestbody["content"]["application/json"]["schema"]:
                                    properties = requestbody["content"]["application/json"]["schema"]["properties"]
                            if "example" in requestbody["content"]["application/json"]:
                                example = requestbody["content"]["application/json"]["example"]

                # try to retrieve the list of valid HTTP return codes and
                # assume that the very first one in the list is the one that
                # we want for our tests. This may or may not be valid for your
                # use case but we can at least add a default to the Excel list
                if "responses" in parser.specification["paths"][path][operation]:
                    responses = parser.specification["paths"][path][operation]["responses"]
                    if len(responses) > 0:
                        expected_status_code = list(responses.keys())[0]
                        # Future tests expect this as integer so let"s try to convert the string
                        try:
                            expected_status_code = int(expected_status_code)
                        except ValueError:
                            # an empty string will cause a fallback to the (Robot) test's default
                            # value of 200 (=> http200)
                            expected_status_code = ""

                service_keys = (operationid, operation, path)
                _service_dictionary[service_keys] = {
                    "properties": properties,
                    "required": required,
                    "example": example,
                    "tags": tags,
                    "summary": summary,
                    "description": description,
                    "expected_status_code": expected_status_code
                }

                # Add the service method variables to our set (eliminates dupes)
                if properties:
                    for prop in properties:
                        varset.add(prop)

        # Convert our set to a list item ...
        _all_service_variables = list(varset)
        #  ... and sort that list alphabetically as it is more convenient to the end user
        _all_service_variables = sorted(_all_service_variables, key=str.lower)

        # fmt: on
        _success = True

    return _success, _servers, _service_dictionary, _all_service_variables


def write_excel_header(
    workbook: xlsxwriter.workbook.Workbook,
    worksheet: xlsxwriter.worksheet.Worksheet,
    all_service_variables: list,
):
    """
    Writes the future Excel file's header variables to the
    file in memory

    Parameters
    ==========
    workbook: 'xlsxwriter.workbook.Workbook'
        our open xlsxwriter workbook
    worksheet: 'xlsxwriter.worksheet.Worksheet'
        our open xlsxwriter worksheet
    all_service_variables: 'list'
        list item, containing a sorted unique list of OpenAPI input variables

    Returns
    =======
    maxcol: int
        maximum column value of our Excel sheet
    """

    # Start the process by setting up the cell formatting for our two use cases
    # we will only take care of header lines here which means that everything
    # that we are going to insert as content will be Bold/Italic
    # Fmt: off
    bold_test_case_cell_format = workbook.add_format({"bold": True, "italic": True})
    bold_test_variables_cell_format = workbook.add_format(
        {"bold": True, "italic": True}
    )
    # fmt: on

    # All cells use Excel's "Text" formatting (NOT "general")
    bold_test_case_cell_format.set_num_format("@")  #  Text
    bold_test_variables_cell_format.set_num_format("@")

    # Finally, we set the color coding as defined in our global variables
    bold_test_variables_cell_format.set_bg_color(test_variables_color_code)
    bold_test_case_cell_format.set_bg_color(test_cases_color_code)

    # Set the Excel file's first columns - their content is always fixed
    # so we can write it to the file without knowing the OpenAPI file's
    # content at this point in time
    worksheet.write(0, 0, "*** Test Case ***", bold_test_case_cell_format)
    worksheet.write(0, 1, "[Documentation]", bold_test_case_cell_format)
    worksheet.write(0, 2, "[Tags]", bold_test_case_cell_format)
    worksheet.write(0, 3, "${API_CALL}", bold_test_case_cell_format)
    worksheet.write(0, 4, "${API_OPERATION}", bold_test_case_cell_format)
    worksheet.write(0, 5, "${EXPECTED_STATUS_CODE}", bold_test_case_cell_format)

    #
    # now add the sorted&unified service variable names to row 0 (headers)
    # we will start at the predefined 'start_column' value
    #
    col = start_column

    # calculate the future maxcol value
    maxcol = start_column + len(all_service_variables)

    # Write the variables to the Excel sheet
    for variable in all_service_variables:
        content = "${" + variable + "}"
        # Add the field to row 0 and the current column
        worksheet.write(0, col, content, bold_test_variables_cell_format)

        # Increase our column counter
        col += 1

    # Finally, return our Excel sheet's "x" dimension to the user
    return maxcol


def write_excel_test_case_data(
    workbook: xlsxwriter.workbook.Workbook,
    worksheet: xlsxwriter.worksheet.Worksheet,
    all_service_variables: list,
    test_cases: dict,
    add_example_data: bool = False,
):
    """
    Writes the future Excel file's header variables to the
    file in memory

    Parameters
    ==========
    workbook: 'xlsxwriter.workbook.Workbook'
        our open xlsxwriter workbook
    worksheet: 'xlsxwriter.worksheet.Worksheet'
        our open xlsxwriter worksheet
    all_service_variables: 'list'
        list item, containing a sorted unique list of OpenAPI input variables
    test_cases: 'dict'
        nested dictionary, containing all test cases with their
        associated optional and required variables
    add_example_data: 'bool'
        If True and a service method's variable has a valid value defined in
        its definition, then that value will be copied to the Excel sheet

    Returns
    =======
    maxrow: int
        maximum row value of our Excel sheet
    """

    # Start the process by setting up the cell formatting for our two use cases
    # we will only take care of data here which means that everything
    # that we are going to insert as content will use standard stext format
    test_case_cell_format = workbook.add_format()
    test_variables_cell_format = workbook.add_format()
    optional_variable_cell_format = workbook.add_format()
    required_variable_cell_format = workbook.add_format()

    # All cells use Excel's "Text" formatting (NOT "general")
    test_case_cell_format.set_num_format("@")  #  Text
    test_variables_cell_format.set_num_format("@")
    optional_variable_cell_format.set_num_format("@")
    required_variable_cell_format.set_num_format("@")

    # Finally, we set the color coding as defined in our global variables
    test_variables_cell_format.set_bg_color(test_variables_color_code)
    test_case_cell_format.set_bg_color(test_cases_color_code)
    optional_variable_cell_format.set_bg_color(optional_variable_color_code)
    required_variable_cell_format.set_bg_color(required_variable_color_code)

    # calculate our maximum row (zero-based index)
    maxrow = len(test_cases)

    # calculate our maximum row (zero-based index)
    maxcol = start_column + len(all_service_variables)

    # Apply a cosmetic change to the Excel sheet's range (1,maxrow) - (maxrow,maxcol)
    # we simply apply the same background color to these cells
    # xlsxwriter cannot deal with regions so we need to do this
    # on a per-cell basis
    #
    # Note that this needs to be done BEFORE we fill the sheet with
    # content as otherwise, we will overwrite the existing "optional"
    # and "required" cell content
    #
    for row in range(1, maxrow + 1):  #  +1 + header
        for col in range(start_column, maxcol):
            worksheet.write(row, col, "", test_variables_cell_format)

    # Row will act as a mere iterator and will start from line 2 (our data storage)
    row = 1

    # Now iterate through all of our test cases
    for test_case in test_cases:
        # deconstruct the key information from the key's tuple
        (test_case_name, test_case_operation, test_case_endpoint) = test_case

        # now get the rest of the information that we need in order to write
        # our test case information to the Excel sheet
        tags = test_cases[test_case]["tags"]
        summary = test_cases[test_case]["summary"]
        properties = test_cases[test_case]["properties"]
        required = test_cases[test_case]["required"]
        expected_status_code = test_cases[test_case]["expected_status_code"]


        # Transform the 'tags' list item into a comma separated value
        if tags:
            tags_csv_string = ",".join(tags)
        else:
            tags_csv_string = ""

        # write the test case header data
        worksheet.write(row, 0, test_case_name, test_case_cell_format)
        worksheet.write(row, 1, summary, test_case_cell_format)
        worksheet.write(row, 2, tags_csv_string, test_case_cell_format)
        worksheet.write(row, 3, test_case_name, test_case_cell_format)
        worksheet.write(row, 4, test_case_operation.upper(), test_case_cell_format)
        worksheet.write(row, 5, expected_status_code, test_case_cell_format)

        # does this service method come with any properties?
        if properties:
            for prop in properties:
                try:
                    # hint: we use the sorted list of variables as xlsxwriter
                    # does not permit accessing data that we have written to
                    # our yet virtual Excel sheet. The order in the Excel sheet
                    # and our variable is still the very same.
                    col = all_service_variables.index(prop)
                except ValueError:
                    col = -1
                # did we find something? Sweet!
                if col != -1:
                    # We already know that we have a match. Set it to "optional" as default
                    # set content and cell format
                    column_content = ""
                    fmt = optional_variable_cell_format
                    if required:
                        if prop in required:
                            column_content = ""
                            fmt = required_variable_cell_format

                    # Now check if this variable has enum properties
                    enum_value = None
                    if "enum" in properties[prop]:
                        logger.debug(msg=f"Variable {prop} has enum content")
                        enum_value = properties[prop]["enum"]

                    # Check if we are supposed to add the variable's example
                    # data to the cell (if present)
                    if add_example_data:
                        if "example" in properties[prop]:
                            column_content = properties[prop]["example"]

                    # finally, write the content to the Excel sheet
                    worksheet.write(row, col + start_column, column_content, fmt)

                    # Do we have a set of valid values for this cell?
                    # If yes, then add that list as data validation rule to the cell
                    # and allow free text entries
                    if enum_value:
                        worksheet.data_validation(
                            row,
                            col + start_column,
                            row,
                            col + start_column,
                            {
                                "validate": "list",
                                "value": enum_value,
                                "show_error": False,
                            },
                        )
        # Increase our row counter and continue with the next test case
        row += 1

    # Clean up the column with for making the file more legible
    # (xlsxwriter does not support autofit so we need to tune this manually)
    worksheet.set_column(2, maxcol, 25)
    worksheet.set_column(0, 1, 50)

    return maxrow


def write_robot_framework_includes_file(
    servers: dict,
    template_string: str,
    target_filename: str,
    openapi_filename: str,
):
    """
    Writes the Robot Framework 'includes.resource' file

    Parameters
    ==========
    servers: 'dict'
        dictionary which contains 1..n applicable base URLs
    template_string: 'str'
        includes.resource template string
    target_filename: 'str'
        Target filename for the 'includes.resource' file that
        is to be written to disc
    openapi_filename: 'str'
        name of our input file (for printing it in the
        output file's header)

    Returns
    =======
    success: bool
        True if write operation was successful
    """

    # This is our base URL's default in case we can't properly identify it
    base_url = "BASE_URL_NOT_FOUND_AND_NEEDS_TO_BE_SET_MANUALLY"

    # Pattern for extracting the (correct) base URL
    # this may not really be necessary as all target URLs do contain the
    # same path. But for now, let's simply assume that it is required
    regex = r"https:\/\/api.*(\/.*\/.*)"
    for server in servers:
        url = server["url"]
        matches = re.search(pattern=regex, string=url)
        if matches:
            base_url = matches[1]

    # replace the URL in our includes file template
    template_string = template_string.replace(
        "REPLACE_ROBOT_BASE_URL_REPLACE", base_url
    )

    template_string = template_string.replace(
        "REPLACE_OPENAPI_FILENAME_REPLACE", openapi_filename
    )
    dt = datetime.strftime(datetime.now(), "%d-%b-%Y %H:%M:%S")
    template_string = template_string.replace("REPLACE_DATETIME_CREATION_REPLACE", dt)

    # and write the includes file to disc
    try:
        with open(target_filename, "w") as f:
            f.write(template_string)
            f.close()
            success = True
    except:
        logger.info(msg=f"Error writing file {target_filename} to disc")
        success = False
    return success


def write_robot_framework_test_case_file(
    all_service_variables: list,
    test_cases: dict,
    target_filename: str,
    openapi_filename: str,
    header_template: str,
    footer_template: str,
    keyword_body_template: str,
    keyword_no_body_template: str,
):
    """
    Writes the SDMS Robot Framework test case file

    Parameters
    ==========
    all_service_variables: list
        list, containing the unique and sorted set of variables for this
    test_cases: dict
        nested dict which contains all variables (including the required ones)
        per url/operation/operationid
    target_filename: 'str'
        Target filename for the 'includes.resource' file that
        is to be written to disc
    openapi_filename: 'str'
        name of our input file (for printing it in the
        output file's header)
    header_template: 'str'
        Robot output file header template
    footer_template: 'str'
        Robot output file footer template
    keyword_body_template: 'str'
        Robot output file template for keywords with request body
    keyword_no_body_template: 'str'
        Robot output file template for keywords without request body

    Returns
    =======
    success: bool
        True if write operation was successful
    """

    # open the Robot file for writing
    try:
        robot_file = open(target_filename, "w")
    except:
        logger.info(msg=f"Cannot open Robot file {target_filename} for writing")
        return False

    # Create the Robot Framework Arguments String that we will use to pass along
    # the vars to each test case
    my_arguments_string = "${API_CALL}  ${API_OPERATION}  ${EXPECTED_STATUS_CODE}"
    for service_var in all_service_variables:
        content = "${" + service_var + "}"
        my_arguments_string += f"  {content}"

    # We now have access to the whole set of arguments for the DataDriver use case
    # Use the RF template, replace the content and write the file header to
    # our Robot output file
    # fmt: off
    _header_string = header_template.replace("REPLACE_DATA_DRIVER_ARGUMENTS_REPLACE", my_arguments_string)
    _header_string = _header_string.replace("REPLACE_OPENAPI_FILENAME_REPLACE", openapi_filename)
    dt = datetime.strftime(datetime.now(), "%d-%b-%Y %H:%M:%S")
    _header_string = _header_string.replace("REPLACE_DATETIME_CREATION_REPLACE", dt)
    # fmt: on
    robot_file.write(_header_string)

    #
    # Now iterate through all of our test cases
    #

    for test_case in test_cases:
        # deconstruct the key information from the key's tuple
        (test_case_name, test_case_operation, test_case_endpoint) = test_case

        # String which contains variable definitions in case there are URL parameters
        url_parameters = ""

        # Check if there seem to be any parameters in our URL
        # If yes, add them (with default settings) to our script and amend the URL format
        # so that Robot can digest it
        if "{" in test_case_endpoint:
            url_parameters += "\n"
            regex = r"\{(.*?)\}"
            matches = re.finditer(regex, test_case_endpoint, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                for groupNum in range(0, len(match.groups())):
                    groupNum = groupNum + 1
                    # Create a set of Robot Framework variable definitions in our script
                    grp = match.group(groupNum)
                    url_parameters += (
                        "    Set Test Variable  ${"
                        + match.group(groupNum)
                        + "}  "
                        + match.group(groupNum)
                        + "\n"
                    )
            # Finally, let's replace all occurrences where there are curly braces in the URL
            # Robot needs these to start with a "$" sign
            test_case_endpoint = test_case_endpoint.replace("{", "${")

        # Convert test case operation to uppercase
        test_case_operation = test_case_operation.upper()

        # now get the rest of the information that we need in order to write
        # our test case information to the Excel sheet
        summary = test_cases[test_case]["summary"]
        properties = test_cases[test_case]["properties"]

        # Based on whether we need to send a JSON Request body or not,
        # let's now pick the correct template
        _keyword_placeholder = (
            keyword_body_template if properties else keyword_no_body_template
        )

        # Assign the HTTP operation (GET, PUT, ...)
        _keyword_placeholder = _keyword_placeholder.replace(
            "REPLACE_OPERATION_REPLACE", test_case_operation
        )

        # Assign the operation ID (= our service method)
        _keyword_placeholder = _keyword_placeholder.replace(
            "REPLACE_OPERATIONID_REPLACE", test_case_name
        )

        # Assign the Test Case Documentation
        _keyword_placeholder = _keyword_placeholder.replace(
            "REPLACE_DOCUMENTATION_REPLACE", summary
        )

        # Assign the keyword arguments
        _keyword_placeholder = _keyword_placeholder.replace(
            "REPLACE_DATA_DRIVER_ARGUMENTS_REPLACE", my_arguments_string
        )

        # Assign the variable definitions (or an empty string if there are none)
        _keyword_placeholder = _keyword_placeholder.replace(
            "REPLACE_URL_PARAMETERS_REPLACE", url_parameters
        )

        # If we need to supply a JSON request body, then let's create it
        if properties:
            logger.debug(
                f"Test Case '{test_case}' requires us to create a JSON request body"
            )

            # our target variable
            properties_generator_string = ""

            # iterate through the variables that belong to this OpenAPI schema
            for prop in properties:
                properties_generator_string += "    ${JsonDictionary}=  Add Variable To Dict If Value Is Not None  VARIABLE_NAME="
                properties_generator_string += prop
                properties_generator_string += "  VARIABLE_VALUE=${"
                properties_generator_string += prop
                properties_generator_string += "}  OUTPUT_DICT=${JsonDictionary}\n"

            # and copy the content to the template
            _keyword_placeholder = _keyword_placeholder.replace(
                "REPLACE_SCHEMA_GENERATOR_STRING_REPLACE", properties_generator_string
            )

        # Replace the HTTP operation
        _keyword_placeholder = _keyword_placeholder.replace(
            "REPLACE_HTTP_OPERATION_REPLACE", test_case_operation
        )

        # Replace the API sub path
        _keyword_placeholder = _keyword_placeholder.replace(
            "REPLACE_API_PATH_REPLACE", test_case_endpoint
        )

        # write our test case to disc
        robot_file.write(_keyword_placeholder)

    # Finally, write the Robot footer template if it is present. We don't replace
    # anything in here but simply write it to our output file 'as is'
    if footer_template:
        robot_file.write(footer_template)

    robot_file.close()
    return True


def transform_openapi_to_robot(
    openapi_filename: str,
    output_filename: str,
    output_dir: str,
    add_example_data: bool,
    jira_access_key: str,
):
    """
    The OpenAPI file & Output Generator master parser

    Parameters
    ==========
    openapi_filename: 'str'
        reference to an input file which contains an OpenAPI API spec JSON/YAML
    output_filename: 'str'
        Robot / Excel target filename without file extension
    output_dir: 'str'
        Target directory mfor the output files
    add_example_data: 'bool'
        if True and the variable's definition contains example data,
        then this example data will be added to the Excel sheet
    jira_access_key: 'str'
        'None' if no Jira tickets are supposed to be generated
        Otherwise, this field needs to contain the base64-encoded
        user:auth combination

    Returns
    =======
    _: 'bool'
        True the operation was successful
    """
    data = None  #  Our OpenAPI file's content

    logger.info(msg="PASS 1 - Read Test Generator output templates")

    # our target filename default settings - amend if necessary
    target_filename = output_filename
    robot_target_filename = os.path.join(output_dir, target_filename + ".robot")
    excel_target_filename = os.path.join(output_dir, target_filename + ".xlsx")

    # SDMS includes reference - will be updated with the matching base URL
    includes_target_filename = os.path.join(output_dir, "includes.resource")

    # create the output directory if necessary
    if not check_and_create_data_directory(output_dir):
        return False

    # get our template texts from the external files
    # Footer is optional and variable value will be 'None' if the file is not present
    (
        success,
        includes_string,
        header_string,
        footer_string,
        keyword_body_string,
        keyword_no_body_string,
    ) = read_template_files()
    if not success:
        return False

    logger.info(msg=f"PASS 2 - Parse OpenAPI file {openapi_filename}")

    # Check if the OpenAPI file exists
    if not check_if_file_exists(openapi_filename):
        logger.info(msg=f"OpenAPI file {openapi_filename} does not exist; aborting")
        return False

    # Now try to parse the OpenAPI file
    success, servers, service_dictionary, all_service_variables = parse_openapi_spec(
        openapi_filename=openapi_filename
    )

    if not success:
        logger.info(msg=f"Cannot parse OpenAPI file{openapi_filename}; aborting")
        return False

    # Prepare our content for debug purposes
    logger.debug("OpenAPI parser successful. Variables:")
    logger.debug(f"Servers: {pformat(servers)}")
    logger.debug(f"Unique set of variables: {pformat(all_service_variables)}")
    logger.debug(f"Service dictionary / API methods: {pformat(service_dictionary)}")

    # At this point in time, we already have parsed the whole OpenAPI file
    # which means that we can immediately start with poppulating
    # our output file(s)

    # Check if we need to create Jira tickets. As the ticket IDs will be part of the
    # Excel file's 'tags' section, we need to create the tickets (and enrich the internal
    # data structures prior to writing the Excel file and the Robot test file
    if jira_access_key:
        logger.info(msg=f"PASS 3 - Create Jira tickets")
        success = create_jira_tickets(
            jira_access_key=jira_access_key,
            test_cases=service_dictionary,
            openapi_filename=openapi_filename,
        )
    else:
        logger.info(msg=f"skipping PASS 3 - no Jira access credentials provided")
        success = True

    if not success:
        logger.info(msg=f"Unable to create Jira tickets")
        return False

    logger.info(msg=f"PASS 4 - Generate Excel file '{excel_target_filename}'")

    # Create the Excel file and the worksheet that we are going to write to
    # Hint: this only creates the in-memory object. At this point in time, we
    # cannot yet check if we can write the file or not
    logger.debug(msg="Create the Excel file")
    workbook = xlsxwriter.Workbook(excel_target_filename)
    worksheet = workbook.add_worksheet()

    # Add the fixed column headers and the set of unique & sorted variables to
    # the Excel sheet. As a result, we will receive the maximum column value for
    # this sheet (x axis)
    maxcol = write_excel_header(
        workbook=workbook,
        worksheet=worksheet,
        all_service_variables=all_service_variables,
    )

    # Now write the text cases to the Excel sheet
    maxrow = write_excel_test_case_data(
        workbook=workbook,
        worksheet=worksheet,
        all_service_variables=all_service_variables,
        test_cases=service_dictionary,
        add_example_data=add_example_data,
    )

    # Try to write the Excel file from memory to disc
    try:
        workbook.close()
    except xlsxwriter.exceptions.FileCreateError:
        logger.info(f"Cannot write Excel file {excel_target_filename} to disc")
        return False

    #
    # END of Excel file generation
    #

    #
    # BEGIN of Robot Framework test case generation
    #

    # Write the Robot Framework 'includes.resource' file to disc
    # (This is our base include file which contains references to
    # our current API as well as include references to our core libs)
    logger.info(
        msg=f"PASS 5 - Generate Robot Framework 'includes' file '{includes_target_filename}'"
    )
    success = write_robot_framework_includes_file(
        servers=servers,
        template_string=includes_string,
        target_filename=includes_target_filename,
        openapi_filename=openapi_filename,
    )
    if not success:
        return False

    # Write the Robot Framework test case file to disc
    logger.info(
        msg=f"PASS 6 - Generate Robot Framework test case file '{robot_target_filename}'"
    )
    success = write_robot_framework_test_case_file(
        all_service_variables=all_service_variables,
        test_cases=service_dictionary,
        target_filename=robot_target_filename,
        openapi_filename=openapi_filename,
        header_template=header_string,
        footer_template=footer_string,
        keyword_body_template=keyword_body_string,
        keyword_no_body_template=keyword_no_body_string,
    )

    # ça s'est fini
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "inputfile",
        type=argparse.FileType("r"),
        help="OpenAPI V3 JSON or YAML Schema input file",
    )
    parser.add_argument(
        "--outputfile",
        default="export",
        type=str,
        help="Name of the Robot / Excel output file (without file extension)",
    )
    parser.add_argument(
        "--jira_access_key",
        default=None,
        type=str,
        help="Jira Basic Auth-encoded access key",
    )
    parser.add_argument(
        "--outputdir",
        default="output",
        type=str,
        help="Name of the target output directory",
    )
    parser.add_argument(
        "--add_example_data",
        dest="add_example_data",
        action="store_true",
        help="Add a variable's example data to the Excel sheet (if present in the OpenAPI spec)",
    )
    parser.set_defaults(add_example_data=False)

    args = parser.parse_args()
    openapi_filename = args.inputfile.name
    output_file = args.outputfile
    output_dir = args.outputdir
    add_example_data = args.add_example_data
    jira_access_key = args.jira_access_key

    logger.info(
        msg=transform_openapi_to_robot(
            openapi_filename=openapi_filename,
            output_filename=output_file,
            output_dir=output_dir,
            add_example_data=add_example_data,
            jira_access_key=jira_access_key,
        )
    )
