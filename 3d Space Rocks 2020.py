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
asteroid_min_spawn_distance = 10000
asteroid_future_distance    = 2000000 # How far the asteroid will travel
asteroid_total              = []
extra_smallasteroids        = []
extra_mediumasteroids       = []
missle_total                = []
asteroid_max                = 1000 # The maximum number of asteroids ***** MUST BE AN EVEN NUMBER  and make sur eto modify loop_test_number global variable*****
spaceship_speed_const       = 200
spaceship_speed_x           = 0
spaceship_speed_y           = 0
spaceship_speed_z           = 0
colors                      = {"orange": (.9,.6,.05,1), "gray": (.1,.1,.1,1), "black": (0,0,0,1), "white": (1,1,1,1), "white-transparent": (1,1,1,0.4), "red": (1,0,0,1), "red-transparent": (1,0,0,0.4), "yellow-tinge": (1,1,0.8,1), "yellow-tinge-transparent": (1,1,0.8,0.4)}
asteroid_test_distance      = 999000 #The test distance. If asteroid greater than asteroid_test_distancem then it will be moved closer
score                       = 0  # Initialize score
score_list                  = [0]
FullSceeen                  = False
Frames                      = True
test_max_min                = [0,0,0,0]
max_player_speed            = 5000

class Begin(ShowBase):
    def __init__(self):
        # Basics
        ShowBase.__init__(self)
        #Setup the window
        base.disableMouse()
        if Frames:
            base.setFrameRateMeter(True)
        base.camLens.setFar(asteroid_spawn_distance * 100)
        # Set mouse and display settings
        render.setAntialias(AntialiasAttrib.MAuto)
        wp = WindowProperties()
        wp.setMouseMode(WindowProperties.M_relative)
        wp.setCursorHidden(True)
        wp.setSize(800,600)
        self.win.requestProperties(wp)
        self.setBackgroundColor(colors.get("black"))
        # Lights
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((0.8, 0.8, 0.8, 1))
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
        # Initialize Collisions
        base.cTrav = CollisionTraverser()
        base.cTrav.setRespectPrevTransform(True)
        self.collHandEvent = CollisionHandlerEvent()
        self.collHandEvent.addInPattern("%fn-into-%in")
        # Add colision sphere to player
        cNode = CollisionNode("player")
        cNode.addSolid(CollisionSphere(0, 0, 0, 1))
        self.player_np = base.camera.attachNewNode(cNode)
        base.cTrav.addCollider(self.player_np, self.collHandEvent)
        self.accept("player-into-asteroid", self.end_game)

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
        self.accept('1', self.angle1)
        self.accept('2', self.angle2)
        self.accept('3', self.angle3)
        self.accept('4', self.angle4)
        self.accept('5', self.angle5)
        self.accept('6', self.angle6)

        # Create the geometry
        self.lastMouseX, self.lastMouseY = 0, 0
        self.startTasks()
        self.createAsteroids()

    def createAsteroids(self):
        self.accept(f"missle-into-asteroid", self.shot_asteroid)
        for i in range(0,asteroid_max):
            print(int((i / asteroid_max)*100) , "% done")
            asteroid = Asteroid()
            asteroid_total.insert(0,asteroid)
            base.cTrav.addCollider(asteroid.c_np, self.collHandEvent)
            asteroid.add_togame()
        # Extra asteroids to be instantly available when asteroids break
        for i in range(0, int(asteroid_max * 0.05)):
            extra_smallasteroids.insert(0,Asteroid("small"))
        for i in range(0, int(asteroid_max * 0.05)):
            extra_mediumasteroids.insert(0,Asteroid("medium"))

    def startTasks(self):
        #The tasks below are the functions run every frame so the game will work
        taskMgr.add(Begin.test_distance, "Test Distance")
        taskMgr.add(self.mouseTask, "Rotate player in hpr")
        taskMgr.add(Begin.spaceship_movement, "Move the Player in xyz")
        taskMgr.add(Begin.remove_old_missles, "Remove old missles")
        taskMgr.add(Begin.score, "Score")

    ##### // Key Press Functions \\ #####
    def spaceship_movement(self):
        global spaceship_speed_const
        global spaceship_speed_x
        global spaceship_speed_y
        global spaceship_speed_z
        global max_player_speed
        cam_pos = base.camera.getPos()

        # These coord modicifations do not appear to be correct according to what the docs for .setPos
        # want. That is becasuse the they are converting from realtice rotation to global positioning
        base.camera.setPos(cam_pos[0] + -spaceship_speed_y, # Spaceship X change per frame
                            cam_pos[1] + spaceship_speed_x, # Spaceship Y change per frame
                            cam_pos[2] + spaceship_speed_z) #   "       Z   "     "    "
        if Begin.keyMap["forward"] or Begin.keyMap["backward"]:
            #acc_const = acceleration constant
            acc_const = 100
            if Begin.keyMap["backward"]:
                acc_const *= -1
            cam_hpr = base.camera.getHpr(render)
            phi, theta = cam_hpr[0], cam_hpr[1]
            phi *= math.pi / 180
            theta *= math.pi / 180
            # Calculate component vectors
            x = math.cos(phi) * math.cos(theta)
            y = math.sin(phi) * math.cos(theta)
            z = math.sin(theta)
            # Calculate the magnitude, and limit speed to that
            mag = math.sqrt((spaceship_speed_x * x)**2 + (spaceship_speed_y * y)**2 + (spaceship_speed_z * z)**2)
            if mag < max_player_speed:
                spaceship_speed_x = min(spaceship_speed_x + acc_const * x, max_player_speed)
                spaceship_speed_y = min(spaceship_speed_y + acc_const * y, max_player_speed)
                spaceship_speed_z = min(spaceship_speed_z + acc_const * z, max_player_speed)
            print(f"speed_x{spaceship_speed_x} speed_y{spaceship_speed_y} speed_z{spaceship_speed_z}")
            print(base.camera.getPos())
            print(f"phi{phi} theta{theta}")

        if Begin.keyMap["roll-left"]:
            camera_r = base.camera.getR()
            base.camera.setR(camera_r - 1)
        if Begin.keyMap["roll-right"]:
            camera_r = base.camera.getR()
            base.camera.setR((camera_r + 1))
        return Task.cont

    def shoot(self):
        missle = Missle()
        base.cTrav.addCollider(missle.c_np, self.collHandEvent)

    ##### // Tasks \\ #####
    def score(self):
        global score
        global score_list
        if (len(score_list) > 0):
            for points in score_list:
                score += points
            score_list = []
            try:
                self.title.clearText()
            except:
                pass
            self.title = OnscreenText(text="Score: {0}".format(score),
                                parent=base.a2dTopLeft, scale=.07,
                                align=TextNode.ALeft, pos=(0.1,-0.1),
                                fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5))
        return Task.cont

    # Test the distance of all asteroids. If the asteroid is too far away turn it around.
    def test_distance(self): 
        global asteroid_max
        global asteroid_test_distance
        for asteroid in asteroid_total:
            asteroid_xyz = asteroid.np.getPos()
            camera_xyz = base.camera.getPos()
            distance = math.sqrt((asteroid_xyz[0] - camera_xyz[0])**2 + (asteroid_xyz[1] - camera_xyz[1])**2 + (asteroid_xyz[2] - camera_xyz[2])**2) # Distance formula
            if distance > asteroid_test_distance: 
                future_pos = asteroid.get_sphere_points(asteroid_spawn_distance, base.camera)
                asteroid.asteroid_lerp.finish()
                asteroid.asteroid_path(future_pos) #move to sphere relative to camera
        return Task.cont

    def mouseTask(self, task):
        global test_max_min
        # h_max : h_min , p_max : p_min
        mw = self.mouseWatcherNode
        if mw.hasMouse():
            # get the window manager's idea of the mouse position
            x, y = mw.getMouseX(), mw.getMouseY()

            if self.lastMouseX is not None:
                dx, dy = x - self.lastMouseX, y - self.lastMouseY
            else:
                # no data to compare with yet
                dx, dy = 0, 0

            self.lastMouseX, self.lastMouseY = x, y
        else:
            x, y, dx, dy = 0, 0, 0, 0

        self.win.movePointer(0,
              int(self.win.getProperties().getXSize() / 2),
              int(self.win.getProperties().getYSize() / 2))
        self.lastMouseX, self.lastMouseY = 0, 0

        # scale position and delta to pixels for user
        w, h = self.win.getSize()

        # rotate box by delta
        base.camera.setH(base.camera, dx * -10)
        base.camera.setP(base.camera, dy * 10)
        test_max_min = [max(test_max_min[0], base.camera.getH(render)), min(test_max_min[1], base.camera.getH(render)), max(test_max_min[2], base.camera.getP(render)), min(test_max_min[3], base.camera.getP(render))]
        #print(f"h_max {test_max_min[0]} : h_min {test_max_min[1]} , p_max {test_max_min[2]} : p_min {test_max_min[3]}")
        #base.camera.setH(base.camera.getH() - dx * 10)
        #base.camera.setP(base.camera.getP() + dy * 10)
        return Task.cont

    def remove_old_missles(self):
        global missle_total
        dt = globalClock.getDt() # delta t per frame
        for missle in missle_total:
            if missle.ttl <= 0:
                render.clearLight(missle.plnp)
                missle.core.removeNode()
            else:
                missle.ttl -= dt
        return Task.cont

    def death_task(self):
        camera_hpr = base.camera.getHpr()
        h_speed = float(base.camera.getTag("h_speed"))
        p_speed = float(base.camera.getTag("p_speed"))
        r_speed = float(base.camera.getTag("r_speed"))
        base.camera.setHpr(camera_hpr[0] + h_speed, camera_hpr[1] + p_speed, camera_hpr[2] + r_speed)
        base.camera.setX(base.camera.getX() + 800)
        return Task.cont


    ##### // Colision Functions \\ #####
    def shot_asteroid(self, collision_entry):
        global score_list
        score_list.append(1)
        #Remove the missle
        missle = collision_entry.getFromNodePath()
        try:
            render.clearLight(missle.parent.find("**/plight"))
        except:
            pass
        missle.removeNode()

        # Gather large asteroid info so still accesable after deleted
        hit_asteroid = collision_entry.getIntoNodePath()
        hap = hit_asteroid.parent.getPos()
        has = hit_asteroid.parent.getTag("size")
        # Remove asteroid from list
        for index in range(0,len(asteroid_total) -1):
            if asteroid_total[index].name == hit_asteroid.name:
                del asteroid_total[index]
                break
        # Delete before smaller asteoids are created to allow for asteroid-into-asteroid collisions
        hit_asteroid.parent.removeNode()
        
        # If small asteroid, just delete, if not create two of smaller size
        # Note: na is short for "new_asteroid", has is "hit_asteroid_size"
        if not(has == "small"):
            # Generate 2 asteroids at oposite poistions (shimmy) within the larger asteoid, and oposite directions
            for index in range(0,2):
                na = extra_smallasteroids.pop() if has == "medium" else extra_mediumasteroids.pop()
                # First asteroid can be random pos & direction
                if index == 0:
                    shimmy = [na.radius * random.randrange(-1,2,2), na.radius * random.randrange(-1,2,2), na.radius * random.randrange(-1,2,2)]
                    spawn_point = [hap[0] + shimmy[0], hap[1] + shimmy[1], hap[2] + shimmy[2]]
                    print(hap)
                    print(shimmy)
                    print(spawn_point)
                    future_location = False
                # Second asteroid should be oposite pos & direction of asteroid 1
                else:
                    spawn_point = [hap[0] + shimmy[0] * -1, hap[1] + shimmy[1] * -1, hap[2] + shimmy[2] * -1]
                    future_location = LPoint3(future_location[0] * -1, future_location[1] * -1, future_location[2] * -1)
                # Add asteroid to the game. This code is the same for both asteroids
                na.add_togame(LPoint3(spawn_point[0], spawn_point[1], spawn_point[2]), future_location)
                future_location = na.future_location
                base.cTrav.addCollider(na.c_np, self.collHandEvent)
                asteroid_total.append(na)
            # Create more asteroid for the ones we just deleted
            for i in range(0,2):
                if na.size == "small":
                    extra_smallasteroids.insert(0,Asteroid("small"))
                else:
                    extra_mediumasteroids.insert(0,Asteroid("medium"))
        else:
            asteroid = Asteroid()
            asteroid_total.insert(0, asteroid)
            base.cTrav.addCollider(asteroid.c_np, self.collHandEvent)
            asteroid.add_togame(asteroid.get_sphere_points(asteroid_spawn_distance, base.camera))

    def end_game(self, collision_entry):
        asteroid = collision_entry.getIntoNodePath()
        # Make the world red
        self.fog.setColor(1,0,0)
        self.fog.setExpDensity(.000004)
        self.setBackgroundColor(1,0,0,1)
        # Set random spin upon death. This is called in the death_task 
        base.camera.setTag("h_speed", str(random.randrange(0,1)))
        base.camera.setTag("p_speed", str(random.randrange(0,1)))
        base.camera.setTag("r_speed", str(random.uniform(0,0.5)))
        # Stop unused tasks in death
        taskMgr.remove("Rotate player in hpr")
        taskMgr.remove("Score")
        taskMgr.remove("Move the Player in xyz")
        # Move player and look so player gets to see their killer
        base.camera.setX(base.camera.getX() + int(asteroid.parent.getTag("radius")))
        base.camera.lookAt(asteroid)
        # Start the death spiral + death text
        taskMgr.add(Begin.death_task, "Death Spin")
        self.title = OnscreenText(text="Your Spaceship has Crashed",
                            parent=base.aspect2d, scale=0.1,
                            align=TextNode.ACenter, pos=(0,0),
                            fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5))

    ##### // Developement Functions \\ #####
    def stop_moving(self):
        global spaceship_speed_x
        global spaceship_speed_y
        global spaceship_speed_z
        spaceship_speed_x = 0
        spaceship_speed_y = 0
        spaceship_speed_z = 0
        print(base.camera.getHpr())
        base.camera.setPos(0,0,0)
        print(base.camera.getPos())

    def angle1(self):
        print("0,0,0")
        base.camera.setHpr(0,0,0)

    def angle2(self):
        print("90,0,0")
        base.camera.setHpr(90,0,0)

    def angle3(self):
        print("180,0,0")
        base.camera.setHpr(180,0,0)

    def angle4(self):
        print("-90,0,0")
        base.camera.setHpr(-90,0,0)

    def angle5(self):
        print("0,90,0")
        print(base.camera.getHpr())
        base.camera.setHpr(0,90,0)

    def angle6(self):
        print("0,-90,0")
        print(base.camera.getHpr())
        base.camera.setHpr(0,-90,0)

    ##### // Misc Functions \\ #####
    def setKey(self, key, value):
        self.keyMap[key] = value

    def fullscreenToggle(self):
        global FullSceeen
        global Frames
        wp = WindowProperties()
        if (not(FullSceeen)):
            wp.setFullscreen(True)
            wp.setCursorHidden(True)
            wp.setMouseMode(WindowProperties.M_relative)
            #self.base.win.getProperties().getXSize()
            #self.base.win.getProperties().getYSize
            wp.setSize(3840,2160)
            base.openMainWindow()
            base.win.requestProperties(wp)
            base.graphicsEngine.openWindows()
            FullSceeen = True
        else:
            wp.setFullscreen(False)
            wp.setCursorHidden(True)
            wp.setMouseMode(WindowProperties.M_relative)
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

    def __init__(self, size=False, step=36):
        types = {"large":  {"radius": 10000, "darkest_gray": 0.3, "lightest_gray": 0.7, "speed": 9000, "speed_percent": 5},
                 "medium": {"radius": 5000,  "darkest_gray": 0.4, "lightest_gray": 0.7, "speed": 180,  "speed_percent": 10},
                 "small":  {"radius": 1000,   "darkest_gray": 0.4, "lightest_gray": 0.7, "speed": 90,   "speed_percent": 20}}
        # Variables needed for the size given
        self.size           = random.choice(["small","medium","large"]) if not(size) else size
        self.radius         = types[self.size]["radius"]
        self.darkest_gray   = types[self.size]["darkest_gray"]
        self.lightest_gray  = types[self.size]["lightest_gray"]
        self.speed          = types[self.size]["speed"]
        self.speed_percent  = types[self.size]["speed_percent"]
        self.step           = step
        self.seed           = int(time.time() * 10000000)
        self.asteroid_min   = self.radius
        self.asteroid_max   = self.radius + (self.radius / 2)
        self.name           = f"{self.size}_{self.seed}"
        # Procedurally generate the asteroid
        self.map            = self.create_map(self.radius)
        geom                = self.create_geom(self.radius)
        self.np             = NodePath(geom)
        # NodePath tags used later, particulary in the collision functions
        self.np.setTag("size", self.size)
        self.np.setTag("radius", str(self.radius))
        
        # Create and add the colision mesh to the asteroid
        cNode = CollisionNode("asteroid")
        cNode.addSolid(CollisionSphere(0,0,0,self.radius + (self.radius / 4)))
        self.c_np = self.np.attachNewNode(cNode)
        

    def add_togame(self, spawn_location=False, future_location=False):
        # Set spawn location + final location + animation between the two
        if spawn_location:
            self.asteroid_path(spawn_location, future_location)
        else:
            spawn_distance      = self.translate((random.random() ** 0.5),0,1,asteroid_min_spawn_distance, asteroid_spawn_distance)
            self.asteroid_path(self.get_sphere_points(spawn_distance), future_location)
        # Show the asteorid to the player 
        self.np.reparent_to(render)

    def create_geom(self, sidelength):
        # Set up the vertex arrays
        vformat = GeomVertexFormat.getV3n3c4()
        vdata   = GeomVertexData("Data", vformat, Geom.UHDynamic)
        vertex  = GeomVertexWriter(vdata, 'vertex')
        normal  = GeomVertexWriter(vdata, 'normal')
        color   = GeomVertexWriter(vdata, 'color')
        geom    = Geom(vdata)

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
        for x in range(0, 181, self.step):
            #Top/Bottom of sphere need to be single points
            if x == 0:
                point_radius = self.simplex_radius(radius, self.seed, 0, 0, 1) 
                map[(0,0)] = (0,0,point_radius, (self.translate(point_radius, self.asteroid_min, self.asteroid_max, self.darkest_gray, self.lightest_gray)))
            elif x == 180:
                point_radius = -(self.simplex_radius(radius, self.seed, 0, 0, -1)) 
                map[(180,0)] = (0,0,point_radius, (self.translate(point_radius, -self.asteroid_min, -self.asteroid_max, self.darkest_gray, self.lightest_gray)))
            #The rest of the sphere
            else:
                for y in range(0, 361, self.step):
                    phi          = x * (math.pi / 180.)
                    theta        = y * (math.pi / 180.)
                    xoff         = math.sin(phi) * math.cos(theta)
                    yoff         = math.sin(phi) * math.sin(theta) 
                    zoff         = math.cos(phi)
                    point_radius = self.simplex_radius(radius, self.seed, xoff, yoff, zoff) 
                    v_x          = point_radius * xoff
                    v_y          = point_radius * yoff
                    v_z          = point_radius * zoff
                    map[(x ,y)]  = (v_x, v_y, v_z, (self.translate(point_radius, self.asteroid_min, self.asteroid_max, self.darkest_gray, self.lightest_gray)))
        return map 

    def asteroid_path(self, start_point, future_location=False): #takes starting location (start_point must be a LPoint3)
        # Create and run the asteroid animation
        if not(future_location):
            self.future_location = self.get_sphere_points(asteroid_future_distance, base.camera)
        else:
            self.future_location = future_location
        self.asteroid_lerp = LerpPosInterval(self.np, # Object being manipulated. The asteroid in this case.
                                            self.speed * random.randrange(1, self.speed_percent, 1), # How fast the asteroid will move in seconds
                                            self.future_location, # future location at end of lerp
                                            start_point) # The start position of the asteroid
        self.asteroid_lerp.start()

    def get_sphere_points(self, radius, relative_to=False): #returns a LPoint3 in sphere. relative_to will return global LPoint3 realtive to given object.
        phi = random.uniform(math.pi / 4,2*math.pi)
        theta = random.uniform(math.pi / 4,2*math.pi)
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
        self.obj = loader.loadModel("./Models/sphere.egg")
        self.obj.setY(asteroid_parent, distance)

class Missle(object):
    def __init__(self):
        camera_hpr = base.camera.getHpr()
        self.name = "missle"
        self.core = loader.loadModel("./Models/sphere.egg")
        self.ttl  = 1 # Time to live in seconds
        self.core.setPos(base.camera, (0,0,0))
        self.core.setHpr(camera_hpr)
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

        # Create hitsphere
        cNode = CollisionNode(self.name)
        cNode.addSolid(CollisionSphere(0,0,0,2))
        self.c_np = self.core.attachNewNode(cNode)

        # Create and run the missle animation
        location = Location(self.core).obj.getPos()
        self.asteroid_lerp = LerpPosInterval(self.core, # Object being manipulated. The missle in this case.
                                            2000, # How long it will take the missle to go from point a to b in seconds
                                            location, # future location at end of lerp
                                            base.camera.getPos(), # The start position of the missle
                                            fluid=1) # Allow for colisions during the lerp
        self.asteroid_lerp.start()
        del location

        self.core.reparentTo(render)

# Note to self. I can use self. in tasks to avoid having to use global variables

demo = Begin()
demo.run()