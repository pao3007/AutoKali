# PeakLogger 3.16.4
# Script 1.5.1

# ###################################################################
# Copyright fos4X GmbH. All rights reserved.
# Contact: info@fos4x.de
from typing import Optional

import numpy as np

from scipy.optimize import curve_fit
from scipy.signal import find_peaks

from .spectrum import FBGSpectrum, Wavelength


class SpectrumCalculation:
    def __init__(self, spectrum: FBGSpectrum):
        self._spectrum = spectrum

    @property
    def spectrum(self) -> FBGSpectrum:
        """FBGSpectrum : Spectrum data of the current calculation."""
        return self._spectrum


class WavelengthCalculation(SpectrumCalculation):
    @property
    def wavelength(self) -> Wavelength:
        raise NotImplementedError


class WindowedWavelengthCalculation(WavelengthCalculation):
    def __init__(self, spectrum: FBGSpectrum, window: float = 1.0):
        """
        Parameters
        ----------
        spectrum : FBGSpectrum
            Spectrum data to calculate the wavelength on.
        window : float, optional
            Width in nm of the data to calculate the wavelength on, centered around the intensity peak.

        Raises
        ------
        ValueError
            In case the window is too wide for the spectrum data.
        """
        super().__init__(spectrum)

        self._window = window

        min_index = self.window_slice.start
        max_index = self.window_slice.stop

        if min_index < 0:
            raise ValueError('FBGSpectrum not wide enough for chosen window. Too few data points left of intensity peak.')
        if max_index >= self.spectrum.wavelengths.size:
            raise ValueError('FBGSpectrum not wide enough for chosen window. Too few data points right of intensity peak.')

    @property
    def window(self) -> float:
        """float : Width of the data to fit in nm."""
        return self._window

    @property
    def window_slice(self) -> slice:
        """slice : Slice centered around the intensity peak +/- `window`."""
        window_in_samples = int(self.window / (self.spectrum.resolution * 2))

        return slice(self.spectrum.peak_index - window_in_samples, self.spectrum.peak_index + window_in_samples)


class GaussCalculation(WindowedWavelengthCalculation):
    """
    Calculates a Gaussian fit on a FBGSpectrum to determine the wavelength of the FBG.
    The Gaussian fit is calculated on the data centered around the intensity peak with a width specified as `window` in nm.
    """

    @property
    def estimated_sigma(self) -> float:
        """float : Estimated Sigma value to start the Gaussian fit."""
        wavelengths = self._spectrum.wavelengths
        intensity_mW = self._spectrum.intensities_mW

        sigma = np.sqrt(np.std(intensity_mW * (wavelengths - self._spectrum.peak_wavelenth)))

        return sigma

    @property
    def sigma(self) -> float:
        """float : Sigma value of the Gaussian fit."""
        (popt, _) = self.gauss_fit

        return popt[2]

    @property
    def wavelength(self) -> Wavelength:
        """float : Wavelength of the FBG in nm using a Gaussian fit."""
        (popt, _) = self.gauss_fit

        return popt[1]

    @property
    def gauss_fit(self):
        """tuple : First element holds the optimal values for the Gaussian fit, the second the estimated covariance."""

        def gauss(x, a, x0, sigma):
            return a * np.exp(-((x - x0) ** 2) / (2 * sigma ** 2))

        wavelengths = self.spectrum.wavelengths[self.window_slice]
        intensities = self.spectrum.intensities_mW[self.window_slice]

        popt, pcov = curve_fit(
            gauss,
            wavelengths,
            intensities,
            p0=[self._spectrum.intensities_mW.max(), self._spectrum.peak_wavelenth, self.estimated_sigma],
            bounds=([0, wavelengths[0], 0], [np.inf, wavelengths[-1], np.inf]),
        )

        return (popt, pcov)

    @property
    def fwhm(self) -> float:
        """float : The full width at half maximum of the Gaussian fit in nm."""
        fwhm = 2 * np.sqrt(2 * np.log(2)) * self.sigma

        return fwhm


class CenterOfGravityCalculation(WindowedWavelengthCalculation):
    """
    Calculates the Center of Gravity (COG) of a FBGSpectrum to determine the wavelength of the FBG.
    The COG is calculated on the data centered around the intensity peak with a width specified as `window` in nm.
    """

    @property
    def wavelength(self) -> Wavelength:
        """float : Wavelength of the FBG in nm using the COG."""
        wavelengths = self.spectrum.wavelengths[self.window_slice]
        intensities = self.spectrum.intensities_mW[self.window_slice]

        return np.multiply(wavelengths, intensities).sum() / intensities.sum()


