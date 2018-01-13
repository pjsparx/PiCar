#!/usr/bin/env python
from __future__ import print_function
try:
    # for Python 3.x
    import tkinter as tk
except ImportError:
    import Tkinter as tk
import tkMessageBox as mb
import math as m
import socket as s
import time
import game_controller as gc             # functions for using a gamepad
import virtual_controller as vc          # a very basic virtual gamepad
import ConfigParser as cfg
import sys

__NO_NETWORK__ = False         # set to true to test without
                               # connecting to a server
__CONNECTED__ = False          # connection status for the server

HARDWARE_CONTROLLER = False    # Existence of a hardware gamepad

# default configuration for the joystick.  These will be updated based
# on the client.cfg file
AZ_AXIS = 0                    # Controller axis: azimuth
EL_AXIS = 1                    # "              "  elevation
STEER_AXIS = 2                 # "              "  steering
DRIVE_AXIS = 3                 # "              "  drive motor
RECENTER_BTN = 8               # Controller button: recenter az/el   
CAPTURE_BTN = 0                # "                " image capture
RECORD_BTN = 1                 # "                " video capture
L_BRAKE_BTN = 6                # "                " left motor brake
R_BRAKE_BTN = 7                # "                " right motor brake
L_REV_BTN = 4                  # "                " left motor reverse
R_REV_BTN = 5                  # "                " right motor reverse
REFRESH_RATE = 10              # refresh rate for controller inputs


SERVO_STEP = float(REFRESH_RATE)/200.0  # step size for az/el servo
                                        # movements this is set to
                                        # take 2 seconds to go from 0
                                        # to 90 degrees


# popup widget for asking what server to connect to
class ServerConfigDialog(tk.Frame):
    def __init__(self, config):
        tk.Frame.__init__(self)

        self.ip = config.get('Network','IP')
        self.port = config.getint('Network','PORT')
        
        # create a new window with a label, entry field, and ok button
        self.top = tk.Toplevel()
        self.label1 = tk.Label(self.top, text="IP Address")
        self.label1.grid(row=0, column = 0)
        self.entry1 = tk.Entry(self.top)
        self.entry1.insert(0,format(self.ip))   # set the default ip
        self.entry1.grid(row=0, column = 1)
        self.label2 = tk.Label(self.top, text="Port")
        self.label2.grid(row=1, column = 0)
        self.entry2 = tk.Entry(self.top)
        self.entry2.insert(0,format(self.port)) # set the default port
        self.entry2.grid(row=1, column = 1)  
        self.okbutton = tk.Button(self.top, text='Ok')
        self.okbutton.grid(row=2, column = 0, columnspan = 2)
        
        
        # bind the button click and and a "return" press to a callback
        self.top.bind("<Return>", self.submit_n_close)
        self.okbutton.bind("<Button-1>", self.submit_n_close)

        # force the focus to the entry field and raise the window
        self.entry1.focus_force()
        self.top.attributes("-topmost", True)
        
    def submit_n_close(self, event):
        # get the value entered by the user
        self.value1 = self.entry1.get()
        self.value2 = self.entry2.get()
        
        # see if it's a valid address
        try:
            s.inet_aton(self.value1)   # try to convert it to a binary address 
            self.top.destroy()   # close the popup window
        except s.error:          # the conversion failed -- invalid address
            # add code for an error popup box
            mb.showerror('Invalid IP', 'The submitted IP address is invalid'
                         ', it should be in the form of 127.0.0.1')
            
            


