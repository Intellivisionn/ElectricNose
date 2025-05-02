*** Settings ***
Library    OperatingSystem
Library    Process
Library    glob

*** Variables ***
${PROJECT_ROOT}    Normalize Path    ${CURDIR}/..
${PYTHON}          python
${DATA_READER}     IntegrationTests.mocks.DataReaderFake
${SENSOR_READER}   IntegrationTests.mocks.SensorReaderFake

*** Test Cases ***
Integration Test With Fake Sensors
    [Documentation]    Integration test using fake sensors with real SensorReader logic.

    # Start sensor reader
    Start Process    ${PYTHON}    -m    ${SENSOR_READER}    cwd=${PROJECT_ROOT}
    Sleep    5s

    # Run data reader
    Start Process    bash    -c    echo test_scent \| ${PYTHON} -m ${DATA_READER}    cwd=${PROJECT_ROOT}
    Sleep    10s

    Terminate All Processes

    ${search_path}=    Normalize Path    ${PROJECT_ROOT}/IntegrationTests/savedData/test_scent_*.json

    FOR    ${i}    IN RANGE    5
        ${matches}=    Glob    ${search_path}
        Exit For Loop If    ${matches}
        Sleep    1s
    END

    Log    Matching path: ${search_path}
    Log    Found files: ${matches}

    Length Should Be    ${matches}    1
    File Should Exist    ${matches[0]}
    ${content}=    Get File    ${matches[0]}
    Should Contain    ${content}    Temperature