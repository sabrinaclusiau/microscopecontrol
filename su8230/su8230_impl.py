import os
import sys
import numpy as np
from math import ceil, floor
import logging
import tkinter
from tkinter import messagebox, simpledialog
from keras.models import load_model

from ORSModel import orsObj, Channel, ROI, Vector3, Graph, CxvFiltering_Mode
from ORSServiceClass.mathutils.otsu import Otsu
from internalProject.microscopeControl.abstract_impl import AbstractImpl
from internalProject.microscopeControl.su8230.su8230_commands import Su8230Commands
from internalProject.microscopeControl.su8230.su8230_tests import Su8230Tests
from internalProject.microscopeControl.su8230.su8230_calibration import get_image_XY_size_for_magnification
from internalProject.microscopeControl.stitching import getTransformation, stitchHighMagToLowMag, stitchHighMagToLowMagWithGraph
from OrsPlugins.orsimageloader import OrsImageLoader


class Su8230Impl(AbstractImpl):

    def __init__(self):
        super().__init__()

    def instantiate_microscope_commands(self):
        self.commands = Su8230Commands()

    def initialize_default_settings(self):
        commands: Su8230Commands = self.get_microscope_commands()
        if commands is None:
            return

        # Go to HOME position
        commands.set_home_position()

        # Turn ON beam
        commands.set_HV_status(on_off='ON')

        # Start beam
        status = commands.get_scan_status()
        if status != 'RUN' or status != 'FREEZING':
            commands.set_scan_status(status='RUN')

    def update_current_state(self,  key, get_command):
        if key not in self.currentState:
            return

        commands = self.get_microscope_commands()
        if commands is None:
            return

        externalCommunication = commands.get_external_communication()
        if externalCommunication is not None:
            dictDecodedMessage = externalCommunication.process_get_command(get_command)
            data = dictDecodedMessage['data']
            self.currentState[key] = data

    def clear_savedir_pc_connected(self, project_name):
        root = tkinter.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)

        # Create a directory if it doesn't exist
        if not os.path.exists(project_name):
            os.makedirs(project_name)
        else:
            choice = messagebox.askyesno('Automatic image acquisition',
                                         'Output directory already exists. Do you want to delete existing data?')
            if choice == True:
                for file in os.listdir(project_name):
                    os.remove(os.path.join(project_name, file))
            else:
                sys.exit('Acquisition stopped because of existing data in output directory')

    def interactive_imaging_grid(self, list_signals,  low_mag_signal, active_signal, magnification, SE_suppress, step_x_um,
                                 capture_scan_mode, capture_image_res, capture_scan_time, capture_integration_number,
                                 project_name):
        """
        Capture 3x3 image grid
        Args:
            params_grid:

        Returns:

        """
        commands: Su8230Commands = self.get_microscope_commands()
        if commands is None:
            return

        # Go to HOME position
        commands.set_home_position()

        # Turn ON beam
        commands.set_HV_status(on_off='ON')

        # Empty the save dir for new images
        self.clear_savedir_pc_connected(project_name)

        # Set capture settings
        logging.info('Set capture settings ...')
        commands.set_capture_settings(scan_mode=capture_scan_mode,
                                      resolution=capture_image_res,
                                      scan_time=capture_scan_time,
                                      integration_number=capture_integration_number)

        # Set magnification mode to High
        commands.set_magnification_mode('High-Mag')

        # Make sure assigned signals are available in high mag mode or option
        detectors_high_mag = commands.get_detector_high_mag()
        detectors_option = commands.get_detector_option()
        available_signals = detectors_high_mag.split(',') + (detectors_option.split(','))
        if list_signals['signal_1'] not in available_signals:
            list_signals['signal_1'] = '*'
        elif list_signals['signal_2'] not in available_signals:
            list_signals['signal_2'] = '*'
        elif list_signals['signal_3'] not in available_signals:
            list_signals['signal_3'] = '*'
        elif list_signals['signal_4'] not in available_signals:
            list_signals['signal_4'] = '*'

        available_low_mag_signals = commands.get_detector_low_mag().split(',')
        if low_mag_signal not in available_low_mag_signals:
            low_mag_signal = '*'

        # Set detectors
        commands.set_detectors(list_of_signals=[list_signals['signal_1'], list_signals['signal_2'],
                                                list_signals['signal_3'], list_signals['signal_4'],
                                                low_mag_signal, SE_suppress])

        # Set selected screen
        current_selected_screen = commands.get_selected_screen()
        if current_selected_screen != active_signal:
            commands.set_selected_screen(selected_screen=active_signal)

        # Set scan speed
        current_scan_speed = commands.get_scan_speed_status()
        commands.set_scan_speed(speed='SLOW1')

        # Set magnification
        commands.set_magnification(magnification=magnification)

        # Start beam
        status = commands.get_scan_status()
        if status != 'RUN' or status != 'FREEZING':
            commands.set_scan_status(status='RUN')

        im_res = 1280  # same as capture
        px_size_ratio_um = 9.921875 * (1280 / float(im_res)) * 10000 / 1000
        param_list = []
        batchList = {}

        step_um = step_x_um
        if step_um == 0:
            step_um = float(im_res) * px_size_ratio_um / float(magnification)
            # step_x_um = step_um

        logging.info(f'Step in x is {round(float(step_um), 3)} um')


        # TODO adjust contrast?
        step_um = int(step_um)
        step_nm = int(step_um) * 1000

        x_current, y_current, z_current, t_current, r_current = commands.get_stage_position()
        x_start = 0
        y_start = 0
        # For 3 images in x direction, we translate twice
        # x step will be half of image (1280 px in X, so 640 x step)
        # x step in nm
        image_ratio = 640 / 480  # 1280 / 960
        x_step = int(640) / step_nm
        y_step = int(480) / (step_nm / image_ratio)
        x_end = int(x_start) + 3 * int((x_step) * step_nm)
        y_end = int(y_start) + 3 * int((y_step) * step_nm / image_ratio)
        n = 1
        for x_translation in range(3):
            for y_translation in range(3):
                positionDict = {}
                # Position is center of image
                mid_x = x_start + x_translation * x_step
                mid_y = y_start + y_translation * y_step
                positionName = f'x: {mid_x}, y: {mid_y}, z: {z_current}, t: {t_current}, r: {r_current}'
                commands.set_stage_XYR(x=mid_x, y=mid_y, r=None)  # x_nm, y_nm, r_deg
                isok = messagebox.showinfo('Automatic image acquisition', 'Please adjust focus')
                logging.info(f'Sample position / {positionName} / registered.')
                positionDict['position'] = commands.get_stage_position_2()
                positionDict['focus'] = commands.get_focus_value()
                positionDict['stigma'] = commands.get_stigma_current()
                logging.info(f'{positionDict}')
                projectPath = os.path.join(project_name, positionName)
                savedir = commands.set_capture_and_save(arg='Single', project_name=projectPath, newFileName=f'grid_{n}')
                n += 1

            # txtfilepath = os.path.join(savedir, '{}_paramters.txt' % projectPath.split('\\')[-1])
            # np.savetxt(txtfilepath, np.array(param_list), delimiter='\t', fmt='%s')

        isok = messagebox.showinfo('Automatic image acquisition', 'Acquisition finished!')

    def run_tests(self):
        tests: Su8230Tests = Su8230Tests()
        if tests is None:
            return

        commands: Su8230Commands = self.get_microscope_commands()
        if commands is None:
            return

        # Test the wait command for set and get
        logging.info('Testing connection ....')
        str_command = "0300 0303 0000 Get InstructName ALL\r\n"
        tests.test_connection(arbitrary_command=str_command, commands=commands)

        # Test getters and setters
        logging.info('Testing commands ....')
        tests.test_commands(commands=commands)

        # Test capture images
        tests.test_capture_settings(commands=commands, project_name='')

    def capture_XbyY_grid(self, x, y, stitchFollowingAcquisitions=False):
        """
        Captures a grid with X by Y images with sufficient overlap to ensure stitching is successful.
        If stitching fails, a beam shift will be performed to increase the overlap and attempt another stitch.

        """
        commands: Su8230Commands = self.get_microscope_commands()
        if commands is None:
            return

        isValid = self.setCaptureSettingsForMicroscope()
        if isValid:
            # Take low mag pic
            low_mag = 20000
            commands.set_magnification(low_mag)
            savedirLowMag = commands.set_capture_and_save(arg=self._saveStatus, project_name=self._filePath,
                                                    newFileName=f'full_image_{low_mag}')
            # Go to high mag
            commands.set_magnification(self.getMagnification())

            # Calculate photosize for x and y steps
            photo_size_x_nm, photo_size_y_nm = get_image_XY_size_for_magnification(self._magnification)
            # Step needs to be of minimum 25 nm increment
            x_step_nm = round(ceil(photo_size_x_nm - photo_size_x_nm / 11) / 25) * 25
            y_step_nm = round(ceil(photo_size_y_nm - photo_size_y_nm / 11) / 25) * 25
            # If xStep or yStep is smaller than 1000 nm, use beam shift
            useBeamShiftX = True if x_step_nm < 900 else False
            useBeamShiftY = True if y_step_nm < 900 else False
            if useBeamShiftX or useBeamShiftY:
                self.gridAcquisitionBeamShift(x_step_nm, y_step_nm, x, y)
            else:
                self.gridAcquisitionStageShift(x_step_nm, y_step_nm, x, y)

            if stitchFollowingAcquisitions:
                stitchHighMagToLowMag(self._filePath, "", low_mag, self.getMagnification(),
                                      x, y, self._xPixelSize, self._yPixelSize)

    def gridAcquisitionBeamShift(self, xStep, yStep, numImagesX, numImagesY):
        commands = self.get_microscope_commands()
        if commands is None:
            return

        pixelSize_nm = 127 / self.getMagnification() / self._xPixelSize * 10 ** 6
        # Find number of beam shifts needed : 1 beam shift = 3.4 * pixel size (nm) and max beam shift is 127
        singleBeamShift = 3.4 * pixelSize_nm  # in nm
        # for X
        numberOfBeamShifts = xStep / singleBeamShift
        numberToChange = numberOfBeamShifts / 127
        fullNumber_X = floor(numberToChange)
        # Convert decimal to image shift
        decimalNumber_X = round((numberToChange % 1) * 127)
        # for Y
        numberOfBeamShifts = yStep / singleBeamShift
        numberToChange = numberOfBeamShifts / 127
        fullNumber_Y = floor(numberToChange)
        # Convert decimal to image shift
        decimalNumber_Y = round((numberToChange % 1) * 127)
        n = 1
        snakeValue = -1
        for xStep in range(numImagesX):
            snakeValue *= -1
            savedir = commands.set_capture_and_save(arg=self._saveStatus, project_name=self._filePath,
                                                    newFileName=f'grid_mag{self._magnification}_{n}')
            n += 1
            for yStep in range(1, numImagesY):
                for aYImageShift in range(fullNumber_Y):
                    commands.set_image_shift_Y(snakeValue * 127)

                commands.set_image_shift_Y(snakeValue * decimalNumber_Y)
                savedir = commands.set_capture_and_save(arg=self._saveStatus, project_name=self._filePath,
                                                        newFileName=f'grid_mag{self._magnification}_{n}')
                n += 1
            for aXImageShift in range(fullNumber_X):
                commands.set_image_shift_X(-127)

            commands.set_image_shift_X(-decimalNumber_X)

    def gridAcquisitionStageShift(self, xStepNm, yStepNm, numImagesX, numImagesY):
        commands = self.get_microscope_commands()
        if commands is None:
            return

        # Current stage position is the center of the image
        cur_x, cur_y, _, _, _ = commands.get_stage_position()
        n = 1
        snakeValue = 1
        for xStep in range(numImagesX):
            for yStep in range(numImagesY):
                # Go in y direction
                isInMovableRange = commands.set_stage_XY(cur_x, cur_y)

                # Do not capture if the new positions were not in movable range
                if isInMovableRange:
                    savedir = commands.set_capture_and_save(arg=self._saveStatus, project_name=self._filePath,
                                                                newFileName=f'grid_mag{self._magnification}_{n}')
                    # Section for stitching checkup
                    # Use two consecutive images - Columns
                    if n > (xStep-1)*numImagesX + 1:
                        self.validateStitchingBetweenImages(savedir + f'grid_mag{self._magnification}_{n}',
                                                                      savedir + f'grid_mag{self._magnification}_{n-1}',
                                                                      isYShift=True)

                    # Use two consecutive images - Rows
                    if n > yStep * numImagesY:
                        self.validateStitchingBetweenImages(savedir + f'grid_mag{self._magnification}_{n}',
                                                                      savedir + f'grid_mag{self._magnification}_{n - 1}',
                                                                      isYShift=False)
                cur_y += snakeValue*yStepNm
                n += 1

            cur_x += xStepNm
            snakeValue *= -1
            cur_y += snakeValue * yStepNm
            # Backlash correction
            # if self._magnification >= 90000:
            #     # Handling back lash at every column
            #     _ = commands.set_stage_XY(cur_x + xStep * xStepNm, cur_y - 2 * yStepNm)

    def validateStitchingBetweenImages(self, filePath1, filePath2, isYShift):
        commands = self.get_microscope_commands()
        if commands is None:
            return False

        photo_size_x = self._xPixelSize
        photo_size_y = self._yPixelSize
        pixelSize_m = 127 / self.getMagnification() / self._xPixelSize / 1000
        listChannels_SE = OrsImageLoader.createDatasetFromFiles(list(filePath1, filePath2), photo_size_x, photo_size_y,
                                                                2, 1, 0, photo_size_x - 1, 0,
                                                                photo_size_y - 1, 0, 2 - 1, 1, 1, 1, 1, pixelSize_m,
                                                                pixelSize_m, pixelSize_m, 1, 0, '', False, False,
                                                                False, 0, '', False, 0.0, 0.0, 1, '')
        translation, _ = getTransformation(listChannels_SE[0], listChannels_SE[1])
        # Check if there is a transformation
        while translation is None:
            # without transformation - beam shift back for more overlap
            # TODO verify what is the optimal beam shift value
            commands.set_image_shift_Y(-50) if isYShift else commands.set_image_shift_X(-50)
            savedir = commands.set_capture_and_save(arg=self._saveStatus,
                                                    project_name=self._filePath,
                                                    newFileName=filePath2)
            listChannels_SE = OrsImageLoader.createDatasetFromFiles(list(filePath1, filePath2), photo_size_x,
                                                                    photo_size_y,
                                                                    2, 1, 0, photo_size_x - 1, 0,
                                                                    photo_size_y - 1, 0, 2 - 1, 1, 1, 1, 1, pixelSize_m,
                                                                    pixelSize_m, pixelSize_m, 1, 0, '', False, False,
                                                                    False, 0, '', False, 0.0, 0.0, 1, '')
            translation, _ = getTransformation(listChannels_SE[0], listChannels_SE[1])

    def tracking(self, project_name=None):
        commands: Su8230Commands = self.get_microscope_commands()
        if commands is None:
            return

        isValid = impl.setCaptureSettingsForMicroscope()
        if isValid:
            low_mag = 20000
            commands.set_magnification(low_mag)
            # Take low mag pic
            savedir = commands.set_capture_and_save(arg=impl._saveStatus, project_name=impl._filePath,
                                                    newFileName=f'full_image_{low_mag}')

        # Segment CNT with thresholding
        pixelSize_m = 127 / low_mag / self._xPixelSize / 1000
        lowMagChannel = OrsImageLoader.createDatasetFromFiles(list(savedir), self._xPixelSize, self._yPixelSize,
                                                                1, 1, 0, self._xPixelSize - 1, 0,
                                                                self._yPixelSize - 1, 0, 0, 1, 1, 1, 1, pixelSize_m,
                                                                pixelSize_m, pixelSize_m, 1, 0, '', False, False,
                                                                False, 0, '', False, 0.0, 0.0, 1, '')
        overviewImage = lowMagChannel[0]
        otsuThreshold, minValue, maxValue = Otsu.getOtsuThresholdAndMinMax(overviewImage, t=0, mask=None, aProgress=None)
        ROIForeground = overviewImage.getAsROIWithinRange(otsuThreshold, maxValue, None, None)

        # Create sparse graph
        skeletonROI = ROIForeground.getSkeletonized(None)
        skeletonROI.setAutoDelete(True)
        # Graph computation
        aGraph = skeletonROI.computeGraph(None)
        commands.set_magnification(impl.getMagnification())
        timeIndex = 0
        # get the vertices map to select positions
        predAndSuccMap = aGraph.getVerticesPredecessorAndSuccessor(timeIndex).getNDArray()
        vertices = aGraph.getVertices(timeIndex)
        # get list of all predecessors and all successors
        predecessors = predAndSuccMap[::2]
        successors = predAndSuccMap[1::2]
        # only keep vertices that have 2 neighbors
        verticesWithPredecessors = np.where(predecessors != -1)
        verticesWithSuccessors = np.where(successors != -1)
        uniques, counts = np.unique(np.append(verticesWithPredecessors, verticesWithSuccessors), return_counts=True)
        validVertices = uniques[np.where(counts == 2)]
        # find center position of low mag image - current position of microscope view
        currentPosition = overviewImage.getBox().getCenter()
        curX = currentPosition.getX()
        curY = currentPosition.getY()
        imageCount = 1
        # vertices are position in space, position microscope at vertices
        for aVertex in validVertices:
            xPos = vertices.at(3 * aVertex)
            yPos = vertices.at(3 * aVertex + 1)
            xDelta = xPos - curX
            yDelta = yPos - curY
            x_step_nm = round(xDelta * 10e8 / 25) * 25
            y_step_nm = round(yDelta * 10e8 / 25) * 25
            # skip vertices in near vicinity
            if abs(x_step_nm) < 600 and abs(y_step_nm) < 400:
                continue

            impl.beamShift(-x_step_nm, y_step_nm, imageCount) if (abs(y_step_nm) < 900 or abs(x_step_nm) < 900) \
                else impl.stageShift(x_step_nm, y_step_nm, imageCount)
            imageCount += 1
            curX = xPos
            curY = yPos

        stitchHighMagToLowMagWithGraph(project_name, overviewImage, aGraph, low_mag, self.getMagnification(), self._xPixelSize, self._yPixelSize,
                                       imageCount)

    def stageShift(self, x_step_nm, y_step_nm, n):
        commands: Su8230Commands = self.get_microscope_commands()
        if commands is None:
            return

        # Current stage position is the center of the image
        cur_x, cur_y, _, _, _ = commands.get_stage_position()
        cur_x += x_step_nm
        cur_y += y_step_nm
        isInMovableRange = commands.set_stage_XY(cur_x, cur_y)

        # Do not capture if the new positions were not in movable range
        if isInMovableRange:
            savedir = commands.set_capture_and_save(arg=self._saveStatus, project_name=self._filePath,
                                                    newFileName=f'image_{self._magnification}_{n}')

    def beamShift(self, x_step_nm, y_step_nm, n):
        commands: Su8230Commands = self.get_microscope_commands()
        if commands is None:
            return

        pixelSize_nm = 127 / impl.getMagnification() / impl._xPixelSize * 10 ** 6
        isXNeg = x_step_nm < 0
        isYNeg = y_step_nm < 0
        # Find number of beam shifts needed : 1 beam shift = 3.4 * pixel size (nm) and max beam shift is 127
        singleBeamShift = 3.4 * pixelSize_nm  # in nm
        # for X
        numberOfBeamShifts = x_step_nm / singleBeamShift
        numberToChange = numberOfBeamShifts / 127
        fullNumber_X = floor(abs(numberToChange))
        # Convert decimal to image shift
        decimalNumber_X = round((numberToChange % 1) * 127)
        # for Y
        numberOfBeamShifts = y_step_nm / singleBeamShift
        numberToChange = numberOfBeamShifts / 127
        fullNumber_Y = floor(abs(numberToChange))
        # Convert decimal to image shift
        decimalNumber_Y = round((numberToChange % 1) * 127)
        for aYImageShift in range(fullNumber_Y):
            commands.set_image_shift_Y(-127 if isYNeg else 127)

        commands.set_image_shift_Y(-decimalNumber_Y if isYNeg else decimalNumber_Y)

        for aXImageShift in range(fullNumber_X):
            commands.set_image_shift_X(-127 if isXNeg else 127)

        commands.set_image_shift_X(-decimalNumber_X if isXNeg else decimalNumber_X)
        savedir = commands.set_capture_and_save(arg=self._saveStatus, project_name=self._filePath,
                                                newFileName=f'image_{impl._magnification}_{n}')

    def captureImageToPredictParameters(self):
        commands: Su8230Commands = self.get_microscope_commands()
        if commands is None:
            return

        isValid = self.setCaptureSettingsForMicroscope()
        # take an image 1280x960 with NP positioned at center
        # Choose arbitrary energy and current
        initialEnergy = 10
        initialCurrent = 5
        savedir = commands.set_capture_and_save(arg=self._saveStatus, project_name=self._filePath,
                                                newFileName=f'imageForModel_{initialEnergy}keV_{initialCurrent}pA')
        # get the image from folder and load it as channel
        savedir = 'D:\\'
        magnification = 100000
        photo_size_x = 1280
        photo_size_y = 960
        photo_size_x_mm = 127 / magnification
        spacing = photo_size_x_mm / photo_size_x * 10 ** -3
        listChannels_BSE = OrsImageLoader.createDatasetFromFiles([savedir + f'image_5kV_emission10uA_modeNorm_cond1_measured51pA_1.tiff'],
            # listChannels_BSE = OrsImageLoader.createDatasetFromFiles([savedir+f'imageForModel_{initialEnergy}keV_{initialCurrent}pA.tiff'],
                                                                 photo_size_x, photo_size_y,
                                                                 1, 1, 0, photo_size_x - 1, 0,
                                                                 photo_size_y - 1, 0, 0, 1, 1, 1, 1, spacing,
                                                                 spacing,
                                                                 spacing, 1, 0, '', False, False, False, 0, '', False,
                                                                 0.0,
                                                                 0.0, 1, '')
        aChannel_BSE = listChannels_BSE[0]
        # # crop the image to the center
        box = aChannel_BSE.getBox()
        box.setDirection0Size(130*spacing)
        box.setDirection1Size(130*spacing)
        box.setCenter(aChannel_BSE.getBox().getCenter())
        c = Channel()
        c.copyShapeFromBox(box, 1)
        aChannel_BSE.copyDataFromCommonRegionInto(c, 0, CxvFiltering_Mode.CXV_FILTER_LINEAR, None)
        c = Channel.atomicLoad(savedir+'testImage.ORSObject', False)
        # send image to models
        testImagesX = np.array([c.getNDArray(0)[0] / 255])
        testImagesX = np.expand_dims(testImagesX, axis=3)
        testXDiceScore = np.array([0.9])
        # Reshape the images.
        #model = load_model('D:/Dragonfly/OrsQtPlateform/python/internalProject/microscopeControl/modelParameterTraining_simulations', compile=False)
        model = load_model('D:/Dragonfly/OrsQtPlateform/python/internalProject/microscopeControl/modelParameterTraining_0.25simulations_real', compile=False)
        predBeamEnergy, predBeamCurrent = model.predict([testImagesX, testXDiceScore])
        predBeamEnergy *= 20
        predBeamCurrent *= 614
        print()


    def captureWithSuggestedParams(self):
        commands: Su8230Commands = self.get_microscope_commands()
        if commands is None:
            return
        # set suggested parameters on microscope
        # commands.set_HV_control(predBeamEnergy)
        # commands.set_emission_current(predBeamCurrent)

        # TODO align beam
        # capture image
        modelType = 'modelSimulations_50_real'
        predBeamEnergy = 15
        predBeamCurrent = 26
        savedir = commands.set_capture_and_save(arg=self._saveStatus, project_name=self._filePath,
                                                newFileName=f'{modelType}_{predBeamEnergy}keV_{predBeamCurrent}pA')
        # TODO compare initial and final images
        # To measure the accuracy of the prediction, or if the model is actually helping, check segmentation before and after


if __name__ == '__main__':
    logging.basicConfig(filename='D:/', level=logging.INFO,
                        format="%(asctime)s.%(msecs)03d[%(levelname)-8s]:%(created).6f %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    impl = Su8230Impl()

    # Parameters

    # Available functions
    # impl.run_tests()
    impl.capture_XbyY_grid(x=3, y=3, stitchFollowingAcquisitions=False)
    # impl.tracking()
    # impl.captureImageToPredictParameters()
    # impl.captureWithSuggestedParams()
