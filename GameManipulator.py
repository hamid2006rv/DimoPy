
# coding: utf-8

# In[196]:

from __future__ import division


# In[197]:

from autopy import *
import scanner
import gc


# In[198]:

# Cache screen size
screen_width, screen_height= screen.get_size()

Scanner = scanner.Scanner();

# COLOR DEFINITIONS
# This is the Dino's colour, also used by Obstacles.
COLOR_DINOSAUR = 5460819 #535353;

PRESS = True;
RELEASE = False;


# In[199]:

import win32gui
import re

class WindowMgr:
    """Encapsulates some calls to the winapi for window management"""
    def __init__ (self):
        """Constructor"""
        self._handle = None

    def find_window(self, class_name, window_name = None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, wildcard):
        '''Pass to win32gui.EnumWindows() to check all the opened windows'''
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) != None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)

    def set_foreground(self):
        """put the window in the foreground"""
        win32gui.SetForegroundWindow(self._handle)


# In[200]:

import time,datetime
def date_now():
    d=datetime.datetime.utcnow()
    for_js=int(time.mktime(d.timetuple())*1000000 + d.microsecond)
    return for_js


# In[201]:

import threading
def set_interval(func, sec):
    def func_wrapper():
        set_interval(func,sec)
        func()
    t = threading.Timer(sec , func_wrapper)
    t.start()
    return t


# In[202]:

