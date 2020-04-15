from direct.showbase.ShowBase import ShowBase
from panda3d.core import Geom, GeomNode, GeomVertexFormat, \
    GeomVertexData, GeomTriangles, GeomVertexWriter, GeomVertexReader
from panda3d.core import NodePath
from panda3d.core import PointLight
from panda3d.core import *
from panda3d.core import VBase4, Vec3
from direct.task import Task
import sys
import random
import math
import collections
from opensimplex import OpenSimplex as opens
import time
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *

asteroid_spawn_distance     = 990000 # How close the asteroids spawn and how far away they will fly to
asteroid_min_spawn_distance = 5000
asteroid_future_distance    = 2000000 # How far the asteroid will travel
asteroid_total              = []
missle_total                = []
asteroid_max                = 1000 # The maximum number of asteroids ***** MUST BE AN EVEN NUMBER  and make sur eto modify loop_test_number global variable*****
spaceship_speed_const       = 50
spaceship_speed_x           = 0
spaceship_speed_y           = 0
spaceship_speed_z           = 0
colors                      = {"orange": (.9,.6,.05,1), "gray": (.1,.1,.1,1), "black": (0,0,0,1), "white": (1,1,1,1), "white-transparent": (1,1,1,0.4), "red": (1,0,0,1), "red-transparent": (1,0,0,0.4), "yellow-tinge": (1,1,0.8,1), "yellow-tinge-transparent": (1,1,0.8,0.4)}
loop_test                   = 0 # Used to limit the number of asteroids that have their distance tested each frame
loop_test_number            = 40 # The number of asteroids to test their distance each frame ***** ASTEROID_MAX MUST BE EVENLY DIVISIBLE BY THIS NUMBER - WILL FIX THIS LATER *****
last_frame_mpos_x           = 0
last_frame_mpos_y           = 0
asteroid_test_distance      = 999000 #The test distance. If asteroid greater than asteroid_test_distancem then it will be moved closer
score                       = 0  # Initialize score
FullSceeen                  = False
Frames                      = True

