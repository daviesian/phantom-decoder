import decoder
import os
import sys
import googlemaps
import private # This file must contain maps_api_key

# Replace the API key below with a valid API key.
gmaps = googlemaps.Client(key=private.maps_api_key)

class Bunch:
    def __init__(self, **kwdict):
        self.__dict__.update(kwdict)


def frames_to_lines(frames):

    last_frames = {
        "SmartBatteryFrame": decoder.EmptyFrame(),
        "BatteryFrame": decoder.EmptyFrame(voltages = [""]*6),
        "MessageFrame": decoder.EmptyFrame()
    }
    lines = [
        ",".join(["latitude", "longitude", "altitude(metres)", "ascent(metres)",
                  "speed(m/s)", "distance(metres)", "time(millisecond)", "datetime(utc)",
                  "satellites",
                  "voltage(v)",
                  "max_altitude(metres)", "max_ascent(metres)", "max_speed(m/s)", "max_distance(metres)",
                  "compass_heading(degrees)",
                  "isPhoto", "isVideo", "rc_elevator", "rc_aileron", "rc_throttle", "rc_rudder",
                  "gimbal_heading(degrees)", "gimbal_pitch(degrees)",
                  "battery_percent", "voltageCell1", "voltageCell2", "voltageCell3", "voltageCell4", "voltageCell5", "voltageCell6",
                  "message"])
    ]

    start_time = None
    max_altitude = None
    max_ascent = None
    max_speed = None
    max_distance = None
    start_altitude = None


    for f in frames:
        last_frames[type(f).__name__] = f

        if isinstance(f, decoder.PositionFrame):
            max_altitude = max(max_altitude,f.ascent)
            max_ascent = max(max_altitude,f.ascent)

            if start_altitude is None:
                e = gmaps.elevation((f.latitude, f.longitude))
                start_altitude = e[0]["elevation"]

        if isinstance(f, decoder.TimeFrame):

            if start_time is None:
                start_time = f.ts

            max_speed = max(max_speed, f.speed)
            max_distance = max(max_distance, f.distance)

            vals = [ last_frames["PositionFrame"].latitude,
                     last_frames["PositionFrame"].longitude,
                     start_altitude + last_frames["PositionFrame"].ascent,
                     last_frames["PositionFrame"].ascent,
                     f.speed,
                     f.distance,
                     f.ts - start_time,
                     f.timestamp.strftime("%d-%m-%Y %H:%M:%S"),
                     last_frames["PositionFrame"].satellites,
                     last_frames["SmartBatteryFrame"].voltage,
                     max_altitude,
                     max_ascent,
                     max_speed,
                     max_distance,
                     last_frames["PositionFrame"].yaw,
                     "FALSE",
                     "FALSE",
                     last_frames["ControllerFrame"].elevator,
                     last_frames["ControllerFrame"].aileron,
                     last_frames["ControllerFrame"].throttle,
                     last_frames["ControllerFrame"].rudder,
                     last_frames["GimbalFrame"].yaw,
                     last_frames["GimbalFrame"].pitch,
                     last_frames["BatteryFrame"].percent,
                     last_frames["BatteryFrame"].voltages[0],
                     last_frames["BatteryFrame"].voltages[1],
                     last_frames["BatteryFrame"].voltages[2],
                     last_frames["BatteryFrame"].voltages[3],
                     last_frames["BatteryFrame"].voltages[4],
                     last_frames["BatteryFrame"].voltages[5],
                     last_frames["MessageFrame"].message,
                     ]

            lines.append(",".join([str(v) for v in vals]))





    return lines


if __name__ == "__main__":

    print(sys.argv[1])
    if len(sys.argv) >= 2:
        path = sys.argv[1]
    else:
        print("Please supply the path of the DJI Flight Log .txt file to convert")

    if len(sys.argv) >= 3:
        outpath = sys.argv[3]
    else:
        outpath = os.path.dirname(path) + os.sep + os.path.basename(path) + ".csv"

    print("Loading %s" % path)
    frames = decoder.decode_file(path)

    print("Decoding file")
    lines = frames_to_lines(frames)


    print("Writing %d lines to %s" % (len(lines), outpath))
    with open(outpath, "w") as csv:
        csv.writelines([line + "\n" for line in lines])
    print("Done")