class GameManipulator:
    def __init__(self):
        # Stores the game position (Globally)
        self.offset= None
        self.width= None

        # Stores points (jumps)
        self.points= 0

        # Listners
        self.onGameEnd= None
        self.onGameStart= None
        self.onSensorData= None

        # Game State
        self.gamestate= 'OVER'

        # GameOver Position
        self.gameOverOffset= [190, -82]

        # Stores an array of "sensors" (Ray tracings)
        # Positions are always relative to global "offset"
        self.sensors= [
            {
                'lastScore':0,
                'lastValue': 1,

              'value': 0,
              'offset': [84, -15], # 64,-15
              'step': [4, 0],
              'length': 0.3,

              # Speed
              'speed': 0,
              'lastComputeSpeed': 0,
               'lastSpeeds':[],

              # Computes size of the object
              'size': 0,
              'computeSize': True,
            },
          ]
        self.lastOutputSet = 'NONE';
        self.lastOutputSetTime = 0;
        
        ######
        w = WindowMgr()
        w.find_window_wildcard(".*http.*")
        w.set_foreground()

    # Find out dinosaur (fast)
    def findGamePosition(self):
        bmp =bitmap.capture_screen()
        skipXFast = 15;
        
        for x in range(20, screen_width,skipXFast):
            dinoPos = Scanner.scanUntil(
                                          # Start position
                                          [x, 80],
                                          # Skip pixels
                                          [0, skipXFast],
                                          # Searching Color
                                          COLOR_DINOSAUR,
                                          # Normal mode (not inverse)
                                          False,
                                          # Iteration limit
                                          500 / skipXFast, bmp)
            if (dinoPos!= None):break
            
        
        for x in range(dinoPos[0] - 50, dinoPos[0]+1):
            pos = Scanner.scanUntil(
                                      # Start position
                                      [x, dinoPos[1] - 2],
                                      # Skip pixels
                                      [0, 1],
                                      # Searching Color
                                      COLOR_DINOSAUR,
                                      # Normal mode (not inverse)
                                      False,
                                      # Iteration limit
                                      100, bmp)

            if (pos!=None): break


        # Did actually found? If not, error!
        if (pos==False):   return None
        

        # Find the end of the game
        endPos = pos;

        while (bmp.get_color(endPos[0] + 3, endPos[1]) == COLOR_DINOSAUR):
            endPos = Scanner.scanUntil(
                                        # Start position
                                        [endPos[0] + 2, endPos[1]],
                                        # Skip pixels
                                        [2, 0],
                                        # Searching Color
                                        COLOR_DINOSAUR,
                                        # Invert mode
                                        True,
                                        # Iteration limit
                                        600,bmp);
        # Did actually found? If not, error!
        if (endPos==False): return None
  
        #Save to allow global access
        self.offset = pos;
        self.width = 600;#endPos[0] - pos[0];
        
        return pos
    
    # Read Game state
    # (If game is ended or is playing)
    def readGameState(self):
        
        bmp= bitmap.capture_screen()
        #gc.collect()
        # Read GameOver

        found = Scanner.scanUntil(
        [
          self.offset[0] + self.gameOverOffset[0],
          self.offset[1] + self.gameOverOffset[1]
        ],
        [2, 0], COLOR_DINOSAUR, False, 20, bmp)
        
        if (found and self.gamestate != 'OVER'):
            self.gamestate = 'OVER';
            # Clear keys
            #self.setGameOutput(0.5);

            # Trigger callback and clear
            self.onGameEnd and self.onGameEnd(self.points)
            self.onGameEnd = None;
        
            print 'GAME OVER: ',self.points
        elif (found == None and self.gamestate != 'PLAYING'):
            self.gamestate = 'PLAYING';

            # Clear points
            self.points = 0;
            self.lastScore = 0;

            # Clear keys
            #self.setGameOutput(0.5);

            # Clear sensors
            self.sensors[0]['lastComputeSpeed'] = 0;
            self.sensors[0]['lastSpeeds'] = [];
            self.sensors[0]['lastValue'] = 1;
            self.sensors[0]['value'] = 1;
            self.sensors[0]['speed'] = 0;
            self.sensors[0]['size'] = 0;

            # Clar Output flags
            self.lastOutputSet = 'NONE';

            # Trigger callback and clear
            self.onGameStart and self.onGameStart();
            #self.onGameStart = None;

            print 'GAME RUNNING ', self.points
            
    # Set action to game
    # Values:
    #  0.00 to  0.45: DOWN
    #  0.45 to  0.55: NOTHING
    #  0.55 to  1.00: UP (JUMP)
    def setGameOutput (self,output):

        self.gameOutput = output;
        self.gameOutputString = self.getDiscreteState(output);

        if (self.gameOutputString == 'DOWN'):
            # Skew
            key.toggle(key.K_DOWN, PRESS)
            key.toggle(key.K_DOWN, RELEASE)
        elif (self.gameOutputString == 'NORM'):
            # DO Nothing
            key.toggle(key.K_UP, RELEASE)
            key.toggle(key.K_DOWN, RELEASE)
        else:
            # Filter JUMP
            if (self.lastOutputSet != 'JUMP'):
                self.lastOutputSetTime = date_now()
        # JUMP
        # Check if hasn't jump for more than 3 continuous secconds
        if (date_now() - self.lastOutputSetTime < 3000):
            key.toggle(key.K_UP, PRESS)
            key.toggle(key.K_UP, RELEASE)
        else:
            key.toggle(key.K_UP, RELEASE)
            key.toggle(key.K_DOWN, RELEASE)
    
        self.lastOutputSet = self.gameOutputString
        
    #
    # Simply maps an real number to string actions
    #
    def getDiscreteState (self, value):
        if (value < 0.45):
            return 'DOWN'
        elif(value > 0.55):
            return 'JUMP'
        return 'NORM';
    
    # Click on the Starting point
    # to make sure game is focused
    def focusGame(self):
        mouse.click()

    # Compute points based on sensors
    #
    # Basicaly, checks if an object has
    # passed trough the sensor and the
    # value is now higher than before
    def computePoints(self):
        for k in self.sensors: 
            sensor = k

        if (sensor['value'] > 0.5 and sensor['lastValue'] < 0.3):
            self.points+=1;
        # console.log('POINTS: '+GameManipulator.points);
    
        
    # Read sensors
    #
    # Sensors are like ray-traces:
    #   They have a starting point,
    #   and a limit to search for.
    #
    # Each sensor can gatter data about
    # the DISTANCE of the object, it's
    # SIZE and it's speed
    #
    # Note: We currently only have a sensor.
    def readSensors(self):
        bmp =bitmap. capture_screen()
        offset = self.offset;

        startTime = date_now();
        
        for k in self.sensors: 
            sensor = k
            
            # Calculate absolute position of ray tracing
            start = [
                    offset[0] + sensor['offset'][0],
                    offset[1] + sensor['offset'][1],
                    ]

            # Compute cursor forwarding
            forward = sensor['value'] * self.width * 0.8 * sensor['length'];

            end = Scanner.scanUntil(
                # Start position
                [start[0], start[1]],
                # Skip pixels
                sensor['step'],
                # Searching Color
                COLOR_DINOSAUR,
                # Invert mode?
                False,
                # Iteration limit
                (self.width * sensor['length']) / sensor['step'][0],
                bmp)
            
            # Save lastValue
            sensor['lastValue'] = sensor['value'];

            # Calculate the Sensor value
            if (end):
                sensor['value'] = (end[0] - start[0]) / (self.width * sensor['length'])

                # Calculate size of obstacle
                endPoint = Scanner.scanUntil(
                    [end[0] + 75, end[1]],
                    [-2, 0],
                    COLOR_DINOSAUR,
                    False,
                    75 / 2,
                    bmp)

                # If no end point, set the start point as end
                if (endPoint==False):
                    endPoint = end
      
                sizeTmp = (endPoint[0] - end[0]) / 100.0
                if (self.points == sensor['lastScore']):
                    # It's the same obstacle. Set size to "max" of both
                    sensor['size'] = max(sensor['size'], sizeTmp);
                else:
                    sensor['size'] = sizeTmp
      
                # We use the current score to check for object equality
                sensor['lastScore'] = self.points;

                # sensor.size = Math.max(sensor.size, endPoint[0] - end[0]);


            else:
                sensor['value'] = 1
                sensor['size'] = 0
    

            # Compute speed
            dt = (date_now() - sensor['lastComputeSpeed']) /1000
           
            
            sensor['lastComputeSpeed'] = date_now()
        
            if (sensor['value'] < sensor['lastValue']):
                # Compute speed
                newSpeed = (sensor['lastValue'] - sensor['value']) / dt
                
                sensor['lastSpeeds'].insert(0,newSpeed)
                
                while (len(sensor['lastSpeeds']) > 10):
                    sensor['lastSpeeds'].pop();
      

                # Take Average
                avgSpeed = 0;
                for k in sensor['lastSpeeds']:
                    avgSpeed += k / len(sensor['lastSpeeds'])
                

                sensor['speed'] = max(avgSpeed , sensor['speed'])

    

            # Save length/size of sensor value
            sensor['size'] = min(sensor['size'], 1.0)

            startTime = date_now()
  

        # Compute points
        self.computePoints()
        # Call sensor callback (to act)
        self.onSensorData()
        
    
    # Call this to start a fresh new game
    # Will wait untill game has ended,
    # and call the `next` callback

    def startNewGame(self):

        def f():
            t=threading.Timer(0.3 , f).start()
            self.readGameState()
            self.readSensors()
            if self.gamestate == 'OVER':
                key.toggle(' ',True)
                key.toggle(' ',False)
            return t
        t=f()


