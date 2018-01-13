#!/usr/bin/env python
from __future__ import print_function
try:
    # for Python 3.x
    import tkinter as tk
except ImportError:
    # for Python 2.6+  (this will won't work on python < 2.6)
    import Tkinter as tk

import tkMessageBox as mb
import math as m
import socket as s
import time

## define the joystick widget as a subclass of a TK frame.  The
## joystick's output is stored as the Joystick.x and Joystick.y
## attributes.  The full-scale output of x and y are in the range
## [-1,1].  The joystick area is 101 pixels across as currently
## implemented.  I should probably find a way to dynamically determine
## this, but for now, it's fixed.  The graphics suck, but that's not
## something I really care about.  The VirtualRemote generates a
## <<V_JSTICK_UPDATE>> event to signal the higher-level
## widgets/windows that they need to re-read the state and act on it
##
## VirtualRemote.state{} =
## {'A0':0.0,'A1':0.0,'A2':0.0,'A3':0.0,'B0':False, 'B1':False} where
## A0-3 are the state of the x and y axes for joystick 0 and 1, and
## B0, and B1 are the state of the buttons.  Axes are in the range
## [-1.0, 1.0] and buttons are True when pressed and False when
## released


                
        
        
class VirtualRemote(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self,parent)  # Init the parent object (Tk Frame)

        self.parent = parent
        self.state = {'A0':0.0, 'A1':0.0, 'A2':0.0, 'A3':0.0,
                      'B0':False, 'B1':False}      # initialize the state vector

        # parameters to make it look more like a pygame joystik
        self.axes = 4
        self.hats = 0
        self.buttons = 2
        
        
        ####################################
        # build the controller by stacking widgets
                
        # add the left joystick
        self.jstick_0 = Joystick(self, parent, pad_size=200)
        self.jstick_0.grid(column = 0, row = 2) 
        self.jstick_0.bind("<<State-Updated>>", self.update_callback)
        self.jstick_0.sticky = True
        self.jstick_0.toplabel = tk.Label(self, text="Joystick 0") 
        self.jstick_0.toplabel.grid(column = 0, row = 1)
        
        # add the right joystick
        self.jstick_1 = Joystick(self, parent, pad_size=200)
        self.jstick_1.grid(column = 1, row = 2) 
        self.jstick_1.bind("<<State-Updated>>", self.update_callback)
        self.jstick_1.sticky = False
        self.jstick_1.toplabel = tk.Label(self, text="Joystick 1") 
        self.jstick_1.toplabel.grid(column = 1, row = 1)        

        # add a couple of buttons
        self.b0 = JButton(self, 0, text = 'B0')
        self.b0.bind("<Button-1>", self.buttonpress)
        self.b0.bind("<ButtonRelease-1>", self.buttonpress)
        self.b0.grid(row=0, column=0)
        self.b1 = JButton(self, 1, text = 'B1')
        self.b1.bind("<Button-1>", self.buttonpress)
        self.b1.bind("<ButtonRelease-1>", self.buttonpress)
        self.b1.grid(row=0, column=1)
        
        
    def buttonpress(self,event):
        # figure out which button was pressed
        button = event.widget
        buttonnumber = 'B{}'.format(button.num)

        # toggle that button's state
        self.state[buttonnumber] = not self.state[buttonnumber]

        # force an upadate
        self.event_generate('<<V_JOYSTICK_UPDATE>>')
        
        
       
    def update_callback(self, event):
        # Pull data from the widgets to create an update state vector
        self.state['A0'] = self.jstick_0.x
        self.state['A1'] = self.jstick_0.y
        self.state['A2'] = self.jstick_1.x
        self.state['A3'] = self.jstick_1.y

        # send the updated state message to the remote connection
        self.event_generate("<<V_JOYSTICK_UPDATE>>")
        
        
class PopupVirtualRemote(tk.Frame):
    def __init__(self):
        tk.Frame.__init__(self)
        
        
        # popup a new window
        self.top = tk.Toplevel()
        remote = self.remote = VirtualRemote(self.top)
        # drop the remote into it       
        remote.pack()
        
        
class JButton(tk.Button):

    def __init__(self,parent,number,*args, **kwargs):
        tk.Button.__init__(self,parent, *args, **kwargs)
        self.num = number
        
        
        
