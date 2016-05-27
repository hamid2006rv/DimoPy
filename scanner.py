
# coding: utf-8

# In[37]:

from autopy import *


# In[38]:

# Cache screen size
screen_width, screen_height= screen.get_size()


# Indexes
X = 0;
Y = 1;


# In[39]:

# Create the "class" wrapper
class Scanner:
    # Check if the given position is outside the Screen
    def isOutOfBound(self, pos) :
        if ( pos[X] < 0 or pos[Y] < 0 or   pos[X] >= screen_width or pos[Y] >= screen_height):
            return True
        return False
    # Limits the x/y values of position to fit the screen
    def makeInBounds(self, pos):
        if (pos[X] < 0):
            pos[X] = 0
        if (pos[X] >= screen_width):
            pos[X] = screen_width - 1
        if (pos[Y] < 0):
            pos[Y] = 0
        if (pos[Y] >= screen_height):
            pos[Y] = screen_height - 1
        return pos
    #  Given start [X, Y], and a DELTA [dX, dY],
    #  maps from "start", adding "delta" to position,
    #  until "matchinColor" is found OR isOutOfBounds.
    #
    #  If iterations reach > iterLimit:
    #    returns null;
    #
    #  if isOutOfBounds:
    #    returns null
    #
    #  otherwise:
    #    return that point
    #
    #  Example: (X direction)
    #    scanUntil([0,0], [1, 0], "000000");
    def scanUntil (self,start, delta, matchColor, inverted, iterLimit, bmp):
        iterations = 0
        # CLONE instead of using the real one
        current = self.makeInBounds([start[X], start[Y]])
        
        
        if (delta[X] == 0 and delta[Y] == 0):
            return None
  
        while (self.isOutOfBound(current)== False):
            # Check current pixel
            color = bmp.get_color(current[X], current[Y])
            
            if (inverted == False and color == matchColor):
				
				return current
				
            if (inverted and color != matchColor):
                return current;
            current[X] += delta[X];
            current[Y] += delta[Y];
            iterations+=1;

            if (iterations > iterLimit):
                return None
    
        return None


