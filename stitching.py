from math import ceil, floor
import cv2
import math
import os
from os import listdir
from tkinter import Tcl
from skimage.measure import ransac
from skimage.transform import EuclideanTransform
import numpy as np

from ORSModel import orsObj, orsVect, Box, ROI, Channel, Vector3, createChannelFromNumpyArray, Graph

from OrsHelpers.visualboxhelper import VisualBoxHelper
from ORSServiceClass.mathutils.otsu import Otsu

from OrsPlugins.orsimageloader import OrsImageLoader
from OrsHelpers.featureextractorhelper.featureextractorhelper import FeatureExtractorHelper
from OrsPythonPlugins.OrsDatasetStitching_a2cacc40fd5a11e7990dc860006dfcdd.regularGrid import RegularGrid
from OrsPythonPlugins.OrsDatasetStitching_a2cacc40fd5a11e7990dc860006dfcdd.layout.gridLayout.gridLayout import GridLayout
from OrsPythonPlugins.OrsDatasetStitching_a2cacc40fd5a11e7990dc860006dfcdd.stitchers.abstractStitcher import AbstractStitcher
from OrsPythonPlugins.OrsDatasetStitching_a2cacc40fd5a11e7990dc860006dfcdd.stitchers.application import *
from OrsPythonPlugins.OrsChannelRegistration.OrsChannelRegistration import OrsChannelRegistration
from internalProject.microscopeControl.su8230.su8230_calibration import get_image_XY_size_for_magnification
from internalProject.microscopeControl.particle_analysis import plotSizeAndEccentricity

# open cv stitching https://colab.research.google.com/drive/11Md7HWh2ZV6_g3iCYSUw76VNr4HzxcX5#scrollTo=Mb0_FCAIE9gO
def detectAndDescribe(image, method=None):
    """
    Compute key points and feature descriptors using an specific method
    """

    if method is None:
        return

    # detect and extract features from the image
    if method == 'sift':
        descriptor = cv2.SIFT_create()
    # elif method == 'surf':
    #     descriptor = cv2.xfeatures2d.SURF_create()
    elif method == 'brisk':
        descriptor = cv2.BRISK_create()
    elif method == 'orb':
        descriptor = cv2.ORB_create()

    # get keypoints and descriptors
    (kps, features) = descriptor.detectAndCompute(image, None)

    return (kps, features)

def createMatcher(method, crossCheck):
    "Create and return a Matcher Object"

    if method == 'sift' or method == 'surf':
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=crossCheck)
    elif method == 'orb' or method == 'brisk':
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=crossCheck)
    return bf


def matchKeyPointsBF(featuresA, featuresB, method):
    bf = createMatcher(method, crossCheck=True)

    # Match descriptors.
    best_matches = bf.match(featuresA, featuresB)

    # Sort the features in order of distance.
    # The points with small distance (more similarity) are ordered first in the vector
    rawMatches = sorted(best_matches, key=lambda x: x.distance)
    print("Raw matches (Brute force):", len(rawMatches))
    return rawMatches

def getTransformation(referenceChannelGUID, toRegChannelGUID):
    img_ndArray1 = orsObj(referenceChannelGUID).getNDArray()[0]
    img_ndArray2 = orsObj(toRegChannelGUID).getNDArray()[0]
    featureDetector = 'sift'
    imageToProcess_1 = FeatureExtractorHelper.normalizeImage(img_ndArray1)
    imageToProcess_2 = FeatureExtractorHelper.normalizeImage(img_ndArray2)
    kps1, descs1 = detectAndDescribe(imageToProcess_1, featureDetector)
    kps2, descs2 = detectAndDescribe(imageToProcess_2, featureDetector)
    bf = cv2.BFMatcher()
    k = 2
    ratio = 0.7
    epsilon = 0.1
    numberOfIterations = 1000
    matches = bf.knnMatch(descs1, descs2, k=k)
    goodMatches = []
    try:
        for m, n in matches:
            if m.distance < ratio * n.distance:
                goodMatches.append(m)
    except ValueError:
        # Not enough matches exist
        pass

    sorted(goodMatches, key=lambda x: x.distance)
    translation, rotation = None, None
    if len(goodMatches) >= 3:  # we need at least 3 samples for ransac
        try:
            center = (imageToProcess_1.shape[1] / 2, imageToProcess_1.shape[0] / 2)
            src_pts = np.array(
                [(kps1[m.queryIdx].pt[0] - center[0], kps1[m.queryIdx].pt[1] - center[1]) for m in goodMatches])
            dst_pts = np.array(
                [(kps2[m.trainIdx].pt[0] - center[0], kps2[m.trainIdx].pt[1] - center[1]) for m in goodMatches])

            transformation_model, _ = ransac((dst_pts, src_pts), EuclideanTransform, min_samples=2,
                                             residual_threshold=epsilon,
                                             max_trials=numberOfIterations)

            rotation = transformation_model.rotation
            translation = Vector3(transformation_model.translation[0], transformation_model.translation[1], 0)
        except:
            pass
        if translation is None or rotation is None:
            try:
                # Ransac failed, we try with an estimation.
                rotation = FeatureExtractorHelper.findEstimatedRotationAngle(goodMatches, kps1, kps2, imageToProcess_1.shape, epsilon, numberOfIterations)
                translation = FeatureExtractorHelper.findEstimatedTranslationVector(goodMatches, kps1, kps2, imageToProcess_1.shape, rotation, epsilon,
                                                                 numberOfIterations)
            except:
                return Vector3(0, 0, 0), 0

    return translation, rotation

