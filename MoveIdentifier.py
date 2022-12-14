# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KHLD41mUtUWIDtSCSXUnvNAyaU44KhUn
"""

from tensorflow import keras
import numpy as np
model = keras.models.load_model("my_model")

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import preprocessing
import numpy as np
import json
import warnings
from scipy import signal, stats
# %matplotlib inline

def identify_move(ax, ay, az, gx, gy, gz):
  shield = 0
  grenade = 0
  reload = 0
  logout = 0
  for j in range(0,64,3):
    ax_features = extract(np.array(ax[j:j+10]))
    ay_features = extract(np.array(ay[j:j+10]))
    az_features = extract(np.array(az[j:j+10]))

    gx_features = extract(np.array(gx[j:j+10]))
    gy_features = extract(np.array(gy[j:j+10]))
    gz_features = extract(np.array(gz[j:j+10]))



    input = np.array(ax_features + ay_features + az_features + gx_features + gy_features + gz_features)
    input =(input-input.mean())/input.std()
    result = np.rint(model.predict(input))

    if result[0] == 1:
      shield = shield + 1
    elif result[1] == 1:
      grenade = grenade + 1
    elif result[2] == 1:
      reload = reload + 1
    else:
      logout = logout + 1
    
    
  if max(shield, grenade, logout, reload) == shield:
    return "shield"
  elif max(shield, grenade, logout, reload) == grenade:
    return "grenade"
  if max(shield, grenade, logout, reload) == reload:
    return "reload"
  if max(shield, grenade, logout, reload) == logout:
    return "logout"

def extract(arr):
    ax = []
    ay = []
    az = []
    gx = []
    gy = []
    gz = []
    
    for a in arr:
        ax.append(a[0])
        ay.append(a[1])
        az.append(a[2])
        
        gx.append(a[3])
        gy.append(a[4])
        gz.append(a[5])
    
    features = []
    for i in extract_raw_data_features_per_row(np.array(ax)):
        features.append(i)
        
    for i in extract_raw_data_features_per_row(np.array(ay)):
        features.append(i)
        
    for i in extract_raw_data_features_per_row(np.array(az)):
        features.append(i)
    
    for i in extract_raw_data_features_per_row(np.array(gx)):
        features.append(i)
        
    for i in extract_raw_data_features_per_row(np.array(gy)):
        features.append(i)
    
    for i in extract_raw_data_features_per_row(np.array(gz)):
        features.append(i)
    
    return features

def extract_raw_data_features_per_row(f_n):
    f1_mean = compute_mean(f_n)
    f1_var = compute_variance(f_n)
    f1_mad = compute_median_absolute_deviation(f_n)
    f1_rms = compute_root_mean_square(f_n)
    f1_iqr = compute_interquartile_range(f_n)
    f1_per75 = compute_percentile_75(f_n)
    f1_kurtosis = compute_kurtosis(f_n)
    f1_min_max = compute_min_max(f_n)
    f1_sma = compute_signal_magnitude_area(f_n)
    #f1_zcr = compute_zero_crossing_rate(f_n)
    f1_sc = compute_spectral_centroid(f_n)
    f1_entropy = compute_spectral_entropy(f_n)
    f1_energy = compute_spectral_energy(f_n)
    f1_pfreq = compute_principle_frequency(f_n)
    return [
        f1_mean,
        f1_var,
        f1_mad,
        f1_rms,
        f1_iqr,
        f1_per75,
        f1_kurtosis,
        f1_min_max,
        f1_sma,
        #f1_zcr,
        f1_sc,
        f1_entropy,
        f1_energy,
        f1_pfreq,
    ]

def compute_mean(data):
    return np.mean(data)

def compute_variance(data):
    return np.var(data)

def compute_median_absolute_deviation(data):
    return stats.median_absolute_deviation(data)

def compute_root_mean_square(data):
    def compose(*fs):
        def wrapped(x):
            for f in fs[::-1]:
                x = f(x)
            return x

        return wrapped

    rms = compose(np.sqrt, np.mean, np.square)
    return rms(data)

def compute_interquartile_range(data):
    return stats.iqr(data)

def compute_percentile_75(data):
    return np.percentile(data, 75)

def compute_kurtosis(data):
    return stats.kurtosis(data)

def compute_min_max(data):
    return np.max(data) - np.min(data)

def compute_signal_magnitude_area(data):
    return np.sum(data) / len(data)

def compute_zero_crossing_rate(data):
    return ((data[:-1] * data[1:]) < 0).sum()

def compute_spectral_centroid(data):
    spectrum = np.abs(np.fft.rfft(data))
    normalized_spectrum = spectrum / np.sum(
        spectrum
    )  # like a probability mass function
    normalized_frequencies = np.linspace(0, 1, len(spectrum))
    spectral_centroid = np.sum(normalized_frequencies * normalized_spectrum)
    return spectral_centroid

def compute_spectral_entropy(data):
    freqs, power_density = signal.welch(data)
    return stats.entropy(power_density)

def compute_spectral_energy(data):
    freqs, power_density = signal.welch(data)
    return np.sum(np.square(power_density))

def compute_principle_frequency(data):
    freqs, power_density = signal.welch(data)
    return freqs[np.argmax(np.square(power_density))]

