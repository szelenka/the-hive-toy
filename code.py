import gc
from os import listdir
from collections import namedtuple
from time import monotonic, sleep
from random import choice
from binascii import hexlify

import board
from busio import SPI
from digitalio import DigitalInOut
from storage import VfsFat, mount
from audioio import AudioOut
from audiocore import WaveFile
from audiomixer import Mixer

from neopixel import NeoPixel
from adafruit_sdcard import SDCard
from adafruit_pn532.spi import PN532_SPI

Color = namedtuple('Color', ('rgb', 'duration', 'index'))
Animal = namedtuple('Animal', ('name', 'colors', 'sounds'))

# soundfile configuration
POWER_ON = ''
SDCARD_READY = ''
ANTENNA_READY = ''
IDLE_REMINDER = ''
IDLE_TIMEOUT = 60
TURN_OFF_TIMEOUT = 300
SLEEP_DURATION = 0.05

# color helpers
OFF = (0,0,0)
WHITE = (255,255,255)
RED = (255,0,0)
ORANGE = (255,50,0)
YELLOW = (255,150,0)
GREEN = (0,255,0)
CYAN = (0,255,255)
BLUE = (0,0,255)
PURPLE = (180,0,255)
VIOLET = (176,12,168)
BROWN = (56,28,2)

# define control pins
PIN_AUDIO = board.A0
NUM_PIXELS = 12
NUM_PIXELS_IN_STRIP = NUM_PIXELS // 2
onboard_pixel = NeoPixel(board.A1, 1, brightness=0.3, auto_write=False)
left_pixels = NeoPixel(board.D5, NUM_PIXELS, brightness=0.3, auto_write=False)
right_pixels = NeoPixel(board.D6, NUM_PIXELS, brightness=0.3, auto_write=False)
cs_sdcard = DigitalInOut(board.A4)
cs_rfid = DigitalInOut(board.A5)
spi = SPI(board.SCK, board.MOSI, board.MISO)

# send a ping sound to let them know it's powered on

# play the audio file on an available channel
class PlayAudio():
    def __init__(self, filename):
        self.filename = filename
        self.audio_binary = None
        self.audio_spl = None
        self.start_time = 0.0
    
    def __enter__(self, *args, **kwargs):
        self.audio = AudioOut(PIN_AUDIO)
        print(f"Playing: {self.filename}")
        try:
            self.audio_binary = WaveFile(open(self.filename, "rb"))
        except OSError as ex:
            print(ex)
            return None

        try:
            self.audio_spl = open(self.filename.replace('.wav', '.csv'), 'r').read().split(',')
        except OSError as ex:
            print(ex)
        
        self.mixer = Mixer(
            voice_count=1, sample_rate=22050, channel_count=1, bits_per_sample=16, samples_signed=True
        )

        self.audio.play(self.mixer)
        self.mixer.voice[0].play(self.audio_binary)
        self.mixer.voice[0].level = 0.35
        self.start_time = monotonic()
        
        return self
        
    def __exit__(self, *args, **kwargs):
        print(f"Stopping: {self.filename}")
        if self.mixer.voice[0].playing:
            self.mixer.voice[0].stop()

        if self.audio.playing:
            self.audio.stop()
            
        self.audio.deinit()
        self.mixer.deinit()

    @property
    def playing(self):
        return self.mixer.voice[0].playing

    @property
    def spl(self):
        if self.audio_spl is None:
            return 0.5

        play_duration = monotonic() - self.start_time
        index = round(play_duration // 0.1)
        try:
            spl = self.audio_spl[index]
        except IndexError:
            spl = self.audio_spl[-1]
            
        return float(spl)
        

def play_sound_and_wait(filename: str):
    with PlayAudio(filename=filename) as a:
        while a.playing:
            pass

play_sound_and_wait('ping.wav')

# 1: setup SDCard first
MOUNT_POINT = '/sd'
ROOT_DIRECTORY = f'{MOUNT_POINT}/formatted'
try:
    sdcard = SDCard(spi, cs_sdcard)
    vfs = VfsFat(sdcard)
    mount(vfs, MOUNT_POINT)
    print(f"Mounted SD Card to: {MOUNT_POINT}")
except OSError as ex:
    print(f"Unable to locate SD Card: {ex}")


# 2: setup PN532 to communicate with MiFare cards
pn532 = PN532_SPI(spi, cs_rfid, debug=False)
pn532.SAM_configuration()
ic, ver, rev, support = pn532.firmware_version
print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))


# Helper to give us a nice color swirl
def wheel(pos: int):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if (pos < 0):
        return [0, 0, 0]
    if (pos > 255):
        return [0, 0, 0]
    if (pos < 85):
        return [int(pos * 3), int(255 - (pos*3)), 0]
    elif (pos < 170):
        pos -= 85
        return [int(255 - pos*3), 0, int(pos*3)]
    else:
        pos -= 170
        return [0, int(pos*3), int(255 - pos*3)]


def show_pixels():
    left_pixels.show()
    right_pixels.show()


def pixel_brightness(brightness: float):
    left_pixels.brightness = brightness
    right_pixels.brightness = brightness


def reset_pixels():
    left_pixels.fill(OFF)
    right_pixels.fill(OFF)
    show_pixels()


