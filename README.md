# Open source magnetometer for characterizing magnetic fields in ultracold experiments

This project is prepared for the ”Open Source Automated Magnetometer” designed to characterize magnetic field sources. This manual provides detailed instructions on how to effectively utilize our system designed specifically for experiments in ultracold physics. The Automated Magnetometer combines a high-precision Hall sensor and a stepper motor to enable precise characterization of magnetic field sources along a one-dimensional range. With this system, one can accurately measure and analyze magnetic fields, making it an essential tool for characterization of permanent and electromagnets. This manual aims to guide users through the installation, setup and operation while ensuring optimal performance and reliable results.

## Installation

The electronic components of the automated magnetometer are managed by an Arduino Mega single-board micro controller. Typically, micro-controllers are programmed with firmware designed to carry out specific operations, which can pose a challenge if modifications to the setup are desired, particularly in the case of open-source projects. To overcome this limitation, we have chosen to use a generic firmware based on the Firmata protocol, which facilitates communication between the software running on a computer and the Arduino board. We utilized the Telemetrix4Arduino firmware. This firmware can be easily uploaded to the microcontroller using the Arduino IDE Library manager. The source code for the firmware can be accessed at the following GitHub repository: https://github.com/MrYsLab/Telemetrix4Arduino.

## Usage

Users can use the GUI to execute specific tasks. Please refer to the user manual for the details.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.
