import struct
from math import degrees
import datetime

def hexstr(arr):
    return " ".join([format(ord(x), "02x") for x in arr])

class Frame(object):

    def __init__(self, raw_frame):
        self.body = raw_frame["body"]
        self.type = raw_frame["type"]

    def __repr__(self):
        return "<Frame %s: %s>" % (self.type, hexstr(self.body))


class PositionFrame(Frame):

    def __init__(self, raw_frame):
        super(PositionFrame, self).__init__(raw_frame)

        lon, lat, alt, x_speed, y_speed, z_speed, pitch, roll, yaw = struct.unpack_from('<ddhhhhhhh', self.body, 0)

        self.longitude = degrees(lon)
        self.latitude = degrees(lat)
        self.altitude = alt / 10.0
        self.x_speed = x_speed / 10.0
        self.y_speed = y_speed / 10.0
        self.z_speed = z_speed / 10.0
        self.pitch = pitch / 10.0
        self.roll = roll / 10.0
        self.yaw = yaw / 10.0 % 360

        self.__unknown = self.body[30:]

    def __repr__(self):
        return "<PositionFrame: (%.05f, %.05f), %4.01f m, %s, %s, %s, %s, %s, %s>" % (self.latitude, self.longitude, self.altitude, self.x_speed, self.y_speed, self.z_speed, self.pitch, self.roll, self.yaw)


class TimeFrame(Frame):

    def __init__(self, raw_frame):
        super(TimeFrame, self).__init__(raw_frame)

        # TODO: Work out first 2 bytes. Probably includes isVideo
        self.speed, self.distance, ts = struct.unpack_from("<ffQ", self.body, 2)

        self.timestamp = datetime.datetime.utcfromtimestamp(ts/1000.0)
        self.__unknown = self.body[:2]

        # Speed is m/s
        # Distance is in metres
        # Timestamp is unix time in ms

    def __repr__(self):
        return "<TimeFrame: %.02f m/s, %.01f m, %s>" % (self.speed, self.distance, self.timestamp)


class ControllerFrame(Frame):

    def __init__(self, raw_frame):
        super(ControllerFrame, self).__init__(raw_frame)

        aileron, elevator, throttle, rudder = struct.unpack_from("<HHHH", self.body, 0)

        self.aileron = aileron / 1024.0 - 1
        self.elevator = elevator / 1024.0 - 1
        self.throttle = throttle / 1024.0 - 1
        self.rudder = rudder / 1024.0 - 1

        self.__unknown = self.body[8:]

    def __repr__(self):
        return "<ControllerFrame: %.02f, %.02f, %.02f, %.02f>" % (self.throttle, self.rudder, self.elevator, self.aileron)


class GimbalFrame(Frame):

    def __init__(self, raw_frame):
        super(GimbalFrame, self).__init__(raw_frame)

        pitch, roll, yaw, self.__unknown1, self.__roll_adjust, self.__unknown2, self.__unknown3, self.__unknown4, self.__unknown5, self.__counter = struct.unpack_from("<hhhBBBBBBI", self.body, 0)

        self.gimbal_pitch = pitch / 10.0
        self.gimbal_roll = roll / 10.0
        self.gimbal_yaw = yaw / 10.0 % 360

    def __repr__(self):
        return "<GimbalFrame: %s, %s, %s, %s>" % (self.gimbal_pitch, self.gimbal_roll, self.gimbal_yaw, self.__counter)


class UnknownFrame(Frame):
    pass


with open("R:/Phantom/Fen Ditton/Evening 1/DJIFlightRecord_2016-06-18_[21-05-26].txt",'rb') as f:
    body = f.read()

__header = body[:12]
body = body[12:]
frames = []

i = 0
while i < len(body):
    frame_type = ord(body[i])
    frame_size = ord(body[i+1])
    frame_end = i+2+frame_size
    frame_body = body[i+2:frame_end]
    trailer = body[frame_end]
    if trailer != '\xff':
        # Probably the end of the file. Don't understand the final chunk yet.
        break

    i+= frame_size+3

    f = {
        "type": frame_type,
        "body": frame_body
    }

    if frame_type == 1:
        frames.append(PositionFrame(f))
    elif frame_type == 5:
        frames.append(TimeFrame(f))
    elif frame_type == 4:
        frames.append(ControllerFrame(f))
    elif frame_type == 3:
        frames.append(GimbalFrame(f))
    else:
        frames.append(UnknownFrame(f))


print "Parsed %d frames" % len(frames)

c = 0
for f in frames:
    if not isinstance(f, UnknownFrame):
        c += 1
        print f

print "Printed %s frames." % c