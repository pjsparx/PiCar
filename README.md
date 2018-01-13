# PiCar
Code for running the Sunrounder camera car based on a Raspberry-Pi

Caveat emptor: 
1. I'm new to python, and have little formal programming training.  That said, I found the code that was distributed by Sunfounder to be abysmal.  It wasn't modular in any way, couldn't handle exceptions, and didn't even work very well.  I figured this would be a reasonable place to start with Python and jumped in.  I have no idea if I've done things in a cannonical fasion, or even if what I've done is safe.  It seems to work in all the test cases I've played with.  I offer it to the public in the hope that it helps someone else, but with no promises or warranty whatsoever.  I welcome constructive feedback.  If all you have to say is that my code sucks, keep it to yoursef.

2. I don't run windows or mac.  This works on Linux Mint, and should work on windows if you have python and pygame installed, but I have no way to know for sure.  Your mileage may vary.

3. This doesn't do anything with video streaming.  I've been using the motion package on the pi, and firefox to connect to it.  There is probably a more efficient method, but I've not spent a lot of time on that part of the problem.

Files in the package:

car_ctl.py -- contains routines for controlling the motors and servos on the car

client.cfg -- config file for the client-side.  This config is used by the computer you are using to remote-control the car.

config -- config file for the server-side.  This config is used by the tcpserver.py file and resides on the Pi

game_controller.py -- routines for initializing and using a hardware game controller.  NOTE: this requires pygame to work

PCA9685.py -- routines for controlling the PWM controller.  This is the only code I kept from the Sunfounder package.

reset -- quick routine to reset the hardware to zero-state.  This stops the motors and centers all the servos

tcpserver.py -- server application that runs on the pi.  listens for valid commands and parses/passes them to car_ctl

testcar.py -- routine to test the various control funcitons.  should be run on the pi

virtual_controller.py -- an on-screen set of joysticks for controlling the car if there is no hardware joystick

To run this code:

1. Edit the config and client.cfg files to suit your needs.  Most likely all you will need to edit is the HOST ip address.  If you are using a hardware joystick/game controller that is different from what I have, you may need to edit the client.cfg file to assign the proper axes and buttons to the various functions. 

2. Dump the whole package in a folder on both the remote-control computer and the pi. gftp is my preferred option for pushing files to the pi.  (google is your friend if you don't know how)  If you want to separate out the client and server files, put tcpserver.py, car_ctl.py, PCA9685.py, reset, testcar.py and config on the RPi.  For the client put client_app.py, game_controller.py, virtual_controller.py, and client.cfg on the computer you're using to control the car. 

3. Log into the pi via vncviewer or ssh (again, google is your friend)

4. Open a terminal, change to the directory where you dumped the package, and type "python tcpserver.py" at the prompt. This will start the server that listens for commands.

5. On the computer from which you will be controlling the car, run the client_app.py script.  In Linux, type "python clinet_app.py" at a terminal prompt. If you run windows, consult google or your local guru.

Assuming you have a hardware controller installed, the clinet program will pop up asking you for an ip address.  If you edited the client.cfg file to use the IP of the Pi, it should already have that info in the box.  Click ok, and you should be able to control the car.  If you don't have a hardware controller, the virtual controller should come on-screen.  Click and drag the black dot as if it were the joystick.  

Todo: 

1. Wrap this in an init-script that can be called at boot so the server automatically starts when the car boots up

2. Find an optimal low-latency video streaming solution for the camera

3. Connect a callback to capture a video frame and tie it to one of the controller buttons.

4. Re-write or clean-up the PCA9685 code
