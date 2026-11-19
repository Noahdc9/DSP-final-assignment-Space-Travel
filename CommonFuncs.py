import numpy as np
from IPython.display import Audio, display

#default case for our project.
Fs = 44100
type time_axis = np.ndarray
type data = np.ndarray

def sineGen(bF, Fs) -> tuple[data, time_axis]:
    """
    Sinusoid generation for continous playback.
    returns (data, time_axis).
    Arguments:
    
        bF: base frequency.
    
        Fs: sampling frequency.
    
    Returns:
        audio_data: data array of signal with Fs samples
        
        time_axis: time axis also with Fs samples.
    """
    time_axis = np.arange(Fs)/Fs
    data = np.sin(2 * np.pi * bF * time_axis)
    return data, time_axis


def squareGen(bF,Fs)-> tuple[data, time_axis]:
    """
    Square generation for continous playback.
    Arguments:
    
        bF: base frequency.
    
        Fs: sampling frequency.
    
    Returns:
        data: data array of signal with Fs samples
        
        time_axis: time axis also with Fs samples.
    """
    time_axis = np.arange(Fs)/Fs
    data = np.sign(np.sin(2 * np.pi * bF * time_axis)) #sign turns value to either 1 or -1 :)
    return data, time_axis


def triangleGen(bF,Fs)-> tuple[data, time_axis]:
    """
    A generator for triangle waves.
    
    Args:
        bF: base frequency.
        
        Fs: sampling frequency.
    
    Returns:
        data: data array of signal with Fs samples
        
        time_axis: time axis also with Fs samples.
    """
    
    time_axis = np.arange(Fs)/Fs
    data = 2/np.pi * np.arcsin(np.sin((2*np.pi*time_axis*bF)))
    return data,time_axis


def sawtoothGen(bF,Fs)-> tuple[data, time_axis]:
    """
    A generator for sawtooth waves.
    
    Args:
        bF: base frequency.
        
        Fs: sampling frequency.
    
    
    Returns:
        data: data array of signal with Fs samples
        
        time_axis: time axis also with Fs samples.
    """
    
    
    time_axis = np.arange(Fs)/Fs
    data = 2 * ((time_axis * bF) % 1.0) - 1
    
    return data, time_axis

type newData = np.ndarray

def ADSRGen(data, ADSR, toneState)-> list[newData]:
    global Fs
    ##the ADSR filter is essentially multiplying our audio with different impulse responses.
    
    ###ATTACK###
    #attack is passed as a value between 0 and 1. I've implemented the attack part as follows:
    if toneState == 0:
        return np.zeros(Fs)
    if toneState == 1: #start of playing; do attack mult.
        
        atkTime = int(44100*ADSR[0])
        decTime = int((44100-atkTime)*ADSR[1]) #we only ramp down in the remainder of the signal; so if attack and decay are both at 1.0,
        #we effectively ignore the decay (since we have to ramp up for the entire signal!)
        attack = np.linspace(0,1,atkTime)
        #after we have the attack ramp, we ramp down from peak to sustain level
        #in the decay time.
        decayRamp = np.linspace(1,ADSR[2],decTime)
        atkDec = np.concatenate((attack,decayRamp))
        susRamp = np.full((44100-len(atkDec)),[ADSR[2]])
        
        
        atkDecSus = np.concatenate((atkDec,susRamp))
        data = data*atkDecSus
    
    elif toneState == (2 or 3):
        ##if state is 2, we are in the default "play at sustain level".
        #we dont actually need to handle the exact size of the audio
        #(2 ^16 / 2 - 1 for 16 bit) since our data until dataPrettify is 
        #normalized between 0 and 1.
        susRamp = np.full(44100,[ADSR[2]])
        data = data * susRamp
    
    elif toneState == 4:
        relTime = int(44100*ADSR[3])
        relRamp = np.linspace(ADSR[2],0,relTime)
        relRamp = np.concatenate((relRamp,np.zeros(44100-len(relRamp))))
        data = relRamp* data
    
    
    
    return data