def stitch_right_to_left_for_column(list_channels_SE, list_channels_BSE, translation, column_idx, layoutData):
    x_size = layoutData['nbCols']
    y_size = layoutData['nbRows']
    for idx in range(y_size):
        # Apply transformation to SE images in column
        referenceChannelGUID = list_channels_SE[idx*x_size + column_idx]
        toRegChannelGUID = list_channels_SE[idx*x_size + column_idx + 1]
        transformationMatrix = AbstractStitcher.getTransformationMatrix(referenceChannelGUID, toRegChannelGUID,
                                                                        translation, None)
        AbstractStitcher.applyTransform(toRegChannelGUID, transformationMatrix)

        # Apply transformation to BSE images in column
        toRegChannelGUID = list_channels_BSE[idx * x_size + column_idx + 1]
        AbstractStitcher.applyTransform(toRegChannelGUID, transformationMatrix)

def stitch_bottom_to_up_for_row(list_channels_SE, list_channels_BSE, translation, row_idx, layoutData):
    x_size = layoutData['nbCols']
    for idx in range(x_size):
        # Apply transformation to SE images in column
        referenceChannelGUID = list_channels_SE[idx + row_idx*x_size]
        toRegChannelGUID = list_channels_SE[idx + row_idx*x_size + x_size]
        transformationMatrix = AbstractStitcher.getTransformationMatrix(referenceChannelGUID, toRegChannelGUID,
                                                                        translation, None)
        AbstractStitcher.applyTransform(toRegChannelGUID, transformationMatrix)

        # Apply transformation to BSE images in column
        toRegChannelGUID = list_channels_BSE[idx + row_idx*x_size + x_size]
        AbstractStitcher.applyTransform(toRegChannelGUID, transformationMatrix)

def generate_output_channels(listOfChannels_SE, listOfChannels_BSE=[]):
    # Create a channel once all the images are stitched
    globalBox = orsObj(listOfChannels_SE[0]).getBox()  # Global box
    globalBox.setDirection2Size(globalBox.getDirection2Spacing())

    for guid in listOfChannels_SE:
        channel = orsObj(str(guid))
        if channel is not None:
            globalBox.growToContain(channel.getBox())

    outputChannel_SE = Channel()
    outputChannel_SE.copyShapeFromBox(globalBox, 1)
    outputChannel_SE.setDataType(orsObj(listOfChannels_SE[0]).getDataType())
    outputChannel_SE.initializeData()
    for guid in listOfChannels_SE:
        channel = orsObj(guid)
        channel.copyDataFromCommonRegionInto(outputChannel_SE, 0, 1, None, False)

    if len(listOfChannels_BSE) == 0:
        return outputChannel_SE, None

    outputChannel_BSE = Channel()
    outputChannel_BSE.copyShapeFromBox(globalBox, 1)
    outputChannel_BSE.setDataType(orsObj(listOfChannels_BSE[0]).getDataType())
    outputChannel_BSE.initializeData()
    for guid in listOfChannels_BSE:
        channel = orsObj(guid)
        channel.copyDataFromCommonRegionInto(outputChannel_BSE, 0, 1, None, False)

    return outputChannel_SE, outputChannel_BSE

