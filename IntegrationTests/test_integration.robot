*** Settings ***
Library    OperatingSystem
Library    Process
Library    glob

*** Variables ***
${PROJECT_ROOT}      ${CURDIR}/..
${PYTHON}            python
${BROKER}            IntegrationTests.mocks.WebSocketFake
${DATA_COLLECTOR}    IntegrationTests.mocks.DataCollectorFake
${SENSOR_READER}     IntegrationTests.mocks.SensorReaderFake
${SAVED_DATA_DIR}    ${PROJECT_ROOT}/IntegrationTests/mocks/savedData
${SENSOR_JSON}       ${PROJECT_ROOT}/IntegrationTests/mocks/sensor_data.json

*** Test Cases ***
Integration Test With Fake Sensors
    [Documentation]    Integration test using fake sensors over WebSocket (no JSON‐fallback).

    # ─── Inject broker URI/port so collector and reader talk to our fake ───
    Set Environment Variable    BROKER_URI    ws://localhost:8765
    Set Environment Variable    BROKER_PORT   8765

    # 1) start the fake WebSocket broker
    Start Process    ${PYTHON}    -m    ${BROKER}    cwd=${PROJECT_ROOT}
    Sleep            1s

    # 2) start the fake sensor producer (registers & broadcasts)
    Start Process    ${PYTHON}    -m    ${SENSOR_READER}
    ...              cwd=${PROJECT_ROOT}
    ...              stdout=IntegrationTests/reader.log
    ...              stderr=IntegrationTests/reader.err
    Sleep            5s

    # 3) start the real DataCollector (connects, receives, writes)
    Start Process    ${PYTHON}    -m    ${DATA_COLLECTOR}
    ...              cwd=${PROJECT_ROOT}
    ...              stdin=test_scent
    Sleep            10s

    Terminate All Processes

    # ─── Verify output file contains at least one reading ───
    ${search_path}=    Normalize Path    ${SAVED_DATA_DIR}/test_scent_*.json
    ${matches}=        Glob             ${search_path}

    Log    Search path: ${search_path}
    Log    Found matches: ${matches}

    Length Should Be    ${matches}    1
    File Should Exist   ${matches}[0]
    ${content}=         Get File         ${matches}[0]
    Should Contain      ${content}       value
    Should Contain      ${content}       timestamp

    # ─── Dump reader logs for debugging ───
    ${reader_stdout}=   Get File         IntegrationTests/reader.log
    ${reader_stderr}=   Get File         IntegrationTests/reader.err
    Log                 Reader STDOUT: ${reader_stdout}
    Log                 Reader STDERR: ${reader_stderr}

    # ─── Clean up ───
    @{files}=           List Files In Directory    ${SAVED_DATA_DIR}   absolute=True
    FOR    ${file}    IN    @{files}
        Remove File    ${file}
    END
    Remove Directory    ${SAVED_DATA_DIR}
    Remove File         ${SENSOR_JSON}