class Begin(ShowBase):
    def __init__(self):
        # Basics
        ShowBase.__init__(self)
        #Setup the window
        base.disableMouse()
        if Frames:
            base.setFrameRateMeter(True)
        base.camLens.setFar(asteroid_spawn_distance * 100)
        render.setAntialias(AntialiasAttrib.MAuto)
        wp = WindowProperties()
        wp.setSize(800,600)
        wp.setCursorHidden(True)
        self.win.requestProperties(wp)
        self.setBackgroundColor(colors.get("black"))
        # Lights
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((0.5, 0.5, 0.5, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(LVector3(0, 45, -45))
        directionalLight.setColor((1, 1, 1, 1))
        directionalLight.setShadowCaster(True)
        render.setLight(render.attachNewNode(directionalLight))
        render.setLight(render.attachNewNode(ambientLight))
        #fog
        self.fog = Fog('distanceFog')
        self.fog.setColor(0, 0, 0)
        self.fog.setExpDensity(.000003)
        render.setFog(self.fog)

        Begin.keyMap = {
            "forward": False, "strafe-left": False, "backward": False, "strafe-right": False, "strafe-up": False, "strafe-down": False, "roll-left": False, "roll-right": False} #True if coresponding key is currently held down.
        #Basic camera movement on the xyz coordinate plane
        self.accept("escape", sys.exit)
        self.accept("w", self.setKey, ["forward", True]) # Pressing the key down sets the state to true. Tasks will function as if pressing key each frame.
        self.accept("w-up", self.setKey, ["forward", False]) # Releasing the key changes the key state in begin.keyMap to False to tasks will stop looping.
        self.accept("a", self.setKey, ["strafe-left", True]) # Both previous comments apply to the following 'accept self.setKey' block of code.
        self.accept("a-up", self.setKey, ["strafe-left", False])
        self.accept("s", self.setKey, ["backward", True])
        self.accept("s-up", self.setKey, ["backward", False])
        self.accept("d", self.setKey, ["strafe-right", True])
        self.accept("d-up", self.setKey, ["strafe-right", False])
        self.accept("space", self.setKey, ["strafe-up", True])
        self.accept("space-up", self.setKey, ["strafe-up", False])
        self.accept("control", self.setKey, ["strafe-down", True])
        self.accept("control-up", self.setKey, ["strafe-down", False])
        self.accept("q", self.setKey, ["roll-left", True])
        self.accept("q-up", self.setKey, ["roll-left", False])
        self.accept("e", self.setKey, ["roll-right", True])
        self.accept("e-up", self.setKey, ["roll-right", False])
        self.accept('mouse1', self.shoot) # Shoots the projectile
        self.accept('f11', self.fullscreenToggle)
        self.accept('f12', self.framesToggle)
        # Development keys
        self.accept('0', self.stop_moving) # Stop moving

        # Create the geometry
        self.startTasks()
        self.createAsteroids()

    def createAsteroids(self):
        for i in range(0,asteroid_max):
            print(int((i / asteroid_max)*100) , "% done")
            asteroid_total.append(Asteroid(random.choice(["small","medium","large"])))

    def startTasks(self):
        #The tasks below are the functions run every frame so the game will work
        taskMgr.add(Begin.test_distance, "Test Distance")
        taskMgr.add(Begin.mouseTask, "Camera Look at Mouse")
        taskMgr.add(Begin.spaceship_movement, "Move the Player or 'spaceship' ")
        taskMgr.add(Begin.remove_old_missles, "Remove old missles")
        taskMgr.add(Begin.score, "Score")

    ##### // Key Press Functions \\ #####
    def spaceship_movement(self):
        global spaceship_speed_const
        global spaceship_speed_x
        global spaceship_speed_y
        global spaceship_speed_z
        #dt = globalClock.getDt() # The change in time since the last frame

        base.camera.setPos(base.camera, spaceship_speed_x, # Spaceship X change per frame
                                        spaceship_speed_y, # Spaceship Y change per frame
                                        spaceship_speed_z) #   "       Z   "     "    "
        if Begin.keyMap["forward"]:
            if spaceship_speed_y < 0:
                spaceship_speed_y += 40 * math.log(-spaceship_speed_y)
            elif spaceship_speed_y < 1:
                spaceship_speed_y = 1.1
            else:
                spaceship_speed_y = 800 * math.log(spaceship_speed_y)
        if Begin.keyMap["backward"]:
            if spaceship_speed_y > 0:
                spaceship_speed_y -= 40 * math.log(spaceship_speed_y)
            elif spaceship_speed_y == 0:
                spaceship_speed_y = -1.1
            else:
                spaceship_speed_y = -(100 * math.log(-spaceship_speed_y))
        if Begin.keyMap["strafe-left"]:
            if spaceship_speed_x > 0:
                spaceship_speed_x -= 40 * math.log(spaceship_speed_x)
            elif spaceship_speed_x == 0:
                spaceship_speed_x = -1.1
            else:
                spaceship_speed_x = -(100 * math.log(-spaceship_speed_x))
        if Begin.keyMap["strafe-right"]:
            if spaceship_speed_x < 0:
                spaceship_speed_x += 40 * math.log(-spaceship_speed_x)
            elif spaceship_speed_x < 1:
                spaceship_speed_x = 1.1
            else:
                spaceship_speed_x = 100 * math.log(spaceship_speed_x)
        if Begin.keyMap["strafe-up"]:
            if spaceship_speed_z < 0:
                spaceship_speed_z += 40 * math.log(-spaceship_speed_z)
            elif spaceship_speed_z < 1:
                spaceship_speed_z = 1.1
            else:
                spaceship_speed_z = 100 * math.log(spaceship_speed_z)
        if Begin.keyMap["strafe-down"]:
            if spaceship_speed_z > 0:
                spaceship_speed_z -= 40 * math.log(spaceship_speed_z)
            elif spaceship_speed_z == 0:
                spaceship_speed_z = -1.1
            else:
                spaceship_speed_z = -(100 * math.log(-spaceship_speed_z))
        if Begin.keyMap["roll-left"]:
            camera_r = base.camera.getR()
            base.camera.setR(camera_r - 1)
        if Begin.keyMap["roll-right"]:
            camera_r = base.camera.getR()
            base.camera.setR((camera_r + 1))
        return Task.cont

    def shoot(self):
        missle = Missle()

    ##### // Tasks \\ #####
    def score(self):
        global score
        self.title = OnscreenText(text="Score: {0}".format(score),
                            parent=base.a2dTopLeft, scale=.07,
                            align=TextNode.ALeft, pos=(0.1,-0.1),
                            fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5))
        return Task.cont

    # Test the distance of all asteroids. If the asteroid is too far away turn it around.
    def test_distance(self): 
        global loop_test
        global loop_test_number
        global asteroid_max
        global asteroid_test_distance
        for index in range(loop_test, loop_test + loop_test_number):
            asteroid = asteroid_total[index]
            asteroid_xyz = asteroid.np.getPos()
            camera_xyz = base.camera.getPos()
            distance = math.sqrt((asteroid_xyz[0] - camera_xyz[0])**2 + (asteroid_xyz[1] - camera_xyz[1])**2 + (asteroid_xyz[2] - camera_xyz[2])**2) # Distance formula
            if distance > asteroid_test_distance: 
                future_pos = asteroid.get_sphere_points(asteroid_spawn_distance, base.camera)
                asteroid.asteroid_lerp.finish()
                asteroid.asteroid_path(future_pos) #move to sphere relative to camera

        # This manages the number of asteroids tested each frame. Also makes sure not to read invalid index of asteroid_total array.
        if loop_test == asteroid_max - loop_test_number:
            loop_test = 0
        else:
            loop_test += loop_test_number
        return Task.cont

    def mouseTask(self):
        # Check to make sure the mouse is readable
        global last_frame_mpos_x
        global last_frame_mpos_y
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            mpos_x = mpos[0]
            mpos_y = mpos[1]
            if (mpos[0] == last_frame_mpos_x):
                mpos_x = 0
            if (mpos[1] == last_frame_mpos_y):
                mpos_y = 0
            base.camera.setP(base.camera, mpos_y * 52) #mpos[1] = y value
            base.camera.setH(base.camera, mpos_x * -50) #[0] = x value
            last_frame_mpos_x = mpos[0]
            last_frame_mpos_y = mpos[1]
            base.win.movePointer(0,
            int(base.win.getProperties().getXSize() / 2),
            int(base.win.getProperties().getYSize() / 2))
        return Task.cont  # Task continues infinitely

    def remove_old_missles(self):
        global missle_total
        dt = globalClock.getDt() # delta t per frame
        for missle in missle_total:
            if missle.ttl <= 0:
                render.clearLight(missle.plnp)
                missle.core.detachNode()
            else:
                missle.ttl -= dt
        return Task.cont

    ##### // Developement Functions \\ #####
    def stop_moving(self):
        global spaceship_speed_x
        global spaceship_speed_y
        global spaceship_speed_z
        spaceship_speed_x = 0
        spaceship_speed_y = 0
        spaceship_speed_z = 0

    #Remove all missiles from the scene.
    def nuke_missles(self):
        global missle_total
        print(missle_total)
        allmissles = render.findAllMatches("sphere.egg")
        print("Nuked " + str(len(allmissles)) + " Missles")
        for missle in missle_total:
            render.clearLight(missle.plnp)
        for objct in allmissles:
            objct.detachNode()
            del objct

    #Remove all asteroids
    def nuke(self):
        allMonkeys = render.findAllMatches(self.asteroid.modelName[:3] + "*" + ".egg")
        print("Nuked " + str(len(allMonkeys)) + " asteroids")
        for objct in allMonkeys:
            objct.detachNode()
            del objct

    ##### // Mist Functions \\ #####
    def setKey(self, key, value):
        self.keyMap[key] = value

    def fullscreenToggle(self):
        global FullSceeen
        global Frames
        wp = WindowProperties()
        if (not(FullSceeen)):
            wp.setFullscreen(True)
            wp.setCursorHidden(True)
            wp.setSize(3840,2160)
            base.openMainWindow()
            base.win.requestProperties(wp)
            base.graphicsEngine.openWindows()
            FullSceeen = True
        else:
            wp.setFullscreen(False)
            wp.setCursorHidden(True)
            wp.setSize(800,600)
            base.openMainWindow()
            base.win.requestProperties(wp)
            base.graphicsEngine.openWindows()
            FullSceeen = False
        #Resizing clears frames. Reset that
        base.setFrameRateMeter(Frames)

    def framesToggle(self):
        global Frames
        if(Frames):
            base.setFrameRateMeter(False)
            Frames = False
        else:
            base.setFrameRateMeter(True)
            Frames = True

class Asteroid(object):

    def __init__(self, size, step=36):
        types = {"large":  {"radius": 10000, "darkest_gray": 0.3, "lightest_gray": 0.7, "speed": 9000, "speed_percent": 5},
                 "medium": {"radius": 5000,  "darkest_gray": 0.4, "lightest_gray": 0.7, "speed": 900,  "speed_percent": 10},
                 "small":  {"radius": 1000,   "darkest_gray": 0.4, "lightest_gray": 0.7, "speed": 90,   "speed_percent": 20}}
        #small should be 1000 -> 1500
        #Step for creating the sphere, lower the number greater the detail of the shpere
        self.radius         = types[size]["radius"]
        self.darkest_gray   = types[size]["darkest_gray"]
        self.lightest_gray  = types[size]["lightest_gray"]
        self.speed          = types[size]["speed"]
        self.speed_percent  = types[size]["speed_percent"]
        self.step           = step
        self.asteroid_min   = self.radius
        self.asteroid_max   = self.radius + (self.radius / 2)
        self.map            = self.create_map(self.radius)
        geom                = self.create_geom(self.radius)
        self.np             = NodePath(geom)
        spawn_distance      = self.translate((random.random() ** 0.5),0,1,asteroid_min_spawn_distance, asteroid_spawn_distance)
        self.asteroid_path(self.get_sphere_points(spawn_distance))
        self.np.reparent_to(render)


    def create_geom(self, sidelength):
        # Set up the vertex arrays
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("Data", vformat, Geom.UHDynamic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        geom = Geom(vdata)

        # Write vertex data
        # Vertex data for the poles needs to be different
        for key , value in self.map.items():
            v_x, v_y, v_z, asteroid_color = value
            n_x, n_y, n_z = 1,1,1
            #c_r, c_g, c_b, c_a = asteroid_color, asteroid_color, asteroid_color, 1
            c_r, c_g, c_b, c_a = asteroid_color, asteroid_color, asteroid_color, 1
            vertex.addData3f(v_x, v_y, v_z)
            normal.addData3f(n_x, n_y, n_z)
            color.addData4f(c_r, c_g, c_b, c_a) 
        #Create triangles
        #top of sphere
        verts_per_row = int(360 / self.step) + 1
        for vert in range(1,verts_per_row + 1):
            tris = GeomTriangles(Geom.UHStatic)
            tris.addVertices(vert + 1, 0, vert)
            tris.closePrimitive()
            geom.addPrimitive(tris)
        #middle of shpere
        for row in range(1, int(180 / self.step) - 1):
            for vert_iir in range(0, verts_per_row - 1): # vert_iir = vertex index in row, not vertex number
                vert_number = verts_per_row * row + vert_iir + 1
                vert_up_row = vert_number - verts_per_row
                #Bottom Triangle in the sphere
                tris = GeomTriangles(Geom.UHStatic)
                tris.add_vertices(vert_up_row, vert_number, vert_up_row + 1)
                tris.close_primitive()
                geom.addPrimitive(tris)
                #Top triangle of square
                tris = GeomTriangles(Geom.UHStatic)
                tris.add_vertices(vert_number + 1, vert_up_row + 1, vert_number)
                tris.close_primitive()
                geom.addPrimitive(tris)
        #bottom of sphere
        last_vert = len(self.map) - 1
        for vert in range(last_vert - verts_per_row, last_vert):
            tris = GeomTriangles(Geom.UHStatic)
            tris.add_vertices(vert - 1, last_vert, vert)
            tris.close_primitive()
            geom.addPrimitive(tris)

        # Create the actual node
        node = GeomNode('geom_node')
        node.addGeom(geom)
        
        return node

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Scale value from input range to output range
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin
        valueScaled = float(value - leftMin) / float(leftSpan)
        return rightMin + (valueScaled * rightSpan)


    def simplex_radius(self, radius, seed, xoff, yoff, zoff):
        noise = opens(seed=seed)
        return self.translate(noise.noise3d(xoff,yoff,zoff),0,1,self.asteroid_min, self.asteroid_max)
        #return radius

    #map for most of the sphere
    def create_map(self, radius):
        map = collections.OrderedDict()
        seed = int(time.time() * 10000000)
        for x in range(0, 181, self.step):
            #Top/Bottom of sphere need to be single points
            if x == 0:
                point_radius = self.simplex_radius(radius, seed, 0, 0, 1) 
                map[(0,0)] = (0,0,point_radius, (self.translate(point_radius, self.asteroid_min, self.asteroid_max, self.darkest_gray, self.lightest_gray)))
            elif x == 180:
                point_radius = -(self.simplex_radius(radius, seed, 0, 0, -1)) 
                map[(180,0)] = (0,0,point_radius, (self.translate(point_radius, -self.asteroid_min, -self.asteroid_max, self.darkest_gray, self.lightest_gray)))
            #The rest of the sphere
            else:
                for y in range(0, 361, self.step):
                    phi = x * (math.pi / 180.)
                    theta = y * (math.pi / 180.)
                    xoff = math.sin(phi) * math.cos(theta)
                    yoff = math.sin(phi) * math.sin(theta) 
                    zoff = math.cos(phi)
                    point_radius = self.simplex_radius(radius, seed, xoff, yoff, zoff) 
                    v_x = point_radius * xoff
                    v_y = point_radius * yoff
                    v_z = point_radius * zoff
                    map[(x ,y)] = (v_x, v_y, v_z, (self.translate(point_radius, self.asteroid_min, self.asteroid_max, self.darkest_gray, self.lightest_gray)))
        return map 

    def asteroid_path(self, start_point): #takes starting location (start_point must be a LPoint3)
        # Create and run the asteroid animation
        self.asteroid_lerp = LerpPosInterval(self.np, # Object being manipulated. The asteroid in this case.
                                            self.speed * random.randrange(1, self.speed_percent, 1), # How fast the asteroid will move in seconds
                                            self.get_sphere_points(asteroid_future_distance, base.camera), # future location at end of lerp
                                            start_point) # The start position of the asteroid
        self.asteroid_lerp.start()

    def get_sphere_points(self, radius, relative_to=False): #returns a LPoint3 in sphere. relative_to will return global LPoint3 realtive to given object.
        phi = random.uniform(0,2*math.pi)
        theta = random.uniform(0,2*math.pi)
        if relative_to:
            rel_xyz = relative_to.getPos()
            x = radius * math.cos(phi) * math.sin(theta) + rel_xyz[0]
            y = radius * math.sin(phi) * math.sin(theta) + rel_xyz[1]
            z = radius * math.cos(theta) + rel_xyz[2]
        else:
            x = radius * math.cos(phi) * math.sin(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(theta)
        return LPoint3(x,y,z)

class Location(object): # Create child of asteroid to find the future position the asteroid will fly to
    def __init__(self, asteroid_parent, distance=asteroid_future_distance):
        self.obj = loader.loadModel("./Models/empty.egg")
        self.obj.setY(asteroid_parent, distance)

class Missle(object):
    def __init__(self):
        print("missle created")
        camera_hpr = base.camera.getHpr()
        self.core = loader.loadModel("./Models/sphere.egg")
        self.core.setPos(base.camera, (0,0,0))
        self.core.setHpr(camera_hpr)
        self.ttl = 1 # Time to live in seconds
        self.core.setScale(600,600,600)
        self.glow = loader.loadModel("./Models/sphere.egg")
        self.core.setTransparency(TransparencyAttrib.MAlpha)
        self.glow.setScale(2,2,2)
        self.glow.reparentTo(self.core)
        self.core.setColor(colors.get("white"))
        self.glow.setColor(colors.get("white-transparent"))
        self.glow.setPos(0,0,0) #relative to parent
        self.core.setLightOff() # remove all other lights from missle so it is a bright white
        missle_total.append(self)

        #Create the light so the missle glows
        plight = PointLight('plight')
        plight.setColor(colors.get("white"))
        plight.setAttenuation(LVector3(0, 0.00008 , 0))
        plight.setMaxDistance(100)
        self.plnp = self.core.attachNewNode(plight) #point light node point
        render.setLight(self.plnp)
        """for asteroid in asteroid_total:
            asteroid.obj.setLight(plnp)""" #Might have to create a node point and attach that in the setup. Then add lights to that node point. I am going to bed now.

        # Create and run the missle animation
        location = Location(self.core).obj.getPos()
        self.asteroid_lerp = LerpPosInterval(self.core, # Object being manipulated. The missle in this case.
                                            1000, # How long it will take the missle to go from point a to b in seconds
                                            location, # future location at end of lerp
                                            base.camera.getPos()) # The start position of the missle
        self.asteroid_lerp.start()
        del location

        self.core.reparentTo(render)

demo = Begin()
demo.run()