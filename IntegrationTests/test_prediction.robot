*** Settings ***
Library           OperatingSystem
Library           Process
Library           Collections
Library           BuiltIn
Library           glob
Library           String

*** Variables ***
${PROJECT_ROOT}       ${CURDIR}/..
${REQ_FILE}           ${CURDIR}/requirements.txt
${PYTHON}             NONE    # placeholder, overwritten in test setup
${BROKER}             DataCommunicator.source.MessageBrokerServer
${ODOUR_RECOGNIZER}   ${PROJECT_ROOT}/OdourRecognizer/source/main.py
${DISPLAY}            ${PROJECT_ROOT}/IntegrationTests/mocks/MockDisplayMain.py
${IO_HANDLER}         ${PROJECT_ROOT}/IntegrationTests/mocks/MockIOMain.py
${SENSOR_READER}      ${PROJECT_ROOT}/IntegrationTests/mocks/SensorReaderFake.py
${SENSOR_JSON}        ${PROJECT_ROOT}/IntegrationTests/mocks/sensor_data.json
${TEST_DURATION}      50s

*** Test Cases ***
Integration Test With Prediction Flow
    [Documentation]    Integration test from SensorReader to OdourRecognizer via WebSocket, asserting prediction phase is reached.

    ${py} =    Evaluate    sys.executable    modules=sys
    Set Test Variable    ${PYTHON}    ${py}
    Log To Console    Python used: ${PYTHON}

    # Install dependencies
    Run Process    ${PYTHON}    -m    pip    install    -r    ${REQ_FILE}
    ...    stdout=NONE    stderr=NONE    shell=True
    Log    Dependencies installed from ${REQ_FILE}

    Set Environment Variable    PYTHONPATH    ${PROJECT_ROOT}
    Set Environment Variable    PYTHONIOENCODING    utf-8
    Set Environment Variable    PYTHONUNBUFFERED    1

    Create Directory    ${PROJECT_ROOT}/IntegrationTests/output

    # ─── Inject broker URI/port so collector and reader talk to our fake ───
    Set Environment Variable    BROKER_URI    ws://localhost:8765
    Set Environment Variable    BROKER_PORT   8765

    # 1) Start the WebSocket broker
    Start Process    ${PYTHON}    -m    ${BROKER}    cwd=${PROJECT_ROOT}
    ...    cwd=${PROJECT_ROOT}    
    ...    stdout=${PROJECT_ROOT}/IntegrationTests/output/broker.log    
    ...    stderr=STDOUT
    Sleep    5s

    Start Process    ${PYTHON}    ${ODOUR_RECOGNIZER}    
    ...    cwd=${PROJECT_ROOT}    
    ...    stdout=${PROJECT_ROOT}/IntegrationTests/output/recognizer.log    
    ...    stderr=STDOUT
    Sleep    2s

    Start Process    ${PYTHON}    ${IO_HANDLER}    
    ...    cwd=${PROJECT_ROOT}    
    ...    stdout=${PROJECT_ROOT}/IntegrationTests/output/io.log    
    ...    stderr=STDOUT
    Sleep    2s

    Start Process    ${PYTHON}    ${DISPLAY}    
    ...    cwd=${PROJECT_ROOT}    
    ...    stdout=${PROJECT_ROOT}/IntegrationTests/output/display.log    
    ...    stderr=STDOUT
    Sleep    2s

    Start Process    ${PYTHON}    ${SENSOR_READER}    
    ...    cwd=${PROJECT_ROOT}    
    ...    stdout=${PROJECT_ROOT}/IntegrationTests/output/sensor.log    
    ...    stderr=STDOUT

    Sleep    ${TEST_DURATION}

    Terminate All Processes
    Sleep    5s

    ${log_path}=    Normalize Path    ${PROJECT_ROOT}/IntegrationTests/output
    ${matches}=     Glob              ${log_path}/*.log
    Should Not Be Empty    ${matches}

    ${display_log_content}=    Get File    ${PROJECT_ROOT}/IntegrationTests/output/display.log    encoding=UTF-8
    @{log_lines}=    Split String    ${display_log_content}    \n

    ${prediction_lines}=    Evaluate    [line for line in ${log_lines} if 'prediction' in line.lower()]
    Should Not Be Empty    ${prediction_lines}

    ${unsure_lines}=    Evaluate    [line for line in ${log_lines} if 'unsure' in line.lower()]
    Should Not Be Empty    ${unsure_lines}

    ${confidence_lines}=    Evaluate    [line for line in ${log_lines} if 'confidence' in line.lower()]
    Should Not Be Empty    ${confidence_lines}