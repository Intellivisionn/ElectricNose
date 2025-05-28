*** Settings ***
Library    OperatingSystem
Library    Process
Library    glob

*** Variables ***
${PROJECT_ROOT}      ${CURDIR}/..
${PYTHON}            python
${BROKER}            DataCommunicator.source.MessageBrokerServer
${DATA_COLLECTOR}    DataCollector.source.data_collector
${SENSOR_READER}     IntegrationTests.mocks.SensorReaderFake
${SAVED_DATA_DIR}    ${PROJECT_ROOT}/savedData
${SENSOR_JSON}       ${PROJECT_ROOT}/IntegrationTests/mocks/sensor_data.json

*** Test Cases ***
Integration Test With Fake Sensors
    [Documentation]    Integration test using fake sensors over WebSocket (no JSON‐fallback).

    # ─── Inject broker URI/port so collector and reader talk to our fake ───
    Set Environment Variable    BROKER_URI    ws://localhost:8765
    Set Environment Variable    BROKER_PORT   8765

    # 1) Start the WebSocket broker
    Start Process    ${PYTHON}    -m    ${BROKER}    cwd=${PROJECT_ROOT}
    Sleep            1s    # Allow broker to bind port before clients connect

    # 2) Start the real DataCollector
    Start Process    ${PYTHON}    -m    ${DATA_COLLECTOR}
    ...              cwd=${PROJECT_ROOT}
    ...              stdin=test_scent

    # 3) Start the fake sensor producer
    Start Process    ${PYTHON}    -m    ${SENSOR_READER}
    ...              cwd=${PROJECT_ROOT}

    # ─── Let the system run a while to collect some data ───
    Sleep            15s

    # ─── Clean up ───
    Terminate All Processes

    # ─── Let the system wait a bit before evaluating ───
    Sleep            5s

    # ─── Verify output file contains at least one reading ───
    ${search_path}=    Normalize Path    ${SAVED_DATA_DIR}/test_scent_*.json
    ${matches}=        Glob             ${search_path}

    Log    Search path: ${search_path}
    Log    Found matches: ${matches}

    Length Should Be    ${matches}    1
    File Should Exist   ${matches}[0]
    ${content}=         Get File         ${matches}[0]
    Should Contain      ${content}       TVOC
    Should Contain      ${content}       BME680Sensor
    Should Contain      ${content}       timestamp

    # ─── Final cleanup ───
    @{files}=           List Files In Directory    ${SAVED_DATA_DIR}   absolute=True
    FOR    ${file}    IN    @{files}
        Remove File    ${file}
    END
    Remove Directory    ${SAVED_DATA_DIR}
    Remove File         ${SENSOR_JSON}