 #!/usr/bin/env python
from __future__ import print_function
import socket as soc
import time as time          # Import necessary modules
import ConfigParser as cfg
import select
import car_ctl as c
import sys
import math as m

# read data from the config file
config = cfg.RawConfigParser()
config.read('config')

# network settings
busnum = config.getint('network', 'busnum') 
HOST = config.get('network', 'HOST')
PORT = config.getint('network','PORT')
BUFSIZ = config.getint('network','BUFSIZ')
CONNECTIONS = config.getint('network','CONNECTIONS')
TIMEOUT = config.getfloat('network','TIMEOUT')

ADDR = (HOST, PORT) # composit address for socket()

# create and connect to a socket
tcpSerSock = soc.socket(soc.AF_INET, soc.SOCK_STREAM)    # Create a socket.
tcpSerSock.setsockopt(soc.SOL_SOCKET, soc.SO_REUSEADDR, 1)
tcpSerSock.bind(ADDR)    # Bind the IP address and port number of the server. 
tcpSerSock.listen(CONNECTIONS)     # listen() defines max number of
                                   # simultaneous connections

# instantiate the car (which will initialize the hardware also)
car = c.Car(config)

def server_loop():
    # run the server
    while True:
        print ('Waiting for connection on {}...'.format(ADDR))
        # Accept() returns a separate client socket when a connection
        # is made. accept() is a blocking function that is suspended
        # before a connectin is made. 

        tcpCliSock, addr = tcpSerSock.accept() 
        tcpCliSock.setblocking(0)        # turn off blocking so the
                                         # watchdog can run
        print('...connection from :', addr)     # Print the IP address of
                                          # the client connected with
                                          # the server.  
	while True:
	    data = ''
            # data =
            # "Left_Motor:+000,Right_Motor:+000,Steer:+000,
            #  Azimuth:+000,Elevation:+000"
            # look to see if there is data read on the socket.  don't
            # call .recv until data is ready so we can implement a
            # timeout timer without .recv taking control and blocking
            # progress.  after TIMEOUT seconds, issue a command to
            # stop the car 
            ready = select.select([tcpCliSock], [], [], TIMEOUT)

            if ready[0]:         # data is ready on the socket
                data = tcpCliSock.recv(BUFSIZ)    # Receive data sent from
                                              # the client.  Analyze
                                              # the command received
                                              # and control the car
                                              # accordingly.
            else:      # in this case, we hit the timeout, stop the
                       # car so it doesn't run away
                car.command_car(0,0,None,None,None)
                break
                
      
            bad_packet = False
            # otherwise we should have valid data to work with parse
            # the message

            if data != '':
                # parse the left motor command
                ind = data.find("L:")
                if ind != -1:
                    try:
                        left_speed = float(data[ind+2:7])
                    except:
                        print('Malformed packet L={}'.format(data[ind+2:7]))
                        bad_packet = True

                else:
                    print('Malformed data packet == no Left_Motor')
                    bad_packet = True
            
                # parse the right motor command    
                ind = data.find("R:")
                if ind != -1:     
                    try:
                        right_speed = float(data[ind+2:ind+7])
                    except:
                        print('Malformed packet R={}'.format(data[ind+2:7]))
                        bad_packet = True

                else:
                    print('Malformed data packet == no Right_Motor')
                    bad_packet = True

                # parse the steering command
                ind = data.find("S:")
                if ind != -1:
                    try:
                        turn = float(data[ind+2:ind+7])
                        turn = pow(turn,3.0)
                    except:
                        print('Malformed packet T={}'.format(data[ind+2:7]))
                        bad_packet = True

                else:
                    print('Malformed data packet == no Steer')
                    bad_packet = True
                
                # parse the azimuth command
                ind = data.find("A:")
                if ind != -1:     
                    try:
                        az = float(data[ind+2:ind+7])
                    except:
                        print('Malformed packet A={}'.format(data[ind+2:7]))
                        bad_packet = True
                else:
                    print('Malformed data packet == no Azimuth')
                    bad_packet = True
                
                # elevation command
                ind = data.find('E:')
                if ind != -1:
                    try:
                        el = float(data[ind+2:ind+7])
                    except:
                        print('Malformed packet E={}'.format(dat[ind+2:7]))
                        bad_packet = True

                else:
                    print('Malformed data packet == no Elevation')
                    bad_packet = True
                
                if not bad_packet:
                    # send complete command to the controllers    
                    car.command_car(left_speed,right_speed,turn,az,el)
            else:
                break

            
if __name__ == "__main__":
    try:
        server_loop()

    except KeyboardInterrupt:
        tcpSerSock.close()
    
