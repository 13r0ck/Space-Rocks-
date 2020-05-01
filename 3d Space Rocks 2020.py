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
from direct.gui.DirectGui import (
    DirectFrame,
    DirectLabel,
    DirectButton)
from direct.showbase.Loader import Loader
import webbrowser

#Gameplay variables
asteroid_spawn_distance     = 3000000 # How close the asteroids spawn and how far away they will fly to
asteroid_min_spawn_distance = 100000
asteroid_future_distance    = asteroid_min_spawn_distance * 10 # How far the asteroid will travel
asteroid_total              = []
extra_smallasteroids        = []
extra_mediumasteroids       = []
missle_total                = []
pointball_total             = []
asteroid_max                = 300 # The maximum number of asteroids ***** MUST BE AN EVEN NUMBER  and make sur eto modify loop_test_number global variable*****
spaceship_speed_x           = 0
spaceship_speed_y           = 0
spaceship_speed_z           = 0
colors                      = {"orange": (.9,.6,.05,1),
                               "gray": (.1,.1,.1,1),
                                "black": (0,0,0,1),
                                "white": (1,1,1,1),
                                "white-transparent": (1,1,1,0.4),
                                "red": (0.4,0,0,0.4),
                                "red-transparent": (0.4,0,0,0.4),
                                "yellow-tinge": (1,1,0.8,1),
                                "yellow-tinge-transparent": (1,1,0.8,0.4),
                                "blue": (0, 0.8,1,1),
                                "blue-transparent": (0,0.6,0.8,0.3),
                                "lightblue-transparent": (0.6,0.6,0.8,0.3)}
asteroid_test_distance      = asteroid_spawn_distance * (29.0 / 30.0) #The test distance. If asteroid greater than asteroid_test_distancem then it will be moved closer
score                       = 0  # Initialize score
fullscreen                  = False
Frames                      = True
test_max_min                = [0,0,0,0]
max_player_speed            = 9000
pointball_value             = 0
title_screen                = None
is_living                   = True
resolution                  = (800,600)
cursor_hidden               = False
# Windows settings
loadPrcFileData('', 'window-title Space Rocks!')
thunderstrike = Loader.loadFont(0, "./Fonts/thunderstrike.ttf")
thunderstrike3d = Loader.loadFont(0, "./Fonts/thunderstrike3d.ttf")


