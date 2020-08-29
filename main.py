  
import os
import osrparse
from osrparse.enums import GameMode, Mod
import lzma, struct, datetime
import copy
from numpy import interp

import pygame

def parse_timestamp_and_replay_length_new(self, replay_data):
    format_specifier = "<qi"
    (self.t, self.replay_length) = struct.unpack_from(format_specifier, replay_data, self.offset)
    self.timestamp = datetime.datetime.min + datetime.timedelta(microseconds=self.t/10)
    self.offset += struct.calcsize(format_specifier)

def parse_new(self, replay_data):
    offset_end = self.offset+self.replay_length
    self.parse_data_offset = self.offset
    if self.game_mode == GameMode.Standard or self.game_mode == GameMode.Osumania:
        datastring = lzma.decompress(replay_data[self.offset:offset_end], format=lzma.FORMAT_AUTO).decode('ascii')[:-1]
        events = [eventstring.split('|') for eventstring in datastring.split(',')]
        self.play_data = [osrparse.replay.ReplayEvent(int(event[0]), float(event[1]), float(event[2]), int(event[3])) for event in events]

    self.offset = offset_end
    self.offset_end = offset_end

def h_toString(self):
    return str(self.time_since_previous_action) +" | "+ str(self.x)

def newinit(self, replay_data):
        self.offset = 0
        self.game_mode = None
        self.game_version = None
        self.beatmap_hash = None
        self.player_name = None
        self.replay_hash = None
        self.number_300s = None
        self.number_100s = None
        self.number_50s = None
        self.gekis = None
        self.katus = None
        self.misses = None
        self.score = None
        self.max_combo = None
        self.is_perfect_combo = None
        self.mod_combination = None
        self.life_bar_graph = None
        self.timestamp = None
        self.play_data = None
        self.data = replay_data
        self.parse_replay_and_initialize_fields(replay_data)

def injectIntoOsrparser():
    osrparse.replay.Replay.parse_timestamp_and_replay_length = parse_timestamp_and_replay_length_new
    osrparse.replay.Replay.parse_play_data = parse_new
    osrparse.replay.Replay.__init__ = newinit
    osrparse.replay.ReplayEvent.toString = h_toString

injectIntoOsrparser()\

def GetMsOD(od, judge):
    if(judge == "300g"):
        return 16
    if(judge == "300"):
        return int(64 - (3*od))
    if(judge == "200"):
        return int(97 - (3*od))
    if(judge == "100"):
        return int(127 - (3*od))
    if(judge == "50"):
        return int(151 - (3*od))
    if(judge == "miss"):
        return int(188 - (3*od))


class Beatmap:

    def __init__(self, path = None):
        self.read = False
        self.path = path

    def readfile(self,path = None):
        if not path and not self.path:
            sys.exit("You need to specify a path to read a beatmap")

        mode = None
        category = None
        self.data = dict()
        self.copy = dict()
        self.objects = list()

        with open(self.path, 'r') as file:
            for line in file.readlines():
                line = line.split("\n")[0]

                if(line == "[General]"):
                    mode = "data"
                    category = "[General]"
                    self.data[category] = dict()
                elif(line == "[Editor]"):
                    mode = "data"
                    category = "[Editor]"
                    self.data[category] = dict()
                elif(line == "[Metadata]"):
                    mode = "data"
                    category = "[Metadata]"
                    self.data[category] = dict()
                elif(line == "[Difficulty]"):
                    mode = "data"
                    category = "[Difficulty]"
                    self.data[category] = dict()
                elif(line == "[Events]"):
                    mode = "copy"
                    category = "[Events]"
                    self.copy[category] = list()
                elif(line == "[TimingPoints]"):
                    mode = "copy"
                    category = "[TimingPoints]"
                    self.copy[category] = list()
                elif(line == "[HitObjects]"):
                    mode = "objects"
                elif(not mode):
                    continue
                else:
                    if(mode == "data"):
                        s = line.split(":")
                        if(len(s)>1):
                            key = s.pop(0)
                            self.data[category][key] = ":".join(s)
                    elif(mode == "copy"):
                        self.copy[category].append(line)
                    elif(mode == "objects"):
                        self.objects.append(HitObject(line))
        self.read = True

    def getHitObjectsColumn(self, column):
        objects = list()

        for obj in self.objects:
            if((int(obj.args[0])-64) / 4 < 16):
                if(column == 1):
                    objects.append(obj)
            elif((int(obj.args[0])-64) / 4 < 48):
                if(column == 2):
                    objects.append(obj)
            elif((int(obj.args[0])-64) / 4 < 80):
                if(column == 3):
                    objects.append(obj)
            elif((int(obj.args[0])-64) / 4 < 112):
                if(column == 4):
                    objects.append(obj)

        return objects

class HitObject:

    def __init__(self,line):
        self.args = line.split(",")

replay = None
beatmap = None

for file in os.listdir("replay/"):
    if file.endswith(".osr"):
        replay = osrparse.replay.parse_replay_file("replay/"+file)

