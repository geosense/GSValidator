# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GSValidatorDialog
                                 A QGIS plugin
 Validace podrobné mapy
                             -------------------
        begin                : 2015-06-26
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Geosense
        email                : krupickova.alzbeta@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic, QtCore
from qgis.core import QgsMapLayer, QGis

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gs_validate_dialog_base.ui'))


class GSValidatorDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(GSValidatorDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.rulesFileButton.clicked.connect(self.selectFile)
        self.outputFileButton.clicked.connect(self.createFile)

    def selectFile(self):
        self.rulesFile.setText(QtGui.QFileDialog.getOpenFileName(self,
                                                                 "Open file with rules (JSON)",
                                                                 QtCore.QDir.homePath(),
                                                                 "JSON file (*.json)"))

    def createFile(self):
        self.outputFile.setText(QtGui.QFileDialog.getSaveFileName(self,
                                                                  "Save errors as *.shp",
                                                                  QtCore.QDir.homePath(),
                                                                  "shapefile (*.shp)"))


