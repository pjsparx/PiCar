#/usr/bin/env python
#
#  Functions to initialize and control the car -- drive motors and steering servo

import PCA9685 as servo
import time
import ConfigParser as cfg
import RPi.GPIO as GPIO
import math as m

class Car ():
    # object class containing the servos and motors on the car
    def __init__(self,config):

        ## read data from the config file
        self.config = cfg.RawConfigParser()
        self.config.read('config')

        
        # initialize the PWM controller
        self.pwm = PWM_setup(self.config)

        ############################
        # set up the turning servo
        channel = config.getint('car','turn_channel')
        max_range = config.getint('car', 'max_turn')
        min_range = config.getint('car', 'min_turn')
        offset = config.getint('car', 'steer_offset')
        self.turn_servo = ServoDevice(self.pwm, channel, max_range,
                                      min_range, offset, self.config)
        

        ############################
        # set up the gimbal servos
        
        # Azimuth servo
        channel = config.getint('camera', 'az_channel')
        max_range = config.getint('camera', 'max_azimuth')
        min_range = config.getint('camera', 'min_azimuth')
        offset = config.getint('camera', 'azimuth_offset')
        self.az_servo = ServoDevice(self.pwm, channel, max_range,
                                    min_range, offset,self.config)
        

        # Elevation servo
        channel = config.getint('camera', 'el_channel')
        max_range = config.getint('camera', 'max_elevation')
        min_range = config.getint('camera', 'min_elevation')
        offset = config.getint('camera', 'elevation_offset')
        self.el_servo = ServoDevice(self.pwm, channel, max_range,
                                    min_range, offset, self.config)
        ###########################
        # set up the motors
        
        # Motor0
        channel = config.getint('car','M0_pwm_ch')
        ctl_1 = config.getint('car','Motor0_A')
        ctl_2 = config.getint('car','Motor0_B')
        reverse = config.getboolean('car','M0_reverse')
        self.motor0 = MotorDevice(self.pwm, channel, ctl_1, ctl_2,
                             reverse, self.config)

        # Motor1
        channel = config.getint('car','M1_pwm_ch')
        ctl_1 = config.getint('car','Motor1_A')
        ctl_2 = config.getint('car','Motor1_B')
        reverse = config.getboolean('car','M1_reverse')
        self.motor1 = MotorDevice(self.pwm, channel, ctl_1, ctl_2,
                             reverse, self.config)

    ####################    
    # command_car(m0, m1, turn, az, el)
    #
    # commands the servos and motors on the car
    #
    # (float) m0 = [-1.0,1.0] speed for the left motor.  Negative
    #              inputs put the motor into reverse.  0 is stop, 1 is
    #              full speed
    #
    # (float) m1 = [-1.0,1.0] speed for the right motor.  Negative
    #              inputs put the motor into reverse.  0 is stop, 1 is
    #              full speed
    #
    # (float) turn = [-1.0,1.0] position for the turn servo.  -1 is the
    #               minimum angle, and 1 the maximum.  As implemented
    #               now, -1 represents approximately -90 degrees annd
    #               1 approximately 90 degrees
    #
    # (float) az = [-1.0,1.0] position for the azimuth servo.  -1 is
    #               the minimum angle, and 1 the maximum.  As
    #               implemented now, -1 represents approximately -90
    #               degrees annd 1 approximately 90 degrees
    #
    # (float) el = [-1.0,1.0] position for the elevation servo.  -1 is
    #               the minimum angle, and 1 the maximum.  As
    #               implemented now, -1 represents approximately -90
    #               degrees annd 1 approximately 90 degrees
    #
    # passing any of the arguments as 'None' will result in that input
    # being unchanged from it's current state
    def command_car(self, m0, m1, turn, az, el):

        if turn != None:
            # set the steering
            self.turn_servo.moveto(turn)

        if az != None:
            # need to multiply by -1 to take care of the fact that the
            # servo is upside-down relative to the turn servo
            # set the azimuth
            self.az_servo.moveto(-az)

        if el != None:
            # set the elevation 
            self.el_servo.moveto(el)

        # command the drive motors 
        if m0 != None:
            self.motor0.setspeed(m0)
        if m1 != None:
            self.motor1.setspeed(m1)
        
class MotorDevice ():
    # pwm is the pwm controller on the car channel is the channel on
    # the pwm controller ctl_1 and ctl_2 control the motor direction
    # and braking ctl_1 set HIGH and ctl_2 set LOW drive the motor
    # forward ctl_1 set LOW and ctl_2 set HIGH drive the motor
    # backwards ctl_1 and ctl_2 set to the same state actively brake
    # the motor the pwm signal modulates the enable on the controller,
    # and acts as a speed control.  The gpio pins are referenced to
    # the board layout

    def __init__(self, pwm, channel, ctl_1, ctl_2, reverse, config):

        # define stuff
        self.max_speed = config.getint('car','max_speed')
        self.reverse = reverse
        self.pwm_ch = channel           # channel on the pwm controller  
        self.pwm = pwm                  # pwm controller to attach to
        self.ctl_1 = ctl_1              # pin number for ctl_1
        self.ctl_2 = ctl_2              # pin number for ctl_2
        self.speed = 0.0                # [-1,1] motor speed

        # configure the GPIO pins as outputs
        pins = [ctl_1, ctl_2]
        GPIO_setup(pins)

        # set the speed to zero
        self.setspeed(0.0)

    def setspeed(self,speed):
        # possible motor speeds are in the range [-1.0,1.0]
        # store the requested speed value
        self.speed = speed
        
        # reverse the direction if called for
        if self.reverse:
            speed *= -1
        
        # set the direction using the GPIO pins
        if speed < 0:     # go backwards
            GPIO.output(self.ctl_1, GPIO.HIGH)
            GPIO.output(self.ctl_2, GPIO.LOW)
            
        elif speed == 0:  # stop
            GPIO.output(self.ctl_1, GPIO.LOW)
            GPIO.output(self.ctl_2, GPIO.HIGH)
            
        else:             # go forwards
            GPIO.output(self.ctl_1, GPIO.LOW)
            GPIO.output(self.ctl_2, GPIO.HIGH)
                        
        # calculate the correct motor speed & command the pwm
        speedPWM = int(m.floor(abs(speed)*4095))  # 4096 possible pwm states
        self.pwm.write(self.pwm_ch, 0, speedPWM)

        
    
    
