'''
Created on Jul 11, 2016

@author: Gus
'''

from math import sin, cos
import sys
import time
from direct.showbase.ShowBase import ShowBase

from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState
from direct.gui.OnscreenText import OnscreenText 
from direct.gui.DirectGui import * 
from pandac.PandaModules import *

from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight
from panda3d.core import Vec3
from panda3d.core import Vec4
from panda3d.core import Point3
from panda3d.core import BitMask32
from panda3d.core import NodePath
from panda3d.core import PandaNode
from panda3d.core import *

from panda3d.bullet import BulletWorld
from panda3d.bullet import BulletHelper
from panda3d.bullet import BulletPlaneShape
from panda3d.bullet import BulletBoxShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletDebugNode
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletCapsuleShape
from panda3d.bullet import BulletCharacterControllerNode
from panda3d.bullet import BulletHeightfieldShape
from panda3d.bullet import BulletTriangleMesh
from panda3d.bullet import BulletTriangleMeshShape
from panda3d.bullet import BulletSoftBodyNode
from panda3d.bullet import BulletSoftBodyConfig
from panda3d.bullet import ZUp

class World(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        self.moving = False
        self.inAir = False
        self.gameState = False
        self.winLose = False
        self.diskCount = 0
        self.health = 100
        self.level = 1
        
        #Gui
        self.title = self.addTitle("I am Mr. Roboto")
        
        self.inst1 = self.addInstructions(1.50, "[ESC]: Quit")
        self.inst2 = self.addInstructions(1.56, "[A]: Rotate Mr. Roboto Left")
        self.inst3 = self.addInstructions(1.62, "[D]: Rotate Mr. Roboto Right")
        self.inst4 = self.addInstructions(1.68, "[W]: Move Mr. Roboto Forwards")
        self.inst5 = self.addInstructions(1.74, "[S]: Move Mr. Roboto Backwards")
        self.inst6 = self.addInstructions(1.80, "[Q]: Rotate Camera Left")
        self.inst7 = self.addInstructions(1.86, "[E]: Rotate Camera Right")
        self.inst8 = self.addInstructions(1.92, "[Space]: Jump")
        
        self.score = OnscreenText(text='Disk: 0/5', style=1, fg=(1, 1, 1, 1), scale=.05,
                        shadow=(0, 0, 0, 1), parent=base.a2dTopLeft,
                        pos=(1.2, -.12), align=TextNode.ALeft)

        self.setupLights()
        # Input
        self.accept('escape', self.mainMenu)
        self.accept('r', self.doReset)
        self.accept('f3', self.toggleDebug)
        self.accept('space', self.doJump)

        inputState.watchWithModifiers('forward', 'w')
        inputState.watchWithModifiers('reverse', 's')
        inputState.watchWithModifiers('turnLeft', 'a')
        inputState.watchWithModifiers('turnRight', 'd')
        
        # Camera Controls
        self.keyMap = {"cam-left": 0, "cam-right": 0}
        self.accept("q", self.setKey, ["cam-left",1])
        self.accept("e", self.setKey, ["cam-right",1])
        self.accept("q-up", self.setKey, ["cam-left",0])
        self.accept("e-up", self.setKey, ["cam-right",0])
        
        # Task
        taskMgr.add(self.update, 'updateWorld')

        self.level1()
        
        
        self.setupDisks()
        self.setupHealth()
        
        base.setBackgroundColor(0.1, 0.1, 0.4, 1)
        base.setFrameRateMeter(True)
        base.disableMouse()
        base.camera.setPos(self.characterNP.getPos())
        base.camera.setHpr(self.characterNP.getHpr())
        base.camera.lookAt(self.characterNP)
        # Create a floater object.  We use the "floater" as a temporary
        # variable in a variety of calculations.
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)
            
            
        # Load sounds
        self.jumpSd = base.loader.loadSfx('sound/effects/jump.mp3')
        self.menuSd = base.loader.loadSfx('sound/effects/menu-pop.mp3')
        self.pickUpSd = base.loader.loadSfx('sound/effects/pickup.mp3')
        self.runningSd = base.loader.loadSfx('sound/effects/running.mp3')
        self.runningSd.setLoop(True)
        
        self.themeSong = base.loader.loadSfx('sound/music/sonic.mp3')
        self.themeSong.setLoop(True)
        self.themeSong.setVolume(0.2)
        self.themeSong.play()
        
        taskMgr.add(self.rotateDisks, 'rotateDisks')
        taskMgr.add(self.updateDisks, 'updateDisks')
        taskMgr.add(self.rotateHealth, 'rotateHealth')
        taskMgr.add(self.updateHealth, 'updateHealth')
        taskMgr.add(self.handleJump, 'handleJump')
        taskMgr.add(self.drainLife, 'drainLife')
        taskMgr.add(self.checkWinLose, 'checkWinLose')
        taskMgr.add(self.updateEnemy, 'updateEnemy')
      
        
    def setKey(self, key, value):
        self.keyMap[key] = value
        
    # Function to put instructions on the screen.
    def addInstructions(self, pos, msg):
        return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1), scale=.05,
                        shadow=(0, 0, 0, 1), parent=base.a2dTopLeft,
                        pos=(0.08, -pos - 0.04), align=TextNode.ALeft)

    # Function to put title on the screen.
    def addTitle(self, text):
        return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1), scale=.07,
                        parent=base.a2dBottomRight, align=TextNode.ARight,
                        pos=(-0.1, 0.09), shadow=(0, 0, 0, 1))
    
    # Pauses the game    
    def pause(self):
        if self.gameState == False:
            taskMgr.remove('updateWorld')
            self.gameState = True
        else:
            taskMgr.add(self.update, 'updateWorld')
            self.gameState = False
        
    def doExit(self, arg):
        if(arg):
            self.cleanup()
            sys.exit(1)
        else:
            taskMgr.add(self.update, 'updateWorld')
            self.gameState = False
            self.dialog.cleanup()

    def doReset(self):
        self.characterNP.setPos(10,10,10)

    def toggleDebug(self):
        if self.debugNP.isHidden():
            self.debugNP.show()
            self.playerCoord =  OnscreenText(text="", style=1, fg=(1, 1, 1, 1), scale=.07,
                        parent=base.a2dBottomRight, align=TextNode.ARight,
                        pos=(-0.1, 0.20), shadow=(0, 0, 0, 1))
        else:
            self.debugNP.hide()
            self.playerCoord.cleanup()

    def doJump(self):
        if self.character.isOnGround():
            self.actorNP.play('jump')
            
            self.jumpSd.play()
            self.runningSd.stop()
        
        self.character.setMaxJumpHeight(6.0)
        
        # Controls the height of the jump
        self.character.setJumpSpeed(10.0)
        self.character.doJump()

    def processInput(self, dt):
        speed = Vec3(0, 0, 0)
        omega = 0.0
        if inputState.isSet('forward'): 
            speed.setY( 12.0)
            if self.moving == False:
                self.moving = True
                if self.character.isOnGround():
                    self.actorNP.setPlayRate(1.50, 'run')
                    self.actorNP.loop('run')
                    self.runningSd.setPlayRate(1.0)
                    self.runningSd.setTime(1)
                    self.runningSd.play()
        
        elif inputState.isSet('reverse'): 
            speed.setY(-6.0)
            if self.moving == False:
                self.moving = True
                if self.character.isOnGround():
                    self.actorNP.setPlayRate(-0.75, 'run')
                    self.actorNP.loop('run')
                    self.runningSd.setPlayRate(0.5)
                    self.runningSd.play()
        else:
            if self.moving == True:
                self.moving = False
                if self.character.isOnGround():  
                    self.actorNP.loop('idle')
                    self.runningSd.stop()
                
        if inputState.isSet('left'):    speed.setX(-6.0)
        if inputState.isSet('right'):   speed.setX( 6.0)
        if inputState.isSet('turnLeft'):  omega =  120.0
        if inputState.isSet('turnRight'): omega = -120.0
        
        if (self.keyMap["cam-left"]!=0):
            base.camera.setX(base.camera, -40 * dt)
        if (self.keyMap["cam-right"]!=0):
            base.camera.setX(base.camera, +40 * dt)

        self.character.setAngularMovement(omega)
        self.character.setLinearMovement(speed, True)

    def update(self, task):
        
        dt = globalClock.getDt()
        self.processInput(dt)
        self.world.doPhysics(dt, 16, 1./240.)

        # If the camera is too far from ralph, move it closer.
        # If the camera is too close to ralph, move it farther.
        camvec = self.characterNP.getPos() - base.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if (camdist > 20.0):
            base.camera.setPos(base.camera.getPos() + camvec*(camdist-20))
            camdist = 20.0
        if (camdist < 5.0):
            base.camera.setPos(base.camera.getPos() - camvec*(5-camdist))
            camdist = 5.0

        self.camera.setZ(5 + self.characterNP.getZ())
        self.floater.setPos(self.characterNP.getPos())
        self.floater.setZ(self.characterNP.getZ() + 2.0)
        base.camera.lookAt(self.floater)
        
        #Prints character location in console DEBUGGING
        text  = 'X:' + str(self.characterNP.getX()) + ' Y: ' + str(self.characterNP.getY()) + ' Z:' + str(self.characterNP.getZ())
        if not self.debugNP.isHidden():
            self.playerCoord.setText(text)
            
        #print self.character.isOnGround()
  
        return task.cont

    def cleanup(self):
        self.world = None
        self.render.removeNode()

    def setupLights(self):
        # Light
        alight = AmbientLight('ambientLight')
        alight.setColor(Vec4(0.5, 0.5, 0.5, 1))
        alightNP = render.attachNewNode(alight)

        dlight = DirectionalLight('directionalLight')
        dlight.setDirection(Vec3(1, 1, -1))
        dlight.setColor(Vec4(0.7, 0.7, 0.7, 1))
        dlightNP = render.attachNewNode(dlight)

        render.clearLight()
        render.setLight(alightNP)
        render.setLight(dlightNP)

    def level1(self):

        # World
        self.debugNP = render.attachNewNode(BulletDebugNode('Debug'))
        self.debugNP.hide()
        
        #Create text on screen
        self.frame = DirectFrame(frameColor = (0 , 1 , 0 , 1), frameSize=(0.1,  0.1, -0.1, 0.1), pos=(-0.9, 0, 0.5))
        self.bar = DirectWaitBar(parent=self.frame, text="Power Remaining", value = self.health, pos=(0,.4,.4), scale= 0.4)

        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        self.world.setDebugNode(self.debugNP.node())
        
        # Set up skybox
        self.skybox = loader.loadModel('models/clouds/blue_sky_sphere/blue_sky_sphere.egg')
        self.skybox.reparentTo(render)
        
        # Modeled environment
        self.environ = loader.loadModel("models/square")      
        self.environ.reparentTo(render)
        self.environ.setPos(0,0,0)
        self.environ.setScale(1000,1000,1)
        
        #Regular texture for the plane
        self.stone_tex = loader.loadTexture("ModelCollection/EnvBuildingBlocks/layingrock/layingrock-c.jpg")
        self.environ.setTexture(self.stone_tex, 1)     
        
        #Normal-map texture for the plane
        self.normal = loader.loadTexture("ModelCollection/EnvBuildingBlocks/layingrock/layingrock-n.jpg")    
        self.ts = TextureStage('ts')
        self.ts.setMode(TextureStage.MNormal)
        
        #Dont know what happened here
        self.directionalLight = DirectionalLight( "directionalLight" )
        self.directionalLight.setColor( Vec4( 1, 1, 1, 1 ) )
        self.directionalLight.setDirection(Vec3(0, 0, -1))
        self.directionalLightNP = render.attachNewNode(self.directionalLight)
        
        self.environ.setLight(self.directionalLightNP)
        
        ts = TextureStage.getDefault()
        self.environ.setTexOffset(ts, -0.5, -0.5)
        self.environ.setTexScale(ts, 128, 128)
        
        self.environ.setTexture(self.ts, self.normal)
        self.environ.setShaderAuto()
        
        # Floor
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        floorNP = render.attachNewNode(BulletRigidBodyNode('Floor'))
        floorNP.node().addShape(shape)
        floorNP.setPos(0, 0, 0)
        floorNP.setCollideMask(BitMask32.allOn())
        self.world.attachRigidBody(floorNP.node())

        # Character
        h = 4
        w = 0.6
        shape = BulletCapsuleShape(w, h - 2 * w, ZUp)

        self.character = BulletCharacterControllerNode(shape, 0.4, 'Player')
        
        self.characterNP = render.attachNewNode(self.character)
        self.characterNP.setPos(0, 410, 0)
        self.characterNP.setH(180)
        self.characterNP.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.character)

        self.actorNP = Actor('ModelCollection/Actors/robot/lack.egg', {
                         'idle' : 'ModelCollection/Actors/robot/lack-idle.egg',
                         'run' : 'ModelCollection/Actors/robot/lack-run.egg',
                        'jump' : 'ModelCollection/Actors/robot/lack-jump.egg',
                         'land' : 'ModelCollection/Actors/robot/lack-land.egg'})

        self.actorNP.reparentTo(self.characterNP)
        self.actorNP.setScale(0.2)
        self.actorNP.setH(180)
        self.actorNP.setPos(0, 0, .5)
        
        # Start the character in the idle position
        self.actorNP.loop('idle')

        self.generateEnemy()
        self.generatePlatforms()
        self.generateLv1Walls()
    
    def level2(self):
        self.level = 2
        #reset Character
        self.positionCharacterLv2()
        
        #reset Disk count
        self.diskCount = 0
        text = 'Disk: ' + str(self.diskCount) + '/5'
        self.score.setText(text)
        
        self.b.destroy()
        #Load level 2 skybox
        self.skybox.removeNode()
        self.skybox = self.skybox = loader.loadModel('models/clouds/PeachSky/PeachSky.egg')
        self.skybox.reparentTo(render)         
        
        #Load level 2 environment
        self.environ.removeNode()
        
        #Load level 2 music
        self.themeSong.stop()
        self.themeSong = base.loader.loadSfx('sound/music/sonic2.mp3')
        self.themeSong.setLoop(True)
        self.themeSong.setVolume(0.2)
        self.themeSong.play()
        
        # Removes all level 1 platforms
        for i in self.platforms1:
            i.removeNode()
            
        for i in self.bulletPlatforms1:
            self.world.remove(i)
            
        for i in self.wallNP:
            self.world.remove(i)
        
        for i in self.wallModel:
            i.removeNode()
        
        #Generate floor:
        self.environ = loader.loadModel("models/square")      
        self.environ.reparentTo(render)
        self.environ.setPos(0,0,0)
        self.environ.setScale(1000,1000,1)
        
        #Regular texture for the plane
        self.stone_tex = loader.loadTexture("models/floor/CityTerrain/maps/M0CM1.tif")
        self.environ.setTexture(self.stone_tex, 1)   
        
        ts = TextureStage.getDefault()
        self.environ.setTexOffset(ts, -0.5, -0.5)
        self.environ.setTexScale(ts, 128, 128)    
        #Generate walls for level
        self.generateLv2Walls()
        self.generateEnemy2()
        self.setupDisks()
        
        taskMgr.remove('updateEnemy')
        taskMgr.add(self.updateEnemy2, 'updateEnemy2')
       
    def setupDisks(self):
        points = [Point3(30,365,3),Point3(-26,251,3),Point3(20,-90,3),Point3(-23,-208,3),Point3(-2,-368,3)]
        self.disks = []
        for i in range(5):
            self.disk = loader.loadModel("ModelCollection/EnvBuildingBlocks/disk/disk.egg")
            self.disk.reparentTo(self.render)
            self.disk.setHpr(0,0,90)
            self.disk.setScale(0.5,0.5,0.5)
            self.disk.setPos(points[i])
            self.disk.setTag("coin", "coin")
            self.disks.append(self.disk)
     
    # Rotates the disks in the level
    def rotateDisks(self, task):
        angleDegrees = task.time * 60.0
        for i in self.disks:
            i.setHpr(angleDegrees, 0, 90)
        
        return task.cont
    
    # Controls the character model when they are jumping
    def handleJump(self, task):
        
        result = self.world.contactTest(self.character)
        if result.getNumContacts() == 0:
            if self.inAir == False:
                self.inAir = True
        elif result.getNumContacts > 0:
            if self.inAir == True:
                self.inAir = False
                if self.moving == False:
                    self.actorNP.loop('idle')
                else:
                    self.actorNP.setPlayRate(1.50, 'run')
                    self.actorNP.loop('run')
                    self.runningSd.setPlayRate(1.0)
                    self.runningSd.setTime(1)
                    self.runningSd.play()
        
        return task.cont
    
    # When player grabs disk, updates score
    def updateDisks(self, task):
        pickup_radius = 5
        for i in self.disks:
            if self.actorNP.getDistance(i) < pickup_radius:
                # Player collected coin, increase score or so
                i.removeNode()
                self.disks.remove(i)
                self.diskCount = self.diskCount + 1
                self.pickUpSd.setTime(0.4)
                self.pickUpSd.play()
                text = 'Disk: ' + str(self.diskCount) + '/5'
                self.score.setText(text)
        
        return task.cont
    
    def setupHealth(self):
        points = [Point3(0,200,3),Point3(0,-200,3)]
        self.batteries = []
        for i in range(2):
            self.battery = loader.loadModel('models/clouds/health/Capsule/Capsule.egg')
            self.battery.reparentTo(self.render)
            self.battery.setScale(0.1)
            self.battery.setPos(points[i])
            self.battery.setTag("health", "health")
            self.batteries.append(self.battery)
            
    def rotateHealth(self, task):
        angleDegrees = task.time * 60.0
        for i in self.batteries:
            i.setHpr(angleDegrees, 0, 0)
        
        return task.cont
    
    def updateHealth(self, task):
        pickup_radius = 10
        for i in self.batteries:
            if self.actorNP.getDistance(i) < pickup_radius:
                # Player collected coin, increase score or so
                i.removeNode()
                self.batteries.remove(i)
                self.pickUpSd.setTime(0.4)
                self.pickUpSd.play()
                
                if self.health > 50:
                    self.health = 100
                else:
                    self.health = self.health + 50
        
        return task.cont
        
    def mainMenu(self):
        self.menuSd.play()
        if self.gameState == False:
            taskMgr.remove('updateWorld')
            taskMgr.remove('rotateDisks')
            self.actorNP.stop()
            self.dialog = YesNoDialog(dialogName = "MainMenu", text="Quit Game?", command= self.doExit)
            self.gameState = True
        else:
            taskMgr.add(self.update, 'updateWorld')
            taskMgr.add(self.rotateDisks,'rotateDisks')
            self.gameState = False
            self.dialog.cleanup()
     
    # Need to change it from bulletBodyNode to collision node       
    def generateEnemy(self):
        h = 4
        w = 0.6
        shape = BulletCapsuleShape(w, h - 2 * w, ZUp)
        
        points = [Point3(30, 300, 2), Point3(-30, 100, 2), Point3(30, -300, 2)]
        
        self.enemies = []
        self.enemiesNP = []
        self.enemiesModels = []
        for i in range(3):
            self.enemy =  BulletCharacterControllerNode(shape, 0.4, 'Enemy')
          
            self.enemyNP = self.render.attachNewNode(self.enemy)
            self.enemyNP.setPos(points[i])
            self.enemyNP.setH(45)
            
            self.enemies.append(self.enemy)
            
            # Can't get enemy to collide with character
            self.enemyNP.setCollideMask(BitMask32.allOn())
            self.world.attachCharacter(self.enemy)
            self.enemiesNP.append(self.enemyNP)
    
            self.enemyActorNP = Actor('ModelCollection/Actors/lego/SecurityGuard/SecurityGuard.egg', {
                             'walk' : 'ModelCollection/Actors/lego/SecurityGuard/SecurityGuard-walk.egg',
                             'run' : 'ModelCollection/Actors/lego/SecurityGuard/SecurityGuard-run.egg',
                             'jump' : 'ModelCollection/Actors/lego/SecurityGuard/SecurityGuard-jump.egg'})
    
            self.enemyActorNP.reparentTo(self.enemyNP)
            self.enemyActorNP.setScale(0.7)
            self.enemyActorNP.setH(180)
            self.enemyActorNP.setPos(0, 0, .4)
            self.enemiesModels.append(self.enemyActorNP)
            
            # Start the character in the idle position
            self.enemyActorNP.loop('run')
            
    def generateEnemy2(self):
        h = 4
        w = 0.6
        shape = BulletCapsuleShape(w, h - 2 * w, ZUp)
        
        points = [Point3(0, 360, 2), Point3(0, 150, 2), Point3(0, -350, 2)]
        
        for i in range(3):
            self.enemy =  BulletCharacterControllerNode(shape, 0.4, 'Enemy')
          
            self.enemyNP = self.render.attachNewNode(self.enemy)
            self.enemyNP.setPos(points[i])
            self.enemyNP.setH(45)
            
            self.enemies.append(self.enemy)
            
            # Can't get enemy to collide with character
            self.enemyNP.setCollideMask(BitMask32.allOn())
            self.world.attachCharacter(self.enemy)
            self.enemiesNP.append(self.enemyNP)
    
            self.enemyActorNP = Actor('ModelCollection/Actors/lego/SecurityGuard/SecurityGuard.egg', {
                             'walk' : 'ModelCollection/Actors/lego/SecurityGuard/SecurityGuard-walk.egg',
                             'run' : 'ModelCollection/Actors/lego/SecurityGuard/SecurityGuard-run.egg',
                             'jump' : 'ModelCollection/Actors/lego/SecurityGuard/SecurityGuard-jump.egg'})
    
            self.enemyActorNP.reparentTo(self.enemyNP)
            self.enemyActorNP.setScale(0.7)
            self.enemyActorNP.setH(180)
            self.enemyActorNP.setPos(0, 0, .4)
            self.enemiesModels.append(self.enemyActorNP)
            
            # Start the character in the idle position
            self.enemyActorNP.loop('run')
    
    def resetEnemies(self):
        points = [Point3(30, 300, 2), Point3(-30, 100, 2), Point3(30, -300, 2), Point3(20, 360, 2), Point3(-10, 150, 2), Point3(0, -350, 2)]
        
        if self.level == 1:
            for i in range(3):
                self.enemiesNP[i].setPos(points[i])
        else: 
            for i in range(6):
                self.enemiesNP[i].setPos(points[i])
            
    def updateEnemy(self, task):
        speed = Vec3(0, 0, 0)
        omega = 0.0
        radius = 30
        
        pursue = [False, False, False]
        
        for i in range(3):
            if self.characterNP.getDistance(self.enemiesModels[i]) < radius:
                pursue[i] = True
                self.enemiesModels[i].lookAt(self.characterNP)
                self.enemiesModels[i].setP(0)
                self.enemiesModels[i].setH(self.enemiesModels[i].getH() + 180)
                
        for i in self.enemiesNP:
            i.lookAt(self.characterNP)  
           
        for i in range(3):
            if pursue[i] == True:
                speed.setY( 11.0)
                self.enemies[i].setLinearMovement(speed, True)
            else:
                speed.setY(0)
                self.enemies[i].setLinearMovement(speed, True)
        
        
        return task.cont

    def updateEnemy2(self, task):
        speed = Vec3(0, 0, 0)
        omega = 0.0
        radius = 30
        
        pursue = [False, False, False, False, False, False]
        
        for i in range(6):
            if self.characterNP.getDistance(self.enemiesModels[i]) < radius:
                pursue[i] = True
                self.enemiesModels[i].lookAt(self.characterNP)
                self.enemiesModels[i].setP(0)
                self.enemiesModels[i].setH(self.enemiesModels[i].getH() + 180)
                
        for i in self.enemiesNP:
            i.lookAt(self.characterNP)  
           
        for i in range(6):
            if pursue[i] == True:
                speed.setY( 11.0)
                self.enemies[i].setLinearMovement(speed, True)
            else:
                speed.setY(0)
                self.enemies[i].setLinearMovement(speed, True)
        
        
        return task.cont
    
    def generatePlatforms(self):
        
        x = 0
        self.bulletPlatforms1 = []
        self.platforms1 = []
        for i in range(5):
            shape = BulletBoxShape(Vec3(20/2,20/2,0.1))
            self.node = BulletRigidBodyNode('Box')
            self.node.addShape(shape)
            
            self.platformNP = self.render.attachNewNode(self.node)
            self.platformNP.setPos(x, 30, 8)
            self.platformNP.setCollideMask(BitMask32.allOn())
            
            #Model for platform
            floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            floorModel.setScale(20, 20, 0.2)
            floorModel.setPos(x, 30, 8)
            floorModel.reparentTo(self.render) 
             
            # make the texture repeated     
            ts = TextureStage.getDefault()
            floorModel.setTexOffset(ts, -0.5, -0.5)
            floorModel.setTexScale(ts, 32, 16)    
            self.platforms1.append(floorModel)
            self.bulletPlatforms1.append(self.node)
            self.world.attachRigidBody(self.node)
            x = x + 50
      
    # Drains character's power periodically       
    def drainLife(self, task):
        self.health = self.health - .02
        
        takeDamageRadius = 3
        
        for i in self.enemiesModels:
            if self.characterNP.getDistance(i) < takeDamageRadius:
                self.health = self.health - 0.05
            
        self.bar['value'] = self.health
        return task.cont
    
    def checkWinLose(self, task):
        if self.diskCount == 5:
            if self.winLose == False:
                self.winLose = True
                if self.level == 1:
                    self.level = self.level + 1
                    self.b = DirectButton(text = ("LEVEL 1 COMPLETE!", "LEVEL 1 COMPLETE!", "LEVEL 1 COMPLETE!", "disabled"), scale=.1, command=self.level2)
                else:
                    self.b = DirectButton(text = ("LEVEL 2 COMPLETE!", "LEVEL 2 COMPLETE!", "LEVEL 2 COMPLETE!", "disabled"), scale=.1, command=self.quit)
        
        if self.health <= 0:
            if self.winLose == False:
                self.winLose = True
                taskMgr.remove('updateWorld')
                self.actorNP.stop()
                self.b = DirectButton(text = ("YOU LOSE", "YOU LOSE", "YOU LOSE", "disabled"), scale=.1, command=self.resetLoss)
            
        return task.cont
    
    def quit(self):
        self.cleanup()
        sys.exit(1)
     
    def resetLoss(self):
        self.winLose = False 
        taskMgr.add(self.update, 'updateWorld')
        self.b.destroy() 
        if self.level == 1:
            for i in self.batteries:
                i.removeNode()
                self.batteries.remove(i)
        self.setupHealth()
        self.resetEnemies() 
        self.characterNP.setPos(0,410,0)
        self.characterNP.setH(180)
        self.health = 100
        
    def positionCharacterLv2(self):
        self.winLose = False
        self.characterNP.setPos(0,400,0)
        self.health = 100
        
    def generateLv1Walls(self):
        # Back Walls
        self.wallNP = []
        self.wallModel = []
        x = -40
        for i in range(5):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, -440, 0)
            self.floorNodePath.setHpr(90,0,90)
            self.world.attachRigidBody(self.floorNode)
            
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, -440, 0)
            self.floorModel.setH(90)
            self.floorModel.reparentTo(self.render) 
            
            self.wallModel.append(self.floorModel)
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4) 
            x = x + 20
            
        # Left Walls
        x = -50
        y = -450
        for i in range(45):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, y, 0)
            self.floorNodePath.setHpr(0,0,90)
            self.world.attachRigidBody(self.floorNode)
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, y, 0)
            self.floorModel.setH(0)
            self.floorModel.reparentTo(self.render)
            self.wallModel.append(self.floorModel) 
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4) 
            y = y + 20
        
        # Right Walls
        x = 50
        y = -450
        for i in range(45):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, y, 0)
            self.floorNodePath.setHpr(0,0,90)
            self.world.attachRigidBody(self.floorNode)
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, y, 0)
            self.floorModel.setH(0)
            self.floorModel.reparentTo(self.render) 
            self.wallModel.append(self.floorModel)
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4) 
            y = y + 20
            
        x = -40
        y = 440
        for i in range(5):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, y, 0)
            self.floorNodePath.setHpr(90,0,90)
            self.world.attachRigidBody(self.floorNode)
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, y, 0)
            self.floorModel.setH(90)
            self.floorModel.reparentTo(self.render) 
            self.wallModel.append(self.floorModel)
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4) 
            x = x + 20
          
        # Middle wall that player needs to squeeze by
        x = -20
        for i in range(4):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, 0, 0)
            self.floorNodePath.setHpr(90,0,90)
            self.world.attachRigidBody(self.floorNode)
            
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, 0, 0)
            self.floorModel.setH(90)
            self.floorModel.reparentTo(self.render) 
            
            self.wallModel.append(self.floorModel)
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4)
            x = x + 20
    
    def generateLv2Walls(self): 
        # Back Walls
        self.wallNP = []
        self.wallModel = []
        x = -40
        for i in range(5):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, -440, 0)
            self.floorNodePath.setHpr(90,0,90)
            self.world.attachRigidBody(self.floorNode)
            
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, -440, 0)
            self.floorModel.setH(90)
            self.floorModel.reparentTo(self.render) 
            
            self.wallModel.append(self.floorModel)
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4) 
            x = x + 20
            
        # Left Walls
        x = -50
        y = -450
        for i in range(45):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, y, 0)
            self.floorNodePath.setHpr(0,0,90)
            self.world.attachRigidBody(self.floorNode)
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, y, 0)
            self.floorModel.setH(0)
            self.floorModel.reparentTo(self.render)
            self.wallModel.append(self.floorModel) 
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4) 
            y = y + 20
        
        # Right Walls
        x = 50
        y = -450
        for i in range(45):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, y, 0)
            self.floorNodePath.setHpr(0,0,90)
            self.world.attachRigidBody(self.floorNode)
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, y, 0)
            self.floorModel.setH(0)
            self.floorModel.reparentTo(self.render) 
            self.wallModel.append(self.floorModel)
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4) 
            y = y + 20
            
        x = -40
        y = 440
        for i in range(5):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, y, 0)
            self.floorNodePath.setHpr(90,0,90)
            self.world.attachRigidBody(self.floorNode)
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, y, 0)
            self.floorModel.setH(90)
            self.floorModel.reparentTo(self.render) 
            self.wallModel.append(self.floorModel)
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4) 
            x = x + 20
          
        # Middle wall that player needs to squeeze by
        x = -20
        for i in range(4):
            self.floorShape = BulletBoxShape(Vec3(20/2,20/2,0.5))
            self.floorNode = BulletRigidBodyNode('Floor')
            self.floorNode.addShape(self.floorShape)
            
            self.floorNodePath = self.render.attachNewNode(self.floorNode)
            self.floorNodePath.setPos(x, 0, 0)
            self.floorNodePath.setHpr(90,0,90)
            self.world.attachRigidBody(self.floorNode)
            
            self.wallNP.append(self.floorNode)
             
            # Back Wall Model
            self.floorModel = self.loader.loadModel("ModelCollection/EnvBuildingBlocks/brick-cube/brick")
            self.floorModel.setScale(1, 20, 10)
            self.floorModel.setPos(x, 0, 0)
            self.floorModel.setH(90)
            self.floorModel.reparentTo(self.render) 
            
            self.wallModel.append(self.floorModel)
            
            #make the texture repeated     
            ts = TextureStage.getDefault()
            self.floorModel.setTexOffset(ts, -0.5, -0.5)
            self.floorModel.setTexScale(ts, 4, 4)
            x = x + 20  
        
game = World()
game.run()

#jump.mp3, menu-pop.mp3 found at soundbible.com
#running.mp3 found at https://www.youtube.com/watch?v=ynFCGUEkrk8
#Theme song found at https://www.youtube.com/watch?v=yRuJfhEeCe8&index=3&list=RDTVEyGntyOZQ
#Theme song for level 2 found at https://www.youtube.com/watch?v=RCcJnffie48
#Pick up sound found at https://www.youtube.com/watch?v=Mh2GQmfN-AI
#Floor for level 2 found at http://alice.org/pandagallery/Environments/index.html
#skybox model found at http://alice.org/pandagallery/Environments/Skies/index.html blue_sky_sphere
#Skybox model for level 2 found at http://alice.org/pandagallery/Environments/Skies/index.html PeachSky