def stitchEntireGrid(project_name_SE, project_name_BSE, magnification=100000, xSize=5, ySize=5,
                          photo_size_x=1280, photo_size_y=960):
    # get list of captured images in the project folder
    images_SE = [project_name_SE + f for f in listdir(project_name_SE) if os.path.splitext(f)[-1] == '.tiff']
    images_BSE = [project_name_BSE + f for f in listdir(project_name_BSE) if os.path.splitext(f)[-1] == '.tiff']
    sorted_files_SE = Tcl().call('lsort', '-dict', images_SE)
    sorted_files_BSE = Tcl().call('lsort', '-dict', images_BSE)

    # add images as channel in dragonfly
    # x_size = 3
    # y_size = 3
    z_size = xSize*ySize
    # magnification = 12000
    # photo_size_x = 1280
    # photo_size_y = 960
    photo_size_x_mm = 127 / magnification
    spacing = photo_size_x_mm / photo_size_x * 10**-3  # in m
    listChannels_SE = OrsImageLoader.createDatasetFromFiles(list(sorted_files_SE), photo_size_x, photo_size_y, z_size, 1, 0, photo_size_x-1, 0,
                                                         photo_size_y-1, 0, z_size-1, 1, 1, 1, 1, spacing, spacing,
                                                         spacing, 1, 0, '', False, False, False, 0, '', False, 0.0,
                                                         0.0, 1, '')
    aChannel_SE = listChannels_SE[0]

    listChannels_BSE = OrsImageLoader.createDatasetFromFiles(list(sorted_files_BSE), photo_size_x, photo_size_y, z_size, 1, 0, photo_size_x-1, 0,
                                                         photo_size_y-1, 0, z_size-1, 1, 1, 1, 1, spacing, spacing,
                                                         spacing, 1, 0, '', False, False, False, 0, '', False, 0.0,
                                                         0.0, 1, '')
    aChannel_BSE = listChannels_BSE[0]
    # organize tiles according to position
    # top to bottom, left to right
    layoutData_SE = {'nbRows': ySize, 'nbCols': xSize, 'nbSlices': 1, 'overlap': 0,
                  'layoutOptions': (OrderOptions.SNAKE_BY_COLUMNS, HorizontalDirection.RIGHT,
                                    VerticalDirection.DOWN),
                  'table': [[GridLayout.CellMark.INCLUDED for x in range(xSize)] for y in range(ySize)],
                  'type': 'Grid',
                  'inputChannel': aChannel_SE.getGUID(),
                  'plugin': None}
    layout_SE = RegularGrid(layoutData_SE)
    listOfChannels_SE = layout_SE.getListChannelGUIDS()

    layoutData_BSE = {'nbRows': ySize, 'nbCols': xSize, 'nbSlices': 1, 'overlap': 0,
                     'layoutOptions': (OrderOptions.SNAKE_BY_COLUMNS, HorizontalDirection.RIGHT,
                                       VerticalDirection.DOWN),
                     'table': [[GridLayout.CellMark.INCLUDED for x in range(xSize)] for y in range(ySize)],
                     'type': 'Grid',
                     'inputChannel': aChannel_BSE.getGUID(),
                     'plugin': None}
    layout_BSE = RegularGrid(layoutData_BSE)
    listOfChannels_BSE = layout_BSE.getListChannelGUIDS()

    # Stitch columns
    # Reference index first, to stitch index second
    column_idx = 0
    pairsToStitch = [(0, 5), (4, 7)]
    for aPair in pairsToStitch:
        referenceChannelGUID = listOfChannels_SE[aPair[0]]
        toRegChannelGUID = listOfChannels_SE[aPair[1]]
        translation, _ = getTransformation(referenceChannelGUID, toRegChannelGUID)
        if translation is not None:
            if aPair[0] > aPair[1]:
                stitch_right_to_left_for_column(listOfChannels_SE, listOfChannels_BSE, translation.getNegated(), column_idx, layoutData_SE)
            else:
                stitch_right_to_left_for_column(listOfChannels_SE, listOfChannels_BSE, translation, column_idx, layoutData_SE)

        column_idx +=1

    # Stitch rows
    row_idx = 0
    pairsToStitch = [(5, 4), (3, 17)]
    for aPair in pairsToStitch:
        referenceChannelGUID = listOfChannels_SE[aPair[0]]
        toRegChannelGUID = listOfChannels_SE[aPair[1]]
        translation, _ = getTransformation(referenceChannelGUID, toRegChannelGUID)
        if translation is not None:
            if aPair[0] > aPair[1]:
                stitch_bottom_to_up_for_row(listOfChannels_SE, listOfChannels_BSE, translation.getNegated(), row_idx, layoutData_SE)
            else:
                stitch_bottom_to_up_for_row(listOfChannels_SE, listOfChannels_BSE, translation, row_idx, layoutData_SE)

        row_idx += 1

    outputChannel_SE, outputChannel_BSE = generate_output_channels(listOfChannels_SE, listOfChannels_BSE)
    outputChannel_SE.atomicSave(os.path.join(project_name_SE, 'Test.ORSObject'), False)
    outputChannel_BSE.atomicSave(os.path.join(project_name_BSE, 'Test.ORSObject'), False)

    # segment features with otsu (use UI to select algorithm)
    otsuThreshold, minValue, maxValue = Otsu.getOtsuThresholdAndMinMax(outputChannel_BSE, t=0, mask=None, aProgress=None)
    ROIForeground = outputChannel_BSE.getAsROIWithinRange(otsuThreshold, maxValue, None, None)

    # particle analysis size distribution (use UI to select measurement)
    plotSizeAndEccentricity(ROIForeground)

