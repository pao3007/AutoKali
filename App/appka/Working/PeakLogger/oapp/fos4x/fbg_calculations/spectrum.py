# PeakLogger 3.16.4
# Script 1.5.1

# ###################################################################
# Copyright fos4X GmbH. All rights reserved.
# Contact: info@fos4x.de

from typing import List, Tuple, Optional, Union

import numpy as np
from scipy.interpolate import interp1d

Wavelength = float
Intensity_dBm = float
Intensity_mW = float

SpectrumDataRaw_dBm = List[Tuple[Wavelength, Intensity_dBm]]
SpectrumDataRaw_mW = List[Tuple[Wavelength, Intensity_mW]]
SpectrumDataNumPy = np.ndarray


class FBGSpectrum:
    """Abstract Spectrum class"""

    def __init__(self, spectrum: Union[SpectrumDataRaw_dBm, SpectrumDataRaw_mW, SpectrumDataNumPy], resolution: Optional[float] = None):
        """
        Parameters
        ----------
        spectrum : SpectrumData
            Raw spectrum data, wavelengths in nm, intensity values in dBm.
            Can be either a list of wavelength-intensity tuples, or a 2-dimensional np.ndarray.
        resolution : float, optional
            Resolution of the spectrum in nm.
        """
        self._spectrum = np.array(spectrum)

        if resolution is None:
            self._resolution = self._get_resolution()
        else:
            self._resolution = resolution

    def _get_resolution(self) -> float:
        min_wavelength = self._spectrum[:, 0].min()
        max_wavelength = self._spectrum[:, 0].max()
        num_samples = self._spectrum[:, 0].size

        return (max_wavelength - min_wavelength) / (num_samples - 1)

    def __mul__(self, other: 'FBGSpectrum') -> 'FBGSpectrum':
        if isinstance(other, (int, float)):
            intensities = self.intensities_mW * other
            return FBGSpectrumMilliWatt(list(zip(self.wavelengths, intensities)))

        elif isinstance(other, np.ndarray):
            if self.intensities_mW.shape != other.shape:
                raise ValueError("Multiplication array must be the same shape as intensities: {}!".format(self.intensities_mW.shape))

            intensities = self.intensities_mW * other
            return FBGSpectrumMilliWatt(list(zip(self.wavelengths, intensities)))

        elif isinstance(other, FBGSpectrum):
            lower_wavelength = max(self.wavelengths.min(), other.wavelengths.min())
            upper_wavelength = min(self.wavelengths.max(), other.wavelengths.max())
            resolution = max(self.resolution, other.resolution)

            spectrum_a = self.__resample_spectrum(self, resolution, lower_wavelength, upper_wavelength)
            spectrum_b = self.__resample_spectrum(other, resolution, lower_wavelength, upper_wavelength)

            return self.__fold_spectra(spectrum_a, spectrum_b)

        else:
            raise NotImplementedError("Spectrum multiplication not implemented for '{}'".format(type(other)))

    @classmethod
    def __resample_spectrum(
        cls, spectrum: 'FBGSpectrum', resolution: float, lower_wavelength: Optional[float] = None, upper_wavelength: Optional[float] = None
    ) -> 'FBGSpectrumMilliWatt':
        """Resamples spectrum data with the specified resolution.

        Parameters
        ----------
        spectrum : FBGSpectrum
            Spectrum to be resampled.
        resolution : float
            New resolution in nm.
        lower_wavelength : float, optional
            New lower wavelength of the resampled spectrum.
        upper_wavelength : float, optional
            New upper wavelength of the resampled spectrum.

        Returns
        -------
        FBGSpectrumMilliWatt
            Resampled spectrum.
        """

        if lower_wavelength is None:
            lower_wavelength = spectrum.wavelengths.min()
        if upper_wavelength is None:
            upper_wavelength = spectrum.wavelengths.max()

        resampled_wavelengths = np.arange(lower_wavelength, upper_wavelength, resolution)

        resampled_intensities = interp1d(spectrum.wavelengths, spectrum.intensities_mW)(resampled_wavelengths)

        resampled_spectrum = FBGSpectrumMilliWatt(list(zip(resampled_wavelengths, resampled_intensities)), resolution)

        return resampled_spectrum

    @classmethod
    def __fold_spectra(cls, spectrum_a: 'FBGSpectrum', spectrum_b: 'FBGSpectrum') -> 'FBGSpectrumMilliWatt':
        """Folds two spectra.
        The spectra need to have the same resolution.
        The returned spectrum width is the wavelengths both inputs have in common.

        Parameters
        ----------
        spectrum_a : FBGSpectrum
        spectrum_b : FBGSpectrum

        Returns
        -------
        FBGSpectrumMilliWatt

        """
        if spectrum_a.resolution != spectrum_b.resolution:
            raise ValueError("Both spectra need to have the same resolution.")

        lower_wavelength = max(spectrum_a.wavelengths.min(), spectrum_b.wavelengths.min())
        upper_wavelength = min(spectrum_a.wavelengths.max(), spectrum_b.wavelengths.max())

        if lower_wavelength >= upper_wavelength:
            raise ValueError("The spectra do not overlap.")

        mask_a = np.where((spectrum_a.wavelengths >= lower_wavelength) & (spectrum_a.wavelengths <= upper_wavelength))
        mask_b = np.where((spectrum_b.wavelengths >= lower_wavelength) & (spectrum_b.wavelengths <= upper_wavelength))

        folded_intensities = spectrum_a.intensities_mW[mask_a] * spectrum_b.intensities_mW[mask_b]
        wavelengths = spectrum_a.wavelengths[mask_a]

        return FBGSpectrumMilliWatt(list(zip(wavelengths, folded_intensities)))

    @property
    def resolution(self) -> float:
        """float : Resolution of the spectrum in nm."""
        return self._resolution

    @property
    def intensities_dBm(self) -> np.ndarray:
        """np.ndarray : One dimensional np.ndarray containing the intensities of the spectrum in dBm."""
        raise NotImplementedError

    @property
    def intensities_mW(self) -> np.ndarray:
        """np.ndarray : One dimensional np.ndarray containing the intensities of the spectrum in mW, normalized to 1 mW input power."""
        raise NotImplementedError

    @property
    def wavelengths(self) -> np.ndarray:
        """np.ndarray : One dimensional np.ndarray containing the wavelengths of the spectrum."""
        return self._spectrum[:, 0].copy()

    @property
    def peak_index(self) -> int:
        """int : Index of the intensity maximum."""
        intensity_mW = self.intensities_mW
        return intensity_mW.argmax()

    @property
    def peak_wavelenth(self) -> Wavelength:
        """float : Wavelength in nm of the intensity maximum."""
        return self.wavelengths[self.peak_index]


