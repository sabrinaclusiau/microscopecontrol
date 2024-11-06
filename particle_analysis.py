import os
from ORSModel import MultiROI
from matplotlib import pyplot as plt
import numpy as np
from scipy import stats
from mpl_toolkits.mplot3d import Axes3D

def plotSizeAndEccentricity(roi):
    # segmentedParticles:MultiROI = MultiROI.atomicLoad(path, False)
    segmentedParticles = roi.getLabelization(0, 0, 0, roi.getXSize() - 1, roi.getYSize() - 1, roi.getZSize() - 1, 0,
                         True, None, None)
    slotCount = segmentedParticles.getScalarValuesSlotCount()
    eccentricity_slot_idx = segmentedParticles.getScalarSlotIndexForDescription('2D Eccentricity', 0)
    eccentricityValues = segmentedParticles.getScalarValues(eccentricity_slot_idx, 0).getNDArray()[1:]
    diameter_slot_idx = segmentedParticles.getScalarSlotIndexForDescription('2D Equivalent Diameter', 0)
    diameterValues = segmentedParticles.getScalarValues(diameter_slot_idx, 0).getNDArray()[1:] * 10**9

    bin_means, bin_edges, binnumber = stats.binned_statistic(diameterValues, eccentricityValues, statistic='mean', bins=8)
    left_edges = bin_edges[:-1]
    width = (left_edges[1] - left_edges[0])
    plt.scatter(diameterValues, eccentricityValues, 10, color='r', zorder=5)
    plt.bar(left_edges, bin_means, align='edge', width=width, zorder=0, color=(0, 0, 0, 0),  edgecolor='black')
    plt.xlabel('Diameter (nm)')
    plt.ylabel('Eccentricity')
    plt.show()

    plt.hist(diameterValues, bins=int(diameterValues.max() - diameterValues.min()), color=(0.2, 0.2, 0.2, 0.2),  edgecolor='black')
    plt.xlabel('Diameter (nm)')
    plt.ylabel('Frequency')
    plt.show()


    plt.hist(eccentricityValues, bins=int((eccentricityValues.max() - eccentricityValues.min())/0.02), color=(0.2, 0.2, 0.2, 0.2),  edgecolor='black')
    plt.xlabel('Eccentricity')
    plt.ylabel('Frequency')
    plt.show()

def plot3DSizeDistributions():
    path = 'D:\\'
    multiROI20k = MultiROI.atomicLoad(os.path.join(path, 'multiROI20K.ORSObject'), False)
    diameter_slot_idx = multiROI20k.getScalarSlotIndexForDescription('2D Equivalent Diameter', 0)
    diameter20kValues = multiROI20k.getScalarValues(diameter_slot_idx, 0).getNDArray()[1:] * 10**9

    multiROI60k = MultiROI.atomicLoad(os.path.join(path, 'multiROI60K.ORSObject'), False)
    diameter_slot_idx = multiROI60k.getScalarSlotIndexForDescription('2D Equivalent Diameter', 0)
    diameter60kValues = multiROI60k.getScalarValues(diameter_slot_idx, 0).getNDArray()[1:] * 10 ** 9

    multiROI200k = MultiROI.atomicLoad(os.path.join(path, 'multiROI200K.ORSObject'), False)
    diameter_slot_idx = multiROI200k.getScalarSlotIndexForDescription('2D Equivalent Diameter', 0)
    diameter200kValues = multiROI200k.getScalarValues(diameter_slot_idx, 0).getNDArray()[1:] * 10 ** 9


    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('Diameter (nm)', fontsize=10, rotation=150)
    ax.set_ylabel('Magnification', fontsize=10)
    ax.set_zlabel('Frequency', fontsize=10, rotation=50)
    colors = [(0.2, 0.1, 0.6), (0.6, 0.1, 0.2), (0.1, 0.6, 0.6)]
    yLabel = ['', '', 'x20k', '', '', '', 'x60k', '', '', 'x200k']
    yspacing = 2.5
    for i, measurement in enumerate([diameter20kValues, diameter60kValues, diameter200kValues]):
        hist, bin_edges = np.histogram(measurement, bins=int(measurement.max() - measurement.min()))
        dx = np.diff(bin_edges)
        dy = np.ones_like(hist)*0.1
        y = i * (1 + yspacing) * np.ones_like(hist)
        z = np.zeros_like(hist)
        left_edges = bin_edges[:-1]
        ax.bar3d(left_edges, y, z, dx, dy, hist, color=colors[i], zsort='average', alpha=0.3)

    plt.yticks(range(-1, 9), yLabel)
    minimum = min(min(diameter200kValues), min(diameter20kValues), min(diameter60kValues))
    maximum = max(max(diameter200kValues), max(diameter20kValues), max(diameter60kValues))
    plt.xticks(np.arange(minimum, maximum+3, 3.4), fontsize=9)
    ax.set_xticks(ax.get_xticks()[::2])
    ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))

    plt.show()


if __name__ == "__main__":
    plot3DSizeDistributions()