class LPOCalculation(WavelengthCalculation):
    """
    Calculates the Linear Phase Operator (LPO) Wavelength of a FBGSpectrum.
    """

    def __init__(self, spectrum: FBGSpectrum, order: int = 100):
        """
        Parameters
        ----------
        spectrum : FBGSpectrum
            Spectrum data to calculate the COG on.
        order : int, optional
        """
        super().__init__(spectrum)

        self._order = order

    @property
    def __subPix(self) -> float:
        return self.__calcSubPixLPO(self.spectrum.intensities_mW, self.spectrum.peak_index, self._order)

    @classmethod
    def __calcSubPixLPO(cls, intensities, peak, order) -> float:
        if intensities[peak - 1] < intensities[peak + 1]:
            subPixPeak = peak + (cls.__gLPO(intensities, peak, order) / (cls.__gLPO(intensities, peak, order) - cls.__eLPO(intensities, peak + 1, order)))
        else:
            subPixPeak = (
                peak - 1 + (cls.__gLPO(intensities, peak - 1, order) / (cls.__gLPO(intensities, peak - 1, order) - cls.__eLPO(intensities, peak, order)))
            )

        return subPixPeak

    @staticmethod
    def __gLPO(intensity, peak, order):
        gLPOPix = 0.0
        for i in range(3, order + 1):
            if i % 2 == 1:
                a = int(((i - 1) / 2))
                gLPOPix = gLPOPix - intensity[peak - a] + intensity[peak + a]
        return gLPOPix

    @staticmethod
    def __eLPO(refSpectrum, peak, order):
        eLPOPix = 0.0
        for i in range(3, order + 1):
            if i % 2 == 1:
                a = int(((i - 1) / 2))
                eLPOPix = eLPOPix - refSpectrum[peak - a] + refSpectrum[peak + a]
        return eLPOPix

    @property
    def wavelength(self) -> Wavelength:
        """float : Wavelength of the FBG in nm using the LPO."""
        sub_pix = self.__subPix

        return self.spectrum.wavelengths[int(sub_pix)] + self.spectrum.resolution * (sub_pix % 1.0)


class AsymmetryCalculation(SpectrumCalculation):
    """
    Calculates the asymmetry of a FBGSpectrum centered around the intensity peak.
    """

    def __init__(self, spectrum: FBGSpectrum, window: float = 1.0):
        """
        Parameters
        ----------
        spectrum : FBGSpectrum
            Spectrum data to calculate the asymmetry on.
        window : float, optional
            Width of the considered spectrum data, centered around the intensity peak in nm.

        Raises
        ------
        ValueError
            In case the window is too wide for the spectrum data.
        """
        super().__init__(spectrum)

        self._gauss = GaussCalculation(spectrum, window)
        self._cog = CenterOfGravityCalculation(spectrum, window)

    @property
    def asymmetry(self) -> float:
        """float : Asymmetry value in nm."""
        return self._cog.wavelength - self._gauss.wavelength


class ReflectivityEstimation(SpectrumCalculation):
    """
    Estimates the reflectivity of the FBG.
    """

    def __init__(
        self, spectrum: FBGSpectrum, lower_wavelength: Wavelength = 1515.0, upper_wavelength: Wavelength = 1580.0, reflectivity_coefficient: float = 0.1
    ):
        """
        Parameters
        ----------
        spectrum : FBGSpectrum
            Spectrum data to estimate its reflectivity.
        lower_wavelength : float, optional
            The lower wavelength boundary in nm of the FBG. Data below this value is discarded.
        upper_wavelength : float, optional
            The upper wavelength boundary in nm of the FBG. Data above this value is discarded.
        reflectivity_coefficient : float, optional
            Measurement device specific coefficient used to estimate the reflectivity.

        Raises
        ------
        ValueError
            In case upper/lower wavelengths are outside of spectrum data.
        """
        super().__init__(spectrum)

        self._lower_wavelength = lower_wavelength
        self._upper_wavelength = upper_wavelength

        self._reflectivity_coefficent = reflectivity_coefficient

        if self._lower_wavelength < self.spectrum.wavelengths.min():
            raise ValueError("Lower wavelength below spectrum's minimum wavelength.")

        if self._upper_wavelength > self.spectrum.wavelengths.max():
            raise ValueError("Lower wavelength above spectrum's maximum wavelength.")

    @property
    def optical_power(self) -> float:
        """float : The estimated optical power in µW returned from the FBG, normalized to 1 mW input power."""
        mask = (self.spectrum.wavelengths > self._lower_wavelength) & (self.spectrum.wavelengths < self._upper_wavelength)

        wavelengths = self.spectrum.wavelengths[mask]
        intensities = self.spectrum.intensities_mW[mask]

        integral = np.trapz(intensities, wavelengths)

        return integral * 1000.0

    @property
    def reflectivity(self) -> float:
        """float : Estimated reflectivity of the FBG ranging from 0.0 to 1.0."""
        return self.spectrum.intensities_mW[self.spectrum.peak_index] / self._reflectivity_coefficent

    @property
    def reflectivity_percentage(self) -> int:
        """int : Estimated reflectivity of the FBG in percent."""
        return int(self.reflectivity * 100)