class FBGSpectrumDecibelMilliWatt(FBGSpectrum):
    """Spectrum from raw data in dBm."""

    def __init__(self, spectrum: Union[SpectrumDataRaw_dBm, SpectrumDataNumPy], resolution: Optional[float] = None):
        """
        Parameters
        ----------
        spectrum : SpectrumData
            Raw spectrum data, wavelengths in nm, intensity values in dBm.
            Can be either a list of wavelength-intensity tuples, or a 2-dimensional np.ndarray.
        resolution : float, optional
            Resolution of the spectrum in nm.
        """
        super().__init__(spectrum, resolution)

    @property
    def intensities_dBm(self) -> np.ndarray:
        """np.ndarray : One dimensional np.ndarray containing the intensities of the spectrum in dBm."""
        return self._spectrum[:, 1].copy()

    @property
    def intensities_mW(self) -> np.ndarray:
        """np.ndarray : One dimensional np.ndarray containing the intensities of the spectrum in mW, normalized to 1 mW input power."""
        return 10 ** (self.intensities_dBm / 10)


class FBGSpectrumMilliWatt(FBGSpectrum):
    """Spectrum from raw data in MilliWatt"""

    def __init__(self, spectrum: Union[SpectrumDataRaw_mW, SpectrumDataNumPy], resolution: Optional[float] = None):
        """
        Parameters
        ----------
        spectrum : SpectrumData
            Raw spectrum data, wavelengths in nm, intensity values in mW.
            Can be either a list of wavelength-intensity tuples, or a 2-dimensional np.ndarray.
        resolution : float, optional
            Resolution of the spectrum in nm.
        """
        super().__init__(spectrum, resolution)

    @property
    def intensities_dBm(self) -> np.ndarray:
        """np.ndarray : One dimensional np.ndarray containing the intensities of the spectrum in dBm."""
        return 10 * np.log10(self.intensities_mW)

    @property
    def intensities_mW(self) -> np.ndarray:
        """np.ndarray : One dimensional np.ndarray containing the intensities of the spectrum in mW, normalized to 1 mW input power."""
        return self._spectrum[:, 1].copy()
