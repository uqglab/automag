import tkinter as tk
import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import matplotlib.pyplot as plt
import sys
import numpy as np
import asyncio
import nest_asyncio
from ttkthemes import ThemedTk
import os
import tkinter.font as font
import json
from AMDev import ArduinoController
import time



class GUIHandler:
    def __init__(self):
        self.arcon = ArduinoController()
        self.loop = asyncio.get_event_loop()
        self.initializeUI()


    def updateLog(self, report):
        
        """
        Update the log file with the provided report.
        """

        file_path = "cache\log.txt"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "a+") as file:
            file.seek(0) 
            existing_rows = file.readlines()
            
            if report + '\n' not in existing_rows:
                file.write(report + '\n')
    

    def write2InfoConsole(self, text):

        """
        Write text to the information console.
        """

        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d - %H:%M:%S]")
        self.info_console.configure(state='normal')
        self.info_console.insert('end', str(timestamp) + ' ' + str(text) + '\n')
        self.info_console.see('end')
        self.info_console.configure(state='disabled')
        report = str(timestamp) + ' ' + str(text)
        self.updateLog(report)
        
        
    def browseFolderPath(self):

        """
        Open a file dialog to browse and select a folder path.
        """

        self.folder_path = tk.filedialog.askdirectory()
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, self.folder_path)

    def saveDataFiles(self):

        """
        Save the data files for raw field measurements, raw stray measurements,
        averaged field measurements, averaged stray measurements and offset values.
        """

        try: 
            save_path = self.folder_entry.get()

            raw_data_on = []
            for i in range(len(self.arcon.rawMnSs[0])):
                for j in range(len(self.arcon.rawMnSs[0][i])):
                    row = []
                    row.append(self.arcon.sensorPositions_mm[i])
                    row.append(self.arcon.rawMnSs[0][i][j])
                    row.append(self.arcon.rawMnSs[1][i][j])
                    row.append(self.arcon.rawMnSs[2][i][j])
                    raw_data_on.append(row)

            raw_data_off = []
            for i in range(len(self.arcon.rawStrays[0])):
                for j in range(len(self.arcon.rawStrays[0][i])):
                    row = []
                    row.append(self.arcon.sensorPositions_mm[i])
                    row.append(self.arcon.rawStrays[0][i][j])
                    row.append(self.arcon.rawStrays[1][i][j])
                    row.append(self.arcon.rawStrays[2][i][j])
                    raw_data_off.append(row)       
            
            averaged_data_on = np.column_stack((self.arcon.sensorPositions_mm, self.arcon.aveMagnets[0], self.arcon.aveMagnets[1], self.arcon.aveMagnets[2]))
            averaged_data_off = np.column_stack((self.arcon.sensorPositions_mm, self.arcon.aveStrays[0], self.arcon.aveStrays[1], self.arcon.aveStrays[2]))
            offset_data = np.column_stack((self.arcon.rawOffsets[0], self.arcon.rawOffsets[1], self.arcon.rawOffsets[2]))     
        
            if save_path:
                np.savetxt(str(save_path) + '/raw_field.txt', raw_data_on, delimiter='\t', comments='', header='pos(mm)   Bx(G)       By(G)       Bz(G)' , fmt= '%.5f')
                np.savetxt(str(save_path) + '/raw_stray.txt', raw_data_off, delimiter='\t', comments='', header='pos(mm)    Bx(G)       By(G)       Bz(G)', fmt= '%.5f')
                np.savetxt(str(save_path) + '/averaged_field.txt', averaged_data_on, delimiter='\t', comments='', header='pos(mm)    Bx(G)       By(G)       Bz(G)', fmt= '%.5f')
                np.savetxt(str(save_path) + '/averaged_stray.txt', averaged_data_off, delimiter='\t', comments='', header='pos(mm)    Bx(G)       By(G)       Bz(G)', fmt= '%.5f')
                np.savetxt(str(save_path) + '/offset_sensor.txt', offset_data, delimiter='\t', comments='', header='Bx(G)       By(G)       Bz(G)', fmt= '%.5f')

            else:
                save_path = os.getcwd() + '/auto_save/' + str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")) + '/'
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                np.savetxt(str(save_path) + '/raw_field.txt', raw_data_on, delimiter='\t', comments='', header='pos(mm)\tBx(G)\tBy(G)\tBz(G)' , fmt= '%.5f')
                np.savetxt(str(save_path) + '/raw_stray.txt', raw_data_off, delimiter='\t', comments='',  header='pos(mm)\tBx(G)\tBy(G)\tBz(G)', fmt= '%.5f')
                np.savetxt(str(save_path) + '/averaged_field.txt', averaged_data_on, delimiter='\t', comments='', header='pos(mm)\tBx(G)\tBy(G)\tBz(G)', fmt= '%.5f')
                np.savetxt(str(save_path) + '/averaged_stray.txt', averaged_data_off, delimiter='\t', comments='', header='pos(mm)\tBx(G)\tBy(G)\tBz(G)', fmt= '%.5f')
                np.savetxt(str(save_path) + '/offset_sensor.txt', offset_data, delimiter='\t', comments='', header='pos(mm)\tBx(G)\tBy(G)\tBz(G)', fmt= '%.5f')

            self.arcon.autoSaveEvent.clear()
            self.enableAllButtons()
            tk.messagebox.showinfo(title='Data Saved', message='Data has been saved succesfully.')
            self.write2InfoConsole('Data has been saved succesfully @' + str(save_path))
        except Exception as e:
                tk.messagebox.showerror(title='Unable to save data', message='Error occured while saving data. \n\nError: '+str(e))
        

    def saveConfigCache(self):

        """
        Save the updated configuration and user input cache files.
        """

        file_path = 'cache/updated_config.json'
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        file_path = 'cache/default_userInput.json'
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open('default_userInput.json', 'w') as file:
            json.dump(self.arcon.userInput, file)    

        with open('default_config.json', 'w') as file:
            json.dump(self.arcon.params, file)

    def saveUserInput(self, entry, param_name):

        """
        Save the user input value for a parameter and update the cache file.
        """    
    
        value = entry.get()

        self.arcon.userInput[param_name] = (value)
        entry.unbind('<Return>')
        entry.bind('<Return>', lambda event: self.saveUserInput(entry, param_name))        
        # self.writeToInfoConsole( '"' + param_name +'"'+ ' has been set to: ' + '"' + str(self.arcon.userInput[param_name])+'"')
        with open('default_userInput.json', 'w') as file:
            json.dump(self.arcon.userInput, file)

    def nonDictList2mm(self, param):
        """
        Convert a non-dictionary list parameter from steps to mm.
        """            

        return([(int(val) * float(self.arcon.params['stepperRev_mm']) / int(self.arcon.params['stepperStepsPerRev'])) for val in param])

    def dictSteps2mm(self, param):
        """
        Convert a dictionary parameter from steps to mm.
        """

        try: 
            if type(self.arcon.params[param]) == list:
                self.arcon.params[str(param)+'_mm'] = [(int(val) * float(self.arcon.params['stepperRev_mm']) / int(self.arcon.params['stepperStepsPerRev'])) for val in self.arcon.params[param]]
            else:
                self.arcon.params[str(param)+'_mm'] = int(self.arcon.params[param]) * float(self.arcon.params['stepperRev_mm']) / int(self.arcon.params['stepperStepsPerRev'])
       
        except:
            if type(self.arcon.userInput[param]) == list:
                self.arcon.userInput[str(param)+'_mm'] = [(int(val) * float(self.arcon.params['stepperRev_mm']) / int(self.arcon.params['stepperStepsPerRev'])) for val in self.arcon.userInput[param]]
            else:
                self.arcon.userInput[str(param)+'_mm'] = int(self.arcon.userInput[param]) * float(self.arcon.params['stepperRev_mm']) / int(self.arcon.params['stepperStepsPerRev'])
   
    def dictmm2steps(self, param):
        try:
            self.arcon.userInput[str(param)[:-3]] = round(float(self.arcon.userInput[param])/float(self.arcon.params['stepperRev_mm'])*int(self.arcon.params['stepperStepsPerRev']))
        except:
            self.arcon.params[str(param)[:-3]] = round(float(self.arcon.params[param])/float(self.arcon.params['stepperRev_mm'])*int(self.arcon.params['stepperStepsPerRev']))

        
    def updateMeasurementInputs(self):
        
        """
        Update the measurement inputs based on user input and configuration parameters.
        """    

        try:
            self.saveUserInput(self.entryrev,'stepperRev_mm')
            self.saveUserInput(self.entry5,'measureEndPoint_mm')
            self.saveUserInput(self.entry6,'measurementStep_mm')
            self.saveUserInput(self.entry7,'measurementDataCount')


            if float(self.arcon.userInput['measurementStep_mm']) == 0:
                self.arcon.userInput['measurementStep_mm'] = float(self.arcon.params['stepperRev_mm']) / float(self.arcon.params['stepperStepsPerRev'])
                self.dictmm2steps('measurementStep_mm')

            self.dictmm2steps('stepperRev_mm')
            self.dictmm2steps('measureEndPoint_mm')
            self.dictmm2steps('measurementStep_mm')

            if int(self.arcon.userInput['measurementStep']) <= float(1 / (self.arcon.params['stepperStepsPerRev'])):
                self.arcon.userInput['measurementStep'] = int(1.0 / (self.arcon.params['stepperStepsPerRev']))

            self.dictSteps2mm('measurementStep')
            self.dictSteps2mm('stepperPosition')

            try:
                self.arcon.userInput['measurementDataCount'] = -(-float(self.arcon.userInput['measureEndPoint_mm'])//float(self.arcon.userInput['measurementStep_mm']))
            except:
                self.arcon.userInput['measureEndPoint_mm'] = float(self.arcon.userInput['measurementStep_mm'])
                self.entry5.insert(0, self.arcon.userInput['measureEndPoint_mm'])

                self.entry5.delete(0, 'end')  
                self.entry5.insert(0, self.arcon.userInput['measureEndPoint_mm']) 
                self.saveUserInput(self.entry5,'measureEndPoint_mm')

                self.updateMeasurementInputs()

            self.arcon.userInput['measureEndPoint_mm'] = int(self.arcon.userInput['measurementDataCount']) * float(self.arcon.userInput['measurementStep_mm'])

            self.entry5.delete(0, 'end')  
            self.entry5.insert(0, self.arcon.userInput['measureEndPoint_mm']) 
            self.saveUserInput(self.entry5,'measureEndPoint_mm')

            self.entry6.delete(0, 'end')  
            self.entry6.insert(0, self.arcon.userInput['measurementStep_mm']) 
            self.saveUserInput(self.entry6,'measurementStep_mm')

            self.entry7.delete(0, 'end')  
            self.entry7.insert(0, self.arcon.userInput['measurementDataCount']) 
            self.saveUserInput(self.entry7,'measurementDataCount')



     

            self.entry5.unbind('<Return>')
            self.entry5.bind('<Return>', lambda event: self.updateMeasurementInputs())      
            self.entry6.unbind('<Return>')
            self.entry6.bind('<Return>', lambda event: self.updateMeasurementInputs())
            self.entry7.unbind('<Return>')
            self.entry7.bind('<Return>', lambda event: self.updateMeasurementInputs())
      
        except Exception as e:

            self.entry5.unbind('<Return>')
            self.entry5.bind('<Return>', lambda event: self.updateMeasurementInputs())      
            self.entry6.unbind('<Return>')
            self.entry6.bind('<Return>', lambda event: self.updateMeasurementInputs())
            self.entry7.unbind('<Return>')
            self.entry7.bind('<Return>', lambda event: self.updateMeasurementInputs())

            self.entry6.delete(0, 'end')  
            self.entry6.insert(0, (1.0 / float(self.arcon.params['stepperStepsPerRev']))) 
            self.saveUserInput(self.entry6,'measurementStep_mm')          
            self.write2InfoConsole(e)

            

    def toggleRealTimeMeasurement(self):
     
        """
        Toggle the real-time measurement on or off.
        """

        self.varRealTimeMeasurement.set(not self.varRealTimeMeasurement.get())
        if self.varRealTimeMeasurement.get() == True:
            try:
                self.measureLiveButton.config(image = self.on)
                self.saveUserInput(self.entry10,'sampleCount'),
                self.arcon.getOneFieldData(self.arcon.userInput['sampleCount']),
                self.runRealTimeMeasurement()
                self.write2InfoConsole('Real-Time measurement toggled on.')

            except:
                self.measureLiveButton.config(image = self.off)
                self.varRealTimeMeasurement.set(False)
                tk.messagebox.showerror(title='Exception on Live Measurement', message='Check Arduino and/or Hall Sensor connection.')

        else:
            self.measureLiveButton.config(image = self.off)
            self.stop_live()
            self.write2InfoConsole('Real-Time measurement toggled off.')


    def toggleMosfetSwitch(self):
         
         """
         Toggle the MOSFET switch on or off.
         """

         state = self.varMosfetSwitch.get()
         try: 
            if state == False: 
                self.varMosfetSwitch.set(True)
                self.currentSwitchButton.config(image = self.on)
                self.loop.run_until_complete(self.arcon.mosfetSwitch.setState(1))
            else:
                self.varMosfetSwitch.set(False)
                self.currentSwitchButton.config(image = self.off)
                self.loop.run_until_complete(self.arcon.mosfetSwitch.setState(0))      
         except:
            tk.messagebox.showerror(title='Exception on Current Switch', message='Check Arduino connection.')
         
    def disableAllButtons(self):
        """
        Disable all buttons in the user interface.
        """
        self.disableButton(self.checkButton)
        self.disableButton(self.calibrateButton)
        self.disableButton(self.permanentButton)
        self.disableButton(self.coilButton)
        self.disableButton(self.moveToButton)
        self.disableButton(self.moveByButton)
        self.disableButton(self.measureOnceButton)
        self.disableButton(self.measureLiveButton)
        self.disableButton(self.currentSwitchButton)
        self.disableButton(self.initButton)
        self.disableButton(self.saveButton)

    def enableAllButtons(self):

        """
        Enable all buttons in the user interface.
        """

        self.enableButton(self.checkButton)
        self.enableButton(self.calibrateButton)
        self.enableButton(self.permanentButton)
        self.enableButton(self.coilButton)
        self.enableButton(self.moveToButton)
        self.enableButton(self.moveByButton)
        self.enableButton(self.measureOnceButton)
        self.enableButton(self.measureLiveButton)
        self.enableButton(self.currentSwitchButton)
        self.enableButton(self.initButton)
        self.enableButton(self.saveButton)



    def disableButton(self, button):
        button["state"] = 'disabled'

    def enableButton(self, button):
        button["state"] = 'normal'

    async def initializeMicroControllerConnection(self):   

        """
        Initialize the connection with the microcontroller (Arduino).
        """

        await self.arcon.initializeMicroController()

        if self.arcon.connectionState == 0:
            tk.messagebox.showerror(title='Exception on Arduino Management', message=self.arcon.exception)
            
            self.write2InfoConsole(self.arcon.exception)
        else:
            tk.messagebox.showinfo(title='Success', message='Connection with Ardiuno Established')
            self.enableAllButtons()
            self.write2InfoConsole('Connection with Ardiuno Established')


    def checkArduino(self):

        """
        Check the connection status with the Arduino.
        """

        try:
            self.arcon.loop.run_until_complete(self.arcon.queryConnection())
            
            if self.arcon.connectionState == True:    
                tk.messagebox.showinfo(title='Success', message='Connected to Ardiuno.')
            elif self.arcon.connectionState == False:
                tk.messagebox.showerror(title='Exception on Arduino Connection', message='Could not establish connection to Arduino.')
        except:
            tk.messagebox.showerror(title='Exception on Arduino Connection', message='Could not establish connection to Arduino.')
                
    def calibrationDistanceSubmit(self):

        """
        Submit the calibration distance entered by the user.
        """

        self.arcon.calibration_range_mm = self.calibrationDistanceEntry.get()
        self.arcon.params['stepperRev_mm'] = float(self.arcon.calibration_range_mm) / int(self.arcon.calibrationRange) * int(self.arcon.params['stepperStepsPerRev'])
        self.entryrev.delete(0, 'end')
        self.entryrev.insert(0, self.arcon.params['stepperRev_mm']) 
        self.sensor1_label_val.config(text=float(self.arcon.params['stepperRev_mm'])*int(self.arcon.params['photosensorPositionA'])/int(self.arcon.params['stepperStepsPerRev'])),
        self.sensor2_label_val.config(text=float(self.arcon.params['stepperRev_mm'])*int(self.arcon.params['photosensorPositionB'])/int(self.arcon.params['stepperStepsPerRev'])),
        self.top.destroy()

    def calibrationPopup(self):

        """
        Create a popup window for entering the calibration distance.
        """

        self.top = tk.Toplevel(self.root)

        label = tk.ttk.Label(self.top, text="Enter the measured distance (mm):")
        label.pack()

        self.calibrationDistanceEntry = tk.ttk.Entry(self.top)
        self.calibrationDistanceEntry.pack()

        button = tk.ttk.Button(self.top, text="Submit", command=self.calibrationDistanceSubmit)
        button.pack()


    async def mainHandler(self):
        
        try:
            self.root.state()
        except:
            # Shut down devices, stop event loop, close loop, and exit the program in case of exception
            self.loop.run_until_complete(self.arcon.shutDownDevices())
            self.loop.stop()
            self.loop.close()
            sys.exit()            

        # Calibration Point A event
        if self.arcon.calibrationEvent0.is_set():
            tk.messagebox.showinfo(title='Calibration Point A', message='Please mark the location of the slider.')
            self.arcon.calibrationUserConfirmEvent.set()
            self.arcon.calibrationEvent0.clear()

        # Calibration Point B event
        if self.arcon.calibrationEvent1.is_set():
            tk.messagebox.showinfo(title='Calibration Point B', message='Please measure the distance.')   
            self.arcon.calibrationUserConfirmEvent.set()
            self.arcon.calibrationEvent1.clear()
        
        # Calibration Point C event
        if self.arcon.calibrationEvent2.is_set():
            self.arcon.calibrationEvent2.clear()
            self.calibrationPopup()

        # Place magnet event        
        if self.arcon.placeMagnetEvent.is_set():
            self.arcon.placeMagnetEvent.clear()
            tk.messagebox.showinfo(title='turn on', message='Please place the permanent magnet or turn on the power supply for electromagnet.')
            self.arcon.placeMagnetConfirmEvent.set()

        # Query stepper position event to update on GUI
        if self.arcon.queryStepperPositionGUIEvent.is_set():
            self.arcon.queryStepperPositionGUIEvent.clear()
            self.dictSteps2mm('stepperPosition')
            self.stepper_label_val.config(text=str(self.arcon.params['stepperPosition_mm']))

        # Autosave upon finishing measurement
        if self.arcon.autoSaveEvent.is_set():
            self.arcon.autoSaveEvent.clear()
            self.saveDataFiles()


        # Update the live magnetic field plot and values
        if self.arcon.newLiveDataEvent.is_set():
            self.arcon.newLiveDataEvent.clear()
            
            self.ax2.cla()
            if self.varXplot.get(): 
                self.ax2.plot(self.arcon.liveResult[4],self.arcon.liveResult[0],'ro')
            if self.varYplot.get(): 
                self.ax2.plot(self.arcon.liveResult[4],self.arcon.liveResult[1],'go')
            if self.varZplot.get():
                self.ax2.plot(self.arcon.liveResult[4],self.arcon.liveResult[2],'bo')
            if self.varRplot.get():
                self.ax2.plot(self.arcon.liveResult[4],self.arcon.liveResult[3],'ko')

            if self.arcon.liveResult[0][-1]:
                self.hallx_label_val.config(text=str(self.arcon.liveResult[0][-1])[:6] + ' G')
                self.hally_label_val.config(text=str(self.arcon.liveResult[1][-1])[:6] + ' G') 
                self.hallz_label_val.config(text=str(self.arcon.liveResult[2][-1])[:6] + ' G') 
                self.hallr_label_val.config(text=str(self.arcon.liveResult[3][-1])[:6] + ' G') 

            self.canvas_2.draw_idle()
            self.ax2.relim()
            self.ax2.autoscale()
            self.ax2.set_title('Live Magnetic Field')
            self.ax2.set_xlabel('Time (s)')
            self.ax2.set_ylabel('Magnetic Field (G)')

        # Update the plots while measuring
        if self.arcon.newDataEvent.is_set():
            self.arcon.newDataEvent.clear()
            self.arcon.sensorPositions_mm = self.nonDictList2mm(self.arcon.sensorPositions)
            self.ax.cla()
            self.ax2.cla()

            if float(self.arcon.userInput['coilCurrent']) == 0:
                divider = 1
                self.ax.set_ylabel('Magnetic Field (G)')
            else:
                divider = float(self.arcon.userInput['coilCurrent'])
                self.ax.set_ylabel('Magnetic Field (G/A)')

            if self.varXplot.get():
                self.ax.plot(self.arcon.sensorPositions_mm[:len(self.arcon.aveMagnets[0])] ,[x / divider for x in self.arcon.aveMagnets[0]],'ro')
                self.ax2.plot(self.arcon.sensorPositions_mm[:len(self.arcon.aveStrays[0])],self.arcon.aveStrays[0],'ro')

            if self.varYplot.get(): 
                self.ax.plot(self.arcon.sensorPositions_mm[:len(self.arcon.aveMagnets[1])] ,[x / divider for x in self.arcon.aveMagnets[1]],'go')
                self.ax2.plot(self.arcon.sensorPositions_mm[:len(self.arcon.aveStrays[1])],self.arcon.aveStrays[1],'go')
            if self.varZplot.get():
                self.ax.plot(self.arcon.sensorPositions_mm[:len(self.arcon.aveMagnets[2])] ,[x / divider for x in self.arcon.aveMagnets[2]],'bo')
                self.ax2.plot(self.arcon.sensorPositions_mm[:len(self.arcon.aveStrays[2])],self.arcon.aveStrays[2],'bo')

            if self.varRplot.get():
                self.ax.plot(self.arcon.sensorPositions_mm[:len(self.arcon.aveMagnets[3])] ,[x / divider for x in self.arcon.aveMagnets[3]],'ko')
                self.ax2.plot(self.arcon.sensorPositions_mm[:len(self.arcon.aveStrays[3])],self.arcon.aveStrays[3],'ko')

            self.canvas.draw_idle()
            self.canvas_2.draw_idle()
            self.ax.relim()
            self.ax.autoscale()
            self.ax2.relim()
            self.ax2.autoscale()
            self.ax.set_title('Coil Magnetic Field')
            self.ax.set_xlabel('Sensor Position (mm)')
            self.ax2.set_title('Stray Magnetic Field')
            self.ax2.set_xlabel('Sensor Position (mm)')
            self.ax2.set_ylabel('Magnetic Field (G)')


            await asyncio.sleep(0)


    #GUI ELEMENTS CREATOR BELOW

    def createInformationConsole(self):
        frame = tk.ttk.LabelFrame(self.root, text="Information Console")
        frame.place(x=832, y=700, width=720, height=180)

        self.info_console = tk.Text(frame, state="disabled")
        self.info_console.place(x=5, y=0, width=705, height=150)

        scrollbar = tk.ttk.Scrollbar(frame, command=self.info_console.yview)
        scrollbar.pack(side="right", fill="y")
        self.info_console.config(yscrollcommand=scrollbar.set)
    
    def createToolbar(self):
        frame = tk.ttk.Frame(self.root, relief=tk.SUNKEN)
        frame.place(x=50, y=40, width=1500, height=35)

        self.initButton = tk.ttk.Button(frame, text="Initialize Arduino", command=lambda: self.loop.create_task(self.initializeMicroControllerConnection()))
        self.initButton.place(x=20, y=3)
        self.checkButton = tk.ttk.Button(frame, text="Check", command=self.checkArduino)
        self.checkButton.place(x=135, y=3)

        folder_label = tk.ttk.Label(frame, text="Folder Path:")
        folder_label.place(x=515, y=8)     
        self.folder_entry = tk.ttk.Entry(frame, width=76)
        self.folder_entry.place(x=605, y=6)
        
        browse_button = tk.ttk.Button(frame, text="Browse", command=self.browseFolderPath)
        browse_button.place(x=1310, y=3)
        
        self.saveButton = tk.ttk.Button(frame, text="Save", command=self.saveDataFiles)
        self.saveButton.place(x=1395, y=3)

    def createDataPlots(self):
        frame = tk.ttk.Frame(self.root, relief=tk.SUNKEN)
        frame.place(x=50, y=90, width=1500, height=505)

        figure = plt.Figure(figsize=(7, 4), dpi=100)
        self.ax = figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(figure, frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, frame)
        self.toolbar.update()
        self.toolbar.place(x=275, y=10)
        self.canvas.get_tk_widget().place(x=25, y=52)
        self.ax.set_title('Coil Magnetic Field')
        self.ax.set_xlabel('Sensor Position (mm)')
        self.ax.set_ylabel('Magnetic Field (G)')

        figure_2 = plt.Figure(figsize=(7, 4), dpi=100)
        self.ax2 = figure_2.add_subplot(111)
        self.canvas_2 = FigureCanvasTkAgg(figure_2, frame)
        self.toolbar_2 = NavigationToolbar2Tk(self.canvas_2, frame)
        self.toolbar_2.update()
        self.toolbar_2.place(x=1025, y=10)
        self.canvas_2.get_tk_widget().place(x=775, y=52)
        self.ax2.set_title('Stray Magnetic Field')
        self.ax2.set_xlabel('Sensor Position (mm)')
        self.ax2.set_ylabel('Magnetic Field (G)')
        
        checkboxframe = tk.ttk.Frame(frame)
        checkboxframe.place(x=670, y=470) #732

        
        self.varXplot = tk.BooleanVar(value=False)
        self.varYplot = tk.BooleanVar(value=False)
        self.varZplot = tk.BooleanVar(value=False)
        self.varRplot = tk.BooleanVar(value=False)


        self.checkbox_x = tk.ttk.Checkbutton(checkboxframe, text='x', variable=self.varXplot, onvalue=True, offvalue=False,  command=lambda:(self.arcon.newDataEvent.set()))
        self.checkbox_y = tk.ttk.Checkbutton(checkboxframe, text='y', variable=self.varYplot, onvalue=True, offvalue=False,  command=lambda:(self.arcon.newDataEvent.set()))
        self.checkbox_z = tk.ttk.Checkbutton(checkboxframe, text='z', variable=self.varZplot, onvalue=True, offvalue=False,  command=lambda:(self.arcon.newDataEvent.set()))
        self.checkbox_r = tk.ttk.Checkbutton(checkboxframe, text='R', variable=self.varRplot, onvalue=True, offvalue=False,  command=lambda:(self.arcon.newDataEvent.set()))  

        style = tk.ttk.Style()
        style.configure("TCheckbutton", font=("TkDefaultFont", 12))
        self.checkbox_x.pack(padx=5,side=tk.LEFT)
        self.checkbox_y.pack(padx=5,side=tk.LEFT)
        self.checkbox_z.pack(padx=5,side=tk.LEFT)
        self.checkbox_r.pack(padx=5,side=tk.LEFT)

    def createCalibrationFrame(self):
        frame = tk.ttk.LabelFrame(self.root, text="Calibration")
        frame.place(x=50, y=600, width=265, height=190)
        label = tk.ttk.Label(frame, text="Displacement (mm / rev):")
        label.place(x=5, y=10)

        self.entryrev = tk.ttk.Entry(frame, width=6)
        self.entryrev.place(x=185,y=8)
        self.entryrev.insert(0, self.arcon.params['stepperRev_mm']) 
        self.entryrev.unbind('<Return>')
        self.entryrev.bind('<Return>', lambda event: self.updateMeasurementInputs()) 
    

        stepper_label = tk.ttk.Label(frame, text="Stepper Position (mm):")
        stepper_label.place(x=5, y=45)
        self.dictSteps2mm('stepperPosition')
        self.stepper_label_val = tk.ttk.Label(frame, text=str(self.arcon.params['stepperPosition_mm']))
        self.stepper_label_val.place(x=185, y=45)

        sensor1_label = tk.ttk.Label(frame, text="Sensor 1 Position (mm):")
        sensor1_label.place(x=5, y=70)
        self.sensor1_label_val = tk.ttk.Label(frame, text=str(self.arcon.params['photosensorPositionA']))
        self.sensor1_label_val.place(x=185, y=70)
        
        sensor2_label = tk.ttk.Label(frame, text="Sensor 2 Position (mm):")
        sensor2_label.place(x=5, y=95)
        self.sensor2_label_val = tk.ttk.Label(frame, text=str(self.arcon.params['photosensorPositionB']))
        self.sensor2_label_val.place(x=185, y=95)

        self.calibrateButton = tk.ttk.Button(frame, text="Calibrate", command=lambda:
                                    (
                                     self.saveUserInput(self.entryrev, 'stepperRev_mm'),
                                     self.dictmm2steps('stepperRev_mm'),
                                     self.loop.create_task(self.arcon.runCalibration()),
                                     

                                     )
                                     )
                                        
        self.calibrateButton.place(x=90, y=125)

    def createMeasurementFrame(self):

        frame = tk.ttk.LabelFrame(self.root, text="Measurement")
        frame.place(x=320, y=600, width=225, height=281)
        label2 = tk.ttk.Label(frame, text='Coil Current (A):')
        label2.place(x=5, y=10)
        entry2 = tk.ttk.Entry(frame, width=8)
        entry2.place(x=128,y=10)
        entry2.insert(0, self.arcon.userInput['coilCurrent']) 
        entry2.bind('<Return>', self.saveUserInput(entry2,'coilCurrent'))

        label3 = tk.ttk.Label(frame, text='Average Count:')
        label3.place(x=5, y=38)

        entry3 = tk.ttk.Entry(frame, width=8)
        entry3.place(x=128,y=38)
        entry3.insert(0, self.arcon.userInput['sampleCount']) 
        entry3.bind('<Return>', self.saveUserInput(entry3,'sampleCount'))


        label5 = tk.ttk.Label(frame, text='Measure (mm):')
        label5.place(x=5, y=66)

        self.entry5 = tk.ttk.Entry(frame, width=8)
        self.entry5.place(x=128,y=66)
        self.entry5.insert(0, self.arcon.userInput['measureEndPoint_mm']) 

        label6 = tk.ttk.Label(frame, text='Step Size (mm):')
        label6.place(x=5, y=94)

        self.entry6 = tk.ttk.Entry(frame, width=8)
        self.entry6.place(x=128,y=94)
        self.entry6.insert(0, self.arcon.userInput['measurementStep_mm']) 
 
        label7 = tk.ttk.Label(frame, text='Step Count:')
        label7.place(x=5, y=122)
        self.entry7 = tk.ttk.Entry(frame, width=8)
        self.entry7.place(x=128,y=122)
        self.entry7.insert(0, self.arcon.userInput['measurementDataCount']) 
       
        self.entry5.bind('<Return>', self.updateMeasurementInputs())       
        self.entry6.bind('<Return>', self.updateMeasurementInputs())
        self.entry7.bind('<Return>', self.updateMeasurementInputs())
        self.entryrev.bind('<Return>', self.updateMeasurementInputs())


        self.coilButton = tk.ttk.Button(frame, text="Measure: Coil Mode",width=27, command=lambda:
                                    (
                                     self.saveUserInput(entry2,'coilCurrent'),
                                     self.saveUserInput(entry3,'sampleCount'),
                                     self.saveUserInput(self.entryrev,'stepperRev_mm'),
                                     self.saveUserInput(self.entry5,'measureEndPoint_mm'),
                                     self.dictmm2steps('measureEndPoint_mm'),
                                     self.updateMeasurementInputs(),
                                     self.disableAllButtons(),
                                     self.loop.create_task(self.arcon.runCoilMode())
                                     )
                                     )
                                        
        self.coilButton.place(x=18, y=196)

        self.permanentButton = tk.ttk.Button(frame, text="Measure: Permanent Mode ", width=27, command=lambda:
                                    (
                                     self.saveUserInput(entry2,'coilCurrent'),
                                     self.saveUserInput(entry3,'sampleCount'),
                                     self.saveUserInput(self.entryrev,'stepperRev_mm'),
                                     self.saveUserInput(self.entry5,'measureEndPoint_mm'),
                                     self.dictmm2steps('measureEndPoint_mm'),
                                     self.updateMeasurementInputs(),
                                     self.disableAllButtons(),
                                     self.loop.create_task(self.arcon.runPermaModeOff()),

                                     )
                                     )
                                        
        self.permanentButton.place(x=18, y=162)

    def createGroupLogo(self):
        self.lablogo = tk.PhotoImage(file = "assets/QGL.png")
        self.lablogo = self.lablogo.subsample(2)
        labellogo = tk.ttk.Label(self.root, image=self.lablogo)
        labellogo.place(x=552, y=700)

    def createManualOperationFrame(self):
        frame = tk.ttk.LabelFrame(self.root, text="Manual Operation")
        frame.place(x=550, y=600, width=1000, height=95)

        label8 = tk.ttk.Label(frame, text='Stepper move to (mm):')
        label8.place(x=5, y=7)

        self.entry8 = tk.ttk.Entry(frame, width=5)
        self.entry8.place(x=170,y=5)
        self.entry8.insert(0, 0)
        self.moveToButton = tk.ttk.Button(frame, text="Move", command=lambda:
                                    (
                                     self.saveUserInput(self.entry8,'stepper_target_position_mm'),
                                     self.dictmm2steps('stepper_target_position_mm'),
                                     self.loop.create_task(self.arcon.stepperMoveAbsolute(int(self.arcon.userInput['stepper_target_position']))),
                                     
                                     self.write2InfoConsole(self.arcon.params['stepperPosition'])
                                     )
                                )
                                                                    
        self.moveToButton.place(x=235, y=3)

        label9 = tk.ttk.Label(frame, text='Stepper move by (mm):')
        label9.place(x=5, y=47)

        self.entry9 = tk.ttk.Entry(frame, width=5)
        self.entry9.place(x=170,y=45)
        self.entry9.insert(0, 0) 

        self.moveByButton = tk.ttk.Button(frame, text="Move", command=lambda:
                                    (
                                     self.arcon.loop.create_task(self.arcon.stepperMoveRelative(round(float(self.entry9.get())/ float(self.arcon.params['stepperRev_mm']) * int(self.arcon.params['stepperStepsPerRev'])))),
                                     self.write2InfoConsole(self.arcon.params['stepperPosition'])
                                     )
                                )
                          
        self.moveByButton.place(x=235, y=43)


        readout_label = tk.ttk.Label(frame,  text='Last Readout:')
        readout_label.place(x=480, y=47)


        hallx_label = tk.ttk.Label(frame,  text='x:')
        hallx_label.place(x=600, y=47)
        self.hallx_label_val = tk.ttk.Label(frame, text=str('nan'))
        self.hallx_label_val.place(x=615, y=47)
        
        hally_label = tk.ttk.Label(frame, text="y:")
        hally_label.place(x=690, y=47)
        self.hally_label_val = tk.ttk.Label(frame, text=str('nan'))
        self.hally_label_val.place(x=705, y=47)

        hallz_label = tk.ttk.Label(frame, text="z:")
        hallz_label.place(x=780, y=47)
        self.hallz_label_val = tk.ttk.Label(frame, text=str('nan'))
        self.hallz_label_val.place(x=660+75+60, y=47)

        hallr_label = tk.ttk.Label(frame, text="R:")
        hallr_label.place(x=870, y=47)
        self.hallr_label_val = tk.ttk.Label(frame, text=str('nan'))
        self.hallr_label_val.place(x=885, y=47)

        self.on = tk.PhotoImage(file = "assets/on.png")
        self.on = self.on.subsample(2)
        self.off = tk.PhotoImage(file = "assets/off.png")
        self.off= self.off.subsample(2)

   
        self.varRealTimeMeasurement = tk.BooleanVar(value=False)        
        self.measureLiveButton = tk.ttk.Button(frame, text='Measure Field over Time:', image = self.off, compound="right",command=lambda:
                                                  (
                                                    self.toggleRealTimeMeasurement()
                                                  )
                                                  
                                                  )
        
        self.varRealTimeMeasurement.set(False)
        self.measureLiveButton.place(x=480, y=1)
             
        self.varMosfetSwitch = tk.BooleanVar(value=False)
        self.currentSwitchButton = tk.ttk.Button(frame, text='Current Switch:', image = self.off, compound="right",command=lambda:
                                                  
                                                   self.toggleMosfetSwitch()
                                                  
                                                  
                                                  )
        
        self.varMosfetSwitch.set(False)
        self.currentSwitchButton.place(x=700, y=1)

        self.measureOnceButton = tk.ttk.Button(frame, text='Measure Field Once', command=lambda:
                                    (
                                    self.saveUserInput(self.entry10,'sampleCount'),
                                    self.arcon.getOneFieldData(self.arcon.userInput['sampleCount']),
                                    self.hallx_label_val.config(text=str(self.arcon.oneFieldData[0])[:6] + ' G') ,
                                    self.hally_label_val.config(text=str(self.arcon.oneFieldData[1])[:6] + ' G') ,
                                    self.hallz_label_val.config(text=str(self.arcon.oneFieldData[2])[:6] + ' G') ,
                                    self.hallr_label_val.config(text=str(self.arcon.oneFieldData[3])[:6] + ' G') ,
                                    )
                                ) 
        
        self.measureOnceButton.place(x=340, y=3)

          
                                        
        label10 = tk.ttk.Label(frame, text='Average:')
        label10.place(x=340, y=47)

        self.entry10 = tk.ttk.Entry(frame, width=4)
        self.entry10.place(x=410,y=45)
        self.entry10.insert(0, self.arcon.userInput['sampleCount']) 
        self.entry10.bind('<Return>', self.saveUserInput(self.entry10,'sampleCount'))

        self.varXplot.set(True)
        self.varYplot.set(True)
        self.varZplot.set(True)
        self.varRplot.set(True)

        self.checkbox_x.bind("<Button-1>")
        self.checkbox_y.bind("<Button-1>")
        self.checkbox_z.bind("<Button-1>")
        self.checkbox_r.bind("<Button-1>")  

    def createMainWindow(self):
        self.root = ThemedTk()
        my_font = font.Font(size=12)
        tk.ttk.Style().configure("TButton", font=my_font)
        self.root.option_add("*Font", my_font)
        self.root.title('Automated Magnetometer GUI')
        self.root.set_theme('arc')
        self.root.wm_geometry("1600x900")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.userExit)

    def userExit(self):
        self.saveConfigCache()

        try:
            self.loop.run_until_complete(self.arcon.shutDownDevices())
            self.loop.stop()
        except:
            pass
        sys.exit()        

    def initializeUI(self):

        self.createMainWindow()
        self.createInformationConsole()
        self.createToolbar()
        self.createDataPlots()
        self.createCalibrationFrame()
        self.createMeasurementFrame()
        self.createGroupLogo()
        self.createManualOperationFrame()
        self.disableAllButtons()
        self.enableButton(self.initButton)

        try:
            self.loop.run_until_complete(self.run_tk())
        except:
            pass
            
    def runRealTimeMeasurement(self):
        self.arcon.streamstate = True
        self.loop.create_task(self.arcon.streamFieldData(self.arcon.userInput['sampleCount']))

    def stop_live(self):
        self.arcon.streamstate = False
        self.arcon.newLiveDataEvent.clear()

    def on_closing(self):
        sys.exit()

    async def run_tk(self):
        self.arcon.newLiveDataEvent = asyncio.Event()
        self.arcon.newDataEvent = asyncio.Event()
        self.arcon.calibrationEvent0 = asyncio.Event()
        self.arcon.calibrationEvent1 = asyncio.Event()
        self.arcon.calibrationEvent2 = asyncio.Event()
        self.arcon.placeMagnetEvent = asyncio.Event()
        self.arcon.autoSaveEvent = asyncio.Event()
       
        fps = 30
        while True:
            
            guiUpdateStartTime = time.time()
            try:
                self.root.update()
                self.loop.create_task(self.mainHandler())
            except:
                self.loop.run_until_complete(self.arcon.shutDownDevices())
                self.loop.stop()
                self.loop.close()
                sys.exit()
                
            guiUpdateEndTime = time.time()
            guiUpdateTime = guiUpdateEndTime-guiUpdateStartTime
            if 1/fps > guiUpdateTime:
                await asyncio.sleep(1/fps-guiUpdateTime)


if __name__ == '__main__':
    
    nest_asyncio.apply()
    handler = GUIHandler()
