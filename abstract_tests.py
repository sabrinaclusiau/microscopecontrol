import logging
from internalProject.microscopeControl.abstract_external_communication import AbstractExternalCommunication
from internalProject.microscopeControl.abstract_commands import AbstractCommands


# TESTS
class AbstractTests:
    def test_connection(self, arbitrary_command, commands:AbstractCommands):
        """
        Tests the socket communication between the external PC and the PC SEM

        """
        if commands is None:
            return

        externalCommunication:AbstractExternalCommunication = commands.get_external_communication()
        if externalCommunication is not None:
            externalCommunication.validate_connection(arbitrary_command)

    def test_commands(self, commands:AbstractCommands):
        """
        Test text commands - results saved in speficied log file

        """
        if commands is None:
            return

        # Test getters
        instrument_name = commands.get_instrument_name()
        logging.info('Instrument name : ' + str(instrument_name))

        version = commands.get_version_information()
        logging.info('Version : ' + str(version))

        xMin, xMax, yMin, yMax, zMin, zMax, tMin, tMax, rMode = commands.get_movable_range_stage()
        logging.info('Xmin: ' + str(xMin) + ', Xmax: ' + str(xMax) + ', ' +
                     'Ymin: ' + str(yMin) + ', Ymax: ' + str(yMax) + ', ' +
                     'Zmin: ' + str(zMin) + ', Zmax: ' + str(zMax) + ', ' +
                     'Tmin: ' + str(tMin) + ', Tmax: ' + str(tMax) + ', Rmode: ' + str(rMode))

        result = commands.get_detector_high_mag()
        logging.info('Detector High Mag: ' + result)

        result = commands.get_detector_low_mag()
        logging.info('Detector Low Mag: ' + result)

        result = commands.get_detector_option()
        logging.info('Detector Option: ' + result)

        size, height = commands.get_sample_settings()
        logging.info('Sample Settings: size ' + str(size) + ', height ' + str(height))

        result = commands.get_HV_status()
        logging.info('HV status: ' + str(result))

        result = commands.get_HV_control()[0]
        logging.info('Vacc: ' + str(result))

        result = commands.get_emission_current()
        logging.info('Emission current: ' + str(result))

        result = commands.get_magnification()
        logging.info('Magnification: ' + str(result))

        result = commands.get_WD()
        logging.info('Working distance: ' + str(result))

        focus_coarse, focus_fine = commands.get_focus_value()
        logging.info('Coarse focus: ' + str(focus_coarse) + ', Fine focus: ' + str(focus_fine))

        result = commands.get_stage_position()
        logging.info('Stage position: ' + str(result))

        result = commands.get_detector_signal()
        logging.info('Detector Signals: ' + str(result))

        result = commands.get_scan_status()
        logging.info('Scan status: ' + str(result))

        result = commands.get_scan_speed_status()
        logging.info('Scan speed: ' + str(result))

        result = commands.get_scan_mode()
        logging.info('Scan mode: ' + str(result))

        result = commands.get_selected_screen()
        logging.info('Selected screen: ' + str(result))

        result = commands.get_stigma_current()
        logging.info('Stigma current: ' + str(result))

        result = commands.get_raster_rotation()
        logging.info('Raster rotation: ' + str(result))

        # Test setters

    def test_capture_settings(self, commands, project_name):
        pass