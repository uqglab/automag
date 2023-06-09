from telemetrix_aio import telemetrix_aio
import time
import numpy as np
import asyncio
import json
import configparser

class ST1168:
    def __init__(self, board, params):
       
        """
        Initializes the ST1168 power control board.

        Args:
            board: The board object used for communication.
            params: Dictionary containing the parameters for the board.
        """

        self.board = board
        self.params = params

        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.pinModeOn())

    async def pinModeOn(self):
        
        """
        Sets the pin modes and initial states of the power control board.
        """

        await self.board.set_pin_mode_digital_output(self.params['mosfetPowerPin'])
        await asyncio.sleep(0.05)
        await self.board.set_pin_mode_digital_output(self.params['mosfetSignalPin'])
        await asyncio.sleep(0.05)
        await self.board.digital_write(self.params['mosfetPowerPin'], 1) 
        await asyncio.sleep(0.05)
        await self.board.digital_write(self.params['mosfetSignalPin'], 0)
        await asyncio.sleep(0.05)

        self.lastpowerState = 0

    async def setState(self, direction):

        """
        Sets the state of the power control board.

        Args:
            direction: The desired state (0 or 1) for the power control.

        Notes:
            - If the direction is 1 and the last power state is different, the signal pin is set to 1.
            - If the direction is 0 and the last power state is different, the signal pin is set to 0.
            - If the direction is the same as the last power state, no action is taken.
        """

        if direction == 1 and self.lastpowerState != direction:
            self.lastpowerState = direction
            await self.board.digital_write(self.params['mosfetSignalPin'], 1)
            await asyncio.sleep(0.2)

        elif direction == 0 and self.lastpowerState != direction:
            self.lastpowerState = direction
            await self.board.digital_write(self.params['mosfetSignalPin'], 0)
            await asyncio.sleep(0.2)

        else:
            pass     
        