# code for running an example instance        
class Example(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        root.title('PyCar Remote')

        self.root = root
        
        # read the network config-file data in client.cfg
        self.config = config = cfg.RawConfigParser()
        config.read('client.cfg')
        self.ip = config.get('Network','IP')
        self.port = config.get('Network','PORT')
        
        
        # make a place to store the last commanded car state
        self.car_state = {'L':0.0,'R':0.0,'S':0.0,'A':0.0,'E':0.0}
                
        # add a button for network config
        self.connect_button = tk.Button(self, text='Connect')
        self.connect_button.grid(column=0, row=0, sticky = 'w')
        self.top_label = tk.Label(self, text="Configured for {}".\
                                  format(self.ip))
        self.top_label.grid(column=1, row=0, columnspan = 1)
        self.connect_button.bind("<Button-1>", self.network_setup_callback)
         

        ########################
        # set up and connect to the network port
        self.network_setup()     #  get the ip and connect to the pi
        self.bind('<<DISCONNECTED>>', self.disconnect_callback)

        # send a command to center all the controls on the car
        if __CONNECTED__:
            self.tcp_client_soc.send('L:+0.0,R:+0.0,S:+0.0,A:+0.0,E:+0.0')
        
        #########################
        # set up the USB game controller
        global HARDWARE_CONTROLLER
        try:
            self.controller_setup()
        except gc.NoController:
            print("couldn't find hardware controller")
            HARDWARE_CONTROLLER = False


        ########################
        # setup and display a joystick widget
        if not HARDWARE_CONTROLLER:
            self.v_controller_setup()

    def v_controller_setup(self):
        v_remote_popup = vc.PopupVirtualRemote()
        v_remote = self.v_remote = v_remote_popup.remote
        #self.v_remote.grid()
        
        # react to events generated by the virtual remote
        self.bind_all('<<V_JOYSTICK_UPDATE>>', self.v_joystick_update)
        
        # configure the virtual remote labels etc...
        v_remote.jstick_0.toplabel.config(text = 'Camera')
        v_remote.jstick_1.toplabel.config(text = 'Steering')

    
    def controller_setup(self):
       
        global HARDWARE_CONTROLLER, AZ_AXIS, EL_AXIS, STEER_AXIS
        global DRIVE_AXIS, RECENTER_BTN, CAPTURE_BTN, RECORD_BTN
        global L_BRAKE_BTN, L_REV_BTN, R_REV_BTN, REFRESH_RATE

        config = self.config
        print("looking for controller")
        self.controller = gc.MyGameController(self.root)
        HARDWARE_CONTROLLER = True
        AZ_AXIS = config.getint('Joystick','AZ_AXIS')
        EL_AXIS = config.getint('Joystick','EL_AXIS')
        STEER_AXIS = config.getint('Joystick','STEER_AXIS')
        DRIVE_AXIS = config.getint('Joystick','DRIVE_AXIS')
        RECENTER_BTN = config.getint('Joystick','RECENTER_BTN')
        CAPTURE_BTN = config.getint('Joystick','CAPTURE_BTN')
        RECORD_BTN = config.getint('Joystick','RECORD_BTN')
        L_BRAKE_BTN = config.getint('Joystick','L_BRAKE_BTN')
        R_BRAKE_BTN = config.getint('Joystick','R_BRAKE_BTN')
        L_REV_BTN = config.getint('Joystick','L_REV_BTN')
        R_REV_BTN = config.getint('Joystick','R_REV_BTN')
        REFRESH_RATE = config.getint('Joystick','REFRESH_RATE')
        
        self.bind_all('<<JOYSTICK_UPDATE>>', self.joystick_update)
        self.controller.delay = 1000//REFRESH_RATE        
        print("found controller")
    
              
    def network_setup(self):

        global __CONNECTED__
        
        # configure the network connection to the pi
        self.call_server_config()       # get the ip from the user
        address = (self.ip, int(self.port))  # combined address
        print(address)
        
        # update the message bar at the top of the window
        self.top_label.config(text="Configured for {}:{}".\
                              format(self.ip, self.port))
        
        # create a socket and use it to connect to the pi 
        if not __NO_NETWORK__:
            # create the socket
            print("setting up socket")
            self.tcp_client_soc = s.socket(s.AF_INET, s.SOCK_STREAM)
            self.tcp_client_soc.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR,1)
            
            # try to connect to it, throw an error if not
            msg = self.tcp_client_soc.connect_ex(address)   # try to connect
            self.tcp_client_soc.settimeout(3)  

            # if the connection was successful, change the connect button
            if msg == 0:
                __CONNECTED__ = True
                self.top_label.config(text = 'Connected to {}:{}'.\
                                      format(self.ip, self.port))
                self.connect_button.config(text = 'Disconnect')
                self.connect_button.bind('<Button-1>',
                                         self.disconnect_callback)

            # if the connection failed, send a message and try to
            # close the socekt
            else:
                print( 'Failed to connect to {}:{} -- {}'.\
                       format(self.ip,self.port,str(msg)))
                __CONNECTED__ = False
                #self.tcp_client_soc.close()

    def v_joystick_update(self, event):
        j_stick = self.v_remote
        c_state = j_stick.state
        car_state = self.car_state

        # command the motors
        car_state['L'] = c_state['A{}'.format(DRIVE_AXIS)]
        car_state['R'] = c_state['A{}'.format(DRIVE_AXIS)]

        # command the steering servo
        car_state['S'] = c_state['A{}'.format(STEER_AXIS)]

        # command the az/el servos
        car_state['A'] = c_state['A{}'.format(AZ_AXIS)]
        car_state['E'] = c_state['A{}'.format(EL_AXIS)]

        self.send_state()
        
        #print("<<V_JOYSTICK_UPDATE>> State = {}".format(car_state))
        
    def joystick_update(self,event):
        c_state = self.controller.state
        car_state = self.car_state

        # command the motors
        car_state['L'] = -c_state['A{}'.format(DRIVE_AXIS)]
        car_state['R'] = -c_state['A{}'.format(DRIVE_AXIS)]

        if c_state['B{}'.format(L_BRAKE_BTN)]:
            car_state['L'] = 0 
        if c_state['B{}'.format(R_BRAKE_BTN)]:
            car_state['R'] = 0

        # deal with potential reverse commands    
        if c_state['B{}'.format(L_REV_BTN)]:
            car_state['L'] *= -1;
        if c_state['B{}'.format(R_REV_BTN)]:
            car_state['R'] *= -1;
        
        # command the steering servo
        car_state['S'] = c_state['A{}'.format(STEER_AXIS)]

        # drive the azimuth/elevation servos
        car_state['A'] = c_state['A{}'.format(AZ_AXIS)]
        car_state['E'] = c_state['A{}'.format(EL_AXIS)]