# define a class for the servo motors
class ServoDevice ():

    ####################
    # class ServoDevice(pwm, channel, max, min, offset, config)
    #
    # pwm = pwm controller instance
    # channel = channel on the pwm controller to command
    # max = max angle to allow (in degrees)
    # min = min angle to allow (in degrees)
    # offset = calibration offset (as fraction of [-1,1] input range
    # config = config data read in previously
    #
    # The ServoDevice.moveto() method expects an input in the range of
    # [-1,1].  -1 drives the counter-clockwise to the maximum angle,
    # and +1 drives it to the max-extent the opposite direction
    
    # define the initialization function
    def __init__(self, pwm, channel, max_range, min_range, offset, config):

        # read the max and min pwm range for the servo from the config file
        max_pwm = config.getfloat('servos','max_pwm')  # (ms)
        min_pwm = config.getfloat('servos','min_pwm')  # (ms)
        pwm_frequency = config.getfloat('servos','pwm_frequency') # (HZ)
        
        # convert to fractions of 4096 sample period (12bit resolution)
        cycle_samples = 4096                          # (samples/period)
        max_duty_cycle = pwm_frequency*max_pwm/1000   # duty cycle
        min_duty_cycle = pwm_frequency*min_pwm/1000
        
        # set the absolute max upper and lower limits
        maxPWM = m.floor(max_duty_cycle * cycle_samples)
        minPWM = m.ceil(min_duty_cycle * cycle_samples)

        # set the parameters
        self.maxPWM = maxPWM
        self.minPWM = minPWM
        self.pwm = pwm
        self.channel = channel
        self.max_range = max_range   # maximum angle (user defined)
        self.min_range = min_range   # minimum angle (user defined)
        self.position = 0
        self.offset = offset
        
        # drive the servo to the center position
        self.moveto(0)

    def moveto(self, cmd):
        # moveto(cmd)  -- cmd is a float in the interval [-1.0,1.0]
        #
        # -1 is mapped to self.min_range degrees, and 1 is mapped to
        # self.max_range to deal with overly large inputs do this
        # first in case the user max and min are larger than the
        # hardware limits (+- 90 degrees)

        angle = cmd*90            # convert the input an angle
        offset = self.offset*180  # calibration offset in deg
        angle-= offset            # apply calibration offset

        # avoid overdriving the servo
        if angle > 90:
            angle = 90 
        elif angle < -90:
            angle = -90

        # map the input to scale between the user defined max and min
        # [min_range, max_range]    

        #half_output_range = (self.max_range - self.min_range)/2.0
        #angle = (cmd+1)*half_output_range + self.min_range + offset

        angle = 90*cmd + offset
        if angle > self.max_range:
            angle = self.max_range
        elif angle < self.min_range:
            angle = self.min_range
        

        #    angle = cmd * self.max_range + offset
            #print 'overscale'
        #elif angle <= 0:
        #    if cmd < 0:
        #        angle = -cmd * self.min_range + offset
        #    else:
        #        angle = cmd * self.min_range + offset

        # convert the angle to pwm samples    
        drive_pwm = int(self.pwm_map(angle))
            
        # send the pwm command to the controller
        self.pwm.write(self.channel, 0, drive_pwm)

        # store the current position
        self.angle = angle + offset
        
    # function to map from controller coords to pwm coords
    def pwm_map(self,angle):

        # norm the angle to the range [0,1]
        normed = float(angle + 90) / 180  
        
        # scale it to pwm units
        output = normed * (self.maxPWM - self.minPWM) + self.minPWM  

        return output
    

# configure GPIO pins as outputs
def GPIO_setup(pins): 

    GPIO.setwarnings(False)   # turn off warnings
    GPIO.setmode(GPIO.BOARD)  # assign pins by physical location (pin
                              # number)

   
    for pin in pins:  
        GPIO.setup(pin,GPIO.OUT)  # set pins as outputs
        GPIO.output(pin, GPIO.LOW) # set pins to LOW


# initialize the pwm/servo controller
def PWM_setup(config):
    busnum = config.getint('network','busnum')
    servo_freq = config.getint('servos','pwm_frequency')
    
    pwm = servo.PWM(busnum)
    pwm.frequency = servo_freq
    return pwm



def turn_test():
    while True:
	turn(-45)
	time.sleep(1)
	turn(0)
	time.sleep(1)
	turn(45)
	time.sleep(1)
	turn(0)
        
if __name__ == '__main__':
    setup()
    turn(0)
