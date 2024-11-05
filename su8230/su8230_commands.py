import logging
from ..abstract_commands import AbstractCommands
from .su8230_external_communication import Su8230ExternalCommunication

class Su8230Commands(AbstractCommands):
    mag_modes = {'High-Mag': 0, 'Low-Mag': 1}
    scan_speeds = {'Rapid1': 10, 'Rapid2': 11, 'FAST1': 12, 'FAST2': 13, 'SLOW1': 20, 'SLOW2': 21, 'SLOW3': 22,
                   'SLOW4': 23, 'SLOW5': 24, 'SLOW6': 25, 'SLOW7': 26, 'CSS1': 30, 'CSS2': 31, 'CSS3': 32, 'CSS4': 33,
                   'CSS5': 34, 'CSS6': 35, 'CSS7': 36, 'REDUCE1': 40, 'REDUCE2': 41, 'REDUCE3': 42}

    scan_mode = {'Normal Scan': 0, 'Spot Position Set': 1, 'Spot mode': 2, 'Area Position Set': 3, 'Area Scan mode': 4}
    selected_screens = {'screen1': 0, 'screen2': 0, 'screen3': 0, 'screen4': 0, 'screenMix': 0}
    alignment_mode = {'Beam Alignment': 0, 'Aperture Alignment': 1, 'Stigma X Alignment': 2,
                      'Stigma Y Alignment': 3, 'ULV Alignment': 4, 'Low Mag Position': 5}
    probe_current = {'Normal': 0, 'High': 1}
    flashing_modes = {'Mild': 0, 'Normal': 1}
    # Capture settings
    capture_scan_mode = {'Rapid': 0, 'Fast': 1, 'Slow': 2, 'CSS': 3, 'Slow1Integration': 4}
    capture_resolution = {'640x480': 0, '1280x960': 1, '2560x1920': 2, '5120x3840': 3}
    capture_scan_time = {'10': 0, '20': 1, '40': 2, '80': 3, '160': 4, '320': 5}
    capture_integration_number = {'8': 0, '16': 1, '32': 2, '64': 3, '128': 4, '256': 5, '512': 6, '1024': 7}

    def __init__(self):
        super().__init__()

    def instantiate_external_communication(self):
        self.external_communication = Su8230ExternalCommunication()
        self.external_communication.set_sem_dir_temp('V:/SemImage/temp')

    # Getters
    def get_instrument_name(self):
        """ SEM returns model name"""
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get InstructName ALL')
            if dictDecodedMessage is not None:
                instrumentName = dictDecodedMessage['data']
                return instrumentName

        return ''

    def get_version_information(self):
        """SEM returns program version"""
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get Version ALL')
            if dictDecodedMessage is not None:
                version = dictDecodedMessage['data']
                return version

        return ''

    def get_HV_status(self):
        """SEM returns HV ON/OFF status
            0: HV-OFF
            1: HV-ON
            2: HV-ON(Deceleration)
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get HVONOFF ALL')
            if dictDecodedMessage is not None:
                hvonoff = dictDecodedMessage['data']
                return int(hvonoff)

        return 0

    def get_HV_control(self):
        """SEM returns present acceleration voltage (Vacc) and deceleration voltage (Vdec)
            Vacc = 0 to 30 000 (0-30kV)
            Vdec = 0 to 3 500 (0-3.5kV)
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get HVCONTROL VACC')
            if dictDecodedMessage is not None:
                vacc, vdec = str(dictDecodedMessage['data']).split(',')
                vacc = float(vacc)/1000
                vdec = float(vdec)/1000
                return vacc, vdec

        return 0, 0

    def get_emission_current(self):
        """SEM returns set value and preset actual value of emission current
            set value: 1 to 500 (0.1 - 50 uA)
            actual value: 1 to 100 000 (0.1 - 10 000 uA)
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get EMISSION NOW')
            if dictDecodedMessage is not None:
                set_value, actual_value = str(dictDecodedMessage['data']).split(',')
                set_value = float(set_value)/1000
                actual_value = float(actual_value)/1000
                return set_value, actual_value
        return 0, 0

    def get_magnification(self):
        """SEM returns present magnification mode (High-Mag/Low-Mag) and magnification value
            Magnification mode:
                0: High-Mag
                1: Low-Mag
            Magnification value:
                5-8 000 000
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get MAGNIFICATION NOW')
            if dictDecodedMessage is not None:
                magmode, mag = str(dictDecodedMessage['data']).split(',')
                # Find string associated to value
                for aMode in self.mag_modes:
                    if int(magmode) == self.mag_modes[aMode]:
                        return aMode, int(mag)

        return '', 0

    def get_WD(self):
        """SEM returns present WD (working distance) value calculated from focus current
            WD: 1500 to 40000 (1.5 to 40.0 mm)
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get WD NOW')
            if dictDecodedMessage is not None:
                wd = dictDecodedMessage['data']
                return float(wd)

        return 0

    def get_focus_value(self):
        """SEM returns focus current DAC value (focus coarse and fine)"""
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get FOCUS NOW')
            if dictDecodedMessage is not None:
                coarse, fine = str(dictDecodedMessage['data']).split(',')
                return int(coarse), int(fine)

        return 0, 0

    def get_stage_position(self):
        """SEM returns present stage coordinates (5 axes, X, Y, Z, T, R)
            X: 0 to 110 000 000 (nm)
            Y: 0 to 110 000 000 (nm)
            Z: 1 500 000 to 40 000 000 (nm)
            T: -5 000 to 70 000 (-5.0 to 70.0 deg)
            R: 0 to 359 900 (0.0 to 359.9 deg)
            Stage controller uploads coordinates periodically to SEM PC when position changes 1 um or more. This command
            gets the coordinates value held in SEM PC. Response time is faster than get_stage_position_2 command, however
            the value has some delay from the actual position change and will heave error less than 1 um.
            If you need accurate value in the range smaller than 1 um, use get_stage_position_2 command.
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get STAGEUNIT MOVEXYZTR')
            if dictDecodedMessage is not None:
                x, y, z, t, r = str(dictDecodedMessage['data']).split(',')
                t = float(t) / 1000
                r = float(r) / 1000
                return int(x), int(y), int(z), t, r

        return 0, 0, 0, 0, 0

    def get_stage_position_2(self):
        """SEM returns present stage coordinates (5 axes, X, Y, Z, T, R)
            X: 0 to 110 000 000 (nm)
            Y: 0 to 110 000 000 (nm)
            Z: 1 500 000 to 40 000 000 (nm)
            T: -5 000 to 70 000 (-5.0 to 70.0 deg)
            R: 0 to 359 900 (0.0 to 359.9 deg)
            Accurate and precise value will be get from stage controller every time when receive this command. Use this
            command instead of the 'get_stage_position' if you need value accurate in nm range. Response time will be
            longer than with 'get_stage_position'
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get STAGEUNIT MOVEXYZTR2')
            if dictDecodedMessage is not None:
                x, y, z, t, r = str(dictDecodedMessage['data']).split(',')
                t = float(t) / 1000
                r = float(r) / 1000
                return int(x), int(y), int(z), t, r

        return 0, 0, 0, 0, 0

    def get_movable_range_stage(self):
        """SEM returns present movable range of stage limited by sample size, insertion of optional detector, etc. Z range
            is of under priority-T setting and T range is of under priority-Z setting. Returned movable range can be used under
            both priority setting
            Xmin, Xmax: 0 to 110 000 000 (nm)
            Ymin, Ymax: 0 to 110 000 000 (nm)
            Zmin, Zmax: 1 500 000 to 40 000 000 (nm)
            Tmin, Tmax: -5 000 to 70 000 (-5.0 to 70.0 deg)
            R mode:
                1: fully rotatable
                2: only 90 deg step
                3: only 180 deg step
                4: inhibited
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get STAGESETTING LIMIT2')
            if dictDecodedMessage is not None:
                xMin, xMax, yMin, yMax, zMin, zMax, tMin, tMax, rMode = str(dictDecodedMessage['data']).split(',')
                tMin = float(tMin) / 1000
                tMax = float(tMax) / 1000
                return int(xMin), int(xMax), int(yMin), int(yMax), int(zMin), int(zMax), tMin, tMax, int(rMode)

        return 0, 0, 0, 0, 0, 0, 0, 0, 0

    def get_detector_signal(self):
        """SEM returns signal name assigned to screen 1 to screen 4.
            Character * is placed when the screen is not displayed. 'MIX' is placed when the image on the screen is mixed
            or color-mixed.
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get DETECTOR SIGNAL')
            if dictDecodedMessage is not None:
                screen1, screen2, screen3, screen4 = str(dictDecodedMessage['data']).split(',')
                return screen1, screen2, screen3, screen4

        return '*', '*', '*', '*'

    def get_detector_high_mag(self):
        """SEM returns signal names assignable to image screen using "Set DETECTOR ALL" command in High-Mag mode. Note
             that the number of parameter changes by present SEM condition. List of possible signal names is as follows.
             Non deceleration mode: SE, LA-BSE, HA-BSE, SE(L), AUX, NONE
             Deceleration mode: SE+BSE, SE, SE/BSE-F, SE(L), AUX, NONE
         """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get DETECTOR HIGHMAG')
            if dictDecodedMessage is not None:
                signal_names = dictDecodedMessage['data']
                return signal_names

        return ''

    def get_detector_low_mag(self):
        """SEM returns signal names assignable to image screen using "Set DETECTOR ALL" command in Low-Mag mode. Note
             that the number of parameter changes by present SEM condition. List of possible signal names is as follows.
             Non deceleration mode: SE(LM), AUX, NONE
             Deceleration mode: SE(LM), SE-L(LM), AUX, NONE
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get DETECTOR LOWMAG')
            if dictDecodedMessage is not None:
                signal_names = dictDecodedMessage['data']
                return signal_names

        return ''

    def get_detector_option(self):
        """SEM returns signal names of optional detectors assignable to image screen using 'Set DETECTOR ALL' command. Note
            that number of parameters changes by present SEM condition. List of possible signal names is as follows. Assignable
            optional detectors are common for non-decelaration and deceleration mode.
            YAG-BSE, PD-BSE, BF-STEM, DF-STEM, EBIC/EBAC
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get DETECTOR OPTION')
            if dictDecodedMessage is not None:
                signal_names = dictDecodedMessage['data']
                return signal_names

        return ''

    def get_sample_settings(self):
        """SEM returns present specified sample size and height setting.
            Possible sample size (include optional size):
                5, 8, 10, 15 (mm)
                1, 2, 3, 4, 5, 6 (inch)
                4, 5 (inch Mask)
            Sample height:
                -2000 to 3000 (-2.0 to 3.0 mm)(0 = standard setting)
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get SPECIMEN ALL')
            if dictDecodedMessage is not None:
                size, height = str(dictDecodedMessage['data']).split(',')
                height = float(height) / 1000
                return size, height

        return 0, 0

    def get_scan_status(self):
        """SEM returns present scan status. In Dual or Quad screen mode, returns RUN or FREEZING when one of the screens
            is running or going to freeze status.
            RUN: Scan running
            FREEZING: Going to freeze
            FREEZE: Frozen
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get SCAN NOW')
            if dictDecodedMessage is not None:
                scan_status = dictDecodedMessage['data']
                return scan_status

        return ''

    def get_scan_speed_status(self):
        """SEM returns present scan speed and number of averaging frames.
            Scan speeds in dict
            Number of averaging frames 1 to 1024 (return 0 when SLOW or CS scan)
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get SCAN SCANSPEED')
            if dictDecodedMessage is not None:
                speed, averaging_frames = str(dictDecodedMessage['data']).split(',')
                # Find string associated to value
                for aSpeed in self.scan_speeds:
                    if int(speed) == self.scan_speeds[aSpeed]:
                        return aSpeed, int(averaging_frames)

        return 0, 0

    def get_scan_mode(self):
        """SEM returns present scan mode
            Scan modes in dict
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get SCAN SCANMODE')
            if dictDecodedMessage is not None:
                scan_mode = dictDecodedMessage['data']
                # Find string associated to value
                for aMode in self.scan_mode:
                    if int(scan_mode) == self.scan_mode[aMode]:
                        return aMode

        return ''

    def get_selected_screen(self):
        """SEM returns screen number that is selected as target of operation.
            If signal mixing image is selected, '4' is returned.
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get SCREEN NOW')
            if dictDecodedMessage is not None:
                selected_screen = dictDecodedMessage['data']
                # Find string associated to value
                for aScreen in self.selected_screens:
                    if int(selected_screen) == self.selected_screens[aScreen]:
                        return aScreen

        return ''

    def get_photo_size(self):
        """SEM returns screen mode and Photo-size. On SU8200 series, two magnification display mode, 'magnification on
            photo size' and 'magnification on display monitor' is available. Field of view of an image with same magnification
            has different value according to magnification display mode and display screen size. Use the Photo-size to
            calculate field of view and pixel size.
            Screen mode:
                0: Single
                1: Dual
                2: Quad
                3: Large
            Photo-size:
                500-3000 (0.5 to 3.0) value is in microns
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get PHOTOSIZE NOW')
            if dictDecodedMessage is not None:
                screen_mode, photo_size = str(dictDecodedMessage['data']).split(',')
                photo_size = float(photo_size)/1000  # turns value into mm
                return int(screen_mode), photo_size

        return 0, 0

    def get_alignment_parameter(self):
        """SEM returns present axis alignment data (DAC setting value of aligner current supply). Actual axis compensation
            data is {return value- Maximum value / 2}. Ex. in case of aperture alignment '0' is minus maximum, '32768' is
            center and '65535' is plus maximum.
            Range of:
                aperture alignment: 0 to 65535
                low mag position alignment: 0 to 65535
                others: 0 to 4095
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get ALIGNMENT NOW')
            if dictDecodedMessage is not None:
                dictAlignmentParameters = {}
                items = str(dictDecodedMessage['data']).split(',')
                dictAlignmentParameters['beam_alignmentX'] = int(items[0])
                dictAlignmentParameters['beam_alignmentY'] = int(items[1])
                dictAlignmentParameters['aperture_alignmentX'] = int(items[2])
                dictAlignmentParameters['aperture_alignmentY'] = int(items[3])
                dictAlignmentParameters['stigma_alignmentXX'] = int(items[4])
                dictAlignmentParameters['stigma_alignmentXY'] = int(items[5])
                dictAlignmentParameters['stigma_alignmentYX'] = int(items[6])
                dictAlignmentParameters['stigma_alignmentYY'] = int(items[7])
                dictAlignmentParameters['ulv_alignmentX'] = int(items[8])
                dictAlignmentParameters['ulv_alignmentY'] = int(items[9])
                dictAlignmentParameters['low_mag_posX'] = int(items[10])
                dictAlignmentParameters['low_mag_posY'] = int(items[11])
                return dictAlignmentParameters

        return {}

    def get_probe_current_and_cond1(self):
        """SEM return present Probe current mode and Cond.1 setting. SU8200 uses these values separately in High-Mag and
            Low-Mag mode. Data read in High-Mag mode is for High-Mag and that read in Low-Mag mode is for Low-Mag. These data
            can be set using 'Set LENSMODE EXECUTE' command. In this case, do not confuse data in High-Mag and Low-Mag mode.
            If not, SEM will be set to incorrect condition.
            Probe current mode:
                0: Normal
                1: High
            Cond. 1 Setting
                10 to 160 (1.0 to 16.0)
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get LENSMODE NOW')
            if dictDecodedMessage is not None:
                probe_current_mode, cond1_setting = str(dictDecodedMessage['data']).split(',')
                cond1_setting = float(cond1_setting)/10
                return int(probe_current_mode), cond1_setting

        return 0, 0

    def get_stigma_current(self):
        """SEM returns present stigma current X, Y (DAC value of current driver). Astigmatism correction value is {return
            value - Max value / 2}. Astigmatism correction is separately adjusted in High-Mag and Low-Mag mode. Data read in
            High-Mag and Low-Mag mode shall be trated separately.
            Stigma : 0 to 65535
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get STIGMAXY NOW')
            if dictDecodedMessage is not None:
                stigmaX, stigmaY = str(dictDecodedMessage['data']).split(',')
                return stigmaX, stigmaY

        return 0, 0

    def get_raster_rotation(self):
        """SEM returns present Raster Rotation status, on/off and rotation angle.
            0: Off, 1: On
            -2000 to 2000 (-200.0 to 200.0 degree)
        """
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command('Get RROTATION NOW')
            if dictDecodedMessage is not None:
                onoff, rotation_angle = str(dictDecodedMessage['data']).split(',')
                rotation_angle = float(rotation_angle)/1000
                return int(onoff), rotation_angle

        return 0, 0

    # Setters
    # TODO with function update_current_state - for all the setters, change the dict current state value
    def set_HV_status(self, on_off):
        """This command sets HV ON/OFF status. Emission current adjustment runs when set during HV is ON.
            ON or OFF
        """
        command = f'Set HVONOFF EXECUTE {on_off}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_HV_control(self, vacc):
        """This command sets acceleration voltage. In HV-ON condition, applied acceleration voltage will be changed. In
            HV-OFF condition, internal value is changed.
            vacc in kV (0.5 to 30 kV)
            100 V step

            return : True if command can be executed
        """

        # Command doesn't work in deceleration mode
        if self.get_HV_status() == 2:
            return False

        vacc *= 1000
        command = f'Set HVCONTROL VACC {vacc}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        return True

    def set_emission_current(self, emission_current):
        """This command sets the emission current. Emission current adjustment runs when set during HV is ON. In HV-Off
            condition, internal value is changed.
            emission_current in uA (0.1 to 30 uA)

            return : True if command can be executed
        """
        # Command doesn't work when HV status is OFF
        if self.get_HV_status() == 0:
            return False

        emission_current *= 10
        command = f'Set EMISSION EXECUTE {emission_current}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        return True

    def set_magnification(self, magnification):
        """This command sets the magnification. If out of possible min / max value is specified, possible lowest or highest
            magnification will be set. Use next set_magnification_mode command to exchange magnification mode (High-Mag / Low-Mag)
            5 to 8 000 0000
        """
        # Make sure the scan status is Run, if frozen the command won't work
        isFrozen = self.get_scan_status() == 'FREEZE'
        if isFrozen:
            self.set_scan_status(0)

        command = f'Set MAGNIFICATION EXECUTE {magnification}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        # If the scan status was frozen, put it back
        if isFrozen:
            self.set_scan_status(1)

    def set_magnification_mode(self, mag_mode):
        """This command sets the magnification mode."""
        if mag_mode not in self.mag_modes:
            logging.info('Set value in command text is not correct (not defined, out of range, etc.)')
            return

        command = f'Set MAGMODE EXECUTE {self.mag_modes[mag_mode]}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_WD(self, wd):
        """This command sets the WD (working distance) value and set focus current.
            1500 to 40 000 (1.5 to 40.0 mm)
            return : True if command can be executed
        """
        # Make sure the magnification mode is High-Mag, in Low-Mag the command won't work
        isLowMag = self.get_magnification()[0] == 1
        if isLowMag:
            self.set_magnification_mode(0)

        # Make sure the scan mode is not Spot or Area Scan mode
        if self.get_scan_mode() == 'Spot mode' or self.get_scan_mode() == 'Area Scan mode':
            return False

        wd *= 1000
        command = f'Set WD HM {wd}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        # If the magnification mode was Low-Mag, put it back
        if isLowMag:
            self.set_magnification_mode(1)

        return True

    def set_focus_value(self, coarse_value, fine_value):
        """This command sets focus current DAC value.
            return : True if command can be executed
        """
        # Make sure the scan status is Run, if frozen the command won't work
        isFrozen = self.get_scan_status() == 'FREEZE'
        if isFrozen:
            self.set_scan_status(0)

        # Make sure the magnification mode is High-Mag, in Low-Mag the command won't work
        isLowMag = self.get_magnification()[0] == 1
        if isLowMag:
            self.set_magnification_mode(0)

        # Make sure the scan mode is not Spot or Area Scan mode
        if self.get_scan_mode() == 'Spot mode' or self.get_scan_mode() == 'Area Scan mode':
            return False

        command = f'Set FOCUS ALL {coarse_value},{fine_value}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        # If the scan status was frozen, put it back
        if isFrozen:
            self.set_scan_status(1)

        # If the magnification mode was Low-Mag, put it back
        if isLowMag:
            self.set_magnification_mode(1)

        return True

    def getIsInMovableRange(self, x, y, z=None, t=None, r=None):
        # Verify that the values are inside the movable range
        xMin, xMax, yMin, yMax, zMin, zMax, tMin, tMax, rMode = self.get_movable_range_stage()
        if x < xMin or x > xMax:
            return False

        if y < yMin or y > yMax:
            return False

        if z is not None:
            if z < zMin or z > zMax:
                return False

        if t is not None:
            if t < tMin or t > tMax:
                return False

        if r is not None:
            if (rMode == 1 and r > 359900) or (rMode == 2 and r > 90000) or (rMode == 3 and r > 180000) \
                    or (rMode == 4 and r > 0):
                return False

        return True

    def set_stage_position(self, x=None, y=None, z=None, t=None, r=None):
        """This command drives stage specifying all 5 axes coordinates value. Movable range of stage can be read using
            get_movable_range_stage command. Present coordinates values used for axes not to be moved. Present stage
            position can be read using get_stage_position_2
            Use set_stage_XYR or set_stage_XY command if only xyr and xy axes need to be moved.
            X: 0 to 110 000 000 (nm) - min step 25 nm
            Y: 0 to 110 000 000 (nm) - min step 25 nm
            Z: 1 000 000 to 40 000 000 (nm) - min step 400 nm
            T: -5 000 to 70 000 (-5.0 to 70.0 deg), 0.0012 deg step
            R: 0 to 359900 (0.0 to 359.9 deg), 0.009 deg step

            return : True if command can be executed
        """
        # Make sure the scan status is Run, if frozen the command won't work
        isFrozen = self.get_scan_status() == 'FREEZE'
        if isFrozen:
            self.set_scan_status(0)

        # Verify that positions are in movable range
        isInMovableRange = self.getIsInMovableRange(x, y, z, t, r)
        if not isInMovableRange:
            return False

        # If the increment is too small, stay at current position
        x_present, y_present, z_present, t_present, r_present = self.get_stage_position_2()
        if abs(x - x_present) < 25:
            x = x_present
        if abs(y - y_present) < 25:
            y = y_present
        if abs(z - z_present) < 400:
            z = z_present
        if abs(t - t_present) < 0.0012:
            t = t_present
        if abs(r - r_present) < 0.009:
            r = r_present

        t *= 1000
        r *= 1000
        command = f'Set STAGEUNIT MOVEXYZTR {x},{y},{z},{t},{r}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        return True

    def set_stage_XYR(self, x=None, y=None, r=None):
        """This command drives stage specifying X, Y and R axes coordinates value. Movable range of stage can be read using
            get_movable_range_stage command. Present coordinates values used for axes not to be moved. Present stage
            position can be read using get_stage_position_2
            Use set_stage_XYR or set_stage_XY command if only xyr and xy axes need to be moved.
            X: 0 to 110 000 000 (nm) - min step 25 nm
            Y: 0 to 110 000 000 (nm) - min step 25 nm
            R: 0 to 359900 (0.0 to 359.9 deg), 0.009 deg step

            return : True if command can be executed
        """
        # Make sure the scan status is Run, if frozen the command won't work
        isFrozen = self.get_scan_status() == 'FREEZE'
        if isFrozen:
            self.set_scan_status(0)

        # Verify that positions are in movable range
        isInMovableRange = self.getIsInMovableRange(x, y, r)
        if not isInMovableRange:
            return False

        # If the increment is too small, stay at current position
        x_present, y_present, z_present, t_present, r_present = self.get_stage_position_2()
        if abs(x - x_present) < 25:
            x = x_present
        if abs(y - y_present) < 25:
            y = y_present
        if abs(r - r_present) < 0.009:
            r = r_present

        r *= 1000
        command = F'Set STAGEUNIT MOVEXYR {x},{y},{r}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        # If the scan status was frozen, put it back
        if isFrozen:
            self.set_scan_status(1)

        return True

    def set_stage_XY(self, x=None, y=None):
        """This command drives stage specifying X, Y axes coordinates value. Movable range of stage can be read using
            get_movable_range_stage command. Present coordinates values used for axes not to be moved. Present stage
            position can be read using get_stage_position_2
            Use set_stage_XYR or set_stage_XY command if only xyr and xy axes need to be moved.
            X: 0 to 110 000 000 (nm) - min step 25 nm
            Y: 0 to 110 000 000 (nm) - min step 25 nm

            return : True if command can be executed
        """
        # Make sure the scan status is Run, if frozen the command won't work
        isFrozen = self.get_scan_status() == 'FREEZE'
        if isFrozen:
            self.set_scan_status(0)

        command = f'Set STAGEUNIT MOVEXY {x},{y},0'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        # If the scan status was frozen, put it back
        if isFrozen:
            self.set_scan_status(1)

        return True

    def set_stage_relative_XY(self, x=0, y=0):
        """This command drives stage specifying relative value X, Y. Resulting coordinates (present position + relative
            value) do not exceed movable range. Write '0' for is not to be moved.
            get_movable_range_stage command. Present coordinates values used for axes not to be moved. Present stage
            position can be read using get_stage_position_2.
            X: -110 000 000 to 110 000 000 (nm)
            Y: -110 000 000 to 110 000 000 (nm)

            return : True if command can be executed
        """
        # Make sure the scan status is Run, if frozen the command won't work
        isFrozen = self.get_scan_status() == 'FREEZE'
        if isFrozen:
            self.set_scan_status(0)

        x_present, y_present, z_present, t_present, r_present = self.get_stage_position_2()
        x_new = x_present + x
        y_new = y_present + y

        # Verify that positions are in movable range
        isInMovableRange = self.getIsInMovableRange(x_new, y_new)
        if not isInMovableRange:
            return False

        command = f'Set STAGEUNIT RELATIVEXY {x},{y}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        # If the scan status was frozen, put it back
        if isFrozen:
            self.set_scan_status(1)

        return True

    def set_stage_move_exchange(self):
        """This command drives stage to specimen exchange position. Note that this command returns 'NG' when the stage
            is already at exchange position. Get present stage coordinates and make judge if stage is at exchange position
            or not. Stage coordinates of exchange position varies by SEM model and by installed optional detectors. It is
            recommended to make you program so as the reference coordinates for exchange position is variable.
        """
        command = 'Set STAGEUNIT MOVEEXCHANGE *'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_home_position(self):
        """This command drives stage to home position."""
        command = 'Set STAGEUNIT MOVEHOME *'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_move_constant_speed(self, **kwargs):
        """This command drives stage to specified direction with constant specified speed. This command drives directly
            the stage controller, and is independent to "Const speed drive" build in SU8200 stage operation tab.
            Use set_stage_move_stop command to stop stage motion.
            X control, Y control :
                0: Stop
                1: Start (with rotation comp.)
                2: Start (without rotation comp.)
            X direction, Y direction:
                0: CW
                1: CCW
            X speed, Y speed:
                1 to 65 535 (nm/s)
        """
        x_control = kwargs['x_control']
        x_direction = kwargs['x_direction']
        x_speed = kwargs['x_speed']
        y_control = kwargs['y_control']
        y_direction = kwargs['y_direction']
        y_speed = kwargs['y_speed']
        command = f'Set STAGEUNIT CONSTMOVE2 {x_control},{x_direction},{x_speed},{y_control},{y_direction},{y_speed}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_stage_move_stop(self):
        """This command stops stage motion if sent during stage is moving."""
        command = 'Set STAGE STOP ' + '*'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_detectors(self, list_of_signals):
        """This command sets signal name for image screen 1 to 4. Additionally, specify SED signal name for Low-Mag mode
            and value for SE Suppress control.
            SE Suppress value: 0 to 100, if not necessary value is 0
            Non deceleration mode: SE, LA-BSE, HA-BSE, SE(L), AUX, NONE
             Deceleration mode: SE+BSE, SE, SE/BSE-F, SE(L), AUX, NONE

             return : True if command can be executed
        """
        if len(list_of_signals) > 6:
            logging.info('Too many signals to display.')
            return False

        data = str(list_of_signals[0])
        for signal in list_of_signals:
            data += (f',{signal}')

        command = 'Set DETECTOR ALL ' + data
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        return True

    def set_scan_status(self, status):
        """This command sets scan status. In Dual and Quad screen mode, all screens are set simultaneously
            0: RUN
            1: Freeze - in slow scan mode, scan continues to the end of the frame and then, frozen
            2: Immediately Freeze - scan stops at any position
        """
        command = 'Set SCAN EXECUTE ' + str(status)
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_scan_speed(self, speed):
        """This command sets scan speed.
            return : True if command can be executed
        """
        if speed not in self.scan_speeds:
            logging.info('Set value in command text is not correct (not defined, out of range, etc.)')
            return False

        # Make sure the scan mode is not Spot or Area Scan mode
        if self.get_scan_mode() == 'Spot mode' or self.get_scan_mode() == 'Area Scan mode':
            return False

        command = 'Set SCAN SCANSPEED ' + str(self.scan_speeds[speed])
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        return True

    def set_scan_mode(self, mode):
        """This command sets scan mode. In Spot and Area Scan mode, analysis point is set at the center and unable to be
            moved. If the position is moved by operation on SEM, the position will be kept. The Analysis Mode setting dialog
            is open by this command execution.
            To set to Spot mode, it is necessary to set to Spot Position Set mode prior. It is also necessary to set to
            Area Position Set before setting to Area Scan mode.
            return : True if command can be executed

        """
        if mode not in self.scan_mode:
            logging.info('Set value in command text is not correct (not defined, out of range, etc.)')
            return False


        command = 'Set SCAN SCANMODE ' + str(self.scan_mode[mode])
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        return True

    def set_selected_screen(self, selected_screen):
        """In Dual or Quad screen mode, this command selects a screen to set it as the target of operation, for example
            the target screen of direct image saving.
            If specified screen is not exist, this command returns 'NG'.
            If a signal-mixing image is displayed, '4' specifies the screen where the image is displayed. In this case,
            1 or 4 for Single screen mode, 0, 1, 4 for Dual screen mode and 0 to 4 for Quad screen mode, is selectable.
        """
        screen_number = 0
        signals = self.get_detector_signal()
        for aSignal in signals:
            if aSignal == selected_screen:
                break
            screen_number += 1

        if screen_number > 3:
            logging.info('Set value in command text is not correct (not defined, out of range, etc.)')
            return

        command = 'Set SCREEN EXECUTE ' + str(screen_number)
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_direct_save(self, arg):
        """This command freezes image if running and saves image. In Dual or Quad screen mode, when Single is specified,
            image on the present selected screen (using set_selected_screen command) is saved, and when All is specified
            images on all screens are saved. The image(s) is saved with fixed file names in fixed folder:
            D:\SemImage\temp
            If this command is repeated, above files are overwritten. It is necessary to move image files putting identical
            name each time before sending this command.
            0: Single
            1: All
        """
        value = None
        if arg == 'Single':
            value = 0
        elif arg == 'All':
            value = 1

        command = f'Set DIRECTSAVE EXECUTE {value}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def validate_capture_setting_parameters(self, scan_mode, resolution, scan_time, integration_number):
        if scan_mode == 0 or scan_mode == 1:
            if resolution == 3:
                return False

            # Not effective
            if scan_time != 0:
                return False

        elif scan_mode == 2:
            if resolution == 0 and scan_time == 5:
                return False
            elif resolution == 1 and scan_time == 0:
                return False
            elif resolution == 2 and scan_time < 2:
                return False
            elif resolution == 3 and scan_time < 3:
                return False

            # Not effective
            if integration_number != 0:
                return False
        elif scan_mode == 3:
            if resolution == 0 and scan_time > 3:
                return False
            elif resolution == 1 and (scan_time == 0 or scan_time == 5):
                return False
            elif resolution == 2 and scan_time < 2:
                return False
            elif resolution == 3:
                return False

            # Not effective
            if integration_number != 0:
                return False
        elif scan_mode == 4:
            if resolution == 3:
                return False

            if integration_number > 4:
                return False

            # Not effective
            if scan_time != 0:
                return False

        return True

    def set_capture_settings(self, scan_mode, resolution, scan_time, integration_number):
        """This command sets parameters for image capturing."""
        is_valid = self.validate_capture_setting_parameters(self.capture_scan_mode[scan_mode],
                                                            self.capture_resolution[resolution],
                                                            self.capture_scan_time[scan_time],
                                                            self.capture_integration_number[integration_number])
        if not is_valid:
            logging.info('Capture settings are not compatible')
            return False

        command = f'Set CAPTURESAVE CAPTURESPEED {self.capture_scan_mode[scan_mode]},{self.capture_resolution[resolution]},{self.capture_scan_time[scan_time]},{self.capture_integration_number[integration_number]}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)
            return True

        return False

    def set_capture_and_save(self, arg, project_name='', newFileName=''):
        """This command runs image capturing and save captured image(s). In Dual or Quad screen mode, when Single is specified
            only the present selected screen (using set_selected_screen command) is captured, and when All is specified,
            all screens are captured and saved. The image(s) is saved with fixed file names in fixed folder:
            D:\SemImage\temp
            If this command is repeated, above files are overwritten. It is necessary to move image files putting identical
            name each time before sending this command.
            0: Single
            1: All
        """
        value = None
        if arg == 'Single':
            value = 0
        elif arg == 'All':
            value = 1

        command = f'Set CAPTURESAVE EXECUTE {value}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            save_dir = externalCommunication.im_transfer(project_name, newFileName)
            logging.info(result)
            return save_dir

    def set_alignment_set(self, mode, x_value, y_value):
        """This command sets axial alignment data. Alignment current is set and electron optical column axis will be changed.
            To read present alingment data, use get_alignment_parameter comment. This command can be used to reproduce
            memorized alignment condition or axial alignment operation.
            For the Range of data value, refer the above Get command.
            It is necessary to set SEM condition to where alignment mode to be set is executable. If this command is sent
            under Inexecutable condition, it is not effective and 'NG' will be returned.
            X values : 0 to 65 535
            Y values : 0 to 4 095
        """
        if mode not in self.alignment_mode:
            logging.info('Set value in command text is not correct (not defined, out of range, etc.)')
            return

        command = f'Set ALIGNMENT EXECUTE {self.alignment_mode[mode]},{x_value},{y_value}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_probe_current_and_cond1(self, probe_current, cond1):
        """This command sets Probe current mode and Condenser lens 1 setting value. To read present data, use
            get_probe_current_and_cond1 command. SU8200 uses these data separately in High-Mag and Low-Mag mode. To reproduce
            previous condition, use data read in High-Mag mode for High-Mag mode setting and use data in Low-Mag mode for
            Low-Mag mode setting. Confusion of data in both magnification modes will cause incorrect SEM condition. This
            command can be used for probe current adjustment.
            In Probe current mode 'Normal', reducing Condenser lens1 setting will result larger probe current. If current
            is not sufficient at Condenser lens1 setting=10(1.0), change Probe current mode to 'High' and set Condenser lens1
            setting to 130(13.0).
            Note that these changes of setting will cause misalignment of column axis. Its needs carrying out axial re-alignment.
            Probe current mode
                0: Normal
                1: High
            Cond 1 setting
                10 to 130 (1.0 to 13.0)
        """
        if probe_current not in self.probe_current:
            logging.info('Set value in command text is not correct (not defined, out of range, etc.)')
            return

        cond1 *= 10
        command = f'Set LENSMODE EXECUTE {self.probe_current[probe_current]},{cond1}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_stigma_current(self, x_value, y_value):
        """This command sets stigma current. Actual astigmatism correction value is (set data - max value /2). Preset stigma
            current value can be read using get_stigma_current command. Stigma current is different in High-Mag and Low-Mag
            mode. SEM holds two sets of data separately. To set previously read stigma current data or modified data, use
            data read in High-Mag mode for High-Mag mode setting and use data read in Low-Mag mode for Low-Mag mode setting.
            X, Y : 0 to 65 535
        """
        command = f'Set STIGMAXY EXECUTE {x_value},{y_value}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_raster_rotation(self, onoff, angle):
        """This command sets On/Off and angle of raster rotation.
            0: Off
            1: On
            Angle:
                -2000 to 2000 (-200.0 to 200.0 deg)
        """
        angle *= 10
        command = f'Set RROTATION EXECUTE {onoff},{angle}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_flashing(self, flashing_mode):
        """This command executes flashing.
            return : True if command can be executed
        """
        if flashing_mode not in self.flashing_modes:
            logging.info('Set value in command text is not correct (not defined, out of range, etc.)')
            return False

        command = f'Set FLASHING EXECUTE {self.flashing_modes[flashing_mode]}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        return True

    def set_degauss(self):
        """This command executes degaussing (demagnetization of magnetic lenses). Note that degaussing will in some cases
            cause change of focus, stigma and axial alignment.
        """
        command = 'Set DEGAUSS EXECUTE *'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_auto_focus(self):
        """This command executes auto-focus."""
        command = 'Set AUTO AFC *'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_auto_stigma(self):
        """This command executes auto-stigma."""
        command = 'Set AUTO ASC *'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_ABC(self, abc_mode, beam_adjust):
        """This command executes ABCC (auto-brightness/contrast adjustment). In Dual or Quad screen mode, when ABC (Single)
            is specified, ABCC will be applied to image on the selected screen (using set_selected_screen command), and
            when ABC(All) is specified, ABCC wil be applied to images on all screens. ABCC is not applied to signals that
            ABCC does not support. If ON is specified for Beam monitor Adjust parameter, beam monitor adjustment will run
            before executing ABC.
            ABC mode:
                0: ABS(Single)
                1: ABC(All)
            Beam monitor adjust:
                0: OFF
                1: ON
        """
        command = f'Set AUTO ABC {abc_mode},{beam_adjust}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_beam_monitor_adjust(self):
        """This command executes beam monitor adjustment."""
        command = 'Set AUTO BMC *'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_contrast_adjust(self, value):
        """This command adjusts image contrast. Plus values increases and minus value decreases image contrast.
            Value : -127 to 127
        """
        command = f'Set PANEL CONTRAST {value}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_brightness_adjust(self, value):
        """This command adjusts image brightness. Plus value increases and minus value decreases image brightness.
            Value: -127 to 127
        """
        command = f'Set PANEL BRIGHTNESS {value}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

    def set_image_shift_X(self, value):
        """This command moves image in horizontal direction by image shift function. Large value moves large distance.
            When image shift value exceeds its movable range, image will not move (not error returned).
            Value: -127 to 127
        """
        # Make sure the magnification mode is High-Mag, in Low-Mag the command won't work
        isLowMag = self.get_magnification()[0] == 1
        if isLowMag:
            self.set_magnification_mode(0)

        # Make sure the scan status is Run, if frozen the command won't work
        isFrozen = self.get_scan_status() == 'FREEZE'
        if isFrozen:
            self.set_scan_status(0)

        command = f'Set PANEL IMAGESHIFTX {int(value)}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        # If the magnification mode was Low-Mag, put it back
        if isLowMag:
            self.set_magnification_mode(1)

        # If the scan status was frozen, put it back
        if isFrozen:
            self.set_scan_status(1)

    def set_image_shift_Y(self, value):
        """This command moves image in vertical direction by image shift function. Large value moves large distance.
            When image shift value exceeds its movable range, image will not move (not error returned).
            Value: -127 to 127
        """
        # Make sure the magnification mode is High-Mag, in Low-Mag the command won't work
        isLowMag = self.get_magnification()[0] == 1
        if isLowMag:
            self.set_magnification_mode(0)

        # Make sure the scan status is Run, if frozen the command won't work
        isFrozen = self.get_scan_status() == 'FREEZE'
        if isFrozen:
            self.set_scan_status(0)

        command = f'Set PANEL IMAGESHIFTY {int(value)}'
        externalCommunication = self.get_external_communication()
        if externalCommunication is not None:
            result = externalCommunication.process_set_command(command)
            logging.info(result)

        # If the magnification mode was Low-Mag, put it back
        if isLowMag:
            self.set_magnification_mode(1)

        # If the scan status was frozen, put it back
        if isFrozen:
            self.set_scan_status(1)
