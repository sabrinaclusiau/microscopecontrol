class AbstractCommands:
    def __init__(self):
        self.external_communication = None
        self.instantiate_external_communication()

    def instantiate_external_communication(self):
        pass

    # Getters
    def get_external_communication(self):
        return self.external_communication

    def get_instrument_name(self):
        """ SEM returns model name"""
        return ''

    def get_version_information(self):
        """SEM returns program version"""
        return ''

    def get_HV_status(self):
        """SEM returns HV ON/OFF status """
        return 0

    def get_HV_control(self):
        """SEM returns present acceleration voltage (Vacc) and deceleration voltage (Vdec)"""
        return 0, 0

    def get_emission_current(self):
        """SEM returns set value and preset actual value of emission current"""
        return 0, 0

    def get_probe_current_and_cond1(self):
        """SEM returns the value for the probe current and Cond1"""
        return 0, 0

    def get_magnification(self):
        """SEM returns present magnification mode (High-Mag/Low-Mag) and magnification value"""
        return 0, 0

    def get_WD(self):
        """SEM returns present WD (working distance) value calculated from focus current"""
        return 0

    def get_focus_value(self):
        """SEM returns focus current DAC value (focus coarse and fine)"""
        return 0, 0

    def get_stage_position(self):
        """SEM returns present stage coordinates (5 axes, X, Y, Z, T, R)"""
        return 0, 0, 0, 0, 0

    def get_movable_range_stage(self):
        """SEM returns present movable range of stage"""
        return 0, 0, 0, 0, 0, 0, 0, 0, 0

    def get_detector_signal(self):
        return ''

    def get_detector_high_mag(self):
        """SEM returns signal names assignable to image screen"""
        return ''

    def get_detector_low_mag(self):
        """SEM returns signal names assignable to image screen"""
        return ''

    def get_detector_option(self):
        """SEM returns signal names of optional detectors assignable to image screen"""
        return ''

    def get_sample_settings(self):
        """SEM returns present specified sample size and height setting"""
        return 0, 0

    def get_scan_status(self):
        """SEM returns present scan status"""
        return ''

    def get_scan_speed_status(self):
        """SEM returns present scan speed and number of averaging frames."""
        return 0, 0

    def get_scan_mode(self):
        """SEM returns present scan mode"""
        return 0

    def get_selected_screen(self):
        """SEM returns screen number that is selected as target of operation."""
        return 0

    def get_photo_size(self):
        """SEM returns screen mode and Photo-size."""
        return 0, 0

    def get_probe_current_and_cond1(self):
        """SEM return present Probe current mode and Cond.1 setting."""

    def get_stigma_current(self):
        """SEM returns present stigma current X, Y """
        return 0, 0

    def get_raster_rotation(self):
        """SEM returns present Raster Rotation status, on/off and rotation angle."""
        return 0, 0

    # Setters
    def set_external_communication(self, external_communication):
        self.external_communication = external_communication

    def set_HV_status(self, on_off):
        """This command sets HV ON/OFF status. """

    def set_HV_control(self, vacc):
        """This command sets acceleration voltage.
            return : True if command can be executed
        """
        return False

    def set_emission_current(self, emission_current):
        """This command sets the emission current.
            return : True if command can be executed
        """
        return False

    def set_probe_current_and_cond1(self):
        """This command sets the probe current and Cond1"""

    def set_magnification(self, magnification):
        """This command sets the magnification."""

    def set_magnification_mode(self, mag_mode):
        """This command sets the magnification mode."""

    def set_WD(self, wd):
        """This command sets the WD (working distance) value and set focus current.
            return : True if command can be executed
        """
        return False

    def set_focus_value(self, coarse_value, fine_value):
        """This command sets focus current DAC value.
            return : True if command can be executed
        """
        return False

    def set_stage_position(self, x, y, z, t, r):
        """This command drives stage specifying all 5 axes coordinates value. Movable range of stage can be read using
            get_movable_range_stage command. Write present coordinates value for axes not to be moved. Present stage
            position can be read using get_stage_position
            return : True if command can be executed
        """
        return False

    def set_home_position(self):
        """This command drives stage to home position."""

    def set_move_constant_speed(self, **kwargs):
        """This command drives stage to specified direction with constant specified speed.
            kwargs: any parameters needed to move stage at constant speed
        """

    def set_stage_move_stop(self):
        """This command stops stage motion if sent during stage is moving."""

    def set_detectors(self, list_of_signals):
        """This command sets signal name for image screens.
            kwargs: any parameters needed to select signals
        """

    def set_scan_status(self, status):
        """This command sets scan status."""

    def set_scan_speed(self, speed):
        """This command sets scan speed.
            return : True if command can be executed
        """
        return False

    def set_scan_mode(self, mode):
        """This command sets scan mode.
            return : True if command can be executed
        """
        return False

    def set_selected_screen(self, selected_screen):
        """This command sets the selected screen."""

    def set_direct_save(self, arg):
        """This command freezes image if running and saves image. """

    def set_capture_settings(self, scan_mode, resolution, scan_time, integration_number):
        """This command sets parameters for image capturing.
            return : True if command can be executed
        """
        return False

    def set_capture_and_save(self, arg, project_name='', newFileName=''):
        """This command runs image capturing and save captured image(s)."""
        return ''

    def set_alignment_set(self, mode, x_value, y_value):
       """This command sets axial alignment data. Alignment current is set and electron optical column axis will be changed."""

    def set_stigma(self, x_value, y_value):
        """This command sets stigma current."""

    def set_raster_rotation(self, onoff, angle):
        """This command sets On/Off and angle of raster rotation."""

    def set_flashing(self, flashing_mode):
        """This command executes flashing.
            return : True if command can be executed
        """
        return False

    def set_auto_focus(self):
        """This command executes auto-focus."""

    def set_auto_stigma(self):
        """This command executes auto-stigma."""

    def set_beam_monitor_adjust(self):
        """This command executes beam monitor adjustment."""

    def set_contrast_adjust(self, value):
        """This command adjusts image contrast. Plus values increases and minus value decreases image contrast."""

    def set_brightness_adjust(self, value):
        """This command adjusts image brightness. Plus value increases and minus value decreases image brightness."""

    def set_image_shift_X(self, value):
        """This command moves image in horizontal direction by image shift function. Large value moves large distance.
            When image shift value exceeds its movable range, image will not move (not error returned).
        """

    def set_image_shift_Y(self, value):
        """This command moves image in vertical direction by image shift function. Large value moves large distance.
            When image shift value exceeds its movable range, image will not move (not error returned).
        """

