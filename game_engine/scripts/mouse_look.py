from bge import logic
from bge.logic import KX_INPUT_NONE, KX_INPUT_JUST_ACTIVATED, KX_INPUT_ACTIVE, KX_INPUT_JUST_RELEASED
from bge import render
from bge import events
from bge import types
from bge import constraints
from mathutils import Vector

from . import utilities
from .utilities import ANGLE_0, ANGLE_90, ANGLE_180, ANGLE_360, AXIS_Z
from math import cos, sin, acos

class MouseLook(types.KX_Camera):
    sensitivity = 0.001
    _error = 0.01
    upper_limit = ANGLE_180
    lower_limit = ANGLE_0

    speed = 0.15
    body_height = 0.2
    body_width = 1.6
    jump_speed = 1
    onground_time = 10
    jumping_time = 8
    def __init__(self, old_owner):
        types.KX_Camera.__init__(self)
        #render.showMouse(True)
        logic.mouse.position = .5, .5

        self.phys_id = self.parent.getPhysicsId()
        if self.phys_id:
            self.phys_parent = constraints.getCharacter(self.parent)
            #print(dir(self.phys_parent))
        else:
            self.phys_parent = None
        self.walk_direction = Vector()

        self.onground = 0
        self.jumping = 0

        self.init_touch_vectors()

    def init_touch_vectors(self):
        height = self.body_height / 2 + self._error
        width = self.body_width / 2
        self.touch_vectors = [Vector((0, 0, -height)),]
        radian = ANGLE_90
        for i in range(8):
            self.touch_vectors.append(
                Vector((cos(radian) * width, sin(radian) * width, -height)))
            radian += ANGLE_360 / 8

    def main(self):
        self.look()
        self.move()

    def look(self):
        sense = self.sensitivity
        x = round(0.5 - logic.mouse.position[0], 2) * sense \
                * render.getWindowWidth()
        y = round(0.5 - logic.mouse.position[1], 2) * sense \
                * render.getWindowHeight()

        laxis_z = self.localOrientation.transposed()[2]
        laxis_z.normalize()
        #laxis_z = self.getAxisVect(AXIS_Z)
        angle = acos(laxis_z.dot(AXIS_Z))
        upper_limit = self.upper_limit - self._error
        lower_limit = self.lower_limit + self._error
        if angle + y > upper_limit:
            y = upper_limit - angle
        elif angle + y < lower_limit:
            y = lower_limit - angle

        self.parent.applyRotation((0, 0, x), False)
        self.applyRotation((y, 0, 0), True)

        logic.mouse.position = .5, .5

    def move(self):
        key = logic.keyboard

        walk_direction = self.walk_direction
        walk_direction[:] = (0, 0, 0)
        speed = self.speed

        if key.events[events.WKEY]:
            walk_direction[1] += 1
        if key.events[events.SKEY]:
            walk_direction[1] -= 1
        if key.events[events.DKEY]:
            walk_direction[0] += 1
        if key.events[events.AKEY]:
            walk_direction[0] -= 1
        walk_direction.normalize()
        walk_direction *= speed

        phys_parent = self.phys_parent
        if phys_parent:
            walk_direction = self.parent.localOrientation * walk_direction
            phys_parent.walkDirection = walk_direction

            if key.events[events.SPACEKEY]:
                #parent.applyForce((0, 0, self.jump_power), True)
                phys_parent.jump()
        elif self.phys_id != 0:
            parent = self.parent

            if self.jumping:
                self.jumping -= 1
                if key.events[events.SPACEKEY]:
                    velocity = parent.getLinearVelocity(True)
                    velocity[2] += self.jump_speed
                    parent.setLinearVelocity(velocity, True)
            else:
                for vec in self.touch_vectors:
                    direction = parent.worldPosition + parent.getAxisVect(vec)
                    obj = parent.rayCastTo(direction, vec.length)
                    if obj:
                        self.onground = self.onground_time
                        break


                if self.onground:
                    self.onground -= 1
                    if key.events[events.SPACEKEY]:
                        velocity = parent.getLinearVelocity(True)
                        velocity[2] = max(velocity[2], self.jump_speed)
                        parent.setLinearVelocity(velocity, True)
                        self.onground = 0
                        self.jumping = self.jumping_time

            parent.applyMovement(walk_direction, True)
        else:
            if key.events[events.EKEY]:
                walk_direction[2] += speed
            if key.events[events.CKEY]:
                walk_direction[2] -= speed
            self.parent.applyMovement(walk_direction, True)


