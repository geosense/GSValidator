# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GSValidator
                                 A QGIS plugin
 Validace podrobné mapy
                             -------------------
        begin                : 2015-06-26
        copyright            : (C) 2015 by Geosense
        email                : krupickova.alzbeta@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GSValidator class from file GSValidator.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .gs_validate import GSValidator
    return GSValidator(iface)
