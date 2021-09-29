#! python3
# add config file and customizable keys (keep mouse controls fixed for now)
from random import random, shuffle, randint
from math import sin, cos, pi, sqrt
import pyglet
from pyglet.window import key,mouse
from pyglet.gl import *
import numpy as np

FPS = 30.0
FOV = 60.0
NEAR = 0.1
FAR = 100.0 
TURNING = 90.0
DEG = pi/180.0

class Engine():
    def __init__(self):
        # initialize window
        config = Config(sample_buffers=1,
                        samples=4,
                        depth_size=16,
                        double_buffer=True,)
        self.width  = 640
        self.height = 480
        self.ratio  = self.width / float(self.height)
        try:
            self.window = pyglet.window.Window(resizable=True, 
                                               #width=self.width,
                                               #height=self.height,
                                               config=config)
        except:
            self.window = pyglet.window.Window(resizable=True, 
                                               #width=self.width,
                                               height=self.height)
        # initialize graphics
        self.initGL()
        # initialize controls/resizing
        self.fullscreen = False
        self.keys = key.KeyStateHandler()
        self.keyDown = {i:False for i in (key.SPACE,
                                          key.ENTER,
                                          key._1,
                                          key._2,
                                          key._3,
                                          key._4,
                                          key._5,
                                          key._6,
                                          key._7,
                                          key._8,
                                          key._9,
                                          key._0,
                                          key.Q,
                                          key.W,
                                          key.E,
                                          key.R,
                                          key.T,
                                          key.Y,
                                          key.U,
                                          key.I,
                                          key.O,
                                          key.P,
                                          key.A,
                                          key.S,
                                          key.D,
                                          key.F,
                                          key.G,
                                          key.H,
                                          key.J,
                                          key.K,
                                          key.L,
                                          key.Z,
                                          key.X,
                                          key.C,
                                          key.V,
                                          key.B,
                                          key.N,
                                          key.M,
                                          key.F1,
                                          key.F2,
                                          key.F3,
                                          key.F4,
                                          key.F5,
                                          key.F6,
                                          key.F7,
                                          key.F8,
                                          key.F9,
                                          key.F10,
                                          key.F11,
                                          key.F12)}
        self.window.push_handlers(self.keys,
                                  self.on_resize)
        # initialize first scene
        self.scene = ClassicMazeScene(self)


    def initGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.5)                  # white background
        glEnable(GL_DEPTH_TEST)                           # enable depth testing
        glClearDepth(1.0)                                 # setup depth buffer
        glDepthFunc(GL_LEQUAL)                            # type of depth testing
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST) # really nice perspective calculations
        glEnable(GL_CULL_FACE)                            # do not draw backfaces
        glEnable(GL_BLEND)                                # add transparency
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) # type of transparency, alpha = 1.0 -> opaque, alpha = 0.0 -> transparent


    def on_resize(self, width, height):
        self.width  = width
        self.height = height
        self.ratio  = self.width / float(self.height)
        return pyglet.event.EVENT_HANDLED


    def changeScene(self, prevScene, nextScene=None):
        # before calling this command:
        #     end prevScene
        #     initialize nextScene
        # this function only changes the pointer in the engine
        if nextScene:
            self.scene = nextScene


