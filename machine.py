'''
    ServoPlotter:   Version 1.0
    Author:         Vishwanath
    Dependencies:   scipy, wxpython, pyserial
'''

import serial
import os
import sys
import wx

from wx.lib import ogl
from time import sleep
from scipy import *
from scipy.ndimage import *
from math import *

'''
    Warnings:
    1. Dont disturb the logic changing circuit in between operations,
       it will start sending garbage values
    2. Maximum of 100 possible COM ports is assumed.
'''

POINT_RADIUS = 5        # Constants for GUI
NUM_POINTS = 10

class myogl(wx.Frame):
    def __init__(self,parent,id):
        #initialise the system
        wx.Frame.__init__(self,parent,id,'OGL 2')

        panel = wx.Panel(self)
        
        self.im = wx.Bitmap('blank_canvas.jpg')
        mycursor = wx.StockCursor(wx.CURSOR_CROSS)
        # Put a boxer here immediately             
        if 'win' in sys.platform:
            sizeinfo = (self.im.Size[0]+16,self.im.Size[1]+68)
        else:
            sizeinfo = self.im.Size
        self.Size = sizeinfo

        #create the canvas and load a circle of unit radius
        canvas = ogl.ShapeCanvas(panel)
        canvas.Size = self.im.Size
        
        # create a bitmap shape to add to the canvas.disable dragging

        pic = ogl.BitmapShape()
        pic.SetBitmap(self.im)
        pic.SetX(int(self.im.Size[0]/2))
        pic.SetY(int(self.im.Size[1]/2))
        pic.SetDraggable(False)     # Disable dragging for the background canvas.
                
        # create a diagram for the canvas.
        diagram = ogl.Diagram()
        canvas.SetDiagram(diagram)
        diagram.SetCanvas(canvas)
        canvas.AddShape(pic)
        diagram.SetGridSpacing(1)
                       
        # create multiple points. add lines to them
        self.points = []
        self.lines = []

        origin = ogl.CircleShape(POINT_RADIUS)
        origin.SetX(20)
        origin.SetY(20)
        origin.SetPen(wx.Pen('red',1))
        self.points.append(origin)
        canvas.AddShape(origin)

        #Create a button to call the plotting program
        plot_btn = wx.Button(panel,label = 'Plot',pos = (0,self.im.Size[1]),size = (60,30))
        plot_btn.Bind(wx.EVT_BUTTON,self.Plot)

        # create one more button to write the points
        write_btn = wx.Button(panel,label = 'Write Points',pos = (60,self.im.Size[1]),size = (100,30))
        write_btn.Bind(wx.EVT_BUTTON,self.Write)
        
        # create an instance of the canvas to help the CreatePoint function
        self.bg = canvas

        # bind an event to the canvas on right click.
        # change rigth click to ctrl + click.
        canvas.Bind(wx.EVT_RIGHT_DOWN,self.CreatePoint)
        
        # show the diagram.
        diagram.ShowAll(True)
        self.Show()

    def CreatePoint(self,event):
        
        if event.RightDown():
            
            x,y = event.GetPositionTuple()
            # create a clientDC to redraw the canvas

            dc = wx.ClientDC(self.bg)
            self.bg.PrepareDC(dc)

            # create a new point when right click event occurs
            point = ogl.CircleShape(POINT_RADIUS)
            point.SetX(x)
            point.SetY(y)
            self.bg.AddShape(point)

            # create a line joining the present point to the last point

            line = ogl.LineShape()
            line.MakeLineControlPoints(2)
            line.Initialise()
           
            point.AddLine(line,self.points[-1])
            
            # append this point to the points list
            self.points.append(point)
            
            # add both the shapes to the canvas.
            
            self.bg.AddShape(line)
            # make the shapes visible. very important step
            point.Show(True)
            line.Show(True)

            # update the canvas
            self.bg.Redraw(dc)
            self.bg.Update()

            # put an event skip. This is very important
            # The event must go through the other methods also.
            # If this line is not given, the program freezes after
            # clicking on the canvas
            event.Skip()
            
    def Plot(self,event):
        '''
            This method will be called when the Plot button is clicked.
        '''
        f = open('points_data.dat')
        for line in f.readlines():
            halt = line.index(',')
            x = int(line[1:halt])
            y = int(line[halt+1:-2])
            x -= 148.5
            y = -y + 210
            print [x, y], p_approx([x, y])
            ptp([x, y])
            
    def Write(self,event):
        '''
            This method is called when the Write button is clicked
        '''
        data = open('points_data.dat','w')
        for point in self.points:
            x = point.GetX()
            y = point.GetY()

            string = '['+str(x)+','+str(y)+']\n'
            data.writelines(string)
        data.close()

def dataExtract(line):
    '''
    This function parses the given line and returns the angle pair 
        and the coordinate pair
    '''
    comma = line.index(':')
    angle_line = line[:comma]
    coord_line = line[comma+1:-1]

    halt = angle_line.index(',')
    a0 = angle_line[1:halt]
    a1 = angle_line[halt+1:-1]

    halt = coord_line.index(',')
    c0 = coord_line[1:halt]
    c1 = coord_line[halt+1:-1]

    return [[float(a0), float(a1)], [float(c0), float(c1)]]