class SNRCalculation(SpectrumCalculation):
    """
    Calculates the Signal to Noise Ratio (SNR) of a spectrum.
    """

    def __init__(
        self,
        spectrum: FBGSpectrum,
        lower_baseline_wavelength: Wavelength = 1530.0,
        upper_baseline_wavelength: Wavelength = 1570.0,
        lower_signal_wavelength: Wavelength = 1500.0,
        upper_signal_wavelength: Wavelength = 1600.0,
    ):
        """
        Parameters
        ----------
        spectrum : FBGSpectrum
            The spectrum to calculate the SNR on.
        lower_baseline_wavelength : float, optional
            Data below this value considered noise. In nm.
        upper_baseline_wavelength : float, optional
            Data above this value considered noise. In nm.
        lower_signal_wavelength : float, optional
            The lower wavelength in nm of the signal to consider.
        upper_signal_wavelength : float, optional
            The upper wavelength in nm of the signal to consider.

        Raises
        ------
        ValueError
            If baseline wavelengths are not within signal wavelength or any of the wavelength boundaries are outside of spectrum data.
        """
        super().__init__(spectrum)

        self._lower_baseline_wavelength = lower_baseline_wavelength
        self._upper_baseline_wavelength = upper_baseline_wavelength

        self._lower_signal_wavelength = lower_signal_wavelength
        self._upper_signal_wavelength = upper_signal_wavelength

        #if self._lower_baseline_wavelength < self._lower_signal_wavelength:
        #    raise ValueError("Lower baseline wavelength below lower signal wavelength.")
        #if self._upper_baseline_wavelength > self._upper_signal_wavelength:
        #    raise ValueError("Upper baseline wavelength above upper signal wavelength.")
        
        #if self._lower_baseline_wavelength < self.spectrum.wavelengths.min():
        #    raise ValueError("Lower baseline wavelength below spectrum's minimum wavelength.")
        #if self._upper_baseline_wavelength > self.spectrum.wavelengths.max():
        #    raise ValueError("Upper baseline wavelength above spectrum's maximum wavelength.")
        
        #if self._lower_signal_wavelength < self.spectrum.wavelengths.min():
        #    raise ValueError("Lower signal wavelength below spectrum's minimum wavelength.")
        #if self._upper_signal_wavelength > self.spectrum.wavelengths.max():
        #    raise ValueError("Upper signal wavelength above spectrum's maximum wavelength.")

    @property
    def baseline(self) -> np.ndarray:
        """np.ndarray : Returns a mask that can be used on the spectrum data to retrieve the values considered noise."""
        return (self.spectrum.wavelengths < self._lower_baseline_wavelength) | (self.spectrum.wavelengths > self._upper_baseline_wavelength)

    @property
    def signal(self) -> np.ndarray:
        """np.ndarray : Returns a mask that can be used on the spectrum data to retrieve the values considered to be the signal."""
        return (self.spectrum.wavelengths > self._lower_signal_wavelength) & (self.spectrum.wavelengths < self._upper_signal_wavelength)

    @property
    def snr(self) -> float:
        """np.ndarray : Return the SNR in dBm."""
        return self.spectrum.intensities_dBm[self.baseline].mean() - self.spectrum.intensities_dBm[self.signal].max()