class ClassicMazeScene:
    def __init__(self, engine):
        self.engine = engine
        self.window = engine.window
        self.keys = self.engine.keys
        self.keyDown = self.engine.keyDown
        self.startScene()


    def startScene(self):
        # build maze
        self.size = np.array([5,5,5,5],'int')
        self.maze = np.zeros(self.size, 'int')
        p = 0.5 # probability of wall
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                for k in range(self.size[2]):
                    for h in range(self.size[3]):
                        self.maze[i,j,k,h] = 1 if random() > p else 0
        # set goal
        self.goal = self.size-1
        # remove wall from goal (if applicable)
        self.maze[self.goal[0], self.goal[1], self.goal[2], self.goal[3]] = 0
        # set user at start
        self.position = np.zeros(4, 'int') #np.array([4,4,4,0])
        # remove wall from start (if applicable)
        self.maze[self.position[0], self.position[1], self.position[2], self.position[3]] = 0
        # set victory status
        self.victory = False
        self.checkVictory()

        # set viewed dimensions
        self.d = np.array([0,1,2,3])
        # set view
        self.rotY = 0.0
        self.rotZ = 0.0
        # mouse controls
        self.dragging = False
        # cross section of 4D: 3D, 3D, 1D
        self.crossSection = 3
        # hint
        self.hint = False
        # generate graphics
        self.generateMaze()
        self.generateGoal()
        self.generateCube()
        self.generateHint()
        self.setMapSizes()
        self.generateMap()

        # do last so that everything is already setup
        self.window.push_handlers(self.on_draw,
                                  self.on_mouse_press,
                                  self.on_mouse_release,
                                  self.on_mouse_drag,
                                  self.on_mouse_scroll,
                                  self.on_resize)
        pyglet.clock.schedule_interval(self.update, 1/FPS)


    def endScene(self):
        self.window.pop_handlers()
        pyglet.clock.unschedule(self.update)


    def update(self, dt):
        self.toggledKeys(dt)
        self.heldKeys(dt)
        if self.victory:
            self.rotZ = (self.rotZ + TURNING*dt*(2/3))%360.0
            self.rotY -= dt*self.rotY/15


    def keyIsDown(self, k):
        if self.keys[k]:
            if not self.keyDown[k]:
                self.keyDown[k] = True
                return True
        else:
                self.keyDown[k] = False
        return False


    def checkVictory(self):
            # check victory condition
            self.victory = True
            for i in range(len(self.position)):
                self.victory &= self.position[i] == self.goal[i]


    def move(self, i, d):
        temp = np.array(self.position)
        temp[i] += d
        # check for wall or boundary
        if 0 <= temp[i] and temp[i] < self.size[i] and self.maze[temp[0],temp[1],temp[2],temp[3]] == 0:
            # move
            self.position = temp

            # re-generate changed graphics
            if i == self.d[3]:
                self.generateMaze()
                self.generateGoal()
            self.generateCube()
            self.generateMap()

            # check whether reached goal
            self.checkVictory()


    def dimensionSwap(self, dim):
        i = np.where(self.d==dim)[0][0]
        if i != 3:
            temp = self.d[i]
            self.d[i] = self.d[3]
            self.d[3] = temp
            self.generateMaze()
            self.generateGoal()
            self.generateCube()
            self.generateHint()
            self.generateMap()


    def toggledKeys(self, dt):
        # movement
        if self.keyIsDown(key.W):
            self.move(0, +1)
        if self.keyIsDown(key.S):
            self.move(0, -1)
        if self.keyIsDown(key.A):
            self.move(1, +1)
        if self.keyIsDown(key.D):
            self.move(1, -1)
        if self.keyIsDown(key.E):
            self.move(2, +1)
        if self.keyIsDown(key.Q):
            self.move(2, -1)
        if self.keyIsDown(key.Z):
            self.move(3, +1)
        if self.keyIsDown(key.C):
            self.move(3, -1)

        # dimension swap
        # 1
        if self.keyIsDown(key._1):
            self.dimensionSwap(0)
        # 2
        if self.keyIsDown(key._2):
            self.dimensionSwap(1)
        # 3
        if self.keyIsDown(key._3):
            self.dimensionSwap(2)
        # 4
        if self.keyIsDown(key._4):
            self.dimensionSwap(3)

        if self.keyIsDown(key.G):
            if self.crossSection == 3:
                self.crossSection = 2
            elif self.crossSection == 2:
                self.crossSection = 1
            else:
                self.crossSection = 3
            self.generateMaze()

        if self.keyIsDown(key.H):
            self.hint = not self.hint
            print(self.hint)
            self.generateHint()

        # generate new maze
        if self.keyIsDown(key.SPACE):
            self.endScene()
            self.startScene()

        # F11 -> fullscreen toggle
        if self.keyIsDown(key.F11):
            self.engine.fullscreen = not self.engine.fullscreen
            self.window.set_fullscreen(self.engine.fullscreen)


    def heldKeys(self, dt):
        if self.keys[key.RIGHT]:
            self.rotZ = (self.rotZ + TURNING*dt)%360.0
        if self.keys[key.LEFT]:
            self.rotZ = (self.rotZ - TURNING*dt)%360.0
        if self.keys[key.UP]:
            self.rotY = (self.rotY + TURNING*dt)%360.0
        if self.keys[key.DOWN]:
            self.rotY = (self.rotY - TURNING*dt)%360.0


    def on_mouse_press(self, x, y, button, modifiers):
        if button & mouse.LEFT:
            if x >= self.mazeX and y >= self.mazeY:
                # rotate maze
                self.dragging = True
            elif x >= self.mapX and y > self.mapY:
                # movement / dimension swap
                halfWidth  = self.mapX + self.mapWidth//2
                halfHeight = self.mapY + self.mapHeight//2
                l = self.mapL*self.mapHeight//2
                d = -1
                if   halfHeight + 2.5*l <= y <= halfHeight + 3.5*l:
                    d = 0
                elif halfHeight + 0.5*l <= y <= halfHeight + 1.5*l:
                    d = 1
                elif halfHeight - 1.5*l <= y <= halfHeight - 0.5*l:
                    d = 2
                elif halfHeight - 3.5*l <= y <= halfHeight - 2.5*l:
                    d = 3
                if d > -1:
                    if halfWidth - (self.size[d]/2)*l <= x <= halfWidth + (self.size[d]/2)*l:
                        self.dimensionSwap(d)
                    elif halfWidth - (self.size[d]/2 + 2)*l <= x <= halfWidth - (self.size[d]/2 + 0.5)*l:
                        # <-
                        self.move(d,-1)
                    elif halfWidth + (self.size[d]/2 + 2)*l >= x >= halfWidth + (self.size[d]/2 + 0.5)*l:
                        # ->
                        self.move(d,+1)

        #
        if button & mouse.MIDDLE:
            self.hint = not self.hint
            self.generateHint()

        # generate new maze
        if button & mouse.RIGHT:
            self.endScene()
            self.startScene()


    def on_mouse_release(self, x, y, button, modifiers):
        if self.dragging:
            self.dragging = False


    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.dragging:
            self.rotZ = (self.rotZ + 180.0*dx/self.mazeWidth)%360.0
            self.rotY = (self.rotY + 180.0*dy/self.mazeHeight)%360.0


    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if scroll_y > 0 or scroll_x > 0:
            if self.crossSection == 3:
                self.crossSection = 2
            elif self.crossSection == 2:
                self.crossSection = 1
            else:
                self.crossSection = 3
            self.generateMaze()
        elif scroll_y < 0 or scroll_x < 0:
            if self.crossSection == 3:
                self.crossSection = 1
            elif self.crossSection == 1:
                self.crossSection = 2
            else:
                self.crossSection = 3
            self.generateMaze()


    def on_resize(self, width, height):
        self.engine.width  = width
        self.engine.height = height
        self.engine.ratio  = self.engine.width / float(self.engine.height)
        self.setMapSizes()
        self.generateMap()
        return pyglet.event.EVENT_HANDLED


    def setMapSizes(self):
        # position of map and maze
        if self.engine.width > self.engine.height:
            # wide
            mapWidth  = self.engine.width//3
            mapHeight = self.engine.height
            self.mazeX          = self.engine.width//3
            self.mazeY          = 0
            self.mazeWidth      = 2*self.engine.width//3
            self.mazeHeight     = self.engine.height
        else:
            # tall
            mapWidth  = self.engine.width
            mapHeight = self.engine.height//3
            self.mazeX          = 0
            self.mazeY          = self.engine.height//3
            self.mazeWidth      = self.engine.width
            self.mazeHeight     = 2*self.engine.height//3
        mapMin = mapWidth if mapWidth < mapHeight else mapHeight
        self.mapX           = abs(mapWidth  - mapMin)//2
        self.mapY           = abs(mapHeight - mapMin)//2
        self.mapWidth       = mapMin
        self.mapHeight      = mapMin
        # size of items in map
        # remember, x and y go from -1 to 1 = 2
        w = 2/(max(self.size)+3) # 0.5 spacer and 1 arrow on each side
        h = 2/8 # 8 = 4 dimensions + 3 spaces between + 0.5 on each end
        self.mapL            = w if w < h else h
        self.mapE            = self.mapL/10 # border thickness
        self.mapRedX         =  self.mapL*(self.size[0]/2) # +/-
        self.mapRedY         = +self.mapL*3.5 # +0/-1
        self.mapGreenX       =  self.mapL*(self.size[1]/2)
        self.mapGreenY       = +self.mapL*1.5
        self.mapBlueX        =  self.mapL*(self.size[2]/2)
        self.mapBlueY        = -self.mapL*0.5
        self.mapAlphaX       =  self.mapL*(self.size[3]/2)
        self.mapAlphaY       = -self.mapL*2.5


    def on_draw(self):
        # game
        glViewport(self.mazeX, self.mazeY, self.mazeWidth, self.mazeHeight)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(FOV, self.mazeWidth / float(self.mazeHeight), NEAR, FAR)
        glMatrixMode(GL_MODELVIEW)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        r = sqrt( self.size[0]*self.size[0] + self.size[1]*self.size[1] + self.size[2]*self.size[2] + self.size[3]*self.size[3] )
        x = self.size[self.d[0]]/2.0
        y = self.size[self.d[1]]/2.0
        z = self.size[self.d[2]]/2.0
        fx = r * cos(self.rotZ*DEG) * cos(self.rotY*DEG)
        fy = r *-sin(self.rotZ*DEG) * cos(self.rotY*DEG)
        fz = r *                      sin(self.rotY*DEG)
        ux =     cos(self.rotZ*DEG) *-sin(self.rotY*DEG)
        uy =    -sin(self.rotZ*DEG) *-sin(self.rotY*DEG)
        uz =                          cos(self.rotY*DEG)
        glu.gluLookAt(z-fx, y-fy, z-fz,\
                      z,    y,    z,\
                      ux, uy, uz)

        # draw
        self.drawMaze()
        self.drawGoal()
        self.drawCube()
        self.drawHint()
        
        # map
        glViewport(self.mapX, self.mapY, self.mapWidth, self.mapHeight)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        #gluPerspective(FOV, self.mapWidth / float(self.mapHeight), 0.1, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.drawMap()


    def generateCube(self):
        self.cubeVerticesGL = []
        self.cubeColorsGL   = []
        self.cubeModeGL     = GL_QUADS
        x = self.position[self.d[0]]
        y = self.position[self.d[1]]
        z = self.position[self.d[2]]
        self.cubeVerticesGL.extend([#  XD
                                    x+0.1, y+0.1, z+0.1,\
                                    x+0.1, y+0.1, z+0.9,\
                                    x+0.1, y+0.9, z+0.9,\
                                    x+0.1, y+0.9, z+0.1,\
                                    #  YD
                                    x+0.1, y+0.1, z+0.1,\
                                    x+0.9, y+0.1, z+0.1,\
                                    x+0.9, y+0.1, z+0.9,\
                                    x+0.1, y+0.1, z+0.9,\
                                    #  ZD
                                    x+0.1, y+0.1, z+0.1,\
                                    x+0.1, y+0.9, z+0.1,\
                                    x+0.9, y+0.9, z+0.1,\
                                    x+0.9, y+0.1, z+0.1,\
                                    #  XU
                                    x+0.9, y+0.1, z+0.1,\
                                    x+0.9, y+0.9, z+0.1,\
                                    x+0.9, y+0.9, z+0.9,\
                                    x+0.9, y+0.1, z+0.9,\
                                    #  YU
                                    x+0.1, y+0.9, z+0.1,\
                                    x+0.1, y+0.9, z+0.9,\
                                    x+0.9, y+0.9, z+0.9,\
                                    x+0.9, y+0.9, z+0.1,\
                                    #  ZU
                                    x+0.1, y+0.1, z+0.9,\
                                    x+0.9, y+0.1, z+0.9,\
                                    x+0.9, y+0.9, z+0.9,\
                                    x+0.1, y+0.9, z+0.9,\
                                    ])
        self.cubeColorsGL.extend([0.0, 0.0, 0.0, 1.0]*4*6)
        # convert to GL format
        self.cubeVerticesGL = (GLfloat * len(self.cubeVerticesGL))(*self.cubeVerticesGL)
        self.cubeColorsGL = (GLfloat * len(self.cubeColorsGL))(*self.cubeColorsGL)


    def generateGoal(self):
        self.goalVerticesGL = []
        self.goalColorsGL   = []
        self.goalModeGL     = GL_QUADS
        same = [self.position[i]==self.goal[i] for i in self.d]
        if same[3] and\
            ((self.crossSection == 3) or\
             (self.crossSection == 2 and sum(same[:3]) >= 1) or\
             (self.crossSection == 1 and sum(same[:3]) >= 2)):
            x = self.goal[self.d[0]]
            y = self.goal[self.d[1]]
            z = self.goal[self.d[2]]
            self.goalVerticesGL.extend([#  XD
                                        x+0.2, y+0.2, z+0.2,\
                                        x+0.2, y+0.2, z+1.0,\
                                        x+0.2, y+1.0, z+1.0,\
                                        x+0.2, y+1.0, z+0.2,\
                                        #  YD
                                        x+0.2, y+0.2, z+0.2,\
                                        x+1.0, y+0.2, z+0.2,\
                                        x+1.0, y+0.2, z+1.0,\
                                        x+0.2, y+0.2, z+1.0,\
                                        #  ZD
                                        x+0.2, y+0.2, z+0.2,\
                                        x+0.2, y+1.0, z+0.2,\
                                        x+1.0, y+1.0, z+0.2,\
                                        x+1.0, y+0.2, z+0.2,\
                                        #  XU
                                        x+1.0, y+0.2, z+0.2,\
                                        x+1.0, y+1.0, z+0.2,\
                                        x+1.0, y+1.0, z+1.0,\
                                        x+1.0, y+0.2, z+1.0,\
                                        #  YU
                                        x+0.2, y+1.0, z+0.2,\
                                        x+0.2, y+1.0, z+1.0,\
                                        x+1.0, y+1.0, z+1.0,\
                                        x+1.0, y+1.0, z+0.2,\
                                        #  ZU
                                        x+0.2, y+0.2, z+1.0,\
                                        x+1.0, y+0.2, z+1.0,\
                                        x+1.0, y+1.0, z+1.0,\
                                        x+0.2, y+1.0, z+1.0,\
                                        ])
            self.goalColorsGL.extend([1.0, 0.4, 0.0, 1.0,\
                                      1.0, 0.6, 0.0, 1.0,\
                                      1.0, 0.8, 0.0, 1.0,\
                                      1.0, 0.6, 0.0, 1.0,\
                                     ]*3)
            self.goalColorsGL.extend([1.0, 0.6, 0.0, 1.0,\
                                      1.0, 0.8, 0.0, 1.0,\
                                      1.0, 1.0, 0.0, 1.0,\
                                      1.0, 0.8, 0.0, 1.0,\
                                     ]*3)
        # convert to GL format
        self.goalVerticesGL = (GLfloat * len(self.goalVerticesGL))(*self.goalVerticesGL)
        self.goalColorsGL   = (GLfloat * len(self.goalColorsGL))  (*self.goalColorsGL)


    def generateMaze(self):
        self.mazeVerticesGL = []
        self.mazeColorsGL   = []
        self.mazeModeGL     = GL_QUADS
        # draw 1D/2D/3D cross sections of 4D
        if self.crossSection == 1:
            self.generate1DSection()
        elif self.crossSection == 2:
            self.generate2DSection()
        elif self.crossSection == 3:
            self.generate3DSection()
        # convert to GL format
        self.mazeVerticesGL = (GLfloat * len(self.mazeVerticesGL))(*self.mazeVerticesGL)
        self.mazeColorsGL   = (GLfloat * len(self.mazeColorsGL))  (*self.mazeColorsGL)


    def generate1DSection(self):
        # init index
        i = np.array([0,0,0,0])
        # use position for hidden dimension
        i[self.d[3]] = self.position[self.d[3]]
        # X
        i[self.d[1]] = self.position[self.d[1]]
        i[self.d[2]] = self.position[self.d[2]]
        for i[self.d[0]] in range(self.size[self.d[0]]):
            if self.maze[i[0],i[1],i[2],i[3]] == 1:
                self.generateBlock(i, drawX=False, drawY=True, drawZ=True)
        # Y
        i[self.d[0]] = self.position[self.d[0]]
        i[self.d[2]] = self.position[self.d[2]]
        for i[self.d[1]] in range(self.size[self.d[1]]):
            if self.maze[i[0],i[1],i[2],i[3]] == 1:
                self.generateBlock(i, drawX=True, drawY=False, drawZ=True)
        # Z
        i[self.d[0]] = self.position[self.d[0]]
        i[self.d[1]] = self.position[self.d[1]]
        for i[self.d[2]] in range(self.size[self.d[2]]):
            if self.maze[i[0],i[1],i[2],i[3]] == 1:
                self.generateBlock(i, drawX=True, drawY=True, drawZ=False)


    def generate2DSection(self):
        # inefficient but effective
        # init index
        i = np.array([0,0,0,0])
        # use position for hidden dimension
        i[self.d[3]] = self.position[self.d[3]]
        # XY
        i[self.d[2]] = self.position[self.d[2]]
        for i[self.d[0]] in range(self.size[self.d[0]]):
            for i[self.d[1]] in range(self.size[self.d[1]]):
                if self.maze[i[0],i[1],i[2],i[3]] == 1:
                    self.generateBlock(i, drawX=False, drawY=False, drawZ=True)
        # XZ
        i[self.d[1]] = self.position[self.d[1]]
        for i[self.d[0]] in range(self.size[self.d[0]]):
            for i[self.d[2]] in range(self.size[self.d[2]]):
                if self.maze[i[0],i[1],i[2],i[3]] == 1:
                    self.generateBlock(i, drawX=False, drawY=True, drawZ=False)
        # YZ
        i[self.d[0]] = self.position[self.d[0]]
        for i[self.d[1]] in range(self.size[self.d[1]]):
            for i[self.d[2]] in range(self.size[self.d[2]]):
                if self.maze[i[0],i[1],i[2],i[3]] == 1:
                    self.generateBlock(i, drawX=True, drawY=False, drawZ=False)


    def generate3DSection(self):
        # init index
        i = np.array([0,0,0,0])
        # use position for hidden dimension
        i[self.d[3]] = self.position[self.d[3]]
        # cycle through all points in visible dimensions
        for i[self.d[0]] in range(self.size[self.d[0]]):
            for i[self.d[1]] in range(self.size[self.d[1]]):
                for i[self.d[2]] in range(self.size[self.d[2]]):
                    if self.maze[i[0],i[1],i[2],i[3]] == 1:
                        self.generateBlock(i)


    def generateBlock(self, i, drawX=False, drawY=False, drawZ=False):
        # set graphical location and color of cube
        x = i[self.d[0]]
        y = i[self.d[1]]
        z = i[self.d[2]]
        r = (1+i[0])/(1+self.size[0]+1)
        g = (1+i[1])/(1+self.size[1]+1)
        b = (1+i[2])/(1+self.size[2]+1)
        a = 1 - (i[3])/(self.size[3]+2)
        # do not draw faces between cubes
        # x-
        i[self.d[0]] -= 1
        if drawX or\
           i[self.d[0]] < 0 or\
           self.maze[i[0], i[1], i[2], i[3]] == 0:
            self.mazeVerticesGL.extend([#  XD
                                        x  ,y  ,z  ,\
                                        x  ,y  ,z+1,\
                                        x  ,y+1,z+1,\
                                        x  ,y+1,z  ,\
                                        ])
            self.mazeColorsGL.extend([r,g,b,a]*4)
        # x+
        i[self.d[0]] += 1
        i[self.d[0]] += 1
        if drawX or\
           i[self.d[0]] >= self.size[self.d[0]] or\
           self.maze[i[0], i[1], i[2], i[3]] == 0:
            self.mazeVerticesGL.extend([#  XU
                                        x+1,y  ,z  ,\
                                        x+1,y+1,z  ,\
                                        x+1,y+1,z+1,\
                                        x+1,y  ,z+1,\
                                        ])
            self.mazeColorsGL.extend([r,g,b,a]*4)
        # y-
        i[self.d[0]] -= 1
        i[self.d[1]] -= 1
        if drawY or\
           i[self.d[1]] < 0 or\
           self.maze[i[0], i[1], i[2], i[3]] == 0:
            self.mazeVerticesGL.extend([#  YD
                                        x  ,y  ,z  ,\
                                        x+1,y  ,z  ,\
                                        x+1,y  ,z+1,\
                                        x  ,y  ,z+1,\
                                        ])
            self.mazeColorsGL.extend([r,g,b,a]*4)
        # y+
        i[self.d[1]] += 1
        i[self.d[1]] += 1
        if drawY or\
           i[self.d[1]] >= self.size[self.d[1]] or\
           self.maze[i[0], i[1], i[2], i[3]] == 0:
            self.mazeVerticesGL.extend([#  YU
                                        x  ,y+1,z  ,\
                                        x  ,y+1,z+1,\
                                        x+1,y+1,z+1,\
                                        x+1,y+1,z  ,\
                                        ])
            self.mazeColorsGL.extend([r,g,b,a]*4)
        # z-
        i[self.d[1]] -= 1
        i[self.d[2]] -= 1
        if drawZ or\
           i[self.d[2]] < 0 or\
           self.maze[i[0], i[1], i[2], i[3]] == 0:
            self.mazeVerticesGL.extend([#  ZD
                                        x  ,y  ,z  ,\
                                        x  ,y+1,z  ,\
                                        x+1,y+1,z  ,\
                                        x+1,y  ,z  ,\
                                        ])
            self.mazeColorsGL.extend([r,g,b,a]*4)
        # z+
        i[self.d[2]] += 1
        i[self.d[2]] += 1
        if drawZ or\
           i[self.d[2]] >= self.size[self.d[2]] or\
           self.maze[i[0], i[1], i[2], i[3]] == 0:
            self.mazeVerticesGL.extend([#  ZU
                                        x  ,y  ,z+1,\
                                        x+1,y  ,z+1,\
                                        x+1,y+1,z+1,\
                                        x  ,y+1,z+1,\
                                        ])
            self.mazeColorsGL.extend([r,g,b,a]*4)
        i[self.d[2]] -= 1


    def blockColor(self, x, y, z, w):
        r = (1+x)/(1+self.size[0]+1)
        g = (1+y)/(1+self.size[1]+1)
        b = (1+z)/(1+self.size[2]+1)
        a = 1 - (w)/(self.size[3]+3)
        return r, g, b, a


    def generateMapSegment(self, d, mapX, mapY):
        l = self.mapL
        e = self.mapE
        # border
        a = 0.3 if self.d[3] == d else 1.0
        if d == 3:
            color = [1.0, 1.0, 1.0, a]
        else:
            color = [0.0, 0.0, 0.0, a]
            color[d] = 1.0
        self.mapVerticesGL.extend([-mapX-e, mapY  +e, +0.1,\
                                   -mapX-e, mapY-l-e, +0.1,\
                                    mapX+e, mapY-l-e, +0.1,\
                                    mapX+e, mapY  +e, +0.1,\
                                   # <-
                                    mapX+(0.5)*l, mapY    , +0.1,\
                                    mapX+(0.5)*l, mapY-l  , +0.1,\
                                    mapX+(1.0)*l, mapY-l/2, +0.1,\
                                    mapX+(1.0)*l, mapY-l/2, +0.1,\
                                   # ->
                                   -mapX-(0.5)*l, mapY    , +0.1,\
                                   -mapX-(1.0)*l, mapY-l/2, +0.1,\
                                   -mapX-(1.0)*l, mapY-l/2, +0.1,\
                                   -mapX-(0.5)*l, mapY-l  , +0.1,\
                                   ])
        self.mapColorsGL.extend([0.0, 0.0, 0.0, a]*2)
        self.mapColorsGL.extend(color*2)
        self.mapColorsGL.extend([0.0, 0.0, 0.0, a]*8)
        # interior background (over border)
        self.mapVerticesGL.extend([ mapX, mapY  , 0.0,\
                                   -mapX, mapY  , 0.0,\
                                   -mapX, mapY-l, 0.0,\
                                    mapX, mapY-l, 0.0,\
                                   ])
        self.mapColorsGL.extend([1.0, 1.0, 1.0, 1.0]*4)
        # cube
        i = np.array(self.position) # easier to type and used for indexing blocks
        self.mapVerticesGL.extend([-mapX+(i[d]+0.1)*l, mapY-(0.1)*l, -0.2,\
                                   -mapX+(i[d]+0.1)*l, mapY-(0.9)*l, -0.2,\
                                   -mapX+(i[d]+0.9)*l, mapY-(0.9)*l, -0.2,\
                                   -mapX+(i[d]+0.9)*l, mapY-(0.1)*l, -0.2,\
                                   ])
        self.mapColorsGL.extend([0.0, 0.0, 0.0, 1.0]*4)
        # goal
        if (d == 0 or i[0] == self.goal[0]) and\
           (d == 1 or i[1] == self.goal[1]) and\
           (d == 2 or i[2] == self.goal[2]) and\
           (d == 3 or i[3] == self.goal[3]):
            self.mapVerticesGL.extend([-mapX+(self.goal[d]+0.2)*l, mapY-(0.0)*l, -0.3,\
                                       -mapX+(self.goal[d]+0.2)*l, mapY-(0.8)*l, -0.3,\
                                       -mapX+(self.goal[d]+1.0)*l, mapY-(0.8)*l, -0.3,\
                                       -mapX+(self.goal[d]+1.0)*l, mapY-(0.0)*l, -0.3,\
                                       ])
            self.mapColorsGL.extend([1.0, 0.7, 0.0, 1.0,\
                                     1.0, 0.4, 0.0, 1.0,\
                                     1.0, 0.7, 0.0, 1.0,\
                                     1.0, 1.0, 0.0, 1.0,\
                                     ])
        # blocks
        for i[d] in range(self.size[d]):
            if self.maze[i[0], i[1], i[2], i[3]] == 1:
                r, g, b, a = self.blockColor(i[0], i[1], i[2], i[3])
                self.mapVerticesGL.extend([-mapX+(i[d]  )*l, mapY  , -0.1,\
                                           -mapX+(i[d]  )*l, mapY-l, -0.1,\
                                           -mapX+(i[d]+1)*l, mapY-l, -0.1,\
                                           -mapX+(i[d]+1)*l, mapY  , -0.1,\
                                           ])
                self.mapColorsGL.extend([r,g,b,a]*4)


    def generateMap(self):
        self.mapVerticesGL = []
        self.mapColorsGL   = []
        self.mapModeGL     = GL_QUADS

        self.generateMapSegment(d=0, mapX=self.mapRedX,   mapY=self.mapRedY)
        self.generateMapSegment(d=1, mapX=self.mapGreenX, mapY=self.mapGreenY)
        self.generateMapSegment(d=2, mapX=self.mapBlueX,  mapY=self.mapBlueY)
        self.generateMapSegment(d=3, mapX=self.mapAlphaX, mapY=self.mapAlphaY)

        # convert to GL format
        self.mapVerticesGL = (GLfloat * len(self.mapVerticesGL))(*self.mapVerticesGL)
        self.mapColorsGL   = (GLfloat * len(self.mapColorsGL))  (*self.mapColorsGL)


    def generateHint(self):
        self.hintVerticesGL = []
        self.hintColorsGL   = []
        self.hintModeGL     = GL_QUADS
        if self.hint:
            h = 0.05
            d = 0.1
            x = self.size[self.d[0]]
            y = self.size[self.d[1]]
            z = self.size[self.d[2]]
            if self.d[0] == 0:
                colorX = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          1.0, 0.0, 0.0, 1.0,\
                          1.0, 0.0, 0.0, 1.0,\
                          ]
            elif self.d[0] == 1:
                colorX = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          0.0, 1.0, 0.0, 1.0,\
                          0.0, 1.0, 0.0, 1.0,\
                          ]
            elif self.d[0] == 2:
                colorX = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 1.0, 1.0,\
                          0.0, 0.0, 1.0, 1.0,\
                          ]
            elif self.d[0] == 3:
                colorX = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          1.0, 1.0, 1.0, 1.0,\
                          1.0, 1.0, 1.0, 1.0,\
                          ]
            if self.d[1] == 0:
                colorY = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          1.0, 0.0, 0.0, 1.0,\
                          1.0, 0.0, 0.0, 1.0,\
                          ]
            elif self.d[1] == 1:
                colorY = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          0.0, 1.0, 0.0, 1.0,\
                          0.0, 1.0, 0.0, 1.0,\
                          ]
            elif self.d[1] == 2:
                colorY = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 1.0, 1.0,\
                          0.0, 0.0, 1.0, 1.0,\
                          ]
            elif self.d[1] == 3:
                colorY = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          1.0, 1.0, 1.0, 1.0,\
                          1.0, 1.0, 1.0, 1.0,\
                          ]
            if self.d[2] == 0:
                colorZ = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          1.0, 0.0, 0.0, 1.0,\
                          1.0, 0.0, 0.0, 1.0,\
                          ]
            elif self.d[2] == 1:
                colorZ = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          0.0, 1.0, 0.0, 1.0,\
                          0.0, 1.0, 0.0, 1.0,\
                          ]
            elif self.d[2] == 2:
                colorZ = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 1.0, 1.0,\
                          0.0, 0.0, 1.0, 1.0,\
                          ]
            elif self.d[2] == 3:
                colorZ = [0.0, 0.0, 0.0, 1.0,\
                          0.0, 0.0, 0.0, 1.0,\
                          1.0, 1.0, 1.0, 1.0,\
                          1.0, 1.0, 1.0, 1.0,\
                          ]
            self.hintVerticesGL.extend([ -d  , -d-h, -d  ,\
                                         -d-h, -d-h, -d-h,\
                                        x+d+h, -d-h, -d-h,\
                                        x+d  , -d-h, -d  ,\
                                         -d  , -d  , -d  ,\
                                         -d  , -d-h, -d  ,\
                                        x+d  , -d-h, -d  ,\
                                        x+d  , -d  , -d  ,\
                                         -d  , -d  , -d-h,\
                                         -d  , -d  , -d  ,\
                                        x+d  , -d  , -d  ,\
                                        x+d  , -d  , -d-h,\
                                         -d-h, -d-h, -d-h,\
                                         -d  , -d  , -d-h,\
                                        x+d  , -d  , -d-h,\
                                        x+d+h, -d-h, -d-h,\
                                         -d  ,y+d  , -d  ,\
                                         -d  ,y+d  , -d-h,\
                                        x+d  ,y+d  , -d-h,\
                                        x+d  ,y+d  , -d  ,\
                                         -d  ,y+d+h, -d  ,\
                                         -d  ,y+d  , -d  ,\
                                        x+d  ,y+d  , -d  ,\
                                        x+d  ,y+d+h, -d  ,\
                                         -d-h,y+d+h, -d-h,\
                                         -d  ,y+d+h, -d  ,\
                                        x+d  ,y+d+h, -d  ,\
                                        x+d+h,y+d+h, -d-h,\
                                         -d  ,y+d  , -d-h,\
                                         -d-h,y+d+h, -d-h,\
                                        x+d+h,y+d+h, -d-h,\
                                        x+d  ,y+d  , -d-h,\
                                         -d-h, -d-h,z+d+h,\
                                         -d  , -d-h,z+d  ,\
                                        x+d  , -d-h,z+d  ,\
                                        x+d+h, -d-h,z+d+h,\
                                         -d  , -d  ,z+d+h,\
                                         -d-h, -d-h,z+d+h,\
                                        x+d+h, -d-h,z+d+h,\
                                        x+d  , -d  ,z+d+h,\
                                         -d  , -d  ,z+d  ,\
                                         -d  , -d  ,z+d+h,\
                                        x+d  , -d  ,z+d+h,\
                                        x+d  , -d  ,z+d  ,\
                                         -d  , -d-h,z+d  ,\
                                         -d  , -d  ,z+d  ,\
                                        x+d  , -d  ,z+d  ,\
                                        x+d  , -d-h,z+d  ,\
                                         -d  ,y+d  ,z+d+h,\
                                         -d  ,y+d  ,z+d  ,\
                                        x+d  ,y+d  ,z+d  ,\
                                        x+d  ,y+d  ,z+d+h,\
                                         -d-h,y+d+h,z+d+h,\
                                         -d  ,y+d  ,z+d+h,\
                                        x+d  ,y+d  ,z+d+h,\
                                        x+d+h,y+d+h,z+d+h,\
                                         -d  ,y+d+h,z+d  ,\
                                         -d-h,y+d+h,z+d+h,\
                                        x+d+h,y+d+h,z+d+h,\
                                        x+d  ,y+d+h,z+d  ,\
                                         -d  ,y+d  ,z+d  ,\
                                         -d  ,y+d+h,z+d  ,\
                                        x+d  ,y+d+h,z+d  ,\
                                        x+d  ,y+d  ,z+d  ,\
                                        ])
            self.hintColorsGL.extend(colorX*16)
            self.hintVerticesGL.extend([ -d  , -d  , -d-h,\
                                         -d-h, -d-h, -d-h,\
                                         -d-h,y+d+h, -d-h,\
                                         -d  ,y+d  , -d-h,\
                                         -d  , -d  , -d  ,\
                                         -d  , -d  , -d-h,\
                                         -d  ,y+d  , -d-h,\
                                         -d  ,y+d  , -d  ,\
                                         -d-h, -d  , -d  ,\
                                         -d  , -d  , -d  ,\
                                         -d  ,y+d  , -d  ,\
                                         -d-h,y+d  , -d  ,\
                                         -d-h, -d-h, -d-h,\
                                         -d-h, -d  , -d  ,\
                                         -d-h,y+d  , -d  ,\
                                         -d-h,y+d+h, -d-h,\
                                         -d  , -d  ,z+d  ,\
                                         -d-h, -d  ,z+d  ,\
                                         -d-h,y+d  ,z+d  ,\
                                         -d  ,y+d  ,z+d  ,\
                                         -d  , -d  ,z+d+h,\
                                         -d  , -d  ,z+d  ,\
                                         -d  ,y+d  ,z+d  ,\
                                         -d  ,y+d  ,z+d+h,\
                                         -d-h, -d-h,z+d+h,\
                                         -d  , -d  ,z+d+h,\
                                         -d  ,y+d  ,z+d+h,\
                                         -d-h,y+d+h,z+d+h,\
                                         -d-h, -d  ,z+d  ,\
                                         -d-h, -d-h,z+d+h,\
                                         -d-h,y+d+h,z+d+h,\
                                         -d-h,y+d  ,z+d  ,\
                                        x+d+h, -d-h, -d-h,\
                                        x+d  , -d  , -d-h,\
                                        x+d  ,y+d  , -d-h,\
                                        x+d+h,y+d+h, -d-h,\
                                        x+d+h, -d  , -d  ,\
                                        x+d+h, -d-h, -d-h,\
                                        x+d+h,y+d+h, -d-h,\
                                        x+d+h,y+d  , -d  ,\
                                        x+d  , -d  , -d  ,\
                                        x+d+h, -d  , -d  ,\
                                        x+d+h,y+d  , -d  ,\
                                        x+d  ,y+d  , -d  ,\
                                        x+d  , -d  , -d-h,\
                                        x+d  , -d  , -d  ,\
                                        x+d  ,y+d  , -d  ,\
                                        x+d  ,y+d  , -d-h,\
                                        x+d+h, -d  ,z+d  ,\
                                        x+d  , -d  ,z+d  ,\
                                        x+d  ,y+d  ,z+d  ,\
                                        x+d+h,y+d  ,z+d  ,\
                                        x+d+h, -d-h,z+d+h,\
                                        x+d+h, -d  ,z+d  ,\
                                        x+d+h,y+d  ,z+d  ,\
                                        x+d+h,y+d+h,z+d+h,\
                                        x+d  , -d  ,z+d+h,\
                                        x+d+h, -d-h,z+d+h,\
                                        x+d+h,y+d+h,z+d+h,\
                                        x+d  ,y+d  ,z+d+h,\
                                        x+d  , -d  ,z+d  ,\
                                        x+d  , -d  ,z+d+h,\
                                        x+d  ,y+d  ,z+d+h,\
                                        x+d  ,y+d  ,z+d  ,\
                                        ])
            self.hintColorsGL.extend(colorY*16)
            self.hintVerticesGL.extend([ -d-h, -d  , -d  ,\
                                         -d-h, -d-h, -d-h,\
                                         -d-h, -d-h,z+d+h,\
                                         -d-h, -d  ,z+d  ,\
                                         -d  , -d  , -d  ,\
                                         -d-h, -d  , -d  ,\
                                         -d-h, -d  ,z+d  ,\
                                         -d  , -d  ,z+d  ,\
                                         -d  , -d-h, -d  ,\
                                         -d  , -d  , -d  ,\
                                         -d  , -d  ,z+d  ,\
                                         -d  , -d-h,z+d  ,\
                                         -d-h, -d-h, -d-h,\
                                         -d  , -d-h, -d  ,\
                                         -d  , -d-h,z+d  ,\
                                         -d-h, -d-h,z+d+h,\
                                        x+d  , -d  , -d  ,\
                                        x+d  , -d-h, -d  ,\
                                        x+d  , -d-h,z+d  ,\
                                        x+d  , -d  ,z+d  ,\
                                        x+d+h, -d  , -d  ,\
                                        x+d  , -d  , -d  ,\
                                        x+d  , -d  ,z+d  ,\
                                        x+d+h, -d  ,z+d  ,\
                                        x+d+h, -d-h, -d-h,\
                                        x+d+h, -d  , -d  ,\
                                        x+d+h, -d  ,z+d  ,\
                                        x+d+h, -d-h,z+d+h,\
                                        x+d  , -d-h, -d  ,\
                                        x+d+h, -d-h, -d-h,\
                                        x+d+h, -d-h,z+d+h,\
                                        x+d  , -d-h,z+d  ,\
                                         -d-h,y+d+h, -d-h,\
                                         -d-h,y+d  , -d  ,\
                                         -d-h,y+d  ,z+d  ,\
                                         -d-h,y+d+h,z+d+h,\
                                         -d  ,y+d+h, -d  ,\
                                         -d-h,y+d+h, -d-h,\
                                         -d-h,y+d+h,z+d+h,\
                                         -d  ,y+d+h,z+d  ,\
                                         -d  ,y+d  , -d  ,\
                                         -d  ,y+d+h, -d  ,\
                                         -d  ,y+d+h,z+d  ,\
                                         -d  ,y+d  ,z+d  ,\
                                         -d-h,y+d  , -d  ,\
                                         -d  ,y+d  , -d  ,\
                                         -d  ,y+d  ,z+d  ,\
                                         -d-h,y+d  ,z+d  ,\
                                        x+d  ,y+d+h, -d  ,\
                                        x+d  ,y+d  , -d  ,\
                                        x+d  ,y+d  ,z+d  ,\
                                        x+d  ,y+d+h,z+d  ,\
                                        x+d+h,y+d+h, -d-h,\
                                        x+d  ,y+d+h, -d  ,\
                                        x+d  ,y+d+h,z+d  ,\
                                        x+d+h,y+d+h,z+d+h,\
                                        x+d+h,y+d  , -d  ,\
                                        x+d+h,y+d+h, -d-h,\
                                        x+d+h,y+d+h,z+d+h,\
                                        x+d+h,y+d  ,z+d  ,\
                                        x+d  ,y+d  , -d  ,\
                                        x+d+h,y+d  , -d  ,\
                                        x+d+h,y+d  ,z+d  ,\
                                        x+d  ,y+d  ,z+d  ,\
                                        ])
            self.hintColorsGL.extend(colorZ*16)
        # convert to GL format
        self.hintVerticesGL = (GLfloat * len(self.hintVerticesGL))(*self.hintVerticesGL)
        self.hintColorsGL   = (GLfloat * len(self.hintColorsGL))  (*self.hintColorsGL)


    def drawMaze(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.mazeVerticesGL)
        glColorPointer(4, GL_FLOAT, 0, self.mazeColorsGL)
        glDrawArrays(self.mazeModeGL, 0, len(self.mazeVerticesGL) // 3)
        self.drawGoal()


    def drawCube(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.cubeVerticesGL)
        glColorPointer(4, GL_FLOAT, 0, self.cubeColorsGL)
        glDrawArrays(self.mazeModeGL, 0, len(self.cubeVerticesGL) // 3)


    def drawGoal(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.goalVerticesGL)
        glColorPointer(4, GL_FLOAT, 0, self.goalColorsGL)
        glDrawArrays(self.goalModeGL, 0, len(self.goalVerticesGL) // 3)


    def drawMap(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.mapVerticesGL)
        glColorPointer(4, GL_FLOAT, 0, self.mapColorsGL)
        glDrawArrays(self.mapModeGL, 0, len(self.mapVerticesGL) // 3)


    def drawHint(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.hintVerticesGL)
        glColorPointer(4, GL_FLOAT, 0, self.hintColorsGL)
        glDrawArrays(self.hintModeGL, 0, len(self.hintVerticesGL) // 3)


if __name__ == '__main__':
    game = Engine()
    pyglet.app.run()
