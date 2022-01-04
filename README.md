# The HIVE

This project contains the [CircuitPython 7.1.0][7] code for the toy made for our kids.

This toy is running on a [Feather M4][1], [PN532 NFC/RFID controller][2], [Speaker][3], some
[NeoPixels][4] and a recycled SD Card reader from an old radio. The [PN532][2] and SD Card reader
share the same [SPI][12] bus, and is powered by a [3.7v 2200mAh][14] battery.

The basic functionality is described in this [YouTube Playlist][5].

## Functionality

- reading RFID chip embedded in a 3D printed spherical animal
- selecting a random WAV file associated with the RFID tag
- playing audio file where the relative [SPL][6] changes the brightness of the LEDs
- low-battery indicator (lights and sound)
- on/off switch
- random input/output ramps 

## Requirements
For the code to run on the [Feather M4][1], you'll need to include these libraries:
- [adafruit_bus_device][8]
- [adafruit_pn532][9]
- [adafruit_sdcard][10]
- [neopixel][11]

## SD Card & Audio Files

The audio files need to be formatted in a very particular format to play on the [Feather M4][1], this 
guide for [converting sound files in Audacity][21].

Then running the [prepare_audio_files.py](./prepare_audio_files.py) script will produce the resulting [SPL][6]
values for that audio file, which will be used to brighten the LED when the matching WAV filename is played.

Then store the WAV and TXT files on the SD card in this structure:
```
|- formatted/
|  |- animals/
|     |- bear/
|        |- 01.wav
|        |- 01.txt
|        |- 02.wav
|        |- 02.txt
|        |- etc.
|     |- etc./
|  |- system/
|     |- power_on/
|        |- 01.wav
|        |- 01.txt
|        |- 02.wav
|        |- 02.txt
|     |- etc./
```

## 3D printing assets

All assets are available on [PrusaPrinters][16].

## Notes

Debugging was performed with [Mu Python][13]. 

Originally we wanted to have the audio files mix in real-time if multiple RFID tags were 
detected in one of the 4 ramps. However, the hardware limitations of the [PN532][2] only 
allows for 2 tags to be read at the same time. 

The [Speaker][3] had interesting feedback when operated on a battery and the voltage was 
not at it's peak. Where leveraging the [audiomixer][15] from CircutPython produced a constant hiss.

Designing the ramps to print on the [Prusa Mini][17] while also adhearing to the [Rhombic Dodecahedron ][18]
design and accomidating the [PN532][2] antenna was challenging. There are still a few locations where the balls
could get "stuck", but are easily nudged out. 

Modeling the geometric shapes in [Fusion 360][19] was very straight-foward, however the character ball designs
was easier to perform in [blender][20] with Sculpting. Although we had to design the screw pattern and negative 
space in [Fusion 360][19] to then import into [blender][20] such that we could take the negative boolean of the 
two models to get a consistent print which allowed us to screw them together after inserting the RFID tag.

Painting the ball figures was pretty straight-forward, although protecting the paint from repeated bouncing off the
ramps is still TBD.

[1]: https://www.adafruit.com/product/3857
[2]: https://www.adafruit.com/product/364
[3]: https://www.adafruit.com/product/3885
[4]: https://www.adafruit.com/product/1461?length=1
[5]: https://www.youtube.com/watch?v=ppjUW_MYzwA&list=PL8L4p4mQPaKocCwQW5a3IMrlqHCrkkY_Y&index=1
[6]: https://en.wikipedia.org/wiki/Sound_pressure#Sound_pressure_level
[7]: https://circuitpython.org/board/feather_m4_express/
[8]: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice/releases
[9]: https://github.com/adafruit/Adafruit_CircuitPython_PN532/releases
[10]: https://github.com/adafruit/Adafruit_CircuitPython_SD/releases
[11]: https://github.com/adafruit/Adafruit_NeoPixel/releases
[12]: https://en.wikipedia.org/wiki/Serial_Peripheral_Interface
[13]: https://codewith.mu/
[14]: https://www.adafruit.com/product/1781
[15]: https://circuitpython.readthedocs.io/en/latest/shared-bindings/audioio/index.html
[16]: https://www.prusaprinters.org/prints/112410-the-hive/files
[17]: https://www.prusa3d.com/category/original-prusa-mini/
[18]: https://en.wikipedia.org/wiki/Rhombic_dodecahedron
[19]: https://www.autodesk.com/products/fusion-360/overview
[20]: https://www.blender.org/
[21]: https://learn.adafruit.com/adafruit-wave-shield-audio-shield-for-arduino/check-your-files
