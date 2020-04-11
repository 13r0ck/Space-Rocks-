#!/usr/bin/env python

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

# This is only needed on Linux with AMD cards, as they don't deal
# well with Cg shaders currently.
from panda3d.core import loadPrcFileData
loadPrcFileData('init', 'basic-shaders-only #t')


class BrownianBlender(ShowBase):
    def __init__(self):
        # Basics
        ShowBase.__init__(self)
        #base.disableMouse()
        base.setFrameRateMeter(True)
        self.accept("escape", sys.exit)
        self.camera.set_pos(-10, -10, 10)
        self.camera.look_at(0, 0, 0)
        self.render.setShaderAuto()
        render.setAntialias(AntialiasAttrib.MAuto) # Enable anti-aliasing
        self.setBackgroundColor(0,0,0,0)
        # Lighta
        #ambientLight = AmbientLight("ambientLight")
        #ambientLight.setColor((0.5, 0.5, 0.5, 1))
        #directionalLight = DirectionalLight("directionalLight")
        #directionalLight.setDirection(LVector3(0, 45, -45))
        #directionalLight.setColor((1, 1, 1, 1))
        #directionalLight.setShadowCaster(True)
        #render.setLight(render.attachNewNode(directionalLight))
        #render.setLight(render.attachNewNode(ambientLight))

        # Light
        light = Spotlight('light')
        light_np = self.render.attachNewNode(light)
        light_np.set_pos(50, 50, 50)
        light_np.look_at(0, 0, 0)
        # Model-light interaction
        #light.setShadowCaster(True)
        #light.getLens().setNearFar(1, 10)
        self.render.setLight(light_np)

        # Create the geometry
        asteroid = Asteroid()

class Asteroid(object):
    def __init__(self, step=1, radius=100):
        #Step for creating the sphere, lower the number greater the detail of the shpere
        self.step =  step
        self.radius = radius
        self.map = self.create_map(self.radius)
        self.asteroid_min = 10
        self.asteroid_max = 15
        print("map created")
        geom = self.create_geom(self.radius)
        print("geom created")
        np = NodePath(geom)
        print("nodepath created")
        np.reparent_to(render)


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
        print("top created")
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
        print("middle created")
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
        return self.translate(noise.noise3d(xoff,yoff,zoff),0,1,10,15)
        #return radius

    #map for most of the sphere
    def create_map(self, radius):
        map = collections.OrderedDict()
        seed = int(time.time())
        for x in range(0, 181, self.step):
            #Top/Bottom of sphere need to be single points
            if x == 0:
                point_radius = self.simplex_radius(radius, seed, 0, 0, 1) 
                map[(0,0)] = (0,0,point_radius, (self.translate(point_radius, 10, 15, 0.3, 0.5)))
            elif x == 180:
                point_radius = -(self.simplex_radius(radius, seed, 0, 0, -1)) 
                map[(180,0)] = (0,0,point_radius, (self.translate(point_radius, -10, -15, 0.3, 0.5)))
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
                    map[(x ,y)] = (v_x, v_y, v_z, (self.translate(point_radius, 10, 15, 0.3, 0.5)))
                    #print(map[(x,y)])
        return map 


demo = BrownianBlender()
demo.run()