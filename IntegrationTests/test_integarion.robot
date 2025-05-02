*** Settings ***
Library    OperatingSystem
Library    Process
Library    glob

*** Variables ***
${PROJECT_ROOT}    ${CURDIR}/../..
${PYTHON}          python
${DATA_READER}     IntegrationTests.mocks.DataReaderFake
${SENSOR_READER}   IntegrationTests.mocks.SensorReaderFake

*** Test Cases ***
Integration Test With Fake Sensors
    [Documentation]    Integration test using fake sensors with real SensorReader logic.

    # Start the SensorReader using module mode
    Start Process    ${PYTHON}    -m    ${SENSOR_READER}    cwd=${PROJECT_ROOT}
    Sleep    5s

    # Simulate input using DataReader (echo piped)
    Start Process    bash    -c    echo test_scent \| ${PYTHON} -m ${DATA_READER}    cwd=${PROJECT_ROOT}
    Sleep    10s

    Terminate All Processes

    ${matches}=    Glob    ${PROJECT_ROOT}/IntegrationTests/savedData/test_scent_*.json
    Length Should Be    ${matches}    1
    File Should Exist    ${matches[0]}
    ${content}=    Get File    ${matches[0]}
    Should Contain    ${content}    Temperature