*** Settings ***
Library    OperatingSystem
Library    Process
Library    glob

*** Variables ***
${FAKE_PATH}      ${CURDIR}/mocks
${PYTHON}         python
${DATA_READER}    IntegrationTests/mocks/DataReaderFake.py
${SENSOR_READER}  IntegrationTests/mocks/SensorReaderFake.py

*** Test Cases ***
Integration Test With Fake Sensors
    [Documentation]    Integration test using fake sensors with real SensorReader logic.

    ${current_pythonpath}=    Get Environment Variable    PYTHONPATH    default=
    Set Environment Variable    PYTHONPATH    ${FAKE_PATH}:${current_pythonpath}

    # Start the SensorReader in the background
    Start Process    ${PYTHON}    ${SENSOR_READER}
    Sleep    5s

    # Simulate input to DataReader (in another process)
    Start Process    bash    -c    echo test_scent | ${PYTHON} ${DATA_READER}
    Sleep    10s

    # Stop all processes
    Terminate All Processes

    # Look for the generated data file
    ${matches}=    Glob    savedData/test_scent_*.json
    Length Should Be    ${matches}    1

    # Verify that the file exists and contains expected sensor key
    File Should Exist    ${matches[0]}
    ${content}=    Get File    ${matches[0]}
    Should Contain    ${content}    Temperature
