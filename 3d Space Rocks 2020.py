from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.interval.IntervalGlobal import * 
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
from direct.actor.Actor import Actor
from direct.task import Task 
from direct.task.Task import Task
from pprint import pprint
import math
import sys
import random


print("Starting 3d Asteroid Simulator 2020")
asteroid_spawn_distance = 990000 # How close the asteroids spawn and how far away they will fly to
asteroid_min_spawn_distance = 5000
asteroid_speed = 90 # Time it takes an asteroid to fly from one side to another in seconds
asteroid_speed_percent = 30 # the pecentage that asteroid_speed can be modified by randomly for each asteroid. 
asteroid_future_distance = 2000000 # How far the asteroid will travel
asteroid_total = []
missle_total = []
asteroid_max = 600 # The maximum number of asteroids ***** MUST BE AN EVEN NUMBER  and make sur eto modify loop_test_number global variable*****
spaceship_speed_const = 10
spaceship_speed_x = 0
spaceship_speed_y = 0
spaceship_speed_z = 0
colors = {"orange": (.9,.6,.05,1), "gray": (.1,.1,.1,1), "black": (0,0,0,1), "white": (1,1,1,1), "white-transparent": (1,1,1,0.4), "red": (1,0,0,1), "red-transparent": (1,0,0,0.4), "yellow-tinge": (1,1,0.8,1), "yellow-tinge-transparent": (1,1,0.8,0.4)}
loop_test = 0 # Used to limit the number of asteroids that have their distance tested each frame
loop_test_number = 60 # The number of asteroids to test their distance each frame ***** ASTEROID_MAX MUST BE EVENLY DIVISIBLE BY THIS NUMBER - WILL FIX THIS LATER *****
last_frame_mpos_x = 0
last_frame_mpos_y = 0
asteroid_test_distance = 990000 #The test distance. If asteroid greater than asteroid_test_distancem then it will be moved closer
score = 0  # Initialize score


