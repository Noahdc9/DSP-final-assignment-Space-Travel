import numpy as np
#default case for our project.

#for pydocs
time_axis = np.ndarray
data = np.ndarray

def sineGen(bF: float, Fs: int = 44100) -> tuple[np.ndarray, np.ndarray]:
    """Sinusoid generation for continous playback.

    Args:
        bF (float): Base frequency.
        Fs (int, optional): Sampling frequency. Defaults to 44100.

    Returns:
        tuple[np.ndarray, np.ndarray]: data and time axis.
    """    
    time_axis = np.arange(Fs)/Fs
    data = np.sin(2 * np.pi * bF * time_axis)
    return data, time_axis


def squareGen(bF: float, Fs: int = 44100) -> tuple[np.ndarray, np.ndarray]:
    """Square generation for continous playback.

    Args:
        bF (float): Base frequency.
        Fs (int, optional): Sampling frequency. Defaults to 44100.

    Returns:
        tuple[np.ndarray, np.ndarray]: data and time axis.
    """
    time_axis = np.arange(Fs)/Fs
    data = np.sign(np.sin(2 * np.pi * bF * time_axis)) #sign turns value to either 1 or -1 :)
    return data, time_axis


def triangleGen(bF: float, Fs: int = 44100) -> tuple[np.ndarray, np.ndarray]:
    """A generator for triangle waves.

    Args:
        bF (float): Base frequency.
        Fs (int, optional): Sampling frequency. Defaults to 44100.

    Returns:
        tuple[np.ndarray, np.ndarray]: .
    """
    
    time_axis = np.arange(Fs)/Fs
    data = 2/np.pi * np.arcsin(np.sin((2*np.pi*time_axis*bF)))
    return data,time_axis


def sawtoothGen(bF: float, Fs: int = 44100) -> tuple[np.ndarray, np.ndarray]:
    """A generator for sawtooth waves.

    Args:
        bF (float): Base frequency.
        Fs (int, optional): Sampling frequency. Defaults to 44100.

    Returns:
        tuple[np.ndarray, np.ndarray]: data and time axis.
    """        
    
    time_axis = np.arange(Fs)/Fs
    data = 2 * ((time_axis * bF) % 1.0) - 1
    
    return data, time_axis

#for pydocs
newData = np.ndarray
def ADSRGen(data: np.ndarray, ADSR, toneState: int, Fs: int = 44100)-> list[int]:
    """Applies a ADSR to the signal

    Args:
        data (list[int]): Input signal
        ADSR (_type_): The ADSR profile
        toneState (int): idk
        Fs (int, optional): Sampling frequency. Defaults to 44100.

    Returns:
        list[int]: Output signal
    """  
    ##the ADSR filter is essentially multiplying our audio with different impulse responses.
    
    ###ATTACK###
    #attack is passed as a value between 0 and 1. I've implemented the attack part as follows:
    if toneState == 0:
        return np.zeros(Fs)
    if toneState == 1: #start of playing; do attack mult.
        
        atkTime = int(Fs*ADSR[0])
        decTime = int((Fs-atkTime)*ADSR[1]) #we only ramp down in the remainder of the signal; so if attack and decay are both at 1.0,
        #we effectively ignore the decay (since we have to ramp up for the entire signal!)
        attack = np.linspace(0,1,atkTime)
        #after we have the attack ramp, we ramp down from peak to sustain level
        #in the decay time.
        decayRamp = np.linspace(1,ADSR[2],decTime)
        atkDec = np.concatenate((attack,decayRamp))
        susRamp = np.full((Fs-len(atkDec)),[ADSR[2]])
        
        
        atkDecSus = np.concatenate((atkDec,susRamp))
        data = data*atkDecSus
    
    elif toneState == (2 or 3):
        ##if state is 2, we are in the default "play at sustain level".
        #we dont actually need to handle the exact size of the audio
        #(2 ^16 / 2 - 1 for 16 bit) since our data until dataPrettify is 
        #normalized between 0 and 1.
        susRamp = np.full(Fs,[ADSR[2]])
        data = data * susRamp
    
    elif toneState == 4:
        relTime = int(Fs*ADSR[3])
        relRamp = np.linspace(ADSR[2],0,relTime)
        relRamp = np.concatenate((relRamp,np.zeros(Fs-len(relRamp))))
        data = relRamp* data
    
    return data