def rainbow_cycle(pixel_index: int, color_index: int):
    rc_index = (pixel_index * 256 // NUM_PIXELS_IN_STRIP) + color_index
    reflect_pixel(pixel_index, wheel(rc_index & 255))


def reflect_pixel(index: int, color: tuple):
    alt_idx = NUM_PIXELS - 1 - index
    # TODO: left_pixels has a bad pixel at 0 so it's wired at 1-5, then 6-11
    if index != 0:
        left_pixels[index-1] = color
    left_pixels[alt_idx-1] = color
    right_pixels[index] = color
    right_pixels[alt_idx] = color


def load_sounds(child_folder: str, parent_folder: str = 'animals'):
    directory = f'{ROOT_DIRECTORY}/{parent_folder}/{child_folder}'
    print(f"Loading files from: {directory}")
    try:
        ret = [f'{directory}/{f}' for f in listdir(directory) if f.endswith('.wav')]
        for f in ret:
            print(f'\t{f}')
        return ret
    except OSError as e:
        print(f"Unable to locate directory: {directory}")
    
    return []


def play_system_sound(filename: str):
    with PlayAudio(filename=filename) as a:
        while a.playing:
            for j in range(0, 255, 1):
                if not a.playing:
                    break
                for i in range(NUM_PIXELS_IN_STRIP):
                    rainbow_cycle(i, j)
                    
                show_pixels()
                pixel_brightness(a.spl)
                
        reset_pixels()


def found_animal(captured_animal: bytearray):
    animal = zoo.get(hexlify(captured_animal), zoo.get(None))
    if animal.name == 'unknown':
        print("Found unknown card with UID: ", hexlify(captured_animal))
    else:
        print("Discovered: ", animal.name)

    try:
        filename = choice(animal.sounds)
    except IndexError:
        print(f"Unable to detect any sounds for: {animal.name}")
        return

    with PlayAudio(filename=filename) as a:
        # animate neopixels for duration of sound
        while a.playing:
            for c in animal.colors:
                if not a.playing:
                    break
                    
                if c.index is None:
                    for p in range(NUM_PIXELS_IN_STRIP):
                        reflect_pixel(p, c.rgb)
                else:
                    for p in c.index:
                        reflect_pixel(p, c.rgb)
                
                pixel_brightness(a.spl)
                show_pixels()
                if a.playing:
                    sleep(c.duration if c.duration is not None else 0.01)

    reset_pixels()
    
    
def pattern_walk(color1, color2 = OFF, pattern_size: int = 2, speed: float = 0.05, reverse: bool = False):
    all_idx = set(list(range(0, NUM_PIXELS_IN_STRIP)))
    gen_list = []
    for _ in reversed(range(0, NUM_PIXELS_IN_STRIP)) if reverse else range(0, NUM_PIXELS_IN_STRIP):
        _list = set([i if i < NUM_PIXELS_IN_STRIP else abs(NUM_PIXELS_IN_STRIP - i) for i in range(_, _ + pattern_size)])
        gen_list += [
            Color(rgb=color1, duration=0, index=all_idx.difference(_list)),
            Color(rgb=color2, duration=speed, index=_list),
        ]
    
    return gen_list
    

# Configuration
zoo = {
    None: Animal(name='unknown', colors=pattern_walk(WHITE, speed=0.01), sounds=load_sounds("unknown")),
    b'31d3c866': Animal(
        name='bear', colors=[Color(rgb=BLUE, duration=0, index=None)], sounds=load_sounds("bear")),
    b'22054d61': Animal(name='bug',colors=[
        Color(rgb=wheel( ((i * 256 // NUM_PIXELS_IN_STRIP) + j) & 255 ), duration=0, index=[i])
        for j in range(0, 255, 10) for i in range(NUM_PIXELS_IN_STRIP)
    ], sounds=load_sounds("bug")),
    b'3290f139': Animal(
        name='dragon', colors=[Color(rgb=GREEN, duration=0, index=None)], sounds=load_sounds("dragon")),
    b'029a2d61': Animal(
        name='fox',colors=[Color(rgb=ORANGE, duration=0, index=None)], sounds=load_sounds("fox")),
    b'02144d61': Animal(
        name='lion',colors=[Color(rgb=YELLOW, duration=0, index=None)], sounds=load_sounds("lion")),
    b'02aef039': Animal(
        name='metroid',colors=[Color(rgb=VIOLET, duration=0, index=None)], sounds=load_sounds("metroid")),
    b'22434a61': Animal(
        name='monkey', colors=[Color(rgb=RED, duration=0, index=None)], sounds=load_sounds("monkey")),
    b'923b4a61': Animal(
        name='owl', colors=[Color(rgb=WHITE, duration=0, index=None)], sounds=load_sounds("owl")),
    b'528af239': Animal(
        name='peacock', colors=pattern_walk(BLUE), sounds=load_sounds("unknown")),
}

# play sound indicating it's ready
power_on = load_sounds('power_on', 'system')
power_off = load_sounds('power_off', 'system')
reminder = load_sounds('reminder', 'system')
play_system_sound(choice(power_on))

ts_last_activity = monotonic()
while True:
    ts_now = monotonic()
    uid = pn532.read_passive_target(timeout=0.5)
    if uid is not None:
        # perform animal actions
        found_animal(captured_animal=uid)
        ts_last_activity = ts_now
    elif ts_now - ts_last_activity > 0 and ( ts_now - ts_last_activity ) % IDLE_TIMEOUT == 0:
        # randomly flash lights/play short sound
        play_system_sound(filename=choice(reminder))
    elif ts_last_activity < ts_now - TURN_OFF_TIMEOUT :
        # issue reminder to turn the device off
        play_system_sound(filename=choice(power_off))
        ts_last_activity = ts_now

    # cooldown period
    sleep(SLEEP_DURATION)
