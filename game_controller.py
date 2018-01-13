#!/usr/bin/env python
from __future__ import print_function
try:
    # for python 3.x
    import tkinter as tk
except ImportError:
    import Tkinter as tk
import pygame 
import sys

## class for initializing a game controller/joystick using pygame.  it
## generates a dictionary self.state containing the current state of
## all the axes, buttons and hats on the controller. self.state takes
## the form {'A0':float, 'B0':Boolean, 'Hat0':(float,float)} where A
## is an axis, B is a button, and H is a hat.

class MyGameController:
    def __init__(self, root):
        self.root = root
        self.state = {}
        self.delay = 100   # delay betwen joystick updates (ms)
        
        # self.state = {'A0':0, 'A1':0, 'A2':0, 'A3':0,\
        #               'B0':False, 'B1':False, 'B2':False,\
        #               'B3':False, 'B4':False, 'B5':False,\
        #               'B6':False, 'B7':False, 'B8':False,\
        #               'B9':False, 'B10':False,'B11':False,\
        #               'Hat0':(0,0)}



        ## initialize the joystick
        pygame.init()
        if(pygame.joystick.get_count() < 1):
            # there weren't any joysticks
            print("No Game Controller Detected")
            raise NoController()
        else:
            # grab the first joystick pygame found (I don't plan on
            # having more than one).
            joystick = pygame.joystick.Joystick(0)
            self.joystick = joystick
            self.joystick.init()

            # figure out how many axes, hat's and buttons there are
            self.axes = joystick.get_numaxes()
            self.buttons = joystick.get_numbuttons()
            self.hats = joystick.get_numhats()
            self.name = joystick.get_name()
            print('{},\n{} axes, {} buttons, {} hats'.format(\
                  self.name, self.axes, self.buttons, self.hats))
            
            # initialize the state dictionary
            self.get_buttons()
            self.get_axes()
            self.get_hats()
            
        # See if there are any events pending in the queue
        self.root.after(0, self.get_events)

    def get_events(self):
        # check the pygame queue for joystick events
        events = pygame.event.get();
        jstick = self.joystick;

        # read and parse the events, updating the state as required
        for event in events:

            # get the controller state
            self.get_buttons()
            self.get_axes()
            self.get_hats()

            # trigger an update if it's a button press event just in
            # case a button is pressed and released between updates
            if event.type == pygame.JOYBUTTONDOWN or \
               event.type == pygame.JOYBUTTONUP:
                self.trigger_update()

        # we need to trigger an update every time this is called as well
        self.trigger_update()

        # reschedule another update for 100ms (10 Hz update rate) from now
        self.root.after(self.delay, self.get_events)
        
    def get_buttons(self):

        jstick = self.joystick
    
        # get the state from each of the buttons
        for c1 in range(self.buttons):
            button = jstick.get_button(c1)
            key = 'B{}'.format(c1)
            self.state[key] = button
            
    def get_axes(self):

        jstick = self.joystick
        
        # get the state of the buttons
        for c2 in range(self.axes):
            axis = jstick.get_axis(c2)
            key = 'A{}'.format(c2)
            self.state[key] = axis

    def get_hats(self):

        jstick = self.joystick
        
        # get the state of each hat
        for c1 in range(self.hats):
            hat = jstick.get_hat(c1)
            key = 'H{}'.format(c1)
            self.state[key] = hat

         
    def trigger_update(self):
        root = self.root
        root.event_generate('<<JOYSTICK_UPDATE>>')

class NoController(Exception):
    def __init__(self):
        Exception.__init__(self, 'No physical controllers installed')    
    
class Example():
    def __init__(self):
        root = tk.Tk()
        root.joystick = MyGameController(root)
    
    
        canvas = tk.Canvas(root, width=500, height=250)
        root.canvas = canvas
        canvas.pack()

        root.ball1 = canvas.create_oval([245, 120],[255, 130], fill='red')
        root.ball2 = canvas.create_oval([220, 100],[230, 110], fill='blue')
        root.bind('<<JOYSTICK_UPDATE>>', self.callback)

        root.mainloop()

    def callback(self,event):
        state = event.widget.joystick.state
        canvas = event.widget.canvas
        ball1 = event.widget.ball1
        ball2 = event.widget.ball2
    
        # set up the joysticks to move the ball
        if state['A0'] != 0 or state['A1'] !=0:
            mvx = int(10 * state['A0']) 
            mvy = int(10 * state['A1'])
            canvas.move(ball1, mvx, mvy)

        if state['A2'] != 0 or state['A3'] !=0:
            mvx = int(10 * state['A2']) 
            mvy = int(10 * state['A3'])
            canvas.move(ball2, mvx, mvy)

        if state['B0'] == 1:
            canvas.itemconfig(ball1, fill='pink')
        else:
            canvas.itemconfig(ball1, fill='red')

        if state['B1'] == 0:
            canvas.itemconfig(ball2, fill='blue')
        else:
            canvas.itemconfig(ball2, fill='green')

        if state['B2'] == 1:
            canvas.config(background = 'orange')
        else:
            canvas.config(background = 'white')
        
    
if __name__ == '__main__':
    e = Example()