class SLSCalculation(SpectrumCalculation):
    """
    Calculates the Side Lobe Suppression (SLS) of the spectrum.
    """

    def __init__(self, spectrum: FBGSpectrum, minimum_prominence: float = 3.0, maximum_prominence: float = 30.0, lower_intensity_cutoff: float = -60.0):
        """
        Parameters
        ----------
        spectrum : FBGSpectrum
            The spectrum to calculate the side lobe.
        minimum_prominence : float, optional
            The minimum prominence in dBm of the side lobe.
        maximum_prominence :
            The maximum prominence in dBm of the side lobe.
        lower_intensity_cutoff : float, optional
            The lower spectrum intensity in dBm, that is considered when searching for the side lobe.
        """
        super().__init__(spectrum)

        self._minimum_prominence = minimum_prominence
        self._maximum_prominence = maximum_prominence

        self._lower_intensity_cutoff = lower_intensity_cutoff

    @property
    def side_lobe_index(self) -> int:
        """int: Spectrum index of the highest side lobe."""
        max_intensity = self.spectrum.intensities_dBm[self.spectrum.peak_index]

        height = (self._lower_intensity_cutoff, max_intensity)
        prominence = (self._minimum_prominence, self._maximum_prominence)

        peaks, _ = find_peaks(self.spectrum.intensities_dBm, height, prominence=prominence)

        highest_peak = np.argmax(self.spectrum.intensities_dBm[peaks])

        return peaks[highest_peak]

    @property
    def sls(self) -> float:
        """float: Side Lobe Suppression in dB."""
        max_intensity = self.spectrum.intensities_dBm[self.spectrum.peak_index]
        max_side_lobe = self.spectrum.intensities_dBm[self.side_lobe_index]

        return max_intensity - max_side_lobe


class ReferenceValueEstimation(ReflectivityEstimation):
    """
    Calculates a rough estimation of the spectrum's reference value on a BlackBird device.
    """

    def __init__(
        self,
        spectrum: FBGSpectrum,
        device_coefficient: float,
        reflectivity_coefficient: float = 0.1,
        lower_wavelength: Wavelength = 1545.0,
        upper_wavelength: Wavelength = 1560.0,
    ):
        """
        Parameters
        ----------
        spectrum :
            The spectrum to calculate the reference value.
        device_coefficient : float, optional
            BlackBird specific coefficient.
        reflectivity_coefficient : float, optional
            Measurement device specific coefficient used to estimate the reflectivity.
        lower_wavelength : float, optional
            The lower wavelength boundary in nm of the FBG. Data below this value is discarded.
        upper_wavelength : float, optional
            The upper wavelength boundary in nm of the FBG. Data above this value is discarded.
        """
        super().__init__(spectrum, lower_wavelength, upper_wavelength, reflectivity_coefficient)

        self._device_coefficient = device_coefficient

    @property
    def reference(self) -> int:
        """int : Estimated reference value."""
        return int(self._device_coefficient * self.optical_power / 1000.0)


class SpectrumOpticalPowerEstimation:
    """
    Estimates the equivalent BlackBird optical power of a spectrum.
    """

    def __init__(self, spectrum: FBGSpectrum, mirror_spectrum: FBGSpectrum, mirror_damping: float, ase_spectrum: Optional[FBGSpectrum] = None):
        """
        Parameters
        ----------
        spectrum : FBGSpectrum
            The spectrum to estimate the optical power
        mirror_spectrum : FBGSpectrum
            Spectrum data of a mirror captured with same measurement device as the `spectrum` measured.
        mirror_damping : float
            Damping of the mirror in dB.
        ase_spectrum : FBGSpectrum, optional
            Additional reference ASE spectrum.
        """
        self.spectrum = spectrum
        self.mirror_spectrum = mirror_spectrum
        self.mirror_damping = mirror_damping
        self.ase_spectrum = ase_spectrum

        if ase_spectrum is not None:
            self.ase_normed = ase_spectrum * (1 / ase_spectrum.intensities_mW[ase_spectrum.peak_index])

            self.spectrum_filtered = spectrum * ase_spectrum
            self.mirror_filtered = mirror_spectrum * ase_spectrum
        else:
            self.spectrum_filtered = spectrum
            self.mirror_filtered = mirror_spectrum

    @property
    def optical_power(self) -> float:
        """float : Estimated optical power in µW, normalized to 1 mW input power."""

        lower_wavelength = max(self.spectrum_filtered.wavelengths.min(), self.mirror_filtered.wavelengths.min())
        upper_wavelength = min(self.spectrum_filtered.wavelengths.max(), self.mirror_filtered.wavelengths.max())

        spectrum_estimator = ReflectivityEstimation(self.spectrum_filtered, lower_wavelength, upper_wavelength)
        mirror_estimator = ReflectivityEstimation(self.mirror_filtered, lower_wavelength, upper_wavelength)

        return (spectrum_estimator.optical_power / mirror_estimator.optical_power) * 10 ** (self.mirror_damping / 10) * 1000.0
