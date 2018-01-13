from __future__ import print_function

import struct
from math import degrees
import datetime
import time
import os
import sys

old_ord = ord
def ord(x):
    if sys.version_info > (3,0,0):
        return x
    else:
        return old_ord(x)

def hexstr(arr):
    return " ".join([format(ord(x), "02x") for x in arr])

class Frame(object):

    def __init__(self, raw_frame):
        self.body = raw_frame["body"]
        self.type = raw_frame["type"]

    def __repr__(self):
        return "<Frame %s: %s>" % (self.type, hexstr(self.body))

# Basically done
class PositionFrame(Frame):

    def __init__(self, raw_frame):
        super(PositionFrame, self).__init__(raw_frame)

        lon, \
        lat, \
        ascent, \
        x_speed, \
        y_speed, \
        z_speed, \
        pitch, \
        roll, \
        yaw, \
        __fly_c_state, \
        _, \
        _, \
        self.satellites, \
        __flight_action, \
        __motor_start_failed_cause, \
        __non_gps_cause, \
        __battery, \
        __s_wave_height, \
        fly_time, \
        __motor_revolution, \
            = struct.unpack_from('<ddhhhhhhhhhhBBBBBBHH', self.body, 0)

        self.longitude = degrees(lon)
        self.latitude = degrees(lat)
        self.ascent = ascent / 10.0
        self.x_speed = x_speed / 10.0
        self.y_speed = y_speed / 10.0
        self.z_speed = z_speed / 10.0
        self.pitch = pitch / 10.0
        self.roll = roll / 10.0
        self.yaw = yaw / 10.0 % 360
        self.fly_time = fly_time / 10.0

    def __repr__(self):
        return "<PositionFrame: (%.05f, %.05f), %4.01f m, %s, %s, %s, %s, %s, %s, %s, %s>" % (self.latitude, self.longitude, self.ascent, self.x_speed, self.y_speed, self.z_speed, self.pitch, self.roll, self.yaw, self.satellites, self.fly_time)

# Basically done
class TimeFrame(Frame):

    def __init__(self, raw_frame):
        super(TimeFrame, self).__init__(raw_frame)

        # TODO: Work out first 2 bytes. Probably includes isVideo
        self.speed, self.distance, self.ts = struct.unpack_from("<ffQ", self.body, 2)

        self.timestamp = datetime.datetime.utcfromtimestamp(self.ts/1000.0)
        self.__unknown = self.body[:2]

        # Speed is m/s
        # Distance is in metres
        # Timestamp is unix time in ms

    def __repr__(self):
        return "<TimeFrame: %.02f m/s, %.01f m, %s>" % (self.speed, self.distance, self.timestamp)

# Basically done
class ControllerFrame(Frame):

    def __init__(self, raw_frame):
        super(ControllerFrame, self).__init__(raw_frame)

        aileron, elevator, throttle, rudder, _, _, _, _, _ = struct.unpack_from("<HHHHHBBBB", self.body, 0)

        self.aileron = aileron / 1024.0 - 1
        self.elevator = elevator / 1024.0 - 1
        self.throttle = throttle / 1024.0 - 1
        self.rudder = rudder / 1024.0 - 1

    def __repr__(self):
        return "<ControllerFrame: %.02f, %.02f, %.02f, %.02f>" % (self.throttle, self.rudder, self.elevator, self.aileron)

# Done
class GimbalFrame(Frame):

    def __init__(self, raw_frame):
        super(GimbalFrame, self).__init__(raw_frame)

        pitch, roll, yaw, \
        self.__mode, \
        self.__roll_adjust, \
        self.__yaw_angle, \
        self.__is_auto_calibration, \
        self.__auto_calibration_result, \
        self.__version, \
        self.__counter = struct.unpack_from("<hhhBBBBBBI", self.body, 0)

        self.pitch = pitch / 10.0
        self.roll = roll / 10.0
        self.yaw = yaw / 10.0 % 360

    def __repr__(self):
        return "<GimbalFrame: %s, %s, %s, %s>" % (self.pitch, self.roll, self.yaw, self.__counter)

# Always identical.
class HomeFrame(Frame):

    def __init__(self, raw_frame):
        super(HomeFrame, self).__init__(raw_frame)

        lat, lon, alt = struct.unpack_from("<ddf", self.body, 0)

        self._go_home_height, = struct.unpack_from("<H", self.body, 30)

        self.latitude = degrees(lat)
        self.longitude = degrees(lon)
        self.pressure_altitude = alt / 10 # See https://en.wikipedia.org/wiki/Pressure_altitude

        self.pressure = 1013.25 * ((1-(self.pressure_altitude/44307.69396))**5.2553)

    def __repr__(self):
        return "<HomeFrame: %s, %s, %s, %s>" % (self.latitude, self.longitude, self.pressure_altitude, self.pressure)



# Always one byte. 0x20 or 0xa0.
class Frame6(Frame):
    pass