class Begin(ShowBase):
    def __init__(self):
        global pointball_value
        global title_screen
        # Basics
        ShowBase.__init__(self)
        #Setup the window
        base.disableMouse()
        self.set_windowsettings()
        base.camLens.setFar(asteroid_spawn_distance * 100)
        self.setBackgroundColor(colors.get("black"))
        # Create the directional and ambient lights, and apply them to the world.
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((0.8, 0.8, 0.8, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(LVector3(0, 45, -45))
        directionalLight.setColor((1, 1, 1, 1))
        directionalLight.setShadowCaster(True)
        render.setLight(render.attachNewNode(directionalLight))
        render.setLight(render.attachNewNode(ambientLight))
        # Create a black fog and apply it to the world.
        self.fog = Fog('distanceFog')
        self.fog.setColor(0, 0, 0)
        self.fog.setExpDensity(.000001)
        render.setFog(self.fog)
        # Initialize Collisions
        base.cTrav = CollisionTraverser()
        base.cTrav.setRespectPrevTransform(True)
        self.collHandEvent = CollisionHandlerEvent()
        self.collHandEvent.addInPattern("%fn-into-%in")
        # Add colision sphere to player for losing state
        cNode = CollisionNode("player")
        cNode.addSolid(CollisionSphere(0, 0, 0, 3))
        self.player_np = base.camera.attachNewNode(cNode)
        base.cTrav.addCollider(self.player_np, self.collHandEvent)
        self.accept("player-into-asteroid", self.end_game)
        self.accept("player-into-pointball", self.score)
        # Setup initial score
        self.title = OnscreenText(text="Score: {0}".format(score),
                            parent=base.a2dTopLeft, scale=.07,
                            align=TextNode.ALeft, pos=(0.1,-0.1),
                            fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5),
                            font=thunderstrike)
        # Add Occluder Culling - I will need to figure this out later
        # occluder_model = self.loader.loadModel("./Models/cone_10vert.egg")
        # render.setOccluder(occluder_model)

        Begin.keyMap = {
                        "forward": False, "strafe-left": False, "backward": False, "strafe-right": False, "strafe-up": False, "strafe-down": False, "roll-left": False, "roll-right": False
                        } #True if coresponding key is currently held down.
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
        self.accept("shift", self.setKey, ["strafe-down", True])
        self.accept("shift-up", self.setKey, ["strafe-down", False])
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

        # Create the menu
        self.quality_name = "Low"
        self.quality_num = 1
        self.frameMain = DirectFrame(
            frameSize = (10,-10,10,-10),
            frameColor = (0, 0, 0, 1))

        self.menu_title = DirectFrame(
            frameSize = (base.a2dLeft, base.a2dRight, 0.55, 0.8),
            frameTexture = loader.loadTexture("./Fonts/title.png"),
            parent = self.frameMain
        )
        
        title_asteroid = Asteroid("small")
        self.menu_asteroid = DirectFrame(
            geom = title_asteroid.np,
            geom_scale = (0.000008,0.000008,0.000008),
            pos = (1.13,0,0.56),
            frameColor = (0,0,0,1),
            enableEdit = 1,
            parent = self.menu_title
        )
        
        title_screen = self.frameMain
        title_screen.menu_asteroid = self.menu_asteroid
        title_screen.start_btn = self.createButton("Start", self.start_game, 0.2)
        title_screen.how_to_btn = self.createButton("How to Play", self.how_to_play, 0)
        title_screen.exit_btn = self.createButton("Quit", sys.exit, -0.2)
        title_screen.res_apply_btn = self.createButton("Apply", self.apply_res_button, -0.4, 1, (-2,2.3,-0.6,1))
        title_screen.res_apply_btn.hide()
        title_screen.resolution_btn = self.createButton(f"Resolution ({resolution[0]} x {resolution[1]})", self.resolution, -0.4)
        title_screen.fullscreen_btn = self.createButton("Toggle Fullscreen", self.fullscreenToggle, -0.6)
        title_screen.quality_btn = self.createButton(f"Qualilty ({self.quality_name})", self.quality, -0.8)
        title_screen.qual_apply_btn = self.createButton("Apply", self.apply_res_button, -0.8, 1, (-2,2.3,-0.6,1))
        title_screen.qual_apply_btn.hide()
        taskMgr.add(Begin.menu, "Menu")

        # Setup game tasks and create the 3d asteroids.
        #self.createAsteroids()


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

    def start_game(self):
        global pointball_value
        # Set mouse and display settings
        self.lastMouseX, self.lastMouseY = 0, 0
        cursor_hidden = True
        self.set_windowsettings()
        self.startTasks()
        # Hide the main Menu
        self.frameMain.hide()
        # Change what the escape key does
        self.accept("escape", self.pause)
        pointball_value = int(time.time())

    def pause(self):
        global is_living
        global score
        pause_pointball_value = pointball_value
        # Show + relase the mouse
        self.frameMain.show()
        cursor_hidden = True
        self.set_windowsettings()
        taskMgr.remove("Rotate player in hpr")
        self.acceptOnce("escape", sys.exit)
        # Change start button text relative to living state + remove death dext if died
        if is_living:
            title_screen.start_btn["text"] = "Resume"
        else:
           aspect2d.find("**/-TextNode").removeNode()
           title_screen.start_btn["text"] = "Retry !"
           score = 0 
        #print(title_screen.start_btn)

    def quality(self):
        qual_dict = {
        # asteroid_number is chosen by 300 was found to be a good number when testing on a low spec machine. The larger ones keep the same density of asteroids as volume increases 
            1: {"quality": "Low",    "asteroid_detail": 36, "fog_quality": 0.000001,  "asteroid_spawn_distance": 3000000, "asteroid_number": 300},
            2: {"quality": "Medium", "asteroid_detail": 30, "fog_quality": 0.0000008, "asteroid_spawn_distance": 4000000, "asteroid_number": 711},
            3: {"quality": "High",   "asteroid_detail": 20, "fog_quality": 0.0000006, "asteroid_spawn_distance": 5000000, "asteroid_number": 1389},
        }
        self.quality_num = self.quality_num + 1 if self.quality_num != 3 else 1
        print(self.quality_num)
        quality = qual_dict[self.quality_num]
        self.quality_name           = quality["quality"]
        self.asteroid_detail        = quality["asteroid_detail"]
        self.fog_quality            = quality["fog_quality"]
        asteroid_spawn_distance     = quality["asteroid_spawn_distance"]
        asteroid_future_distance    = asteroid_min_spawn_distance * 10
        asteroid_test_distance      = asteroid_spawn_distance * (29.0 / 30.0)
        asteroid_max                = quality["asteroid_number"]
        text = f"Quality ({self.quality_name})"
        title_screen.quality_btn["text"] = (text, text, f" {text}!", text)
        title_screen.qual_apply_btn.show()

    def resolution(self):
        global resolution
        res_list = [
            # 4:3
            (800,600),
            (1024,768),
            (1920,1440),
            (4096,3071),
            # 5:4
            (1280,1024),
            # 16:9
            (1280,720),
            (1366,768),
            (1600,900),
            (1920,1080),
            (2560,1440),
            (3840,2160),
            (4096,2304),
            #16:10
            (1440,900),
            (1680,1050),
            (2304,1440),
            (4096,2560),
            # 21:9
            (2160,1080),
            (3440,1440)
        ]
        index = res_list.index(resolution)
        
        resolution = res_list[index + 1] if index < len(res_list) - 1 else res_list[0]
        if base.getSize() == resolution:
            title_screen.res_apply_btn.hide()
        else:
            title_screen.res_apply_btn.show()
        text = f"Resolution ({resolution[0]} x {resolution[1]})" 
        title_screen.resolution_btn["text"] = (text, text, f" {text}!", text)

    def apply_res_button(self):
        title_screen.res_apply_btn.hide()
        self.set_windowsettings()

    def how_to_play(self):
        webbrowser.open('https://github.com/13r0ck/3d-Space-Rocks-Simulator-2020')

    def createButton(self, text, command, verticalPos, horisontalPos=0, frame_size=(-8,8,-0.6,1)):
        btn = DirectButton(
            text=(text, text, f" {text}!", text),
            text_fg=(1,1,1,1),
            pad=(0.7,0.3),
            frameSize=frame_size,
            frameTexture="./Images/Button_Frame.png",
            relief=1,
            text_font=thunderstrike,
            text_scale=0.9,
            scale = 0.1,
            command = command,
            pos = (horisontalPos,0, verticalPos)
        )
        btn.reparentTo(self.frameMain)
        return btn

    def startTasks(self):
        #The tasks below are the functions run every frame so the game will work
        taskMgr.add(Begin.test_distance, "Test Distance")
        taskMgr.add(self.mouseTask, "Rotate player in hpr")
        taskMgr.add(Begin.spaceship_movement, "Move the Player in xyz")
        taskMgr.add(Begin.remove_old_missles, "Remove old missles")
        taskMgr.add(Begin.pointballManager, "Pointballs Manager")
        

    def menu(self):
        h,p,r = title_screen.menu_asteroid["geom_hpr"]
        title_screen.menu_asteroid["geom_hpr"] = LVecBase3f(h + 2.5, 0,0)
        return Task.cont

    ##### // Key Press Functions \\ #####
    def spaceship_movement(self):
        global spaceship_speed_x
        global spaceship_speed_y
        global spaceship_speed_z
        global max_player_speed
        # Move the player on the global axis. This is how momentum is not interupted
        cam_pos_init = base.camera.getPos()
        base.camera.setPos(cam_pos_init[0] + spaceship_speed_x, # Spaceship X change per frame
                            cam_pos_init[1] + spaceship_speed_y, # Spaceship Y change per frame
                            cam_pos_init[2] + spaceship_speed_z) #   "       Z   "     "    "
        # Ff a key is pressed, then we will need to do other calulations this frame.
        if Begin.keyMap["forward"] or Begin.keyMap["backward"] or Begin.keyMap["strafe-left"] or Begin.keyMap["strafe-right"] or Begin.keyMap["strafe-up"] or Begin.keyMap["strafe-down"]:
            local_x, local_y, local_z = 0, 0, 0
            cam_pos1 = base.camera.getPos()
            # Add aribitraty movement on the local axis relative to the key pressed.
            if Begin.keyMap["forward"]:
                local_x += 10
            if Begin.keyMap["backward"]:
                local_x -= 10
            if Begin.keyMap["strafe-right"]:
                local_y += 10
            if Begin.keyMap["strafe-left"]:
                local_y -= 10
            if Begin.keyMap["strafe-up"]:
                local_z += 10
            if Begin.keyMap["strafe-down"]:
                local_z -= 10
            base.camera.setPos(base.camera, local_y, local_x, local_z)
            cam_pos2 = base.camera.getPos()
            #Calculate the global velocity change from the local change
            # Note: dv_xyz delta velocity xyz
            dv_xyz = []
            dt = globalClock.getDt()
            dv_xyz = [(cam_pos2[i] - cam_pos1[i]) / dt for i in range(0,3)]
            # Calcualte the magnitude to limit player speed
            mag = math.sqrt((spaceship_speed_x)**2 + (spaceship_speed_y)**2 + (spaceship_speed_z)**2)
            if mag < max_player_speed:
                spaceship_speed_x += dv_xyz[0]
                spaceship_speed_y += dv_xyz[1]
                spaceship_speed_z += dv_xyz[2]
            else:
                possible_x, possible_y, possible_z = spaceship_speed_x, spaceship_speed_y, spaceship_speed_z
                possible_x += dv_xyz[0]
                possible_y += dv_xyz[1]
                possible_z += dv_xyz[2]
                possible_mag = math.sqrt((possible_x)**2 + (possible_y)**2 + (possible_z)**2) 
                if possible_mag < mag:
                    spaceship_speed_x += dv_xyz[0]
                    spaceship_speed_y += dv_xyz[1]
                    spaceship_speed_z += dv_xyz[2]
        # Separate from the top movement. Allow for camera rotation    
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

    def do_null(self):
        # Redefine the accept key to this to ignore key
        pass

    ##### // Tasks \\ #####
    def score(self, collision_entry):
        global score
        global thunderstrike
        pointball = collision_entry.getIntoNodePath().parent
        score += int(pointball.getTag("value"))
        render.clearLight(pointball.find("**/plight"))
        pointball.removeNode()
        self.title.clearText()
        self.title = OnscreenText(text="Score: {0}".format(score),
                            parent=base.a2dTopLeft, scale=.07,
                            align=TextNode.ALeft, pos=(0.1,-0.1),
                            fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5),
                            font=thunderstrike)
        return Task.cont

    # Test the distance of all asteroids. If the asteroid is too far away turn it around.
    def test_distance(self): 
        global asteroid_max
        global asteroid_test_distance
        for asteroid in asteroid_total:
            if asteroid.ttl > 0:
                asteroid.ttl -= globalClock.getDt()
            else:
                asteroid_xyz = asteroid.np.getPos()
                camera_xyz = base.camera.getPos()
                distance = math.sqrt((asteroid_xyz[0] - camera_xyz[0])**2 + (asteroid_xyz[1] - camera_xyz[1])**2 + (asteroid_xyz[2] - camera_xyz[2])**2) # Distance formula
                if distance > asteroid_test_distance: 
                    start_point = asteroid.get_sphere_points(asteroid_spawn_distance, base.camera)
                    asteroid.asteroid_lerp.finish()
                    asteroid.asteroid_path(start_point) #move to sphere relative to camera
                    asteroid.ttl = 1
                    #asteroid.c_np.show()
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

        # rotate camera by delta
        base.camera.setH(base.camera, dx * -60)
        base.camera.setP(base.camera, dy * 60)
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

    def pointballManager(self):
        global pointball_total
        dt = globalClock.getDt() # delta t per frame
        for pointball in pointball_total:
            # Animate the size
            scale_xyz = pointball.one.getScale()
            time = pointball.ttl_max - pointball.ttl
            dampened_cos = pointball.max_size * math.exp(0.36 * -time) * math.cos(0.5 * math.pi * time)
            dampened_sin = pointball.max_size * math.exp(0.36 * -time) * math.sin(0.5 * math.pi * time)
            pointball.one.setScale(dampened_cos, dampened_cos, dampened_cos)
            pointball.two.setScale(dampened_sin, dampened_sin, dampened_sin)
            # Move towards player if in range
            try:
                if pointball.center.getDistance(base.camera) < pointball.attraction_distance:
                    cam_2_ball = pointball.center.getPos(base.camera)
                    total = cam_2_ball[0] + cam_2_ball[1] + cam_2_ball[2]
                    percent_xyz = [cam_2_ball[i] / total for i in range(0, 3)]
                    pointball.center.setPos(base.camera,
                                            cam_2_ball[0] - 20000 * percent_xyz[0],
                                            cam_2_ball[1] - 20000 * percent_xyz[1],
                                            cam_2_ball[2] - 20000 * percent_xyz[2])
            except:
                pass
            # Remove Old PointBalls
            if pointball.ttl <= 0:
                render.clearLight(pointball.plnp)
                pointball.center.removeNode()
            else:
                pointball.ttl -= dt
        #for index in range(0,len(pointball_total)- 1):
        #    if pointball_total[index].ttl <= 0:
        #        del pointball_total[index]
        return Task.cont

    def death_task(self):
        camera_hpr = base.camera.getHpr()
        h_speed = float(base.camera.getTag("h_speed"))
        p_speed = float(base.camera.getTag("p_speed"))
        r_speed = float(base.camera.getTag("r_speed"))
        base.camera.setHpr(camera_hpr[0] + h_speed, camera_hpr[1] + p_speed, camera_hpr[2] + r_speed)
        base.camera.setX(base.camera.getX() + 1000)
        return Task.cont

    ##### // Colision Functions \\ #####
    def shot_asteroid(self, collision_entry):
        global score_list
        global pointball_total
        global pointball_value

        #Remove the missle
        missle = collision_entry.getFromNodePath()
        try:
            render.clearLight(missle.parent.find("**/plight"))
        except:
            pass
        missle.removeNode()
        # Gather large asteroid info so still accesable after deleted
        # Note: na is short for "new_asteroid", has is "hit_asteroid_size"
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
        if not(has == "small"):
            # Generate 2 asteroids at oposite poistions (shimmy) within the larger asteoid, and oposite directions
            for index in range(0,2):
                na = extra_smallasteroids.pop() if has == "medium" else extra_mediumasteroids.pop()
                # First asteroid can be random pos & direction
                if index == 0:
                    shimmy = [na.radius * random.randrange(-1,2,2), na.radius * random.randrange(-1,2,2), na.radius * random.randrange(-1,2,2)]
                    spawn_point = [hap[0] + shimmy[0], hap[1] + shimmy[1], hap[2] + shimmy[2]]
                    future_location = False
                # Second asteroid should be oposite pos & direction of asteroid 1
                else:
                    spawn_point = [hap[0] + shimmy[0] * -1, hap[1] + shimmy[1] * -1, hap[2] + shimmy[2] * -1]
                    future_location = LPoint3(future_location[0] * -1, future_location[1] * -1, future_location[2] * -1)
                # Add asteroid to the game. This code is the same for both asteroids
                pl3_spawn = LPoint3(spawn_point[0], spawn_point[1], spawn_point[2])
                na.add_togame(pl3_spawn, future_location)
                na.np.setTag("Created", "True")
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
            # Create the point ball
            current_time = int(time.time())
            new_pointball_value = max(100 - (current_time - pointball_value), 20)
            pointball = PointBall(hap, new_pointball_value)
            pointball_total.append(pointball)
            pointball_value = current_time
            base.cTrav.addCollider(pointball.c_np, self.collHandEvent)
            # Add a new asteroid to the scene to
            asteroid = Asteroid()
            asteroid_total.insert(0, asteroid)
            base.cTrav.addCollider(asteroid.c_np, self.collHandEvent)
            asteroid.add_togame(asteroid.get_sphere_points(asteroid_spawn_distance, base.camera))

    def end_game(self, collision_entry):
        global is_living
        is_living = False
        asteroid = collision_entry.getIntoNodePath()
        # Make the world red
        self.fog.setColor(0.5,0,0)
        self.fog.setExpDensity(.000001)
        self.setBackgroundColor(0.5,0,0,1)
        # Set random spin upon death. This is called in the death_task 
        base.camera.setTag("h_speed", str(random.randrange(0,1)))
        base.camera.setTag("p_speed", str(random.randrange(0,1)))
        base.camera.setTag("r_speed", str(random.uniform(0,0.5)))
        # Stop unused tasks in death
        taskMgr.remove("Rotate player in hpr")
        taskMgr.remove("Score")
        taskMgr.remove("Move the Player in xyz")
        self.accept('mouse1', self.do_null)
        # Move player and look so player gets to see their killer
        base.camera.setX(base.camera.getX() + int(asteroid.parent.getTag("radius")) * 2)
        base.camera.lookAt(asteroid)
        # Start the death spiral + death text
        taskMgr.add(Begin.death_task, "Death Spin")
        self.death_text = OnscreenText(text="Your Spaceship has Crashed !",
                            font=thunderstrike,
                            parent=base.aspect2d, scale=0.1,
                            align=TextNode.ACenter, pos=(0,0),
                            fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5))
        self.death_text.reparentTo(aspect2d)
        

    ##### // Developement Functions \\ #####
    def stop_moving(self):
        global spaceship_speed_x
        global spaceship_speed_y
        global spaceship_speed_z
        spaceship_speed_x = 0
        spaceship_speed_y = 0
        spaceship_speed_z = 0
        print(f"camera hpr {base.camera.getHpr()}")
        print(f"camera pos {base.camera.getPos()}")

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
        print("270,0,0")
        base.camera.setHpr(270,0,0)

    def angle5(self):
        print("0,-90,0")
        base.camera.setHpr(0,90,0)

    def angle6(self):
        print("0,90,0")
        print(base.camera.getHpr())
        base.camera.setHpr(0,-90,0)

    ##### // Misc Functions \\ #####
    def setKey(self, key, value):
        self.keyMap[key] = value

    def fullscreenToggle(self):
        global fullscreen
        global Frames
        if (not(fullscreen)):
            fullscreen = True
            self.set_windowsettings()
        else:
            fullscreen = False
            self.set_windowsettings()

    def set_windowsettings(self, reset_window=False):
        global fullscreen
        global cursor_hidden
        wp = WindowProperties()
        wp.setCursorHidden(cursor_hidden)
        base.setFrameRateMeter(Frames)
        wp.setFullscreen(fullscreen)
        wp.setSize(resolution)
        self.win.requestProperties(wp)
        if cursor_hidden:
            wp.setMouseMode(WindowProperties.M_relative)
        else:
            wp.setMouseMode(0)
        if reset_window:
            base.openMainWindow()
            base.graphicsEngine.openWindows()
        render.setAntialias(AntialiasAttrib.MAuto)

    def framesToggle(self):
        global Frames
        if(Frames):
            base.setFrameRateMeter(False)
            Frames = False
        else:
            base.setFrameRateMeter(True)
            Frames = True

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Scale value from input range to output range
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin
        valueScaled = float(value - leftMin) / float(leftSpan)
        return rightMin + (valueScaled * rightSpan)