class Asteroid(object):
    def __init__(self):
        self.modelName = "asteroid" + str(random.randrange(1,25,1)) # Name must be at least 3 charachters long
        self.obj = loader.loadModel("./Models/" + self.modelName + ".egg")
        """I NEED TO RE-EXPORT THE ASTEROID MODELS > THEY ARE NOT BEING AFFECTED BY COLORS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        self.obj.setColor(colors.get("gray")) #(gray, gray, gray, 1)
        self.obj.setScale((random.randrange(900, 9000, 1) ,random.randrange(900, 9000, 1) ,random.randrange(900, 9000, 1)))
        while True:
            spawn_distance = asteroid_spawn_distance * (random.random() ** 0.5) # **0.5 to evenly distribute by the inverse squared law
            if spawn_distance < asteroid_min_spawn_distance:
                break
        self.asteroid_path(self.get_sphere_points(asteroid_spawn_distance / (random.random() ** 0.5))) # Start the asteroid from any random position in the 
        asteroid_total.insert(0,self)
        self.obj.reparentTo(render)

    def asteroid_path(self, start_point): #takes starting location (start_point must be a LPoint3)
        # Create and run the asteroid animation
            self.asteroid_lerp = LerpPosInterval(self.obj, # Object being manipulated. The asteroid in this case.
                                                asteroid_speed * random.randrange(-asteroid_speed_percent, asteroid_speed_percent, 1), # How fast the asteroid will move in seconds
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

    def handle_missle_colision(self, entry):
        global score
        score += 1
        print(entry)


class Missle(object):
    def __init__(self):
        camera_hpr = base.camera.getHpr()
        self.core = loader.loadModel("./Models/sphere.egg")
        self.core.setPos(base.camera, (0,0,0))
        self.core.setHpr(camera_hpr)
        self.ttl = 0.5 # Time to live in seconds
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
        plight.setAttenuation(LVector3(0, 0.000005 , 0))
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

class Location(object): # Create child of asteroid to find the future position the asteroid will fly to
    def __init__(self, asteroid_parent, distance=asteroid_future_distance):
        self.obj = loader.loadModel("./Models/empty.egg")
        self.obj.setY(asteroid_parent, distance)
        


class begin(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        base.disableMouse()  # Disable mouse-based camera-control
        base.setFrameRateMeter(True) # Show the frame rate

        # Create an instance of fog called 'distanceFog'.
        self.fog = Fog('distanceFog')
        self.fog.setColor(0, 0, 0)
        self.fog.setExpDensity(.000004)
        # the fog.
        render.setFog(self.fog)

        #base.oobe()
        #base.enableParticles() # Enables the pyhsics engine. Called particels because panda3d is werid
        begin.keyMap = {
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

        self.accept('k', self.createAsteroids) # K for Kreate - Creates asteroids
        self.accept('n', self.nuke) # N for Nuke - Removes all asteroids
        self.accept('p', self.nuke_missles) #P for pop missles
        self.accept('mouse1', self.imma_fireing_ma_lazar) # Shoots the projectile
        self.accept('0', self.stop_moving) # Stop moving
        self.accept('t', self.test_key) #calls a funtion for testing purposes
        #base.camLens.setFov(20)
        base.camLens.setFar(asteroid_spawn_distance)
        render.setAntialias(AntialiasAttrib.MAuto) # Enable anti-aliasing

        #Hide the Mouse
        props = WindowProperties()
        props.setCursorHidden(True)
        self.win.requestProperties(props)

        #Set the background color to black
        self.setBackgroundColor(colors.get("black"))
        self.setupLights()

        #Create the world
        self.createAsteroids()

    ##### // Game Play Functions \\ #####
    def imma_fireing_ma_lazar(self):
        missle = Missle()

    def stop_moving(self):
        global spaceship_speed_x
        global spaceship_speed_y
        global spaceship_speed_z
        spaceship_speed_x = 0
        spaceship_speed_y = 0
        spaceship_speed_z = 0


    ##### // Initial setup functions are below this line \\ #####
    print("Creating Asteroids")
    def createAsteroids(self, number=asteroid_max): # Can be used to create as many asteroids as wanted. Defalut is 500 for testing purposes.
        for i in range(number):
            self.asteroid = Asteroid()
        
        #The tasks below are the functions run every frame so the game will work
        taskMgr.add(begin.test_distance, "Test Distance")
        taskMgr.add(begin.mouseTask, "Camera Look at Mouse")
        taskMgr.add(begin.spaceship_movement, "Move the Player or 'spaceship' ")
        taskMgr.add(begin.remove_old_missles, "Remove old missles")
        taskMgr.add(begin.score, "Score")

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

    def test_key(self):
        pprint("You found the test key!")

    def setupLights(self):  # This function sets up some default lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.02, 0.02, 0.02, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(LVector3(0, 45, -45))
        #directionalLight.setColor((0.5, 0.5, 0.5, 1))
        render.setLight(render.attachNewNode(directionalLight))
        render.setLight(render.attachNewNode(ambientLight))

    def setKey(self, key, value):
        self.keyMap[key] = value

##### // All Tasks are below this line \\ #####
# Test the distance of all asteroids. If the asteroid is too far away turn it around.
    def test_distance(self): 
        global loop_test
        global loop_test_number
        global asteroid_max
        global asteroid_test_distance
        for index in range(loop_test, loop_test + loop_test_number):
            asteroid = asteroid_total[index]
            asteroid_xyz = asteroid.obj.getPos()
            camera_xyz = base.camera.getPos()
            distance = math.sqrt((asteroid_xyz[0] - camera_xyz[0])**2 + (asteroid_xyz[1] - camera_xyz[1])**2 + (asteroid_xyz[2] - camera_xyz[2])**2) # Distance formula
            if distance > asteroid_test_distance: # Need to figure out exactly what is a good distance for after the ">"
                future_pos = asteroid.get_sphere_points(asteroid_spawn_distance, base.camera)
                #print("Asteroid #", asteroid.obj.name , " is too faw away at " , distance , "Moving to " , future_pos)
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
            else:
                missle.ttl -= dt
        return Task.cont


    def spaceship_movement(self):
        global spaceship_speed_const
        global spaceship_speed_x
        global spaceship_speed_y
        global spaceship_speed_z
        #dt = globalClock.getDt() # The change in time since the last frame

        base.camera.setPos(base.camera, spaceship_speed_x, # Spaceship X change per frame
                                        spaceship_speed_y, # Spaceship Y change per frame
                                        spaceship_speed_z) #   "       Z   "     "    "
        if begin.keyMap["forward"]:
            if spaceship_speed_y < 0:
                spaceship_speed_y += 40 * math.log(-spaceship_speed_y)
            elif spaceship_speed_y < 1:
                spaceship_speed_y = 1.1
            else:
                spaceship_speed_y = 1000 * math.log(spaceship_speed_y)
        if begin.keyMap["backward"]:
            if spaceship_speed_y > 0:
                spaceship_speed_y -= 40 * math.log(spaceship_speed_y)
            elif spaceship_speed_y == 0:
                spaceship_speed_y = -1.1
            else:
                spaceship_speed_y = -(100 * math.log(-spaceship_speed_y))
        if begin.keyMap["strafe-left"]:
            if spaceship_speed_x > 0:
                spaceship_speed_x -= 40 * math.log(spaceship_speed_x)
            elif spaceship_speed_x == 0:
                spaceship_speed_x = -1.1
            else:
                spaceship_speed_x = -(100 * math.log(-spaceship_speed_x))
        if begin.keyMap["strafe-right"]:
            if spaceship_speed_x < 0:
                spaceship_speed_x += 40 * math.log(-spaceship_speed_x)
            elif spaceship_speed_x < 1:
                spaceship_speed_x = 1.1
            else:
                spaceship_speed_x = 100 * math.log(spaceship_speed_x)
        if begin.keyMap["strafe-up"]:
            if spaceship_speed_z < 0:
                spaceship_speed_z += 40 * math.log(-spaceship_speed_z)
            elif spaceship_speed_z < 1:
                spaceship_speed_z = 1.1
            else:
                spaceship_speed_z = 100 * math.log(spaceship_speed_z)
        if begin.keyMap["strafe-down"]:
            if spaceship_speed_z > 0:
                spaceship_speed_z -= 40 * math.log(spaceship_speed_z)
            elif spaceship_speed_z == 0:
                spaceship_speed_z = -1.1
            else:
                spaceship_speed_z = -(100 * math.log(-spaceship_speed_z))
        if begin.keyMap["roll-left"]:
            camera_r = base.camera.getR()
            base.camera.setR(camera_r - 1)
        if begin.keyMap["roll-right"]:
            camera_r = base.camera.getR()
            base.camera.setR((camera_r + 1))
        return Task.cont
    
    def score(self):
        global score
        self.title = OnscreenText(text="Score: {0}".format(score),
                            parent=base.a2dTopLeft, scale=.07,
                            align=TextNode.ALeft, pos=(0.1,-0.1),
                            fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5))
        return Task.cont

bigBucks = begin()
bigBucks.run()

"""
**********           Done           **********
> Spawn asteroids in sphere
> Continue to spawn asteroids around the ship as flown through space
> Add missle
> Add asteroid movement animation
> Give missles glow, and remove old missles so more than 13 will glow
> Add basic score UI

********** Things that I need to do **********

> Detect when missle hits asteroid, then add a point
> Generate asteroids in rectangular, sphereical, and pill shape
> create 3 different sizes of asteroids w/ different speed
    > At begininning all should be large, and med/small will only show becasue of shooting.
> Add rotation to asteroids
> Break asteroids upon impact with missle
> Asteroids should break upon impact w/ eachother, but not give points.
> Add a fail state to the game.
> Organize the code, I should do this now, but I am lazy
> Upgrade point system to be relative to ship speed, and density/speed of asteroid (easy, medium, hard)
> Add a delay in space ship turning to make the game better
> Add hud that shows points, global direction of ship, and lag between mouse and direction of ship
> Particle effects
> Main Menu (Dificulty select, and start) it would be cool if it looked like the original asteroids.
    > This should include a name on the window.
> Add a fail menu
> Add loading menu (should be quick, but looks good.)
"""