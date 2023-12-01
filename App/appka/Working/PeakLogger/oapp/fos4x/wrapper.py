# PeakLogger 3.17.8
# Script 1.5.1

from fos4x.fbg_calculations.spectrum import FBGSpectrumDecibelMilliWatt
from fos4x.fbg_calculations.spectrum_calculations import CenterOfGravityCalculation, GaussCalculation, SpectrumOpticalPowerEstimation, SNRCalculation, ReflectivityEstimation, AsymmetryCalculation, SLSCalculation

def get_spectrum_data(wavelengths, intensities):

    spectrum = FBGSpectrumDecibelMilliWatt(list(zip(wavelengths, intensities)))

    cog = CenterOfGravityCalculation(spectrum)
    gauss = GaussCalculation(spectrum)
    ref = ReflectivityEstimation(spectrum)
    snr = SNRCalculation(spectrum)
    asymmetry = AsymmetryCalculation(spectrum)
    sls = SLSCalculation(spectrum)

    cog_wavelength = cog.wavelength
    #sigma = gauss.estimated_sigma
    gauss_wavelength = gauss.wavelength
    gauss_fwhm = gauss.fwhm * 1000

    #print("Reflectivity: {}%".format(ref.reflectivity_percentage))
    #print("Optical Power: {:.1f}".format(ref.optical_power))
    #print("COG Wavelength: {:.3f} nm".format(cog.wavelength))
    #print("Sigma: {:.3f}".format(gauss.estimated_sigma))
    #print("Gauss Wavelength: {:.3f} nm".format(gauss.wavelength))
    #print("Gauss FWHM: {:.1f}".format(gauss.fwhm * 1000))
    #print("SNR: {:.2f} dBm".format(snr.snr))

    return cog_wavelength, gauss_wavelength, gauss_fwhm, ref.reflectivity, ref.optical_power, snr.snr, asymmetry.asymmetry, sls.sls

def get_optical_power_estimation(wavelengths, intensities, \
                                 r_wavelengths, r_intensities, \
                                 ase_wavelengths, ase_intensities):
    spectrum = FBGSpectrumDecibelMilliWatt(list(zip(wavelengths, intensities)))
    r_spectrum = FBGSpectrumDecibelMilliWatt(list(zip(r_wavelengths, r_intensities)))
    ase_spectrum = FBGSpectrumDecibelMilliWatt(list(zip(ase_wavelengths, ase_intensities)))
    mirror_damping = 0.6

    optical_power_estimation = SpectrumOpticalPowerEstimation(spectrum, r_spectrum, mirror_damping, ase_spectrum)
    return optical_power_estimation.optical_power

    