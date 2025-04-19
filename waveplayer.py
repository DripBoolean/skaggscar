import wave

import numpy as np

import picobot_api
import time

def play(filename):
    picobot_api.init()

    f = wave.open(filename)

    process_rate = 0.02

    channels = f.getnchannels()
    sample_width = f.getsampwidth()

    process_frames = int(process_rate * f.getframerate())

    for i in range(0, f.getnframes(), process_frames):
        start_time = time.time()
        f.setpos(i)
        lh = []
        rh = []
        for j in range(process_frames):
            data = f.readframes(1)
            lh.append(int.from_bytes(data[:sample_width], "little", signed=True))
            #rh.append(int.from_bytes(data[3:5], "little", signed=True))
        lh = np.fft.rfft(lh)
        alh = list(map(abs, lh))
        mlh = max(alh)
        imlh = alh.index(mlh)
        freq = imlh/process_rate
        
        process_time = time.time() - start_time
        
        if process_time > process_rate:
            print("Stream is delayed, try increasing the process_rate")
        else:
            time.sleep(process_rate - process_time)
        #time.sleep(process_rate - (end_time - start_time))
        if freq > 0 and freq < 20000:
            picobot_api.playTone(int(freq), process_rate)
            