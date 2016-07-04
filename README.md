# phantom-decoder

### Decode flight record TXT files from DJI GO app
#### Tested with DJI Phantom 4

The DJI GO app stores flight records for every flight, collecting data from the aircraft at ~10 Hz. 
The files are given names corresponding to the time of the flight (e.g. `DJIFlightRecord_2016-06-18_[21-05-26].txt`) 
and are stored in `/DJI/dji.pilot/FlightRecord/` on Android.

Although they have the `.txt` extension, the data is stored in an undocumented, proprietary format. This repository 
contains Python scripts for decoding the files into more useful `.csv` files, ideal for use with software like [Dashware](http://www.dashware.net/).

## How to use

Run `python txt2csv.py path-to-file.TXT`. This will create `path-to-file.csv` in the same directory as the original `.TXT` file.

## File Format

Bytes 0-11 are some sort of header and have not yet been decoded.

From byte 12 onwards, the file contains a stream of variable length frames. Each frame is structured as follows:

* Byte 0: **Frame type** - Frame types 1,2,3,4,5,6,7,8,9,11,13,15 have been observed
* Byte 1: **Payload length** - The number of bytes of data following this header
* Bytes 2-n: **Payload** - Different for each frame type. See below.
* Byte n+1: **0xFF** - Frame delimiter. This isn't really necessary, but it's there anyway.

```
|---------------|-----------------|------------------------------------------|------|----
| type (1 byte) | length (1 byte) | payload (n bytes)                        | 0xFF | ...
|---------------|-----------------|------------------------------------------|------|----
```


### Frame Types

The various frames appear with different frequencies and each contain different types of data. Position, battery, gimbal, etc. 
Their formats are described here. All multi-byte encodings are little-endian.

#### Frame 1 - **Position**

This frame is always 53 (`0x35`) bytes long. Appears at ~10 Hz

```
Offset  | Type                | Field                    | Unit
--------|---------------------|--------------------------|------------
      0 | 64-bit double       | Longitude                | radians
      8 | 64-bit double       | Latitude                 | radians
     16 | 16-bit signed int   | Ascent above start point | metres * 10
     18 | 16-bit signed int   | X Speed                  | m/s * 10
     20 | 16-bit signed int   | Y Speed                  | m/s * 10
     22 | 16-bit signed int   | Z Speed                  | m/s * 10
     24 | 16-bit signed int   | Pitch                    | degrees * 10
     26 | 16-bit signed int   | Roll                     | degrees * 10
     28 | 16-bit signed int   | Yaw (compass heading)    | degrees * 10
     30 | 16-bit unsigned int | Fly C State              | ?
     32 | 16-bit ?            | ?                        | 
     34 | 16-bit ?            | ?                        | 
     36 | unsigned byte       | Visible GPS satellites   | count
     37 | unsigned byte       | Flight Action            | ?
     38 | unsigned byte       | Motor Start Failed Cause | ?
     39 | unsigned byte       | Non GPS Cause            | ?
     40 | unsigned byte       | Battery                  | ?
     41 | unsigned byte       | S Wave Height            | ?
     42 | 16-bit unsigned int | Fly time                 | seconds * 10
     44 | 16-bit unsigned int | Motor Revolution         | ?
```

#### Frame 2 - **Home Point**

This frame reports details of the current Home Point.

```
Offset  | Type           | Field             | Unit
--------|----------------|-------------------|------------
      0 | 64-bit double  | Latitude          | radians
      4 | 64-bit double  | Longitude         | radians
      8 | 16-bit float   | Pressure Altitude | metres * 10
```

Note that *pressure altitude* is the barometric altitude assuming a pressure at sea-level of 1013.25 millibars. See https://en.wikipedia.org/wiki/Pressure_altitude

#### Frame 3 - **Gimbal**

This frame reports the current state of the camera gimbal.

```
Offset  | Type                | Field                   | Unit
--------|---------------------|-------------------------|------------
      0 | 16-bit signed int   | Pitch                   | degrees * 10
      2 | 16-bit signed int   | Roll                    | degrees * 10
      4 | 16-bit signed int   | Yaw (compass heading)   | degrees * 10
      6 | unsigned byte       | Mode                    | ?
      7 | unsigned byte       | Roll Adjust             | ?
      8 | unsigned byte       | Yaw Angle               | ?
      9 | unsigned byte       | Is Auto Calibration     | ?
     10 | unsigned byte       | Auto Calibration Result | ?
     11 | unsigned byte       | Version                 | ?
     12 | 16-bit unsigned int | Counter                 | ?
```

#### Frame 4 - **Controller**

This frame reports the status of the radio controller at a frequency of ~10 Hz.

```
Offset  | Type                | Field    | Unit
--------|---------------------|----------|------------
      0 | 16-bit unsigned int | Throttle | position (0 - 2048)
      2 | 16-bit unsigned int | Rudder   | position (0 - 2048)
      4 | 16-bit unsigned int | Elevator | position (0 - 2048)
      6 | 16-bit unsigned int | Aileron  | position (0 - 2048)
```

The remaining bytes certainly contain the state of all the other controls, but are yet to be decoded.

#### Frame 5 - **Time**

This frame contains a current UTC time stamp, among other things

```
Offset  | Type                | Field      | Unit
--------|---------------------|------------|------------
      0 | byte                | ?          | 
      1 | byte                | ?          |
      2 | 32-bit float        | Speed      | m/s
      6 | 32-bit float        | Distance   | metres
     10 | 64-bit unsigned int | Time (UTC) | milliseconds since UNIX epoch
```


#### Frame 6 - *Unknown*

#### Frame 7 - **Battery 1**

This frame contains general raw information about the battery state.

```
Offset  | Type                | Field            | Unit
--------|---------------------|------------------|------------
      0 | unsigned byte       | Level            | percent
      1 | 16-bit unsigned int | Current PV       | ? * 1000
      3 | 16-bit unsigned int | Current Capacity | mAh
      5 | 16-bit unsigned int | Total Capacity   | mAh
      7 | unsigned byte       | Life             | ?
      8 | 32-bit unsigned int | Charge Cycles    | count
     12 | 16-bit unsigned int | Error Type       | ?
     14 | 16-bit signed int   | Current          | mA * 1000
     16 | 16-bit unsigned int | Cell 1 Voltage   | volts * 1000
     16 | 16-bit unsigned int | Cell 2 Voltage   | volts * 1000
     16 | 16-bit unsigned int | Cell 3 Voltage   | volts * 1000
     16 | 16-bit unsigned int | Cell 4 Voltage   | volts * 1000
     16 | 16-bit unsigned int | Cell 5 Voltage   | volts * 1000
     16 | 16-bit unsigned int | Cell 6 Voltage   | volts * 1000
     16 | 16-bit unsigned int | Serial No.       | 
     16 | 16-bit DOS date     | Manufacture Date | see below
     16 | 16-bit unsigned int | Temperature      | Kelvin * 10
```

The Manufacture Date is packed into 16 bits using the MS-DOS Date encoding. See `decoder.py` for decoding.

#### Frame 8 - **Battery 2**

This frame contains calculated battery statistics.

```
Offset  | Type                | Field             | Unit
--------|---------------------|-------------------|------------
      0 | 16-bit unsigned int | Useful Time       | seconds
      2 | 16-bit unsigned int | Go Home Time      | seconds
      4 | 16-bit unsigned int | Land Time         | seconds
      6 | 16-bit unsigned int | Go Home Battery   | ?
      8 | 16-bit unsigned int | Land Battery      | ?
     10 | 32-bit float        | Safe Fly Radius   | ?
     14 | 32-bit float        | Volume Consume    | ?
     18 | 16-bit unsigned int | Status            | ?
     20 | 16-bit unsigned int | Go Home Status    | ?
     22 | 16-bit unsigned int | Go Home Countdown | ?
     24 | 16-bit unsigned int | Voltage           | volts * 1000
     26 | byte                | Level             | percent
     27 | byte                | Low Warning       | ?
```

#### Frame 9 - **Message**

This frame is recorded when the DJI GO app displays messages to the pilot. The entire payload is an ASCII string. There is no null-termination.

#### Frame 11 - *Unknown*

#### Frame 13 - **Aircraft**

This frame contains details of the aircraft.

```
Offset  | Type                | Field                 | Unit
--------|---------------------|-----------------------|------------
      0 | byte                | Drone Type            | ?
      1 | byte                | App Type              | ?
      2 | byte                | App Major Version     | 
      3 | byte                | App Minor Version     | 
      4 | byte                | App Revision          | 
      5 | 10-byte string      | Aircraft Serial No.   | 
     15 | 32-byte string      | Aircraft Name         |
     47 | 64-bit unsigned int | Activation Time       | seconds since UNIX epoch
     57 | 10-byte string      | Camera Serial No.     |
     67 | 10-byte string      | Controller Serial No. |
     77 | 10-byte string      | Battery Serial No.    |
```

The `Activaction Time` field contains the time when the aircraft was first powered on.

#### Frame 15 - *Unknown*