#            car_state['A'] = 0.0
#            #car_state['E'] = 0.0
#            #print("recentered")
#        else:
#            val = c_state['A{}'.format(AZ_AXIS)]
#            current = car_state['A'];
#            current += val*SERVO_STEP
#            if current <= 0:
#                car_state['A'] = max(current, -1.0)
#            else:
#                car_state['A'] = min(current, 1.0)
#
#        val = c_state['A{}'.format(EL_AXIS)]
#        current = car_state['E'];
#        current -= val*SERVO_STEP
#        if current <= 0:
#            car_state['E'] = max(current, -1.0)
#        else:
#            car_state['E'] = min(current, 1.0)
        

        self.send_state()
        
        
    # call up the server configuration dialog   
    def call_server_config(self):
        popup = ServerConfigDialog(self.config)
        popup.wait_window(popup.top)
        self.ip = popup.value1
        self.port = popup.value2

        
    def shutdown():
        self.tcp_client_soc.close()
        

        
    # send the state message to the remote server to control the car    
    def send_state(self):
        global __CONNECTED__
        
        state = self.car_state
        statemessage = 'L:{0:+5.2f},R:{1:+5.2f},S:{2:+5.2f},'\
                       'A:{3:+5.2f},E:{4:+5.2f}'\
                       .format(state['L'],state['R'],state['S'],\
                               state['A'],state['E'])

        # send the statemessage if we are connected to the server
        if __CONNECTED__:
            try:
                self.tcp_client_soc.send(statemessage)
            except:
                __CONNECTED__ = False
                self.event_generate("<<DISCONNECTED>>")
                
        # if __NO_NETWORK__, print the state message 
        elif __NO_NETWORK__:
            print(statemessage, end='\r')
            sys.stdout.flush()
    
    def disconnect_callback(self,event):
        global __CONNECTED__

        try:
            self.tcp_client_soc.shutdown()
            self.tcp_client_soc.close()
        except:
            print("Couldn't close the connection")
            
        __CONNECTED__ = False
        self.connect_button.config(text = 'Connect')
        self.connect_button.bind('<Button-1>', self.network_setup_callback)
        
    def network_setup_callback(self, event):
        # callback function for event-driven network setup
        self.network_setup()
      
    
if __name__ == "__main__":

    
    try:
        
        # Open a root window and put a title on it
        root = root.self = tk.Tk()  # create a top-level window
        root.title('Smart Car Remote Control')

        # Put the controller in the new window
        v_remote = Example(root)  # run the example
        v_remote.pack()

        # run it
        root.mainloop()
        
    except KeyboardInterrupt:
        
        v_remote.shutdown