class Asteroid(object):

    def __init__(self, size=False, step=36):
        types = {"large":  {"radius": 50000, "darkest_gray": 0.5, "lightest_gray": 0.8, "speed": 9000, "speed_percent": 5},
                 "medium": {"radius": 30000,  "darkest_gray": 0.6, "lightest_gray": 0.8, "speed": 180,  "speed_percent": 10},
                 "small":  {"radius": 10000,   "darkest_gray": 0.6, "lightest_gray": 0.8, "speed": 90,   "speed_percent": 20}}
        # Variables needed for the size given
        self.size           = random.choice(["small","medium","large"]) if not(size) else size
        self.radius         = types[self.size]["radius"]
        self.darkest_gray   = types[self.size]["darkest_gray"]
        self.lightest_gray  = types[self.size]["lightest_gray"]
        self.speed          = types[self.size]["speed"]
        self.speed_percent  = types[self.size]["speed_percent"]
        self.step           = step
        self.seed           = int(time.time() * 10000000)
        self.ttl            = 1 # time to live before getting distance tested
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
        self.np.setTag("Created", "False")
        self.np.setTag("Name", self.name)
        
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
                                            start_point, # The start position of the asteroid
                                            fluid=1)
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
        self.obj.setPos(asteroid_parent, spaceship_speed_x, spaceship_speed_y + distance, spaceship_speed_z)

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
        plight.setMaxDistance(1000)
        self.plnp = self.core.attachNewNode(plight) #point light node point
        render.setLight(self.plnp)

        # Create hitsphere
        cNode = CollisionNode(self.name)
        cNode.addSolid(CollisionSphere(0,0,0,1))
        self.c_np = self.core.attachNewNode(cNode)

        # Create and run the missle animation
        
        end_location = Location(self.core).obj.getPos()
        start_location = base.camera.getPos()
        start_location[0] += spaceship_speed_x
        start_location[1] += spaceship_speed_y
        start_location[2] += spaceship_speed_z
        """
        #Calcualte future distance
        cam_hpr = base.camera.getHpr()
        phi, theta = cam_hpr[0], Begin.translate(0, cam_hpr[1], -180,180,0,2*math.pi)
        phi *= math.pi / 180
        # component vecotrs
        x = asteroid_future_distance * math.cos(phi) * math.cos(theta)
        y = asteroid_future_distance * math.sin(phi) * math.cos(theta)
        z = asteroid_future_distance *  math.sin(theta)
        """

        self.asteroid_lerp = LerpPosInterval(self.core, # Object being manipulated. The missle in this case.
                                            2000, # How long it will take the missle to go from point a to b in seconds
                                            end_location, # future location at end of lerp
                                            start_location, # The start position of the missle
                                            fluid=1) # Allow for colisions during the lerp
        self.asteroid_lerp.start()
        del end_location

        self.core.reparentTo(render)