for file in os.listdir("replay/"):
    if file.endswith(".osu"):
        beatmap = Beatmap("replay/"+file)
        beatmap.readfile()

if replay == None:
    print("No replay found")
    exit()

pygame.init()



class Screen:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.window = pygame.display.set_mode((self.width,self.height))

    def DrawLineAt(self, ms, color):
        pygame.draw.line(self.window, color, (0,self.height/2 - ms), (self.width,self.height/2 - ms), 1)

        if ms != 0:
            pygame.draw.line(self.window, color, (0,self.height/2 + ms), (self.width,self.height/2 + ms), 1)

def DrawDeviancePoint(screen, x, y, od):
    size = 1
    
    if(abs(y) <= GetMsOD(od, "300g")):
        pygame.draw.circle(screen.window, (210, 77, 240), (x,-y + int(screen.height/2)), size)
    elif(abs(y) <= GetMsOD(od, "300")):
        pygame.draw.circle(screen.window, (240, 197, 77), (x,-y + int(screen.height/2)), size)
    elif(abs(y) <= GetMsOD(od, "200")):
        pygame.draw.circle(screen.window, (129, 240, 77), (x,-y + int(screen.height/2)), size)
    elif(abs(y) <= GetMsOD(od, "100")):
        pygame.draw.circle(screen.window, (77, 145, 240), (x,-y + int(screen.height/2)), size)
    elif(abs(y) <= GetMsOD(od, "50")):
        pygame.draw.circle(screen.window, (197, 207, 219), (x,-y + int(screen.height/2)), size)
    elif(y >= -GetMsOD(od, "miss")):
        pygame.draw.circle(screen.window, (245, 93, 93), (x,-y + int(screen.height/2)), size)

def DrawDevianceGraph(replay_data, beatmap, deviances, od):
    screen = Screen(900,400)
    pygame.display.set_caption(replay_data.player_name+"'s replay on "+beatmap.data["[Metadata]"]["Title"]+" "+beatmap.data["[Metadata]"]["Version"])

    screen.window.fill((22,22,22))

    screen.DrawLineAt(0, (100,100,100))
    screen.DrawLineAt(GetMsOD(od, "300g"), (210, 77, 240))
    screen.DrawLineAt(GetMsOD(od, "300"), (240, 197, 77))
    screen.DrawLineAt(GetMsOD(od, "200"), (129, 240, 77))
    screen.DrawLineAt(GetMsOD(od, "100"), (77, 145, 240))
    screen.DrawLineAt(GetMsOD(od, "50"), (197, 207, 219))
    screen.DrawLineAt(GetMsOD(od, "miss"), (245, 93, 93))

    mint = deviances[0][0]
    maxt = deviances[len(deviances)-1][0]
    for d in deviances:
        DrawDeviancePoint(screen, int(interp(d[0],[mint,maxt],[0,screen.width])), d[1], od)

    pygame.display.update()

    running = True

    # main loop
    while running:
        # event handling, gets all event from the event queue
        for event in pygame.event.get():
            # only do something if the event is of type QUIT
            if event.type == pygame.QUIT:
                # change the value to False, to exit the main loop
                running = False

keypress = list()
keyrelease = list()

pressed = [False,False,False,False]
current_time = replay.play_data.pop(0).time_since_previous_action
replay.play_data.pop(0)

for event in replay.play_data:
    current_time += event.time_since_previous_action
    i = 3
    for k in "{0:04b}".format(int(event.x)):
        if(k == '1' and not pressed[i]):
            keypress.append([current_time,i])
            pressed[i] = True
        if(k == '0' and pressed[i]):
            keyrelease.append([current_time,i])
            pressed[i] = False
        i-=1

columns = dict()
for k in range(1,5):
    columns[k-1] = beatmap.getHitObjectsColumn(k)

od = float(beatmap.data["[Difficulty]"]["OverallDifficulty"])

deviances = list()
for kp in keypress:
    if(len(columns[kp[1]]) <= 0):
        continue
    
    difference = kp[0] - int(columns[kp[1]][0].args[2])
    if(difference > -GetMsOD(od, "miss") and difference < GetMsOD(od, "50")):
        deviances.append([kp[0],difference])
        columns[kp[1]].pop(0)

gaps = [list(),list(),list(),list(),list()]
last = [-1,-1,-1,-1]
lastt = -1

i = 0
while(i<len(keypress)):
    kp = keypress[i]
    t = kp[0]
    col = kp[1]
    
    if(last[col] != -1):
        diff = t - last[col]
        gaps[col].append(diff)
        gaps[4].append(t - lastt)

    last[col] = t
    lastt = t

    i+=1

with open("gaps.csv","w") as f:
    f.write("1,2,3,4,T\n")

    i = 0
    while(i<len(gaps[4])):
        for k in range(0,4):
            f.write("\"")
            if(i<len(gaps[k])):
                f.write(str(gaps[k][i]))
            f.write("\",")
        f.write("\""+str(gaps[4][i])+"\"\n")

        i+=1

DrawDevianceGraph(replay, beatmap,deviances, od)