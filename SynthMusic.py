import numpy as np
import pygame
import pyaudio
import sympy as sp
import matplotlib.pyplot as plt
from IPython.display import Audio, display
import CommonFuncs as CF

def audioGeneration(loop=True, chords=[], intervals=[]):
    if(len(chords)> (len(intervals)+1)):
        print("more chords than intervals; truncating final chords.")
        for i in range(len(chords) - (len(intervals)+1)):
            del chords[-1]
    return chords, intervals    
    
out = audioGeneration(True,[0,1,2,3,4],[0,1,2,3])

print(out)