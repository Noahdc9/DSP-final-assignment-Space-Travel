import numpy as np
import pygame
import pyaudio
import sympy as sp
import matplotlib.pyplot as plt
from IPython.display import Audio, display
import CommonFuncs as CF


###TONETABLE
SHARPS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def build_tone_map(start_octave: int = 2, end_octave: int = 8, a4_hz: float = 440.0) -> dict[str, float]:
    tone_map: dict[str, float] = {}
    for octave in range(start_octave, end_octave + 1):
        for semitone, note in enumerate(SHARPS):
            # A4 is MIDI note 69; C4 is MIDI note 60
            midi_note = (octave + 1) * 12 + semitone
            freq = a4_hz * (2.0 ** ((midi_note - 69) / 12.0))
            tone_map[f"{note}{octave}"] = round(freq, 3)
    return tone_map
    #generate audio for all chords. make audio of chords
    #chords are as follows:
    #[Tone#1, Tone#1_type(sin/sq/tri/saw), Tone#2, Tone#2_type(sin/sq/tri/saw), etc.]
    
toneMap = build_tone_map() 
    
    
def audioGeneration(loop=True, chords=[],chordLengths=[], intervals=[]):
    #first ensure equal chords and chordlengths count.
    if(len(chords)>len(chordLengths)):
        print("not enough defined lengths, assuming half a second each.")
        for i in range(len(chords) - len(chordLengths)):
            chordLengths.append(0.5)
    if(len(chordLengths)>len(chords)):
        print("too many chordlengths. truncating")
        for i in range(len(chords)-len(chordLengths)):
            chordLengths.pop()
    
    #second we ensure we have a common amount of chords to intervals.
    #count if intervals should be exactly (chords - 1).
    if(len(chords)> (len(intervals)+1)):
        print("more chords than intervals; truncating final chords.")
        for i in range(len(chords)-len(intervals)):
            chords.pop()
    if(len(intervals) >= len(chords)):
        print("more intervals than needed, truncating list")
        for i in range((len(intervals)+1)-len(chords)):
            intervals.pop()            
    
    
    

    d = np.array([], dtype=np.float64)
    
    for i in range(len(chords)):
        #if chord is poorly made...
        if len(chords)% 2 != 0:
            print("chord was uneven length, exiting...")
            return -1,-1
        
        
        tones = CF.sineGen(0,44100)  
        for k in range(len(chords[i])//2):
            #make a list of the tones
            
            ##append to tones        
            #dependent on what second param is(1=sin,2=sq,3=tri,4=saw)
            
            match (chords[i][(k*2+1)]):
                case 1:
                    temp, _ = (CF.sineGen(toneMap[chords[i][(k*2)]]))                       
                case 2:
                    temp, _ = (CF.squareGen(toneMap[chords[i][(k*2)]]))                         
                case 3:
                    temp, _ = (CF.triangleGen(toneMap[chords[i][(k*2)]]))
                case 4:
                    temp, _ = (CF.sawtoothGen(toneMap[chords[i][(k*2)]]))
            tones += temp
            
            
        ###todo:     
        
        #multiply with chord length.
        chord_wave = np.asarray(np.tile(tones, chordLengths[i] if chordLengths[i]%1 == 0 else chordLengths[i]+1 ),dtype=np.float64).ravel()[:chordLengths[i]*44100]
        d = np.concatenate([d, chord_wave])
        #append spacing between chords.
        if(i != len(intervals)):
            d = np.concatenate([d, (np.zeros(44100*intervals[i]))])
    totalTime = 0
    for i in range(len(chordLengths)):
        totalTime += chordLengths[i]
    print(totalTime)
    
    t = np.arange(len(d))/44100
    print("right after linspace:", len(t), totalTime)
    return t,d   
    
