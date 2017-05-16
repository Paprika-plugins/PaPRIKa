# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Paprika
                                 A QGIS plugin
 perform the Paprika Method with QGIS
                             -------------------
        begin                : 2017-01-09
        copyright            : (C) 2017 by SIG
        email                : ylecomte@sig.eu.com
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
    """Load Paprika class from file Paprika.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .paprika import Paprika
    return Paprika(iface)
