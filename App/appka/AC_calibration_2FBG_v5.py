# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 13:38:28 2022

@author: ErayMyumyun
"""

import os
import math
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from IPython.display import display
from colorama import Fore, Back, Style
import AC_functions_2FBG_v3 as fun
#%% Location of data and scrips
# Path where the scripts are  (AC_functions_2FBG_v2 and AC_calibration_2FBG_v2)
Scriptpath = r'c:\Users\tsalat.SYLEX\Desktop\Python'

# Main path is where the sensitivities.csv and time_corrections.csv will be saved.
# If sensitivities.csv and time_corrections.csv do not exist, they will be automatically generated
Main_folder_path = (r"c:\Users\tsalat.SYLEX\Desktop\Python\Data_Folder")
Opt_path = (r"c:\Users\tsalat.SYLEX\Desktop\Python\Data_Folder\AC-1000\Opt\90794")
Ref_path = (r"c:\Users\tsalat.SYLEX\Desktop\Python\Data_Folder\AC-1000\Ref\90794")

# Changes dir to where the scripts are saved. This way cells can be run without issue
os.chdir(Scriptpath)


#%% Reference values
# Ref_sensitivity = 1.048689
# Ref_sensitivity = 1.054050                                                   # Old sensitivity
Ref_sensitivity = 1.0795
# Ref_sensitivity = 0.009975789                                                  #0.010061

# Sampling frequencies of optical and reference signal
Opt_samp_freq = 800
Ref_samp_freq = 12800

# Cutoff frequenties for the filter. [lowend, highend]
# If you want a lowpass filter change the lowend to 0 and if you want a highpass filter change the highend to 0.5*Ref_samp_freq
CutOffOpt = [5, Opt_samp_freq/2-1]
# CutOffOpt = [5, 500]
CutOffRef = [5, Ref_samp_freq/2-1]

# At which frequency to measure the sensitivity
GainMark = 50 #Frequency at which sensitivity is determined, adjust as desired
#%% Optional settings
# 1 if Enlight was used
Enlight = 0

# 1 if other software is used. Give how many rows need to be skipped in data file
Else = 1
skiprows = 4

# 1 if Faz is used. Skiprows not used wih Faz, Faz does not add headers or anything else.
Faz = 0

# 1 to make plots, 0 to not make them
Make_plots = 0

# X axis limits 
xScale = [10, 100]           # Frequency spectrum x axis limit
xScaleTransfer = [10, 100]    # Power spectrum and Bode analysis x axis limit

# 1 to filter signal, 0 to not filter
Filter_on = 1
# 1 to downsample reference signal to optical signal frequency,0 to upsample optical signal to reference signal frequency
Downsample_ref = 1

# Necessary settings in normal calibration, can be disabled if desired
Adjust_time_correction = 1
Do_spectrum = 1
# 0 to obtain sensitivity from data file, enter value if other sensitivity is desired
Set_sensitivity = 0
#%% Gets all the fullnames of txt files in Opt_path and Ref_path. CSV FILES ARE IGNORED!
opt_file_names = fun.detect_txt_files(Opt_path)
ref_file_names = fun.detect_txt_files(Ref_path)
#%% Print the names of all the txt files.
# Get only the names of the txt files
Opt_name = []
for I in opt_file_names:
    O = I[len(Opt_path)+1:]
    Opt_name.append(O)
    
Ref_name = []
for I in ref_file_names:
    O = I[len(Ref_path)+1:]
    Ref_name.append(O)

# Prints the files names and changes the background to let you know you need to make a choice
for I in range(0, len(Opt_name)):
    print(Fore.RED + Back.WHITE + str(I+1), end = " ")
    print("Opt: " + Opt_name[I] + " - Ref: " + Ref_name[I] + Style.RESET_ALL)
#%% Gives a prompt to choose which txt file to run.
Test_id = int(input(Fore.RED + Back.WHITE + "Select the sensor to calibrate from above and past the number here:" + Style.RESET_ALL))
#Test_id = 2
#%% Load timeshifts and sensitivities
# If timeshift and sensitivy file are present, they will be loaded, otherwise they will be created
os.chdir(Main_folder_path)
if os.path.isfile('time_corrections.csv') is False:
    time_corrections = -3*np.ones((len(opt_file_names)+1,1))
    time_corrections = time_corrections.reshape(len(time_corrections, ))
    np.savetxt('time_corrections.csv',time_corrections)
else:
    time_corrections = np.loadtxt('time_corrections.csv')

if os.path.isfile('sensitivities.csv') is False:
    sensitivities = 1e-10*np.ones((len(opt_file_names)+1,1))
    sensitivities = sensitivities.reshape(len(sensitivities, ))
    np.savetxt('sensitivities.csv',sensitivities)
else:
    sensitivities = np.loadtxt('sensitivities.csv')
#%% Checks if sensitivities.csv and time_corrections.csv are the correct size and if not, it corrects it
if len(opt_file_names) > len(time_corrections):
    Cor_time = -3*np.ones((len(opt_file_names)-len(time_corrections),1))
    Cor_time = Cor_time.reshape(len(Cor_time, ))
    time_corrections = np.concatenate((time_corrections, Cor_time))

if len(opt_file_names) > len(sensitivities):
    Cor_sens = 1e-10*np.ones(((len(opt_file_names)-len(sensitivities),1)))
    Cor_sens = Cor_sens.reshape(len(Cor_sens, ))
    sensitivities = np.concatenate((sensitivities, Cor_sens))
#%% Data loading
opt_file_name = opt_file_names[Test_id-1]
ref_file_name = ref_file_names[Test_id-1]
display(['///////////  Test ' + str(Test_id) + '  ///////////'])
display(['Analysing: ' + str(opt_file_name)])
# If csv of data is present it will be loaded, otherwise data file will be analyzed and csv file with wavelengths will be created
# Adjust functions depending on used interrogator software

if os.path.isfile(opt_file_name[0:-4]+'.csv') is True:
    DataOptRel = np.loadtxt(opt_file_name[0:-4]+'.csv')
    display(['Optical .csv file found'])
else:
    if Enlight == 1:
        display(['Optical .csv file not found. Creating .csv file ...'])
        DataOptRel = fun.read_Enlight_Data_AC(opt_file_name)
        np.savetxt(opt_file_name[0:-4]+'.csv',DataOptRel)
        display(['.csv file complete'])
    if Faz == 1:
        display(['Optical .csv file not found. Creating .csv file ...'])
        DataOptRel = fun.read_txt_file(opt_file_name, 0)[0:, (8, 14)]*10**9
        np.savetxt(opt_file_name[0:-4]+'.csv',DataOptRel)
        display(['.csv file complete'])
    if Else == 1:
        display(['Optical .csv file not found. Creating .csv file ...'])
        DataOptRel = fun.read_txt_file_AC(opt_file_name, skiprows)
        np.savetxt(opt_file_name[0:-4]+'.csv',DataOptRel)
        display(['.csv file complete'])

# Loading of reference data, same as optical data
if os.path.isfile(ref_file_name[0:-4]+'.csv') is True:
    DataRefRel = np.loadtxt(ref_file_name[0:-4]+'.csv')
    display(['Reference .csv file found'])
else:
    display(['Reference .csv file not found. Creating .csv file ...'])
    DataRefRel = fun.read_txt_file(ref_file_name,23)
    np.savetxt(ref_file_name[0:-4]+'.csv',DataRefRel)
    display(['Reference .csv file done'])
#%% Data Selection
# Loads saved sensitivity for analyzing and adjusting
if Set_sensitivity != 0:
    Sensitivity_opt = Set_sensitivity
    Adjust_gain = 0
else:
    Sensitivity_opt = sensitivities[Test_id-1]
    Adjust_gain = 1

if math.isnan(Sensitivity_opt) == True:
    Sensitivity_opt = 1e-10

display(['Center wavelength = ' + str(round(DataOptRel[0,0],5)) + ' and ' + str(round(DataOptRel[0,1],5)) + ' nm'])
#Calculate acceleration from optical data and previously determined sensitivity
optical_sensor_data = fun.calculateAC(-(DataOptRel[:,0] - DataOptRel[:,1]) + (DataOptRel[0,0] - DataOptRel[0,1]), Sensitivity_opt)
#Calculate acceleration from reference data and corresponsing sensitivity for reference sensor
reference_sensor_data= DataRefRel[:,1]/Ref_sensitivity
#%% Time Syncing
# Creating time arrays for optical and reference signal according to sampling frequency
TimeOpt = np.linspace(1/Opt_samp_freq,len(optical_sensor_data)/Opt_samp_freq,num=len(optical_sensor_data))
TimeRef = np.linspace(1/Ref_samp_freq,len(reference_sensor_data)/Ref_samp_freq,num=len(reference_sensor_data))
# Load timecorrection shift from file and adjust time of reference signal
ShiftLeft= -time_corrections[Test_id-1]
TimeRefShifted = TimeRef + ShiftLeft
#%% Filtering
# Currently bandpass filtering is used, if other form of filtering is desired, adjust cutoff frequency accordingly
if Filter_on == 1:
    if CutOffOpt[0] == 0:
        B,A = signal.butter(3,CutOffOpt[1]/(0.5*Opt_samp_freq),'lowpass')
    else:
        if CutOffOpt[1] == 0.5*Opt_samp_freq:
            B,A = signal.butter(3,CutOffOpt[0]/(0.5*Opt_samp_freq),'highpass')
        else:
            CutOffOpt = [CutOffOpt[0]/(0.5*Opt_samp_freq), CutOffOpt[1]/(0.5*Opt_samp_freq)]
            B,A = signal.butter(3,CutOffOpt,'bandpass')
    opt_sens_filtered = signal.filtfilt(B, A, optical_sensor_data)
    
    if CutOffRef[0] == 0:
        B,A = signal.butter(3,CutOffRef[1]/(0.5*Ref_samp_freq),'lowpass')
    else:
        if CutOffRef[1] == 0.5*Ref_samp_freq:
            B,A = signal.butter(3,CutOffRef[0]/(0.5*Ref_samp_freq),'highpass')
        else:
            CutOffRef = [CutOffRef[0]/(0.5*Ref_samp_freq), CutOffRef[1]/(0.5*Ref_samp_freq)]
            B,A = signal.butter(3,CutOffRef,'bandpass')
    ref_sens_filtered = signal.filtfilt(B, A, reference_sensor_data)
else:
    opt_sens_filtered = optical_sensor_data
    ref_sens_filtered = reference_sensor_data
#%% Preparing data for bode analisis
# Downsample reference signal to immitate nyquist effects.
# Or upsample Optical signal for better time shift estimate.

if Downsample_ref == 1:
    # Optical signal remains the same
    OptSensResampled = opt_sens_filtered
    TimeOptSensResampled = TimeOpt
    
    # Resampling reference signal through interpolation
    ref_sens_resampled = fun.resample_by_interpolation(ref_sens_filtered, Ref_samp_freq, Opt_samp_freq)
    ref_sens_resampled_time = fun.resample_by_interpolation(TimeRefShifted, Ref_samp_freq, Opt_samp_freq)
    
    # Determining sample difference and resizing signals accordingly
    SampleDiff = round(ShiftLeft*Opt_samp_freq)
    OptSensResized, RefSensResized = fun.SignalResize(OptSensResampled, ref_sens_resampled, SampleDiff)
    
    # Creating of new time arrays according to resize signal length and sampling frequency
    TimeOptSensResized = np.linspace(1/Opt_samp_freq, len(OptSensResized)/Opt_samp_freq,num = len(OptSensResized))
    TimeRefSensResized = np.linspace(1/Opt_samp_freq, len(RefSensResized)/Opt_samp_freq,num = len(RefSensResized))
    BodeSampFreq = Opt_samp_freq
else:
    # Resampling optical signal through interpolation
    OptSensResampled = fun.resample_by_interpolation(opt_sens_filtered, Opt_samp_freq, Ref_samp_freq)
    TimeOptSensResampled = fun.resample_by_interpolation(TimeOpt, Opt_samp_freq, Ref_samp_freq)
    
    # Reference signal remains the same
    ref_sens_resampled = ref_sens_filtered
    ref_sens_resampled_time = TimeRefShifted
    
    # Determining sample difference and resizing signals accordingly
    SampleDiff = round(ShiftLeft*Ref_samp_freq)
    OptSensResized, RefSensResized = fun.SignalResize(OptSensResampled,ref_sens_filtered,SampleDiff)
    
    # Creating of new time arrays according to resize signal length and sampling frequency
    TimeOptSensResized = np.linspace(1/Ref_samp_freq,len(OptSensResized)/Ref_samp_freq,num=len(OptSensResized))
    TimeRefSensResized = np.linspace(1/Ref_samp_freq,len(RefSensResized)/Ref_samp_freq,num=len(RefSensResized))
    BodeSampFreq = Ref_samp_freq
#%% Fourier analysis
display(['Computing Fourier Analisis...'])
# Estimating power spectral density through periodogram function
if Do_spectrum == 1:
    FreqOptPSD,OptPSD = signal.periodogram(OptSensResized, BodeSampFreq)
    FreqRefPSD,RefPSD = signal.periodogram(RefSensResized, BodeSampFreq)

# Creating a low pass filter for smoothening graphs. The '10' below is the frequency
Smooth_freq = [5/(0.5*Opt_samp_freq)]
B,A = signal.butter(3, Smooth_freq, 'lowpass')

# Smoothening FreqOptPSD and FreqRefPSD
SmoothOptPSD = signal.filtfilt(B, A, OptPSD)
SmoothRefPSD = signal.filtfilt(B, A, RefPSD)

# Smootheing of signals transfer function through lowpass filter
NFFT = 2**math.ceil(math.log2(abs(len(OptSensResized))))

# Determining of transfer function to be smoothened
Transfer,FreqTransfer = fun.FourierAnalisis(RefSensResized, OptSensResized, BodeSampFreq)

# Smoothening the signal with a lowpass.
SmoothTransfer = signal.filtfilt(B, A, abs(Transfer))

# Estimate the magnitude squared coherence estimate of the signals
FreqCoherence,Coherence = signal.coherence(RefSensResized, OptSensResized, fs = BodeSampFreq, nperseg = round(NFFT/20), noverlap = round(NFFT/40), nfft = NFFT)

# Smootheing of coherence array
SmoothCoherence = signal.filtfilt(B, A, Coherence)
#%% Determine gain at set frequency
GainAtMark = fun.interp1_for_remco(FreqTransfer, SmoothTransfer,GainMark)
# Convert gain to sensitivity and save for further use
if Adjust_gain == 1:
    sensitivities[Test_id-1] = Sensitivity_opt*GainAtMark
    display(['Sensitivity of ' + str(sensitivities[Test_id-1]*1000.0) + ' pm/g' + ' at ' + str(GainMark) + ' Hz ' + 'and offset is ' + str(round(DataOptRel[0,1] - DataOptRel[0,0],5) - sensitivities[Test_id-1]) + ' nm'])
else:
    display(['Sensitivity of ' + str(sensitivities[Test_id-1]*1000.0) + ' pm/g' + ' at ' + str(GainMark) + ' Hz ' + ' Offset is ' + str(round(DataOptRel[0,1] - DataOptRel[0,0],5) - sensitivities[Test_id-1]) + ' nm'])
#%% Calcualating flatness of sensitivity between edge-frequencies, these can be adjusted as desired
flatness_edge_l = 10  # Left flatness edge frequency
flatness_edge_r = 100  # Right flatness edge frequency
display(['Sensitivity flatness between ' + str(flatness_edge_l) + ' Hz and ' + str(flatness_edge_r) + ' Hz is: ' + str(round(abs(fun.interp1_for_remco(FreqTransfer,20*np.log(abs(SmoothTransfer)),flatness_edge_l) - fun.interp1_for_remco(FreqTransfer,20*np.log(abs(SmoothTransfer)),flatness_edge_r)),1))])
#%% Symmetry check
display(['Maximum acceleration = ' + str(round(max(opt_sens_filtered), 3)) + ' g and ' + 'minimum acceleration = ' + str(round(min(opt_sens_filtered), 4))])
display(['Difference in symmetry = ' + str(round(((max(opt_sens_filtered) - abs(min(opt_sens_filtered)))/max(opt_sens_filtered))*100, 4)) + '%'])
#%% Make Phase Array and determine phase difference
AngleSetFreq = 30
phase_difference = np.unwrap(np.angle(Transfer))*180/np.pi

# Smoothing of the phase difference
phase_difference_smooth = signal.filtfilt(B,A, phase_difference)

phase_shift = fun.interp1_for_remco(FreqTransfer,phase_difference_smooth,AngleSetFreq)
phase_difference_shifted = phase_difference_smooth - phase_shift
#%% Time correction from phase data
phase_mark = 50
phase_at_mark = fun.interp1_for_remco(FreqTransfer,phase_difference_shifted,phase_mark)
TimeCorrection = phase_at_mark/360/phase_mark
display(['Calculated TimeCorrection is: ' + str(TimeCorrection)])
# Saving of time correction for further use
if (Adjust_time_correction == 1) and (Adjust_gain == 1):
    if abs(TimeCorrection) > 0.001/BodeSampFreq:
        display(['Time correction used'])
        time_corrections[Test_id-1] = time_corrections[Test_id-1] + (1 / 0.9)*TimeCorrection
    else:
        display(['TimeCorrection not used'])
else:
    display(['TimeCorrection not used'])
#%% Save timecorrections and sensitivities
os.chdir(Main_folder_path)
np.savetxt('time_corrections.csv',time_corrections)
np.savetxt('sensitivities.csv',sensitivities)
#%% Plotting
plt.rcParams.update({'font.size':18})                                          # Change font size
yScaleBode = [-10,10]
yScalePhase = [-5,5]
x_tick = [10,25,50,75,100,125,150,175,200]

TitleFontSize=12
LabelFontSize=16
BodeLineWidth=3
if Make_plots:  
    plt.figure(num = 'Raw data')
    plt.plot(TimeOpt, optical_sensor_data,label = 'Optical')
    plt.plot(TimeRefShifted, reference_sensor_data, label= 'Reference')
    plt.legend(prop = {"size":12})
    plt.title('Shifted data', fontsize = TitleFontSize)
    plt.ylabel('Acceleration [g]', fontsize = LabelFontSize)
    plt.xlabel('Time[s]', fontsize = LabelFontSize)
    plt.grid(which = 'both')
    plt.minorticks_on()
    manager = plt.get_current_fig_manager()
    manager.window.showMaximized()
    plt.show()
    
    if Filter_on:
        plt.figure(num = 'Filtered data')
        plt.plot(TimeOpt, opt_sens_filtered, label = 'Optical')
        plt.plot(TimeRefShifted, ref_sens_filtered, label = 'Reference')
        plt.legend()
        plt.title('Filtered data', fontsize = TitleFontSize)
        plt.ylabel('Acceleration [g]', fontsize = LabelFontSize)
        plt.xlabel('Time[s]', fontsize = LabelFontSize)
        plt.grid(which = 'both')
        plt.minorticks_on()
        manager = plt.get_current_fig_manager()
        manager.window.showMaximized()
        plt.show()
    
    plt.figure(num = 'Resized filtered data')
    plt.plot(TimeOptSensResized, OptSensResized, label = 'Optical')
    plt.plot(TimeRefSensResized, RefSensResized, label = 'Reference')
    plt.legend()
    plt.title('Resampled and resized data of ' + Opt_name[Test_id-1], fontsize=TitleFontSize)
    plt.ylabel('Acceleration [g]', fontsize = LabelFontSize)
    plt.xlabel('Time[s]', fontsize = LabelFontSize)
    plt.grid(which = 'both')
    plt.minorticks_on()
    manager = plt.get_current_fig_manager()
    manager.window.showMaximized()
    plt.show()
   
    if Do_spectrum:
        plt.figure(num = 'Power spectrum')
        plt.plot(FreqOptPSD, 20*np.log(abs(SmoothOptPSD)), label = 'Optical')
        plt.plot(FreqRefPSD, 20*np.log(abs(SmoothRefPSD)), label = 'Reference')
        plt.legend()
        plt.title('Spectrum of ' + Opt_name[Test_id-1], fontsize = TitleFontSize)
        plt.ylabel('Spectral Density [dB]', fontsize = LabelFontSize)
        plt.xlabel('Frequency [Hz]', fontsize = LabelFontSize)
        plt.xlim(xScaleTransfer)
        plt.grid(which = 'both')
        plt.minorticks_on()
        manager = plt.get_current_fig_manager()
        manager.window.showMaximized()
        plt.show()
   
    plt.figure(num = 'Bode analysis')
    plt.plot(FreqTransfer, 20*np.log(abs(SmoothTransfer)), linewidth = BodeLineWidth)
    plt.title('Bode Analysis')#' of ' + Opt_name[Test_id-1], fontsize = TitleFontSize)
    plt.ylim(-10, 10)
    plt.xlabel('Frequency [Hz]', fontsize = LabelFontSize)
    plt.ylabel('Gain [dB]', fontsize = LabelFontSize)
    plt.xlim(xScaleTransfer)
    plt.grid(which = 'both')
    plt.minorticks_on()
    manager = plt.get_current_fig_manager()
    manager.window.showMaximized()
    plt.show()
    
    fig, axs = plt.subplots(2, num = 'Frequency response')
    axs[0].plot(FreqTransfer, 20*np.log(abs(SmoothTransfer)), linewidth = BodeLineWidth)
    axs[0].set_title('Bode')
    axs[0].set_xticks(x_tick)
    axs[0].set_xlim(xScale)
    axs[0].set_ylim(yScaleBode)
    axs[0].set_xlabel('Frequency [Hz]', fontsize = LabelFontSize)
    axs[0].set_ylabel('Gain [dB]', fontsize = LabelFontSize)
    axs[0].grid(which='both')
    axs[0].minorticks_on()
    axs[1].plot(FreqTransfer, phase_difference_shifted, linewidth = BodeLineWidth)
    axs[1].set_title('Phase')
    axs[1].set_xticks(x_tick)
    axs[1].set_xlim(xScale)
    axs[1].set_ylim(yScalePhase)
    axs[1].set_xlabel('Frequency [Hz]', fontsize = LabelFontSize)
    axs[1].set_ylabel('Phase [°]', fontsize = LabelFontSize)
    axs[1].grid(which='both')
    axs[1].minorticks_on()
    plt.tight_layout()
    manager = plt.get_current_fig_manager()
    manager.window.showMaximized()
    plt.show()