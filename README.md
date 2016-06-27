# phantom-decoder

### Decode flight record TXT files from DJI GO app
#### Tested with DJI Phantom 4

The DJI GO app stores flight records for every flight, collecting data from the aircraft at ~10 Hz. 
The files are given names corresponding to the time of the flight (e.g. `DJIFlightRecord_2016-06-18_[21-05-26].txt`) 
and are stored in `/DJI/dji.pilot/FlightRecord/` on Android.

Although they have the `.txt` extension, the data is stored in an undocumented, proprietary format. This repository 
contains Python scripts for decoding the files into more useful `.csv` files, ideal for use with software like [Dashware](http://www.dashware.net/).

## File Format

Bytes 0-11 are some sort of header and have not yet been decoded.

From byte 12 onwards, the file contains a stream of variable length frames. Each frame is structured as follows:

* Byte 0: **Frame type** - Frame types 1,2,3,4,5,6,7,8,9,11,13,15 have been observed
* Byte 1: **Payload length** - The number of bytes of data following this header
* Bytes 2-n: **Payload** - Different for each frame type. See below.
* Byte n+1: **0xFF** - Frame delimiter. This isn't really necessary, but it's there anyway.

```
-------------------------------------------------------------------------------------
| type (1 byte) | length (1 byte) | payload (n bytes)                        | 0xFF |
-------------------------------------------------------------------------------------
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
      4 | 64-bit double       | Latitude                 | radians
      8 | 16-bit signed int   | Ascent above start point | metres * 10
     10 | 16-bit signed int   | X Speed                  | m/s * 10
     12 | 16-bit signed int   | Y Speed                  | m/s * 10
     14 | 16-bit signed int   | Z Speed                  | m/s * 10
     16 | 16-bit signed int   | Pitch                    | degrees * 10
     18 | 16-bit signed int   | Roll                     | degrees * 10
     20 | 16-bit signed int   | Yaw (compass heading)    | degrees * 10
     22 | 16-bit unsigned int | Fly C State              | ?
     24 | 16-bit ?            | ?                        | ?
     26 | 16-bit ?            | ?                        | ?
     28 | unsigned byte       | Visible GPS satellites   | count
     29 | unsigned byte       | Flight Action            | ?
     30 | unsigned byte       | Motor Start Failed Cause | ?
     31 | unsigned byte       | Non GPS Cause            | ?
     32 | unsigned byte       | Battery                  | ?
     33 | unsigned byte       | S Wave Height            | ?
     34 | 16-bit unsigned int | Fly time                 | seconds * 10
     36 | 16-bit unsigned int | Motor Revolution         | ?
```

#### Frame 2 - **Home Point**

#### Frame 3 - **Gimbal**

#### Frame 4 - **Controller**

#### Frame 5 - **Time**

#### Frame 6 - *Unknown*

#### Frame 7 - **Battery 1**

#### Frame 8 - **Battery 2**

#### Frame 9 - **Message**

#### Frame 11 - *Unknown*

#### Frame 13 - **Aircraft**

#### Frame 15 - *Unknown*