#for pydocs
fourierData = np.ndarray
frequencyBin = np.ndarray
def fourierHandle(data: np.ndarray, Fs = 44100, windowing: bool = False, chunks: int = 42) -> tuple[np.ndarray, np.ndarray]: # tuple[fourierData,frequencyBin]:# 42 because its the answer to everything
    """idk

    Args:
        data (np.array[int]): Input signal
        Fs (int, optional): Sampling fequency. Defaults to 44100.
        windowing (bool, optional): Does this window. Defaults to False.
        chunks (int, optional): How many chuncks/bins should be made. Defaults to 42.

    Returns:
        tuple[np.ndarray, np.ndarray]: Fourier data and freqency bins
    """    
    #we make windowing possible, but since we generate one second of data and dont expect it to be interrupted,
    #we dont really need windowing. We can indeed run it on the entire second of audio.
    if windowing:
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
    
   
##FILTERIIINGG
#for pydocs
filteredData = np.ndarray
def filtering(data: np.ndarray, freq: np.ndarray, type: str,order: int, cutoff: int, upperCutoff: int = 0)->list[int]:
    """Takes non-DB convered, fourier-transformed, normalized data and the corresponding frequency components and filters it either using a low or highpass.
    Ensure that freq and data are same lengths; otherwise filtermask will pad the data, and you will have issues later.
    
    Args:
        data (np.array[int]): The fourier transformed data.
        freq (np.array[int]): The frequency components of the fft data.
        type (str): Can be 'low', 'both' and 'high'.
        order (int): The order of the exponential in the cutoff of the filter.
        cutoff (int): The desired cutoff frequency.
        upperCutoff (int, optional): _description_. Defaults to 0.

    Raises:
        ValueError: If 'type' is not valid.

    Returns:
        list[int]: the data array, now filtered.
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
    else:
        raise ValueError("Type was not 'low', 'both' or 'high'.")

    return filteredData



def bandPass(data: np.ndarray, freq: np.ndarray, lowerBandFreq: int, upperBandFreq: int, Q: int) -> list[int]:
    """Takes data, frequency bins in fourier and lower/upper bandfrequencies, aswell as a Q (sharpness) and returns filtered data.

    Args:
        data (np.array[int]): The fourier transformed data.
        freq (np.array[int]): The frequency bins.
        lowerBandFreq (int): The lower frequency of the bandpass.
        upperBandFreq (int): The upper frequency of the bandpass.
        Q (int): The steepness of the bandPass.

    Returns:
        list[int]: The filtered data
    """
    
    f0 = np.floor(((upperBandFreq + lowerBandFreq) / 2)) #find the central frequency - floor it so we get one frequency at all times.)
    std = f0 / (2 * Q)#std deviation
    filterMask = np.exp(-(freq - f0)**2/ (2*std**2)) #formula for bandpass dropoff.
    filteredData = data * filterMask
    return filteredData
    
def allPass(data: np.ndarray, freq: np.ndarray, type: str = "linear", center: float = 1_000.0, width: int = 500) -> list[int]:
    """An all pass filter

    Args:
        data (np.array[int]): The fourier transformed data.
        freq (np.array[int]): The frequency bins.
        type (str, optional): Determines the type. Can be 'pole' or 'linear'. Defaults to "linear".
        center (float, optional): IDK. Defaults to 1_000.0.
        width (int, optional): IDK. Defaults to 500.

    Raises:
        ValueError: If 'type' is not valid.

    Returns:
        list[int]: The data array, now filtered.
    """    
    if type == "pole":
        normDist = (freq - center) / width
        phase_curve = -2.0*np.arctan(normDist)
    elif type == "linear":
        phase_curve = np.linspace(0.0,1.0,len(freq))
    #elif type == "Phaser": maybe do later?
    else:
        raise ValueError("Type was not 'pole' or 'linear'.")

    
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