def stitchHighMagToLowMag(forStitching='', copyStitching='', lowMag=20000, magnification=100000, xSize=5, ySize=5,
                          photo_size_x=1280, photo_size_y=960):
    # Get list of captured images in the project folder
    images_SE = [copyStitching + f for f in listdir(copyStitching) if os.path.splitext(f)[-1] == '.tiff']
    sorted_files_SE = Tcl().call('lsort', '-dict', images_SE)
    images_BSE = [forStitching + f for f in listdir(forStitching) if os.path.splitext(f)[-1] == '.tiff']
    sorted_files_BSE = Tcl().call('lsort', '-dict', images_BSE)

    # magnification = 13000
    # lowMag = 1800
    # xSize = 5
    # ySize = 5
    # photo_size_x = 1280
    # photo_size_y = 960
    zSize = xSize * ySize

    # Compute spacing from image info
    photo_size_x_nm, photo_size_y_nm = get_image_XY_size_for_magnification(magnification)
    x_step_nm = round(ceil(photo_size_x_nm - photo_size_x_nm / 11) / 25) * 25
    y_step_nm = round(ceil(photo_size_y_nm - photo_size_y_nm / 11) / 25) * 25
    xStep = x_step_nm*10e-10
    yStep = y_step_nm*10e-10
    photo_size_x_mm = 127 / magnification
    spacing = photo_size_x_mm / photo_size_x * 10 ** -3  # in m
    spacingLowMag = 127 / lowMag / photo_size_x * 10 ** -3  # in m

    # Create a box of grid image size to guide registration
    box = Box()
    box.setDirection0Spacing(spacing)
    box.setDirection1Spacing(spacing)
    box.setDirection2Spacing(spacing)
    box.setDirection0Size(photo_size_x*spacing)
    box.setDirection1Size(photo_size_y*spacing)
    box.setDirection2Size(spacing)

    # load low mag image
    # lowMagChannel = Channel.atomicLoad(f'{pathBSE}\\lowMagChannel.ORSObject', False)
    channel_SE_lowmag = OrsImageLoader.createDatasetFromFiles([sorted_files_BSE[0]], photo_size_x, photo_size_y, 1,
                                                              1, 0, photo_size_x - 1, 0, photo_size_y - 1, 0, 0,
                                                              1, 1, 1, 1, spacingLowMag, spacingLowMag, spacingLowMag,
                                                              1, 0, '', False, False, False, 0, '', False, 0.0, 0.0, 1, '')
    lowMagChannel = channel_SE_lowmag[0]

    # Add grid images as channel in dragonfly
    channels_SE = OrsImageLoader.createDatasetFromFiles(list(sorted_files_SE), photo_size_x, photo_size_y, zSize + 1,
                                                        1, 0, photo_size_x - 1, 0, photo_size_y - 1, 0, zSize,
                                                        1, 1, 1, 1, spacing, spacing, spacing, 1, 0, '', False,
                                                        False, False, 0, '', False, 0.0, 0.0, 1, '')
    channels_BSE = OrsImageLoader.createDatasetFromFiles(list(sorted_files_BSE), photo_size_x, photo_size_y,
                                                        zSize + 1,
                                                        1, 0, photo_size_x - 1, 0, photo_size_y - 1, 0, zSize,
                                                        1, 1, 1, 1, spacing, spacing, spacing, 1, 0, '', False,
                                                        False, False, 0, '', False, 0.0, 0.0, 1, '')

    # initial center of first image on low mag (the grid first image top left)
    lowMagCenter = lowMagChannel.getBox().getCenter()
    # Reposition a mask using box created to help find the registration area
    maskBox = box.copy()
    # pad the mask (pad values can be changed in UI)
    maskBox.setDirection0Size((photo_size_x + 200) * spacing)
    maskBox.setDirection1Size((photo_size_y + 100) * spacing)
    visualBox = VisualBoxHelper.createVisualBoxFromBox(aBox=maskBox)
    mask = ROI()
    mask.copyShapeFromBox(maskBox, 1)
    aShape = visualBox.getShape(0)
    mask.paintShape3D(aShape, 1, 0)
    maskCenter = lowMagCenter

    # Current position
    cur_x = maskCenter.getX()
    cur_y = maskCenter.getY()
    n = 0

    # high mag images taken with snake pattern
    snakeValue = 1
    listChannels_SE = []
    listChannels_BSE = []
    for xIndex in range(xSize):
        for yIndex in range(ySize):
            n+= 1
            # Get each grid image - slice of the channel
            zIndex = xSize*xIndex + yIndex
            aChannel_SE = createChannelFromNumpyArray(channels_SE[0].getNDArray()[zIndex])
            aChannel_BSE = createChannelFromNumpyArray(channels_BSE[0].getNDArray()[zIndex])
            # Place high mag image box at approximately the right position on low mag image to guide registration
            maskCenter.setY(cur_y)
            maskCenter.setX(cur_x)
            box.setCenter(maskCenter)
            aChannel_BSE.setBox(box)
            boxForMask = mask.getBox()
            boxForMask.setCenter(maskCenter)
            mask.setBox(boxForMask)
            # mask.atomicSave(os.path.join(copyStitching, f'mask{n}.ORSObject'), False)
            # Register high mag channel to low mage channel
            # tune registration in UI : xTranslationInitial, yTranslationInitial, xSampling and ySampling
            transformationMatrix, metricSimilarity = OrsChannelRegistration.register(fixedChannel=lowMagChannel,
                                                                                     mobileChannel=aChannel_BSE,
                                                                                     useScale=False, useRotation=False,
                                                                                     useTranslation=True,
                                                                                     xScaleInitial=0.1,
                                                                                     yScaleInitial=0.1,
                                                                                     zScaleInitial=0.1,
                                                                                     xRotationInitial=0.174533,
                                                                                     yRotationInitial=0.174533,
                                                                                     zRotationInitial=0.174533,
                                                                                     xTranslationInitial=250e-9,
                                                                                     yTranslationInitial=250e-9,
                                                                                     zTranslationInitial=200e-9,
                                                                                     xScaleSmallest=0.01,
                                                                                     yScaleSmallest=0.01,
                                                                                     zScaleSmallest=0.01,
                                                                                     xRotationSmallest=0.00872665,
                                                                                     yRotationSmallest=0.00872665,
                                                                                     zRotationSmallest=0.00872665,
                                                                                     xTranslationSmallest=spacing,
                                                                                     yTranslationSmallest=spacing,
                                                                                     zTranslationSmallest=spacing,
                                                                                     nearestInterpolationMethod=False,
                                                                                     mutualInfoRegistrationMethod=True,
                                                                                     xSampling=1, ySampling=1,
                                                                                     zSampling=1, mask=mask,
                                                                                     useMultiScale=False)
            # Apply tranformation to the grid SE and BSE image (using the box)
            mobileChannelBox = aChannel_BSE.getBox()
            aChannel_SE.setBox(mobileChannelBox)
            listChannels_SE.append(aChannel_SE.getGUID())
            listChannels_BSE.append(aChannel_BSE.getGUID())
            cur_y += snakeValue * yStep

        # Reposition the box for next image
        cur_x += xStep
        snakeValue *= -1
        cur_y += snakeValue * yStep

        #maskCenter.setY(maskCenter.getY() - snakeValue * yStep)

    # Create output channel from list of stitched images
    outputChannel_SE, outputChannel_BSE = generate_output_channels(listChannels_BSE, listChannels_SE)
    outputChannel_SE.atomicSave(os.path.join(copyStitching, 'Test1.ORSObject'), False)
    outputChannel_BSE.atomicSave(os.path.join(forStitching, 'Stitched1.ORSObject'), False)

    # segment features with otsu (use UI to select algorithm)
    otsuThreshold, minValue, maxValue = Otsu.getOtsuThresholdAndMinMax(outputChannel_BSE, t=0, mask=None, aProgress=None)
    ROIForeground = outputChannel_BSE.getAsROIWithinRange(otsuThreshold, maxValue, None, None)

    # particle analysis size distribution (use UI to select measurement)
    plotSizeAndEccentricity(ROIForeground)

