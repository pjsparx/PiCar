#!/usr/bin/env python
import RPi.GPIO as GPIO
import car_ctl as c
import socket as s
import time as time
import ConfigParser as cfg
import PCA9685 as servo

# read data from the config file
config = cfg.RawConfigParser()
config.read('config')

# network settings
busnum = config.getint('network', 'busnum') 
HOST = config.get('network', 'HOST')
PORT = config.getint('network','PORT')
BUFSIZ = config.getint('network','BUFSIZ')
CONNECTIONS = config.getint('network','CONNECTIONS')

ADDR = (HOST, PORT) # composit address for socket()



def test_servo(config):
    pwm = c.PWM_setup(config)  # initialize the pwm controller
    
    channel = 0
    max_range = 90
    min_range = -90
    offset = 0
    servo = c.ServoDevice(pwm, channel, max_range, min_range, offset, config)
    
    angles = [-1, -.75, -.675, -.5, -.375, -.25, -.125, 0, .125,
              .25, .375, .5, .675, .75, 1]
    speeds = [-1, -.5, -.25, 0, .25, .5, 1]
    
    for angle in angles:
        servo.moveto(angle)
        print 'angle={}'.format(angle)
        time.sleep(1)

    servo.moveto(0)

def test_motor(config):
    pwm = c.PWM_setup(config)  # initialize the pwm controller
    channel = config.getint('car','M0_pwm_ch')
    ctl_1 = config.getint('car','Motor0_A')
    ctl_2 = config.getint('car','Motor0_B')
    reverse = config.getboolean('car','M0_reverse')

    speeds = [-1, -.5, -.25, 0, .25, .5, 1]
    
    motor = c.MotorDevice(pwm, channel, ctl_1, ctl_2, reverse, config)

    for speed in speeds:
        motor.setspeed(speed)
        time.sleep(3)

    motor.setspeed(0)
    
def test_car(config):

    angles = [-1, -.5, 0, .5, 1]
    speeds = [-1, -.5, -.25, 0, .25, .5, 1]

    car = c.Car(config)
    
    for speed in speeds:
        car.command_car(speed,0,0,0,0)
        time.sleep(2)
        car.command_car(0,speed,0,0,0)
        time.sleep(2)
        car.command_car(speed,speed,0,0,0)
        time.sleep(2)
        
    for angle in angles:
        car.command_car(0,0,angle,angle,angle)
        time.sleep(2)

    car.command_car(0,0,0,0,0)


test_servo(config)
# test_motor(config)
#test_car(config)