class MMC5983MA:
    def __init__(self, board):

        """
        Initializes the MMC5983MA hall sensor and Events.

        Args:
            board: The board object used for communication.
        """

        self.board = board
        self.loop = asyncio.get_event_loop()

        self.loop.run_until_complete(self.board.set_pin_mode_i2c())

        self.readXYZEvent = asyncio.Event()
        self.measurementEvent = asyncio.Event()
        self.XBits17to10Event = asyncio.Event()
        self.XBits09to02Event = asyncio.Event()
        self.YBits17to10Event = asyncio.Event()
        self.YBits09to02Event = asyncio.Event()
        self.ZBits17to10Event = asyncio.Event()
        self.ZBits09to02Event = asyncio.Event()
        self.XYZBits01to00Event = asyncio.Event()

        self.deviceAddress = 48
        self.controlRegister0 = 9
        self.status = 8

    def getResolutionCount(self, bitMode):

        """
        Calculates the resolution count based on the bit mode.

        Args:
            bitMode: The bit mode value.

        Returns:
            The resolution count.
        """

        return((1 << bitMode) - 1)
    
    async def setSensor(self):
       
        """
        Sets the sensor (polarization + direction) and conducts a measurement.
        """

        self.loop.run_until_complete(self.board.i2c_write(self.deviceAddress, [self.controlRegister0, 8]))
        self.loop.run_until_complete(self.board.i2c_write(self.deviceAddress, [self.controlRegister0, 1]))

        await self.queryMagMeasurement()

    async def queryMagMeasurement(self):

        """
        Queries the magnetic measurement from the sensor.
        """

        self.Meas_M_Done = 0 
        while self.Meas_M_Done == 0:
            await self.board.i2c_read(self.deviceAddress, self.status, 1, self.checkMeasurementCallback)
            await self.measurementEvent.wait()
            self.measurementEvent.clear()

    async def checkMeasurementCallback(self, data):

        """
        Callback function for checking the completion of magnetic measurement.

        Args:
            data: The data received from the sensor.
        """

        self.Meas_M_Done = (data[-2]) & 0b1
        self.measurementEvent.set()
    
    async def resetSensor(self):

        """
        Resets the sensor (polarization - direction) and conducts a measurement.
        """

        self.loop.run_until_complete(self.board.i2c_write(self.deviceAddress, [self.controlRegister0, 16]))
        self.loop.run_until_complete(self.board.i2c_write(self.deviceAddress, [self.controlRegister0, 1]))
        await self.queryMagMeasurement()

    def readXYZBits(self, bit_mode):

        """
        Reads and merges the X, Y, and Z bits based on the specified bit mode.

        Args:
            bit_mode: The bit mode value.

        Returns:
            The merged X, Y, and Z bits.
        """

        self.loop.run_until_complete(self.getXYZBits())

        if bit_mode == 18:
            bitsX = self.merge18Bits(self.XBits17to10, self.XBits09to02, self.XBits01to00)
            bitsY = self.merge18Bits(self.YBits17to10, self.YBits09to02, self.YBits01to00)
            bitsZ = self.merge18Bits(self.ZBits17to10, self.ZBits09to02, self.ZBits01to00)
            return(bitsX, bitsY, bitsZ)
        
        elif bit_mode == 16:

            bitsX = self.merge16Bits(self.XBits17to10, self.XBits09to02)
            bitsY = self.merge16Bits(self.YBits17to10, self.YBits09to02)
            bitsZ = self.merge16Bits(self.ZBits17to10, self.ZBits09to02)
            return(bitsX, bitsY, bitsZ)

    def merge18Bits(self, bit1, bit2, bit3):
        
        """
        Merges three sets of bits into a single 18-bit value.

        Args:
            bit1: The first set of bits.
            bit2: The second set of bits.
            bit3: The third set of bits.

        Returns:
            The merged 18-bit value.
        """ 

        mergedValue = (bit1 << 10) | (bit2 << 2) | bit3
        return mergedValue

    def merge16Bits(self, bit1, bit2):
        
        """
        Merges two sets of bits into a single 16-bit value.

        Args:
            bit1: The first set of bits.
            bit2: The second set of bits.

        Returns:
            The merged 16-bit value.
        """

        mergedValue = (bit1 << 10) | bit2
        return mergedValue


    def getHallSensorOutput(self, averageCount, bitMode=18):

        """
        Retrieves the hall sensor output.

        Args:
            averageCount: The number of measurements to average.
            bitMode: The bit mode value.

        Returns:
            The averaged field , raw field, and raw offset.
        """

        rawResult = [[], [], [], []]
        aveResult = [None, None, None, None]
        rawOffset = [[], [], [], []]

        resCount = self.getResolutionCount(bitMode)

        for _ in range(int(averageCount)):

            self.loop.run_until_complete(self.setSensor())
            bitsX, bitsY, bitsZ = self.readXYZBits(bitMode)
            posCurrentX = 8*(bitsX - 0.5*resCount)/(0.5*resCount)
            posCurrentY = 8*(bitsY - 0.5*resCount)/(0.5*resCount)
            posCurrentZ = 8*(bitsZ - 0.5*resCount)/(0.5*resCount)

            self.loop.run_until_complete(self.resetSensor())
            bitsX, bitsY, bitsZ = self.readXYZBits(bitMode)
            negCurrentX = 8*(bitsX - 0.5*resCount)/(0.5*resCount)
            negCurrentY = 8*(bitsY - 0.5*resCount)/(0.5*resCount)
            negCurrentZ = 8*(bitsZ - 0.5*resCount)/(0.5*resCount)

            rawOffset[0].append((posCurrentX + negCurrentX) / 2)
            rawOffset[1].append((posCurrentY + negCurrentY) / 2)           
            rawOffset[2].append((posCurrentZ + negCurrentZ) / 2)
            rawResult[0].append(((posCurrentX - negCurrentX) / 2))
            rawResult[1].append(((posCurrentY - negCurrentY) / 2))
            rawResult[2].append(((posCurrentZ - negCurrentZ) / 2))

        aveResult[:3] = [np.average(rawResult[i]) for i in range(3)]
        aveResult[3] = np.linalg.norm(aveResult[:3])

        return aveResult, rawResult , rawOffset

    async def callbackXBits17to10(self, data):

        """
        Callback function for reading x-axis bits 17th to 10th.

        Args:
            data: The data received from the sensor.
        """

        self.XBits17to10=data[-2]
        self.XBits17to10Event.set()

    async def callbackXBits09to02(self, data):

        """
        Callback function for reading x-axis bits 9th to 2nd.

        Args:
            data: The data received from the sensor.
        """

        self.XBits09to02 =data[-2]
        self.XBits09to02Event.set()

    async def callbackYBits17to10(self, data):

        """
        Callback function for reading y-axis bits 17th to 10th.

        Args:
            data: The data received from the sensor.
        """

        self.YBits17to10= data[-2]
        self.YBits17to10Event.set()

    async def callbackYBits09to02(self, data):

        """
        Callback function for reading y-axis bits 9th to 2nd.

        Args:
            data: The data received from the sensor.
        """
        
        self.YBits09to02 = data[-2]
        self.YBits09to02Event.set()

    async def callbackZBits17to10(self, data):

        """
        Callback function for reading z-axis bits 17th to 10th.

        Args:
            data: The data received from the sensor.
        """

        self.ZBits17to10= data[-2]
        self.ZBits17to10Event.set()

    async def callbackZBits09to02(self, data):

        """
        Callback function for reading z-axis bits 9th to 2th.

        Args:
            data: The data received from the sensor.
        """

        self.ZBits09to02 = data[-2]
        self.ZBits09to02Event.set()

    async def callbackXYZBits01to00(self, data):

        """
        Callback function for reading remaining bits for x-y-z-axis bits 1st to 0th.

        Args:
            data: The data received from the sensor.
        """

        self.XBits01to00 =  (data[-2] >> 6) & 0b11
        self.YBits01to00 =  (data[-2] >> 4) & 0b11
        self.ZBits01to00 =  (data[-2] >> 2) & 0b11

        self.XYZBits01to00Event.set()

    async def callbackXYZAll(self, data):

        """
        Callback function for reading all XYZ bits. 7 bytes are asked. 

        Args:
            data: The data received from the sensor.
        """        
        self.XBits17to10 = data[-8]
        self.XBits09to02 = data[-7]
        self.YBits17to10 = data[-6]
        self.YBits09to02 = data[-5]
        self.ZBits17to10 = data[-4]
        self.ZBits09to02 = data[-3]

        self.XBits01to00 =  (data[-2] >> 6) & 0b11
        self.YBits01to00 =  (data[-2] >> 4) & 0b11
        self.ZBits01to00 =  (data[-2] >> 2) & 0b11
        self.readXYZEvent.set()


    async def getXYZBits(self):

        """
        Ask to reads all XYZ bits from the sensor. 
        7 bytes are asked and the callbackXYZAll waits until it receives 7 bytes.
        """

        await self.board.i2c_read(self.deviceAddress, 0, 7, self.callbackXYZAll)               
        await self.readXYZEvent.wait()
        self.readXYZEvent.clear()

