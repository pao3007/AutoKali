# PeakLogger 3.16.4
# Script 1.5.1

# ###################################################################
# Copyright fos4X GmbH. All rights reserved.
# Contact: info@fos4x.de

from typing import NamedTuple


class BlackbirdOpticalPowerCalibration(NamedTuple):
    """Provides required parameters for the BlackbirdOpticalPowerEstimation.

    Attributes
    ----------
    optical_output_power_gradient : float
        Increase of optical power output by device per percent point of laser power. Typically a value of 5.0. [µW/%]
    optical_output_power_offset : float
        Optical output power at `lower_laser_power_boundary`. [µW]
    optical_input_power_sensitivity : float
        Increase of reference value per optical power measured by device. Typically a value of 1.5e6. [digits/µW]
    optical_input_power_offset : int
        Offset of reference value. Typically a value of about 35000. [digits]
    lower_laser_power_boundary : int
        Lower boundary above which optical output power increases linearly by `optical_output_power_gradient`. [%]
    upper_laser_power_boundary : int
        Upper boundary below which optical output power increases linearly by `optical_output_power_gradient`. [%]
    """

    optical_output_power_gradient: float
    optical_output_power_offset: float

    optical_input_power_sensitivity: float
    optical_input_power_offset: int

    lower_laser_power_boundary: int = 50
    upper_laser_power_boundary: int = 100


class BlackbirdOpticalPowerEstimation:
    def __init__(self, reference: int, laser_power: int, calibration: BlackbirdOpticalPowerCalibration):
        """
        Parameters
        ----------
        reference : int
            Measured reference value.
        laser_power : int
            Laser power setting at time of measurement.
        calibration : BlackbirdOpticalPowerCalibration
            Optical Power Calibration of measurement device's socket used.

        Raises
        ------
        ValueError
            In case `laser_power` is out of range for `calibration`.
        """
        self.reference = reference
        self.laser_power = laser_power

        self.calibration = calibration

        if laser_power > calibration.upper_laser_power_boundary:
            raise ValueError("Laser Power too high for specified measurement device calibration.")
        if laser_power < calibration.lower_laser_power_boundary:
            raise ValueError("Laser Power too low for specified measurement device calibration.")

    @property
    def optical_output_power(self):
        """float : Estimated optical output power in µW of the socket."""
        return (
            self.calibration.optical_output_power_gradient * (self.laser_power - self.calibration.lower_laser_power_boundary)
            + self.calibration.optical_output_power_offset
        )

    @property
    def optical_return_power(self):
        """float : Estimated optical power returned to the measurement device's socket in µW."""
        return (self.reference - self.calibration.optical_input_power_offset) / self.calibration.optical_input_power_sensitivity

    @property
    def fbg_integrated_reflectivity_coefficient(self):
        """float : Reflectivity of the measured FBG."""
        return self.optical_return_power / self.optical_output_power

    @property
    def optical_power(self):
        """float : Estimated optical power returned with a 1mW light source in µW."""
        return self.fbg_integrated_reflectivity_coefficient * 1000.0