class MouseLookFoot(types.KX_GameObject):
    def __init__(self, old_owner):
        types.KX_GameObject.__init__(self)
        self.hit_objects = []
        self.collisionCallbacks.append(self._hit)
    def _hit(self, other):
        #self.hit_objects.append(other)
        print("UHO")

class MouseLook(types.KX_GameObject):
    sensitivity = 0.001
    _error = 0.01
    upper_limit = ANGLE_180
    lower_limit = ANGLE_0

    speed = 0.15
    body_height = 0.2
    body_width = 1.6
    jump_speed = 1.0
    jumping_time = 8
    jump_speed_max = 16.0
    onground_time = 10

    def __init__(self, old_owner):
        types.KX_GameObject.__init__(self)
        #render.showMouse(True)
        logic.mouse.position = .5, .5

        self.phys_id = self.getPhysicsId()
        if self.phys_id:
            self.phys_chara = constraints.getCharacter(self)
        else:
            self.phys_chara = None

        self.head = self.foot = None
        for c in self.children:
            if "HEAD" in c:
                self.head = c
            elif "FOOT" in c:
                self.foot = c
                self.foot_sensor = c.sensors["FOOT"]

        self.walk_direction = Vector()

        self.onground = 0
        self.jumping = 0

    def main(self):
        self.look()
        self.move()

    def look(self):
        sense = self.sensitivity
        x = round(0.5 - logic.mouse.position[0], 2) * sense \
                * render.getWindowWidth()
        y = round(0.5 - logic.mouse.position[1], 2) * sense \
                * render.getWindowHeight()

        head = self.head or self
        laxis_z = head.localOrientation.transposed()[2]
        laxis_z.normalize()
        #laxis_z = self.getAxisVect(AXIS_Z)
        angle = acos(laxis_z.dot(AXIS_Z))
        upper_limit = self.upper_limit - self._error
        lower_limit = self.lower_limit + self._error
        if angle + y > upper_limit:
            y = upper_limit - angle
        elif angle + y < lower_limit:
            y = lower_limit - angle

        self.applyRotation((0, 0, x), False)
        head.applyRotation((y, 0, 0), True)

        logic.mouse.position = .5, .5

    def move(self):
        key = logic.keyboard

        walk_direction = self.walk_direction
        walk_direction[:] = (0, 0, 0)
        speed = self.speed

        if key.events[events.WKEY]:
            walk_direction[1] += 1
        if key.events[events.SKEY]:
            walk_direction[1] -= 1
        if key.events[events.DKEY]:
            walk_direction[0] += 1
        if key.events[events.AKEY]:
            walk_direction[0] -= 1
        walk_direction.normalize()
        walk_direction *= speed

        phys_chara = self.phys_chara
        if phys_chara:
            walk_direction = self.localOrientation * walk_direction
            phys_chara.walkDirection = walk_direction

            if key.events[events.SPACEKEY]:
                #parent.applyForce((0, 0, self.jump_power), True)
                phys_chara.jump()
        elif self.phys_id != 0:
            if self.jumping:
                self.jumping -= 1
                if key.events[events.SPACEKEY]:
                    velocity = self.getLinearVelocity(True)
                    velocity[2] += self.jump_speed
                    if velocity[2] > self.jump_speed_max:
                        velocity[2] = self.jump_speed_max
                    self.setLinearVelocity(velocity, True)
            elif self.foot:
                if self.foot_sensor.hitObject:
                    self.onground = self.onground_time

                if self.onground:
                    self.onground -= 1
                    if key.events[events.SPACEKEY]:
                        velocity = self.getLinearVelocity(True)
                        velocity[2] = max(velocity[2], self.jump_speed)
                        self.setLinearVelocity(velocity, True)
                        self.onground = 0
                        self.jumping = self.jumping_time

            self.applyMovement(walk_direction, True)
        else:
            if key.events[events.EKEY]:
                walk_direction[2] += speed
            if key.events[events.CKEY]:
                walk_direction[2] -= speed
            self.applyMovement(walk_direction, True)

def register(cont):
    utilities.register(MouseLook, cont)