def stitchHighMagToLowMagWithGraph(project_name, overviewImage, cntGraph, lowMag, magnification, photo_size_x, photo_size_y, zSize):
    # Get list of captured images in the project folder
    # project_name_BSE = 'D:\\'
    images_SE = [project_name + f for f in listdir(project_name) if os.path.splitext(f)[-1] == '.tiff']
    sorted_files_SE = Tcl().call('lsort', '-dict', images_SE)
    # images_BSE = [project_name_BSE + f for f in listdir(project_name_BSE) if os.path.splitext(f)[-1] == '.tiff']
    # sorted_files_BSE = Tcl().call('lsort', '-dict', images_BSE)

    # Add images as channel in dragonfly
    # zSize = 11
    # magnification = 100000
    # photo_size_x = 1280
    # photo_size_y = 960
    photo_size_x_mm = 127 / magnification
    spacing = photo_size_x_mm / photo_size_x * 10 ** -3  # in m
    spacingLowMag = 127 / lowMag / photo_size_x * 10 ** -3  # in m
    box = Box()
    box.setDirection0Spacing(spacing)
    box.setDirection1Spacing(spacing)
    box.setDirection2Spacing(spacing)
    box.setDirection0Size(photo_size_x*spacing)
    box.setDirection1Size(photo_size_y*spacing)
    box.setDirection2Size(spacing)

    channel_SE_lowmag = OrsImageLoader.createDatasetFromFiles([sorted_files_SE[0]], photo_size_x, photo_size_y, 1,
                                                              1, 0, photo_size_x - 1, 0, photo_size_y - 1, 0, 0,
                                                              1, 1, 1, 1, spacingLowMag, spacingLowMag, spacingLowMag,
                                                              1, 0, '', False, False, False, 0, '', False, 0.0, 0.0, 1, '')
    channels_SE = OrsImageLoader.createDatasetFromFiles(list(sorted_files_SE[1:]), photo_size_x, photo_size_y, zSize + 1,
                                                        1, 0, photo_size_x - 1, 0, photo_size_y - 1, 0, zSize,
                                                        1, 1, 1, 1, spacing, spacing, spacing, 1, 0, '', False,
                                                        False, False, 0, '', False, 0.0, 0.0, 1, '')
    # channels_BSE = OrsImageLoader.createDatasetFromFiles(list(sorted_files_BSE), photo_size_x, photo_size_y,
    #                                                     zSize + 1,
    #                                                     1, 0, photo_size_x - 1, 0, photo_size_y - 1, 0, zSize,
    #                                                     1, 1, 1, 1, spacing, spacing, spacing, 1, 0, '', False,
    #                                                     False, False, 0, '', False, 0.0, 0.0, 1, '')
    lowMagChannel = channel_SE_lowmag[0]
    lowMagCenter = lowMagChannel.getBox().getCenter()
    listChannels_SE = []
    listChannels_BSE = []
    maskBox = box.copy()
    maskBox.setDirection0Size((photo_size_x+1000)*spacing)
    maskBox.setDirection1Size((photo_size_y+1000)*spacing)
    visualBox = VisualBoxHelper.createVisualBoxFromBox(aBox=maskBox)
    # Use a mask to help find the registration area
    mask = ROI()
    mask.copyShapeFromBox(maskBox, 1)
    aShape = visualBox.getShape(0)
    mask.paintShape3D(aShape, 1, 0)
    # n = 0
    timeIndex = 0
    # todo send vertices used directly from acquisitions
    predAndSuccMap = cntGraph.getVerticesPredecessorAndSuccessor(timeIndex).getNDArray()
    vertices = cntGraph.getVertices(timeIndex)
    predecessors = predAndSuccMap[::2]
    successors = predAndSuccMap[1::2]
    verticesWithPredecessors = np.where(predecessors != -1)
    verticesWithSuccessors = np.where(successors != -1)
    uniques, counts = np.unique(np.append(verticesWithPredecessors, verticesWithSuccessors), return_counts=True)
    validVertices = uniques[np.where(counts == 2)]
    maskCenter = lowMagCenter
    currentPosition = overviewImage.getBox().getCenter()
    curX = currentPosition.getX()
    curY = currentPosition.getY()
    maskToUse = None
    zIndex = 0
    for aVertex in validVertices:
        xPos = vertices.at(3*aVertex)
        yPos = vertices.at(3*aVertex + 1)
        xDelta = xPos - curX
        yDelta = yPos - curY
        x_step_nm = round(xDelta * 10e8 / 25) * 25
        y_step_nm = round(yDelta * 10e8 / 25) * 25
        if abs(x_step_nm) < 600 and abs(y_step_nm) < 400:
            continue

        # Get each slice as a channel
        aChannel_SE = createChannelFromNumpyArray(channels_SE[0].getNDArray()[zIndex])
        # aChannel_BSE = createChannelFromNumpyArray(channels_BSE[0].getNDArray()[zIndex])
        # use graph vertex positions to position mask on low mag image to help registration
        maskCenter.setX(xPos)
        maskCenter.setY(yPos)
        box.setCenter(maskCenter)
        aChannel_SE.setBox(box)
        boxForMask = mask.getBox()
        boxForMask.setCenter(maskCenter)
        mask.setBox(boxForMask)
        # mask.atomicSave(os.path.join(project_name_SE, f'mask{zIndex}.ORSObject'), False)

        # Register high mag channel to low mage channel
        # smallest step : high mag pixel size, initial step: low mag pixel size, mutual info
        # tune registration in UI : xTranslationInitial, yTranslationInitial, xSampling and ySampling
        transformationMatrix, metricSimilarity = OrsChannelRegistration.register(fixedChannel=lowMagChannel,
                                                                                 mobileChannel=aChannel_SE,
                                                                                 useScale=False, useRotation=False,
                                                                                 useTranslation=True,
                                                                                 xScaleInitial=0.1,
                                                                                 yScaleInitial=0.1,
                                                                                 zScaleInitial=0.1,
                                                                                 xRotationInitial=0.174533,
                                                                                 yRotationInitial=0.174533,
                                                                                 zRotationInitial=0.174533,
                                                                                 xTranslationInitial=400e-9,
                                                                                 yTranslationInitial=400e-9,
                                                                                 zTranslationInitial=400e-9,
                                                                                 xScaleSmallest=0.001,
                                                                                 yScaleSmallest=0.001,
                                                                                 zScaleSmallest=0.001,
                                                                                 xRotationSmallest=0.00872665,
                                                                                 yRotationSmallest=0.00872665,
                                                                                 zRotationSmallest=0.00872665,
                                                                                 xTranslationSmallest=spacingLowMag,
                                                                                 yTranslationSmallest=spacingLowMag,
                                                                                 zTranslationSmallest=spacingLowMag,
                                                                                 nearestInterpolationMethod=False,
                                                                                 mutualInfoRegistrationMethod=True,
                                                                                 xSampling=5, ySampling=2,
                                                                                 zSampling=1, mask=maskToUse,
                                                                                 useMultiScale=False)
        # mobileChannelBox = aChannel_SE.getBox()
        # aChannel_BSE.setBox(mobileChannelBox)
        listChannels_SE.append(aChannel_SE.getGUID())
        # listChannels_BSE.append(aChannel_BSE.getGUID())
        zIndex += 1
        curX = xPos
        curY = yPos



    outputChannel_SE, outputChannel_BSE = generate_output_channels(listChannels_SE, listChannels_BSE)
    outputChannel_SE.atomicSave(os.path.join(project_name, 'Unstitched.ORSObject'), False)
    # outputChannel_BSE.atomicSave(os.path.join(project_name_BSE, 'Stitched.ORSObject'), False)

if __name__ == "__main__":
    # stitchHighMagToLowMagWithGraph()
    pathSE = f'Z:\\'
    pathBSE = f'Z:\\'
    # stitchEntireGrid(pathSE, pathBSE)
    # stitchHighMagToLowMag(forStitching=pathBSE, copyStitching=pathSE)