type fourierData = np.ndarray
type frequencyBin = np.ndarray
def fourierHandle(data, windowing="false",chunks=42) -> tuple[fourierData,frequencyBin]:# 42 because its the answer to everything
    """
    
    
    Returns:
        Magnitude:
        Freq:
        Magnitude_db:
    """
    
    global Fs
#we make windowing possible, but since we generate one second of data and dont expect it to be interrupted,
#we dont really need windowing. We can indeed run it on the entire second of audio.
    if windowing=="true":
        chunkSize = Fs / chunks 
        frames = chunks*2
        chunksList =[]
        for i in range(frames):
                chunksList.append(data[i*(chunkSize/2):])
        window = np.hamming(len(data))
        windowedData = window * data
    
    
    
        fourierData = np.fft.rfft(windowedData)
    
    
    
    else:
        fourierData = np.fft.rfft(data)
    
    freq = np.fft.rfftfreq(len(data), 1 / Fs)
    
    

    return fourierData, freq  
    
type filteredData = np.ndarray
    ##FILTERIIINGG
def filtering(data, freq, type,order, cutoff, upperCutoff=0 )->list[filteredData]:
    """
    Takes non-DB convered, fourier-transformed, normalized data and the corresponding frequency components and filters it either using a low or highpass.
    
    Arguments:
        data: the fourier transformed data.
        freq: the frequency components of the fft data.
        cutoff: the desired cutoff frequency.
        order: the order of the exponential in the cutoff of the filter. (how steep the cutoff is, essentially...)
    
    Returns:
        filteredData: the dataarray, now filtered.
        
    ensure that freq and data are same lengths; otherwise filtermask will pad the data, and you will have issues later.
    """
    if (type == 'low'):
        filterMask = 1.0 / np.sqrt(1.0 + (freq / cutoff) ** (2 * order))
        filteredData = data * filterMask
        
    elif type == 'high':
        filterMask = 1.0 / np.sqrt(1.0 + (cutoff / freq) ** (2 * order))
        filteredData = data * filterMask
    elif type == 'both':
        lowMask = 1.0 / np.sqrt(1.0 + (freq / upperCutoff) ** (2 * order))
        highMask = 1.0 / np.sqrt(1.0 + (cutoff / freq) ** (2 * order))
        filterMask = lowMask*highMask
        filteredData = data*filterMask
    return filteredData



def bandPass(data,freq,lowerBandFreq,upperBandFreq,Q)->list[filteredData]:
    """
    Takes data, frequency bins in fourier and lower/upper bandfrequencies, aswell as a Q (sharpness)
    and returns filtered data.
    
    Arguments:
        data: the fourier transformed data.
        freq: the frequency bins.
        lowerBandFreq: the lower frequency of the bandpass.
        upperBandFreq: the upper frequency of the bandpass.
        Q: the steepness of the bandPass.
    
    
    """
    
    
    f0 = np.floor(((upperBandFreq + lowerBandFreq) / 2)) #find the central frequency - floor it so we get one frequency at all times.)
    std = f0 / (2 * Q)#std deviation
    filterMask = np.exp(-(freq - f0)**2/ (2*std**2)) #formula for bandpass dropoff.
    filteredData = data * filterMask
    return filteredData
    
def allPass(data,freq,type="linear",center=1000.0,width=500):
    if type == "pole":
        normDist = (freq - center) / width
        phase_curve = -2.0*np.arctan(normDist)
    elif type == "linear":
        phase_curve = np.linspace(0.0,1.0,len(freq))
    #elif type == "Phaser": maybe do later?
    
    phases = np.angle(data) + phase_curve 
    phases[0] = 0.0
    phases[-1] = 0.0
    
    filteredData = np.abs(data) * np.exp(1j*phases)   
    
        
    return filteredData

#just a function to get back to timedomain, which creates a time axis for convenience.

def backToTheFromTime(fourierData)-> tuple[time_axis,data]:
    out = np.fft.irfft(fourierData)
    t = np.linspace(0,1,len(out))
    return t,out