# make a joystick widget with a "nob" that the user can drag around a canvas
class Joystick(tk.Frame):
  
    # set up the init function
    def __init__(self, parent, *args, **kwargs):

        self.parent = parent
        
        # get the joystick size from kwargs or set it to 101
        self.pad_size = kwargs.get('pad_size',101)
        
        tk.Frame.__init__(self, parent)

        # set up the dimensions and center-point
        x0 = m.ceil(self.pad_size/2)
        y0 = m.ceil(self.pad_size/2)
        r = 0.3 * x0

        # store them in the class structure
        self.x0 = x0
        self.y0 = y0
        self.r = r

        # initialize the joystick coordinates
        self.x = 0
        self.y = 0

        # add an atribute to determine if the joystick stays where you
        # left it or springs back to the center when let go
        self.sticky = False 
                
        # create the canvas widget
        self.canvas = tk.Canvas(self, width=self.pad_size,
                                height=self.pad_size,
                                background='#888') 
        self.canvas.grid(row=0)  

        # add a label below the joystick with the current joystick
        # output valuse in it
        self.label = tk.Label(self, text='X: {}  Y: {}'\
                              .format(self.x, self.y))
        self.label.grid(row=1)
        
        # bounding box for the joystick at center
        stick_0_bb = (x0 - r, y0 - r, x0 + r, y0 + r)
          
        # start by drawing the joystick in the center of the canvas
        joystick_area = self.canvas
        self.nob = joystick_area.create_oval(stick_0_bb, fill="black")      
        
        # bind the callback function to the button-pressed motion event
        joystick_area.bind( "<ButtonPress-1>", self.j_stick_movetoclick)
        joystick_area.bind( "<B1-Motion>", self.j_stick_movetoclick)
        joystick_area.bind( "<ButtonRelease-1>", self.j_stick_center_callback)

             
    # define callback functions to use when we click-drag on the canvas
    def j_stick_movetoclick(self, event):
        '''Move the joystick knob to where the mouse is'''
        canvas = self.canvas;
        nob = self.nob;

        # get the current position of the joystick nob on the canvas

        old_position = canvas.coords(nob)

        # figure out how far it needs to move and move it
        dx = canvas.canvasx(event.x - self.r) - old_position[0]
        dy = canvas.canvasy(event.y - self.r) - old_position[1]
        canvas.move(nob, dx, dy)

        # update the joystick position/output make sure the range of
        # possible outputs is (-1,1) -- deals with cases where the
        # stick is dragged outside the box
        if ( event.x < 0 ):
            tmp_x = 0
        elif ( event.x >  self.pad_size ):
            tmp_x = self.pad_size
        else:
            tmp_x = event.x          

        if ( event.y < 0 ):
            tmp_y = 0
        elif ( event.y > self.pad_size ):
            tmp_y = self.pad_size
        else:
            tmp_y = event.y

        # convert grid coordinates into [-1,1] value
        x = 2.0 * (float(tmp_x) / float(self.pad_size) - 0.5) 
        y = -2.0 * (float(tmp_y) / float(self.pad_size) - 0.5)

        # store the value and update the label on the joystick
        self.x = x
        self.y = y
        self.label.config(text='X: {:3.1f}  Y: {:3.1f}'.\
                          format(self.x, self.y))
        self.label.update_idletasks()

        # trigger an update to the state-vector
        self.event_generate("<<State-Updated>>")

    def j_stick_center_callback(self,event):
        if not self.sticky:
            self.j_stick_center()

    def force_center(self,event):
        self.j_stick_center()
        
    def j_stick_center(self):
        # move the joystick back to center
                
        canvas = self.canvas
        nob = self.nob 

        # get the current position of the joystick nob on the canvas
        oldposition = canvas.coords(nob)
        x1 = oldposition[0]
        y1 = oldposition[1]
        x2 = oldposition[2]
        y2 = oldposition[3]
            
        # figure out how far it needs to move and move it
        dx = self.x0 - x1 - self.r
        dy = self.y0 - y1 - self.r
        canvas.move(nob, dx, dy)
            
        # update the joystick position/output
        self.x = 0
        self.y = 0          
        self.label.config(text='X: 0  Y: 0'.format(self.x, self.y))
            
        # trigger an update
        self.event_generate("<<State-Updated>>")

           
# code for running an example instance        
class Example(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        root.title('PyCar Remote')

        
        # make and display a joystick widget
        self.remote = VirtualRemote(self)
        self.remote.grid()

    def shutdown():
        print("shutdown")
        
    
if __name__ == "__main__":

    
    try:
        
        # make a canvas widget that can act like a simple joystick
        root = root.self = tk.Tk()  # create a top-level window
        root.title('Smart Car Remote Control')

        
        # make a frame and put a virtual remote in it
        #f = tk.Frame(top)
        v_remote = Example(root)  # run the example
        v_remote.grid()
        
        root.mainloop()
        
    except KeyboardInterrupt:
        
        v_remote.shutdown
