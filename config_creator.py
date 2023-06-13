import json

default_config = {

    #Stepper Control Defaults
    'stepperInterface': 8,
    'stepperCtrlPins': [3, 5, 4, 6],
    'stepperPowerPins': [2, 7],
    'stepperSpeed': 1000,
    'stepperMaxSpeed': 1000,
    'stepperPosition': 0,
    'stepperPosition_mm': 0,
    'stepperRev': 400,
    'photosensorPins': [48, 50],
    


    'digitalInput': {},
    'photosensorPowerPin': 52,
    'photosensorPositionA': None,
    'photosensorPositionB': None,

    'mosfetSignalPin': 51,
    'mosfetPowerPin': 53,
}

default_userInput = {
   
    'coilCurrent': 0,
    'sampleCount': 1,
    'measurementStep_mm': 1.25,
    'measurementStep': 200,
    'measure_start': 0,
    'measureEndPoint': 100,
    'measureEndPoint_mm': 125,
    'measurementDataCount': 0,
    'stepperRev_mm': 1.25,
}


with open('default_config.json', 'w') as file:
    json.dump(default_config, file)

with open('default_userInput.json', 'w') as file:
    json.dump(default_userInput, file)



# Print the dictionary with all the elements