# Basically done.
class BatteryFrame(Frame):

    def __init__(self, raw_frame):
        super(BatteryFrame, self).__init__(raw_frame)

        self.percent, \
        current_pv, \
        self.current_capacity, \
        self.total_capacity, \
        self.life, \
        self.loop_num, \
        self.error_type, \
        current, \
        voltage_cell_1, \
        voltage_cell_2, \
        voltage_cell_3, \
        voltage_cell_4, \
        voltage_cell_5, \
        voltage_cell_6, \
        self.serial_no, \
        _date, \
        temperature = struct.unpack_from("<BHHHBIHhHHHHHHHHH", self.body, 0)

        self.current_pv = current_pv / 1000.0
        self.current = current / 1000.0
        self.voltages = [voltage_cell_1 / 1000.0, voltage_cell_2 / 1000.0, voltage_cell_3 / 1000.0, voltage_cell_4 / 1000.0, voltage_cell_5 / 1000.0, voltage_cell_6 / 1000.0]
        self.manufacture_date = datetime.date((ord(self.body[-4]) >> 1) + 1980,((ord(self.body[-4]) & 0x1) << 3) | (ord(self.body[-5]) >> 5),ord(self.body[-5]) & 0x1f)
        self.temperature = temperature / 10 - 273.15

    def __repr__(self):
        return "<BatteryFrame: %s %s %s %s %s %s %s %s %s %s %s %s>" % (self.percent,
                                                                                self.current_pv,
                                                                                self.current_capacity,
                                                                                self.total_capacity,
                                                                                self.life,
                                                                                self.loop_num,
                                                                                self.error_type,
                                                                                self.current,
                                                                                self.voltages,
                                                                       self.serial_no,
                                                                       self.manufacture_date,
                                                                       self.temperature)

# Basically done
class SmartBatteryFrame(Frame):

    def __init__(self, raw_frame):
        super(SmartBatteryFrame, self).__init__(raw_frame)

        self.useful_time, \
        self.go_home_time, \
        self.land_time, \
        self.go_home_battery, \
        self.land_battery, \
        __safe_fly_radius, \
        __volume_consume, \
        __status, \
        __go_home_status, \
        __go_home_countdown, \
        voltage, \
        self.percent, \
        self.low_warning, \
            = struct.unpack_from("<HHHHHffHHHHBB", self.body, 0)

        self.voltage = voltage / 1000.0

    def __repr__(self):
        return "<SmartBatteryFrame: %s %s %s %s %s %s %s %s>" % (self.useful_time,
                                                                 self.go_home_time,
                                                                 self.land_time,
                                                                 self.go_home_battery,
                                                                 self.land_battery,
                                                                 self.voltage,
                                                                 self.percent,
                                                                 self.low_warning)


class MessageFrame(Frame):

    def __init__(self, raw_frame):
        super(MessageFrame, self).__init__(raw_frame)

        self.message = struct.unpack("%ss" % len(self.body), self.body)

    def __repr__(self):
        return "<MessageFrame: '%s'>" % (self.message)


# Always entirely zero
class Frame11(Frame):
    pass


# Done
class AircraftFrame(Frame):
    def __init__(self, raw_frame):
        super(AircraftFrame, self).__init__(raw_frame)

        self.drone_type, \
        self.app_type, \
        app_version_1, \
        app_version_2, \
        app_version_3, \
        self.aircraft_serial_no, \
        aircraft_name, \
        active_timestamp, \
        self.camera_serial_no, \
        self.controller_serial_no, \
        self.battery_serial_no, \
            = struct.unpack_from("<BBBBB10s32sQ10s10s10s", self.body)

        self.app_version = [app_version_1, app_version_2, app_version_3]
        self.aircraft_name = aircraft_name.replace("\0","")
        self.active_timestamp = time.ctime(active_timestamp)

    def __repr__(self):
        return "<AircraftFrame: %s %s %s %s %s %s %s %s %s>" % (self.drone_type,
                                                                      self.app_type,
                                                                      self.app_version,
                                                                      self.aircraft_serial_no,
                                                                      self.aircraft_name,
                                                                      self.active_timestamp,
                                                                      self.camera_serial_no,
                                                                      self.controller_serial_no,
                                                                      self.battery_serial_no)



# Not many, not long. All identical. No idea.
class Frame15(Frame):
    pass


class UnknownFrame(Frame):
    pass

class EmptyFrame(Frame):

    def __init__(self, **kwargs):
        super(EmptyFrame, self).__init__({
            "body": None,
            "type": None
        })

        self.__dict__.update(kwargs)

    def __getattr__(self, item):
        return ""

    def __repr__(self):
        return "<EmptyFrame>"

def decode_buffer(f):
    body = f['body']


def decode_file(path):

    with open(path,'rb') as f:
        body = f.read()

    __header = body[:100]
    body = body[100:]
    frames = []
    print("Body len: %d" % len(body))

    i = 0
    while i < len(body):
        frame_type = ord(body[i])
        frame_size = ord(body[i+1])
        frame_end = i+2+frame_size
        frame_body = body[i+2:frame_end]
        trailer = body[frame_end]
        if trailer != 0xff:
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
        elif frame_type == 2:
            frames.append(HomeFrame(f))
        elif frame_type == 6:
            frames.append(Frame6(f))
        elif frame_type == 7:
            frames.append(BatteryFrame(f))
        elif frame_type == 8:
            frames.append(SmartBatteryFrame(f))
        elif frame_type == 9:
            frames.append(MessageFrame(f))
        elif frame_type == 11:
            frames.append(Frame11(f))
        elif frame_type == 13:
            frames.append(AircraftFrame(f))
        elif frame_type == 15:
            frames.append(Frame15(f))
        else:
            frames.append(UnknownFrame(f))


    print("Parsed %d frames" % len(frames))

    return frames

if __name__ == "__main__":
    path = "R:\Phantom\Log Test\Loft 2\DJIFlightRecord_2016-06-25_[13-10-22].txt" #folder + "\\" + f

    frames = decode_file(path)

    for f in frames:
        if isinstance(f, HomeFrame):
            print(f)
            break

