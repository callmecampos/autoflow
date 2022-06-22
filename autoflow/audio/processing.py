"""
Tasks:
- Beat detection
- Beat / verse splitting
- Transient analysis
- Spectrum visualization and interaction
- Etc.
"""

from lib2to3.pytree import convert
import os, io, youtube_dl, yt_dlp
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
from pydub import AudioSegment
import numpy as np
import subprocess

from enum import Enum

class Codec(Enum):
    WAV = "wav"
    FLAC = "flac"

def download_youtube(url, base_path=".", convert_to=Codec.FLAC):
    print(f"Extracting info for URL: {url}")
    video_info = youtube_dl.YoutubeDL().extract_info(
        url = url,
        download=False
    )

    base_filename = video_info['title']
    query_filename = f"{base_filename}.%(ext)s"
    options={
        'format': 'bestaudio/best',
        'keepvideo': False,
        'outtmpl': os.path.join(base_path, query_filename),
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])

    print("Download complete... {}".format(query_filename))

    filename = f"{base_filename}.{video_info['ext']}"

    if convert_to == Codec.FLAC:
        # ffmpeg -i audio.xxx -c:a flac audio.flac
        command = ['ffmpeg', '-i', filename, '-c:a', 'flac', f'{base_filename}.flac']
        subprocess.run(command,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
    elif convert_to == Codec.WAV:
        # ffmpeg -i ./Diablo.webm -c:a pcm_f32le ./out.wav
        command = ['ffmpeg', '-i', filename, '-c:a', 'pcm_f32le', f'{base_filename}.wav']
        subprocess.run(command,stdout=subprocess.PIPE,stdin=subprocess.PIPE)

    # next - audio processing steps - spleeter and syllabic timing detection with priors... phonetic priors or nah...

def is_wav(filepath):
    return filepath.split(".")[-1] == "wav"

def is_flac(filepath):
    return filepath.split(".")[-1] == "flac"

def flac_to_wav_bytes(flac_file: str) -> io.BytesIO:
    flac = AudioSegment.from_file(flac_file, format='flac')
    stream = io.BytesIO()
    flac.export(stream, format='wav')

    return stream

def plot_spectrogram(filepath, start=0, end=-1, channel=-1):
    if is_wav(filepath):
        sample_rate, samples = wavfile.read(filepath)
    elif is_flac(filepath):
        sample_rate, samples = wavfile.read(flac_to_wav_bytes(filepath))
    else:
        raise Exception(f"Invalid file path (not WAV or FLAC) {filepath}")

    if len(samples.shape) == 2 and samples.shape[1] == 2:
        if (channel == -1):
            samples = np.mean(samples, axis=1) # FIXME: better way to go to mono than just averaging??? what info do we lose?
        else:
            samples = samples.T[channel]

    frequencies, times, spectrogram = signal.spectrogram(samples[start:end], sample_rate)

    print(frequencies, times)

    plt.pcolormesh(times, frequencies, spectrogram)
    # plt.imshow(spectrogram)
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.show()

    """
    Ideal: play song over spectrogram and show where it's happening (animated spectrogram with bar)
    - This can likely happen on iOS side as well
    - TODO: I don't care about frequency, just time beats -- detecting syllables and speech -- that should definitely already exist
    - TODO: getting time and duration detections on each syllable (passed in as a prior!!!)

    NEXT:
    - Spleeter (compare performance)
    - Consumer producer model of modules in generic audio library!!! visualization and stuff probs shouldn't be in python
    """

    return samples[start:end], sample_rate, frequencies, times, spectrogram