class interpolate:
    '''
        New class for interpolating between two points
        The class now will depend less on the actual geometry of image
    '''
    def __init__(self,point1,point2):
        if point1 == point2:
            self.l2points = [point1]
        else:
            global data_xy
            self.data = array(data_xy)
            self.x1,self.y1 = point1
            self.x2,self.y2 = point2
            self.l0points = self.prescale(point1,point2)
            self.l1points = map(self.p_approx,self.l0points)
            self.l2points = self.rmvDuplicates(self.l1points)

    def prescale(self,p1,p2):
        x1,y1 = p1
        x2,y2 = p2

        theta = atan2((y2-y1),(x2-x1))
        dist = (y2-y1)*(y2-y1) + (x2-x1)*(x2-x1)
        dist = pow(dist,0.5)

        scale = dist / 0.1
        print 'num points scaled: '+str(int(scale))

        r0 = (dist*1.0)/scale
        newpoints = []

        for i in range(0,int(scale+1)):
            x = x1 + r0*i*cos(theta)
            y = y1 + r0*i*sin(theta)
            newpoints.append([x,y])
            
        return newpoints

    def rmvDuplicates(self,plist):
        newlist = []

        for i in plist:
            if i not in newlist:
                newlist.append(i)
        return newlist
    
    def p_approx(self,point):
        data = self.data
        p = array(point)
        dists = data - p
        dists *= dists
        dists = dists[:,0] + dists[:,1]
        x = where(dists == dists.min())

        return data[x][0].tolist()

def p_approx(point):
    global data_xy
    data = array(data_xy)
    p = array(point)
    dists = data - p
    dists = dists*dists
    dists = dists[:,0] + dists[:,1]
    x = where(dists == dists.min())
    return data[x][0].tolist()


def sendData(angle1,angle2):
    '''
        This function will send the two angles to the micro controller
        The format for data is #abc:pqr@
        where abc is the first angle(ATtiny pin15) and pqr(ATtiny pin16)
        is the second angle

        Initially, The function will check if the data buffer is holding
        U, in which case the device is ready to accept the data

        Once the data is sent, the device will send D, to confirm that
        data is received
    '''
    global dev
    cfm = dev.read(1)
    angle1 = 180 - angle1    # the motor is reversed. hence this change
    angle2 = 180 - angle2
    if cfm == 'U':
        f1_num = 1000+int(angle2)
        f2_num = 1000+int(angle1)
        f1 = str(f1_num)[1:]
        f2 = str(f2_num)[1:]

        dat = '#'+f1+':'+f2+'@'
        print 'Sending data to device'
        for char in dat:
            dev.write(char)
            t = dev.read(1)
            if t == 'r':
                print 'Data read by device'
        ack = dev.read(1)
        if ack == 'D':
            print 'Data receive acknowledged'
            
def extract(string):
    '''
        This function parses the control files to extract the data. The data is
        assumed to be of the following format:
        [abc.d,xyz.w]\n
        change the index values if the format is different
    '''
    halt = string.index(',')
    c1 = float(string[1:halt])
    c2 = float(string[halt+1:-2])
    return [c1,c2]
    
# initiate the device. The device will be operating at 4800bps, no parity
# and one stop bit

dev = serial.Serial()
dev.setBaudrate(4800)
dev.setParity('N')
dev.stopbits = 1
dev.setTimeout(0.1)

def ptp(point):
    '''
        This function is used to move the plotter head from one point
        to another. This function uses linear interpolation and is 
        a high level function.
    '''
    global last_point
    global data_xy
    global data_theta
    
    plist = interpolate(last_point, point).l2points
    print len(plist) ,' points in the path'
    for p in plist:
        a0,a1 = data_theta[data_xy.index(p)]
        print a0, a1
        sendData(a0,a1)
        last_point = p
        
# Enumerate the comm ports
for i in range(100):
    try:
        dev.setPort(i)
        print "Trying port COM",(i+1)
        dev.open()
        break
    except serial.SerialException:
        pass
if i>=99:
    print 'Device not found. Will exit now'
    sys.exit('Device Error')
print 'Opened COM port',i+1
print 'Ready to send data'

dev.write('0')  # this character is sent to invoke the device to send a U.

data_xy = []
data_theta = []

try:
    workfile = open('workspace.dat')
except:
    print 'Control file not found'
    sys.exit('FileError')

for line in workfile.readlines():
    temp = dataExtract(line)
    data_xy.append(temp[1])
    data_theta.append(temp[0])

sendData(0.0, 91.0)     # Initialise the position

init_point = data_xy[data_theta.index([0.0,91.0])]
last_point = init_point

# Start the GUI.

app = wx.PySimpleApp()
ogl.OGLInitialize()
frame = myogl(None,id = 0)
app.MainLoop()
app.Destroy()

