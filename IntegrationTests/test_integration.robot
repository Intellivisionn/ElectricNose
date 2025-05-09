*** Settings ***
Library    OperatingSystem
Library    Process
Library    glob

*** Variables ***
${PROJECT_ROOT}    ${CURDIR}/..
${PYTHON}          python
${DATA_READER}     IntegrationTests.mocks.DataReaderFake
${SENSOR_READER}   IntegrationTests.mocks.SensorReaderFake
${SAVED_DATA_DIR}  ${PROJECT_ROOT}/IntegrationTests/mocks/savedData
${SENSOR_JSON}     ${PROJECT_ROOT}/IntegrationTests/mocks/sensor_data.json

*** Test Cases ***
Integration Test With Fake Sensors
    [Documentation]    Integration test using fake sensors with real SensorReader logic.

    ${PROJECT_ROOT}=    Normalize Path    ${CURDIR}/..
    ${PYTHON}=          Set Variable    python
    ${DATA_READER}=     Set Variable    IntegrationTests.mocks.DataReaderFake
    ${SENSOR_READER}=   Set Variable    IntegrationTests.mocks.SensorReaderFake
    ${SAVED_DATA_DIR}=  Set Variable    ${PROJECT_ROOT}/IntegrationTests/mocks/savedData
    ${SENSOR_JSON}=     Set Variable    ${PROJECT_ROOT}/IntegrationTests/mocks/sensor_data.json

    Start Process    ${PYTHON}    -m    ${SENSOR_READER}
    ...    cwd=${PROJECT_ROOT}
    ...    stdout=IntegrationTests/reader.log
    ...    stderr=IntegrationTests/reader.err
    Sleep    5s

    Start Process    ${PYTHON}    -m    ${DATA_READER}    cwd=${PROJECT_ROOT}    stdin=test_scent
    ...    cwd=${PROJECT_ROOT}
    Sleep    10s

    Terminate All Processes

    ${search_path}=    Normalize Path    ${SAVED_DATA_DIR}/test_scent_*.json
    ${matches}=    Glob    ${search_path}

    Log    Search path: ${search_path}
    Log    Found matches: ${matches}

    Length Should Be    ${matches}    1
    File Should Exist    ${matches[0]}
    ${content}=    Get File    ${matches[0]}
    Should Contain    ${content}    Temperature

    ${reader_stdout}=    Get File    IntegrationTests/reader.log
    ${reader_stderr}=    Get File    IntegrationTests/reader.err
    Log    Reader STDOUT: ${reader_stdout}
    Log    Reader STDERR: ${reader_stderr}

    ${files}=    List Files In Directory    ${SAVED_DATA_DIR}   absolute=True
    FOR    ${file}    IN    @{files}
        Remove File    ${file}
    END
    Remove Directory    ${SAVED_DATA_DIR}
    Remove File    ${SENSOR_JSON}
