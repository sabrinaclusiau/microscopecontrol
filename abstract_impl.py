import logging
from .abstract_commands import AbstractCommands

class AbstractImpl:
    def __init__(self):
        self.currentState = {}
        # self.save_current_state()  # Takes too long, uncomment when ready

        # Microscope parameters
        self.commands = None
        self.instantiate_microscope_commands()
        self._magnification = 100000
        self._voltage = 5  # kV
        self._workingDistance = 7000  # in um
        self._emissionCurrent = 20  # in uA
        self._scanSpeed = 'SLOW2'
        self._scanMode = 'Normal Scan'

        # Image capture settings
        self._filePath = f'D:\\'
        self._xPixelSize = 640
        self._yPixelSize = 480
        self._captureSettings = {'scan_mode': 'Slow',
                                 'resolution': f'{self._xPixelSize}x{self._yPixelSize}',
                                 'scan_time': '80',
                                 'integration_number': '8'}
        self._selectedScreen = 'screen1'
        self._saveStatus = 'Single'

    def instantiate_microscope_commands(self):
        return

    def get_microscope_commands(self):
        return self.commands

    def initialize_default_settings(self):
        pass

    def save_current_state(self):
        commands = self.get_microscope_commands()
        if commands is None:
            return

        self.currentState['hv_status'] = commands.get_HV_status()
        self.currentState['v_acc'] = commands.get_HV_control()[0]
        self.currentState['emission_current_values'] = commands.get_emission_current()
        self.currentState['magnification'] = commands.get_magnification()
        self.currentState['WD'] = commands.get_WD()
        self.currentState['focus_coarse_fine'] = commands.get_focus_value()
        self.currentState['stage_position'] = commands.get_stage_position()
        self.currentState['detectors_signals'] = commands.get_detector_signal()
        self.currentState['scan_status'] = commands.get_scan_status()
        self.currentState['scan_speed'] = commands.get_scan_speed_status()
        self.currentState['scan_mode'] = commands.get_scan_mode()
        self.currentState['selected_screen'] = commands.get_selected_screen()
        self.currentState['stigma_current'] = commands.get_stigma_current()
        self.currentState['raster_rotation'] = commands.get_raster_rotation()
        self.currentState['probe_current_cond1'] = commands.get_probe_current_and_cond1()

    def update_current_state(self,  key, get_command):
        pass

    def reset_to_last_saved_state(self):
        commands = self.get_microscope_commands()
        if commands is None:
            return

        commands.set_HV_status(on_off=self.currentState['hv_status'])
        commands.set_HV_control(vacc=self.currentState['v_acc'])
        commands.set_emission_current(emission_current=self.currentState['emission_current_values'])
        commands.set_magnification_mode(mag_mode=self.currentState['magnification'][0])
        commands.set_magnification(magnification=self.currentState['magnification'][1])
        commands.set_WD(wd=self.currentState['WD'])
        commands.set_focus_value(coarse_value=self.currentState['focus_coarse_fine'][0],
                             fine_value=self.currentState['focus_coarse_fine'][1])
        commands.set_stage_position(x=self.currentState['stage_position'][0],
                                y=self.currentState['stage_position'][1],
                                z=self.currentState['stage_position'][2],
                                t=self.currentState['stage_position'][3],
                                r=self.currentState['stage_position'][4])
        commands.set_detectors(list(self.currentState['detectors_signals']))
        commands.set_scan_status(self.currentState['scan_status'])
        commands.set_scan_speed(self.currentState['scan_speed'])
        commands.set_scan_mode(self.currentState['scan_mode'])
        commands.set_selected_screen(self.currentState['selected_screen'])
        commands.set_stigma(x_value=self.currentState['stigma_current'][0],
                        y_value=self.currentState['stigma_current'][1])
        commands.set_raster_rotation(onoff=self.currentState['raster_rotation'][0],
                                 angle=self.currentState['raster_rotation'][1])
        commands.set_probe_current_and_cond1(probe_current=self.currentState['probe_current_cond1'][0],
                                             cond1=self.currentState['probe_current_cond1'][1])

    def getCurrentState(self):
        return self.currentState

    def getMagnification(self):
        return self._magnification

    def setMagnification(self, magnification):
        self._magnification = magnification

    def setCaptureSettingsForMicroscope(self):
        commands = self.get_microscope_commands()
        if commands is None:
            return

        return commands.set_capture_settings(scan_mode=self._captureSettings['scan_mode'],
                                             resolution=self._captureSettings['resolution'],
                                             scan_time=self._captureSettings['scan_time'],
                                             integration_number=self._captureSettings['integration_number'])

