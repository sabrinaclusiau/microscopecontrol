import logging
from internalProject.microscopeControl.abstract_tests import AbstractTests
from internalProject.microscopeControl.su8230.su8230_commands import Su8230Commands


class Su8230Tests(AbstractTests):
    def test_capture_settings(self, commands:Su8230Commands, project_name):
        """
        Test the different capture settings available - scan mode, scane resolution, scan time and integration number.

        Some scan settings are not compatible - if the combination is not valid, image is NOT captured and saved

        Saved file name contains the capture settings

        """
        if commands is None:
            return

        # Direct save will go to D:\SemImage\temp
        # commands.set_direct_save('Single')
        project_name = f'D:\\'

        # For the same position
        n = 0
        for aScanMode in commands.capture_scan_mode:
            for aResolution in commands.capture_resolution:
                for aScanTime in commands.capture_scan_time:
                    for anIntegrationNumber in commands.capture_integration_number:
                        isValid = commands.set_capture_settings(scan_mode=aScanMode,
                                                      resolution=aResolution,
                                                      scan_time=aScanTime,
                                                      integration_number=anIntegrationNumber)
                        if isValid:
                            savedir = commands.set_capture_and_save(arg='Single', project_name=project_name,
                                                                    newFileName=f'scanMode_{aScanMode}_resolution_{aResolution}_scanTime_{aScanTime}_integrationNumber_{anIntegrationNumber}_{n}')
                            n += 1