class PointBall(object):
    def __init__(self, position, value):
        #Invisiible point so that both spheres have the same parent
        self.name = "pointball"
        self.center = NodePath(PandaNode("Pointball center"))
        self.ttl = 15 #Time to live in seconds
        self.ttl_max = 15
        self.max_size = 9000
        self.attraction_distance = 900000
        self.center.setPos(position)
        self.center.setTag("value", str(value))
        # Create 1st sphere
        self.one = loader.loadModel("./Models/sphere.egg")
        self.one.setColor(colors.get("blue-transparent"))
        self.one.setScale(self.max_size,self.max_size,self.max_size)
        self.one.setLightOff()
        self.one.reparentTo(self.center)
        #Create 2nd sphere
        self.two = loader.loadModel("./Models/sphere.egg")
        self.two.setColor(colors.get("lightblue-transparent"))
        self.two.setScale(self.max_size,self.max_size,self.max_size)
        self.two.setLightOff()
        self.two.reparentTo(self.center)

        #Create the light so the missle glows
        plight = PointLight('plight')
        plight.setColor(colors.get("blue"))
        plight.setAttenuation(LVector3(0, 0.000006 , 0))
        plight.setMaxDistance(100)
        self.plnp = self.center.attachNewNode(plight) #point light node point
        render.setLight(self.plnp)

        # Create Collision hitsphere
        cNode = CollisionNode(self.name)
        cNode.addSolid(CollisionSphere(0,0,0,self.max_size * 20))
        self.c_np = self.center.attach_new_node(cNode)
        #Render to scene
        self.center.reparentTo(render)


# Note to self. I can use self. in tasks to avoid having to use global variables

demo = Begin()
demo.run()