class ArduinoController():

    def __init__(self):

        self.loop = asyncio.get_event_loop()

        self.getConfig()

        self.queryStepperPostionEvent = asyncio.Event()
        self.queryMoveRelativeEvent = asyncio.Event()
        self.queryMoveAbsoluteEvent = asyncio.Event()
        self.queryPhotosensorEvent = asyncio.Event()
        self.queryConnectionEvent = asyncio.Event()
        self.queryStepperMoveEvent = asyncio.Event()
        self.calibrationUserConfirmEvent = asyncio.Event()
        self.queryStepperPositionGUIEvent = asyncio.Event()
        self.placeMagnetConfirmEvent = asyncio.Event()

    def getConfig(self):

        """
        Load configuration from JSON files and initialize digitalInput dictionary.
        """

        # Load data from JSON file
        with open('default_config.json', 'r') as file:
            self.params = json.load(file)
    
        with open('default_userInput.json', 'r') as file:
            self.userInput = json.load(file)

        # Create keys in the digital_input dictionary for each pin in sensor_input_pins
        for pin in str(self.params['photosensorPins']):
            key = str(pin)
            self.params['digitalInput'][key] = 0        

    async def initializeMicroController(self):  

        """
        Initialize the microcontroller, connect to it, and initialize components.
        """

        try:
            self.board = telemetrix_aio.TelemetrixAIO(close_loop_on_shutdown=True)
            self.connectionState = True

            self.hallSensor = MMC5983MA(self.board)
            self.mosfetSwitch = ST1168(self.board, self.params)

            self.loop.create_task(self.initializeStepper())
            self.loop.create_task(self.initializePhotosensor())
  
        except Exception as e:
            self.connectionState = False
            self.exception = e



    async def initializeStepper(self):
     
        """
        Initialize the stepper motor with the configured parameters.
        """

        try:
            self.motor = await self.board.set_pin_mode_stepper( interface=self.params['stepperInterface'], 
                                                                pin1=self.params['stepperCtrlPins'][0], 
                                                                pin2=self.params['stepperCtrlPins'][1], 
                                                                pin3=self.params['stepperCtrlPins'][2], 
                                                                pin4=self.params['stepperCtrlPins'][3])

            await self.board.stepper_set_max_speed(self.motor,self.params['stepperMaxSpeed'])
            await self.board.stepper_set_speed(self.motor, self.params['stepperSpeed'])
            await self.board.stepper_set_current_position(self.motor, self.params['stepperPosition'])
            await self.board.set_pin_mode_digital_output(self.params['stepperPowerPins'][0])
            await self.board.set_pin_mode_digital_output(self.params['stepperPowerPins'][1])
            await self.board.digital_write(self.params['stepperPowerPins'][0], 1)
            await self.board.digital_write(self.params['stepperPowerPins'][1], 1) 
            await self.board.stepper_set_acceleration(self.motor, 1000)
           
        except Exception as e:
            self.exception = e

    async def initializePhotosensor(self):
       
        """
        Initialize the photosensor by configuring the pins and enabling power.
        """

        try:

            await self.board.set_pin_mode_digital_output(self.params['photosensorPowerPin']) 
            await self.board.digital_write(self.params['photosensorPowerPin'], 1) 
            await self.board.set_pin_mode_digital_input(self.params['photosensorPins'][0], callback=self.callbackDigitalInput)
            await self.board.set_pin_mode_digital_input(self.params['photosensorPins'][1], callback=self.callbackDigitalInput)
            
        except Exception as e:
            self.exception = e

    async def shutDownDevices(self):
       
        """
        Shut down all devices by turning off power and disconnect from microcontroller
        """

        try:
            await self.board.digital_write(self.params['photosensorPowerPin'], 0) 
            await self.board.digital_write(self.params['stepperPowerPins'][0], 0)
            await self.board.digital_write(self.params['stepperPowerPins'][1], 0) 
            await self.board.digital_write(self.params['mosfetSignalPin'], 0)
            await self.board.shutdown()
        except:
            pass
    async def callbackDigitalInput(self, data):
      
        """
        Callback function for handling digital input changes.
        """

        self.params['digitalInput'][str(data[1])] = data[2]

        if int(data[2]) == 0:
            self.queryPhotosensorEvent.set()

    async def callbackConnectionQuery(self, data):
        """
        Callback function for handling connection query response. Verfying connection with the microcontroller.
        """

        self.connectionState = True
        self.queryConnectionEvent.set()

    async def queryConnection(self):
        """
        Query the connection status of the microcontroller. Verifying connection with the microcontroller.
        """
        try:
            await self.board.loop_back('o', callback=self.callbackConnectionQuery)
            await asyncio.wait_for(self.queryConnectionEvent.wait(), timeout=0.5)
            self.queryConnectionEvent.clear()
        except:
            await self.board.shutdown()
            self.connectionState = False

    async def callbackgetStepperPosition(self, data):
        """ 
        Callback function for retrieving the current stepper position.
        """     

        self.params['stepperPosition'] = data[2]
        self.queryStepperPostionEvent.set()
        self.queryStepperPositionGUIEvent.set()
 
    async def callbackqueryStepperMove(self, data):
        """
        Callback function for handling stepper move queries. When a move is complete.
        """        
        self.queryStepperMoveEvent.set()

    async def stepperCollisionMove(self,stepCount):
      
        """
        Move to the opposite direction whenever slider blocks a photosensor. until photosensor not blocked.
        """

        await self.board.stepper_get_current_position(self.motor, self.callbackgetStepperPosition)
        await self.queryStepperPostionEvent.wait()
        self.queryStepperPostionEvent.clear()

        await self.board.stepper_move(self.motor, stepCount)
        await self.board.stepper_set_speed(self.motor, self.params['stepperSpeed'])
        self.move_task = self.loop.create_task(self.board.stepper_run_speed_to_position(self.motor, completion_callback=self.callbackqueryStepperMove))        

        while True:
            try:
                await asyncio.wait_for(self.queryStepperMoveEvent.wait(), timeout=0.001)
                break
            except:
                await asyncio.sleep(0.001)           
                
        await self.board.stepper_get_current_position(self.motor, self.callbackgetStepperPosition)
        await self.queryStepperPostionEvent.wait()    
        self.queryStepperPostionEvent.clear()

    async def stepperMoveRelative(self,stepCount):

        """
        Move the stepper motor relative to its current position.
        """

        self.queryMoveRelativeEvent.set()
        self.queryStepperMoveEvent.clear()

        await self.board.stepper_get_current_position(self.motor, self.callbackgetStepperPosition)
        await self.queryStepperPostionEvent.wait()    
        self.queryStepperPostionEvent.clear()

        await self.board.stepper_move(self.motor, stepCount)
        await self.board.stepper_set_speed(self.motor, self.params['stepperSpeed'])
        await self.board.stepper_run_speed_to_position(self.motor, completion_callback=self.callbackqueryStepperMove)
        

        while True:
            if self.queryStepperMoveEvent.is_set():
                break
            if self.params['digitalInput'][str(self.params['photosensorPins'][0])] == 0 or self.params['digitalInput'][str(self.params['photosensorPins'][1])] == 0:
                self.loop.run_until_complete(self.board.stepper_stop(self.motor))
                while self.params['digitalInput'][str(self.params['photosensorPins'][0])] == 0 or self.params['digitalInput'][str(self.params['photosensorPins'][1])] == 0:
                    self.loop.run_until_complete(self.stepperCollisionMove(int(-stepCount/abs(stepCount))))
                    await self.queryStepperMoveEvent.wait()
                    self.queryStepperMoveEvent.clear()
                break
            await asyncio.sleep(0) 
            
        self.queryStepperMoveEvent.clear()
        await self.board.stepper_get_current_position(self.motor, self.callbackgetStepperPosition)
        await self.queryStepperPostionEvent.wait()   
        self.queryStepperPostionEvent.clear() 
        self.queryMoveRelativeEvent.clear()

    async def stepperMoveAbsolute(self, new_position):

        """
        Move the stepper motor to an absolute position.
        Using quotient and remainder if the steps exceeds the maximum bit value of Arduino.
        """

        self.queryMoveAbsoluteEvent.set()
        self.queryStepperMoveEvent.clear()

        current_pos = int(self.params['stepperPosition'])

        distance_to_pos = (new_position - current_pos)

        if distance_to_pos != 0:
            direction = distance_to_pos/abs(distance_to_pos)
        else:
            return

        quotient, remainder = divmod(abs(distance_to_pos),32767)
        while quotient > 0: 

            for _ in range(quotient):
                self.queryStepperMoveEvent.clear()

                await self.board.stepper_move(self.motor, int(32767*direction*quotient))
                await self.board.stepper_set_speed(self.motor, self.params['stepperSpeed'])
                await self.board.stepper_run_speed_to_position(self.motor, completion_callback=self.callbackqueryStepperMove) 

                while True:
                    if self.queryStepperMoveEvent.is_set():
                        break                    
                    if self.params['digitalInput'][str(self.params['photosensorPins'][0])] == 0 or self.params['digitalInput'][str(self.params['photosensorPins'][1])] == 0:
                        # print('collision detection')
                        self.loop.create_task(self.board.stepper_stop(self.motor))
                        await asyncio.sleep(0.05)
                        while self.params['digitalInput'][str(self.params['photosensorPins'][0])] == 0 or self.params['digitalInput'][str(self.params['photosensorPins'][1])] == 0:
                            self.queryStepperMoveEvent.clear()
                            self.loop.run_until_complete(self.stepperCollisionMove(int(-direction)))
                            await self.queryStepperMoveEvent.wait()
                            self.queryStepperMoveEvent.clear()

                        return
                    await asyncio.sleep(0)

      
                self.queryStepperMoveEvent.clear()
                await self.board.stepper_get_current_position(self.motor, self.callbackgetStepperPosition)
                await self.queryStepperPostionEvent.wait()
                self.queryStepperPostionEvent.clear()
                quotient -= quotient

        if remainder != 0: 
            self.queryStepperMoveEvent.clear()

            
            await self.board.stepper_move(self.motor, int(direction*remainder))
            await self.board.stepper_set_speed(self.motor, self.params['stepperSpeed'])
            await self.board.stepper_run_speed_to_position(self.motor, completion_callback=self.callbackqueryStepperMove)

            while True:
                if self.queryStepperMoveEvent.is_set():
                    break                    
                if self.params['digitalInput'][str(self.params['photosensorPins'][0])] == 0 or self.params['digitalInput'][str(self.params['photosensorPins'][1])] == 0:
                    self.loop.create_task(self.board.stepper_stop(self.motor))
                    while self.params['digitalInput'][str(self.params['photosensorPins'][0])] == 0 or self.params['digitalInput'][str(self.params['photosensorPins'][1])] == 0:
                        self.queryStepperMoveEvent.clear()
                        self.loop.run_until_complete(self.stepperCollisionMove(int(-direction)))
                        await self.queryStepperMoveEvent.wait()
                        self.queryStepperMoveEvent.clear()
                    break
                await asyncio.sleep(0)         

            self.queryStepperMoveEvent.clear()
            await self.board.stepper_get_current_position(self.motor, self.callbackgetStepperPosition)
            await self.queryStepperPostionEvent.wait()    
            self.queryStepperPostionEvent.clear()
            self.queryMoveAbsoluteEvent.clear()

    async def runCalibration(self):
            
        """
        Run the calibration process for the stepper motor and photosensor.
        """

        self.calibrationUserConfirmEvent.clear()

        self.loop.create_task(self.stepperMoveRelative(42949672))
        self.queryMoveRelativeEvent.set()

        while self.queryMoveRelativeEvent.is_set() == True:
            await asyncio.sleep(0)

        self.loop.run_until_complete(self.board.stepper_stop(self.motor))
        # await asyncio.sleep(0.05)
        self.calibrationEvent0.set()
        await self.calibrationUserConfirmEvent.wait()
        self.calibrationUserConfirmEvent.clear()
        await self.board.stepper_get_current_position(self.motor, self.callbackgetStepperPosition)
        await self.queryStepperPostionEvent.wait()    
        self.queryStepperPostionEvent.clear()

        self.calibrationPointA = self.params['stepperPosition'] 
        self.params['photosensorPositionB'] = self.params['stepperPosition']         



        self.loop.create_task(self.stepperMoveRelative(-42949672))
        self.queryMoveRelativeEvent.set()

        while self.queryMoveRelativeEvent.is_set() == True:
            await asyncio.sleep(0)

        self.loop.run_until_complete(self.board.stepper_stop(self.motor))
        # await asyncio.sleep(0.05)
        self.calibrationEvent1.set()
        await self.calibrationUserConfirmEvent.wait()
        self.calibrationUserConfirmEvent.clear()

        await self.board.stepper_get_current_position(self.motor, self.callbackgetStepperPosition)
        await self.queryStepperPostionEvent.wait()    
        self.queryStepperPostionEvent.clear()
        self.calibrationPointB = self.params['stepperPosition'] 

        self.calibrationRange = abs(self.calibrationPointB-self.calibrationPointA)
        self.calibrationEvent2.set()

        self.params['photosensorPositionA'] = self.params['stepperPosition']
        self.params['photosensorPositionB'] = self.params['photosensorPositionB'] - self.params['photosensorPositionA']
        self.params['photosensorPositionA'] = 0

        self.calibrationRange = abs(self.calibrationPointB-self.calibrationPointA)
        self.calibrationEvent2.set()
        await self.board.stepper_set_current_position(self.motor, 0)
        await self.board.stepper_get_current_position(self.motor, self.callbackgetStepperPosition)
        await self.queryStepperPostionEvent.wait()    
        self.queryStepperPostionEvent.clear()
 

    def getOneFieldData(self, average_count):

        """
        Get one set of field data from the Hall sensor.
        """

        aveResult, rawResult , rawOffset = self.hallSensor.getHallSensorOutput(average_count)
        self.oneFieldData = aveResult



    async def streamFieldData(self, average_count):
        """
        Stream field data from the Hall sensor.
        """
        self.liveResult = [[], [], [], [], []]

        count_span = int(60)
        startTime = time.time()

        while self.streamstate == True:
            
            aveResult, _, _ = self.hallSensor.getHallSensorOutput(average_count)

            currentTime = time.time()
            spanTime = currentTime - startTime


            for i in range(4):
                self.liveResult[i].append(aveResult[i])
            # [self.liveResult[i].append(aveResult[i]) for i in range(4)]
            self.liveResult[4].append(spanTime)

            if spanTime > count_span:
                [self.liveResult[i].__delitem__(0) for i in range(5)]
            
            self.newLiveDataEvent.set()
            # await asyncio.sleep(0.05)

       

    def runCoilModeMagnet(self, average_count):
    
        """
        Data logging for the measurements where magnet is present (or coil current is flowing).
        """ 

        self.loop.run_until_complete(self.mosfetSwitch.setState(1))
        aveResult, rawResult, rawOffset = self.hallSensor.getHallSensorOutput(average_count)
        MnSX = aveResult[0]
        MnSY = aveResult[1]
        MnSZ = aveResult[2]
        
        self.aveMnSs[0].append(MnSX)
        self.aveMnSs[1].append(MnSY)
        self.aveMnSs[2].append(MnSZ)

        self.rawMnSs[0].append(rawResult[0])
        self.rawMnSs[1].append(rawResult[1])
        self.rawMnSs[2].append(rawResult[2])

        self.rawOffsets[0].append(rawOffset[0])
        self.rawOffsets[1].append(rawOffset[1])
        self.rawOffsets[2].append(rawOffset[2])

        return(MnSX, MnSY, MnSZ)

    def runCoilModeStray(self, average_count):
        """
        Data logging for the measurements where magnet is absent (or coil current is blocked).
        """ 
        self.loop.run_until_complete(self.mosfetSwitch.setState(0))
        aveResult, rawResult, rawOffset = self.hallSensor.getHallSensorOutput(average_count)
        strayX = aveResult[0]
        strayY = aveResult[1]
        strayZ = aveResult[2]

        self.aveStrays[0].append(aveResult[0])
        self.aveStrays[1].append(aveResult[1])
        self.aveStrays[2].append(aveResult[2])
        self.aveStrays[3].append(np.linalg.norm([aveResult[0], aveResult[1], aveResult[2]]))

        self.rawStrays[0].append(rawResult[0])
        self.rawStrays[1].append(rawResult[1])
        self.rawStrays[2].append(rawResult[2])

        self.rawOffsets[0].append(rawOffset[0])
        self.rawOffsets[1].append(rawOffset[1])
        self.rawOffsets[2].append(rawOffset[2])

        return(strayX, strayY, strayZ)

    async def runCoilMode(self):
        """
        run the measurement in coil mode.
        """
        self.coilModeStartTime = time.time()

        self.aveMagnets = [[], [], [], []]
        self.aveStrays = [[], [], [], []]
        self.rawStrays = [[], [], []]
        self.rawOffsets = [[], [], []]
        self.aveMnSs = [[], [], []]
        self.rawMnSs = [[], [], []]
        self.sensorPositions = []


        start = int(self.params['stepperPosition'])
        end = int(self.userInput['measureEndPoint']) + start
        step = int(self.userInput['measurementStep'])
        average_count = int(self.userInput['sampleCount'])

        powerSkip = 0

        if start > end:
            step = -step

        for new_pos in range(start,end+step,step):
            powerSkip += 1
            self.loop.run_until_complete(self.stepperMoveAbsolute(new_pos))
            self.sensorPositions.append(new_pos-start)

            if powerSkip % 2 == 0:
                MnSX, MnSY, MnSZ = self.runCoilModeMagnet(average_count)
                strayX, strayY, strayZ = self.runCoilModeStray(average_count)
            else:
                strayX, strayY, strayZ = self.runCoilModeStray(average_count)
                MnSX, MnSY, MnSZ = self.runCoilModeMagnet(average_count)

            magnetX = MnSX - strayX
            magnetY = MnSY - strayY
            magnetZ = MnSZ - strayZ

            self.aveMagnets[0].append(magnetX)
            self.aveMagnets[1].append(magnetY)
            self.aveMagnets[2].append(magnetZ)
            magnetR = np.linalg.norm([magnetX, magnetY, magnetZ])
            self.aveMagnets[3].append(magnetR)

            self.newDataEvent.set()
            await asyncio.sleep(0.5)
        
        self.autoSaveEvent.set()
        self.coilModeEndTime = time.time()
        self.runCoilModeTime = self.coilModeEndTime - self.coilModeStartTime

    async def runPermaModeOff(self):
        """
        performs permanent mode with absence of the magnet (or the coil current is blocked) 
        """
        self.runPermaModeStartTime = time.time()

        self.hallSensor.getHallSensorOutput(1)
        
        self.aveMagnets = [[], [], [], []]
        self.aveStrays = [[], [], [], []]
        self.rawStrays = [[], [], []]
        self.rawOffsets = [[], [], []]
        self.aveMnSs = [[], [], []]
        self.rawMnSs = [[], [], []]
        self.sensorPositions = []

        self.loop.run_until_complete(self.mosfetSwitch.setState(0))
        self.start = int(self.params['stepperPosition'])
        self.end = int(self.userInput['measureEndPoint'])+self.start
        self.step = int(self.userInput['measurementStep'])
        average_count = int(self.userInput['sampleCount'])
      
        if self.start > self.end:
            self.step = -self.step

        for new_pos in range(self.start,self.end+self.step,self.step):
            self.loop.run_until_complete(self.stepperMoveAbsolute(new_pos))
            self.sensorPositions.append(new_pos-self.start)

            
            strayX, strayY, strayZ = self.runCoilModeStray(average_count)

            self.newDataEvent.set()
            await asyncio.sleep(0.02)

        self.magnetoffend = time.time()

        userMagnetPlacingStartTime = time.time()
        self.placeMagnetEvent.set()
        await self.placeMagnetConfirmEvent.wait()
        self.placeMagnetConfirmEvent.clear()

        userMagnetPlacingEndTime = time.time()
        self.userMangetPlacingTime = userMagnetPlacingEndTime - userMagnetPlacingStartTime
        self.loop.create_task(self.runPermaModeOn())            
   

    async def runPermaModeOn(self):

        """
        performs permanent mode with presence of the magnet (or the coil current is flowing) 
        """


        self.magnetonstart = time.time()


        self.hallSensor.getHallSensorOutput(1)

        average_count = int(self.userInput['sampleCount'])
        self.loop.run_until_complete(self.mosfetSwitch.setState(1))

        self.step = self.step * -1
        for new_pos in range(self.end,self.start+self.step,self.step):
            self.newDataEvent = asyncio.Event()
            self.loop.run_until_complete(self.stepperMoveAbsolute(new_pos))

            MnSX, MnSY, MnSZ = self.runCoilModeMagnet(average_count)

            magnetX = MnSX - self.aveStrays[0][-len(self.aveMnSs[0])]
            magnetY = MnSY - self.aveStrays[1][-len(self.aveMnSs[1])]
            magnetZ = MnSZ - self.aveStrays[2][-len(self.aveMnSs[2])]

            self.aveMagnets[0].insert(0, magnetX)
            self.aveMagnets[1].insert(0, magnetY)
            self.aveMagnets[2].insert(0, magnetZ)
            magnetR = np.linalg.norm([magnetX, magnetY, magnetZ])
            self.aveMagnets[3].insert(0, magnetR)

            self.newDataEvent.set()
            await asyncio.sleep(0.5)

        self.autoSaveEvent.set()
        self.runPermaModeEndTime = time.time()
        self.runPermaModeTime = self.runPermaModeEndTime - self.runPermaModeStartTime - self.userMangetPlacingTime