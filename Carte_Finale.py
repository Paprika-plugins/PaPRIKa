import processing
from qgis.core import *
from qgis.gui import *
from osgeo import gdal, ogr, osr
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import os


def genere_carteFinale(pP,pR,pI,pKa,Carte_P, Carte_R, Carte_I, Carte_Ka, doss):
    #Preparation des variables
    print (type(pI), type(pP), type(pKa), type(pR))
    print os.path.dirname(os.path.abspath(__file__))

        #croisement
    #Preparation des Rasters pour le calcul
    #verification de la validite des couches 
    rCarte_I = QgsRasterLayer(str(doss)+'/I_factor.tif', "I factor")
    rCarte_P = QgsRasterLayer(str(doss)+'/P_factor.tif', "P factor")
    rCarte_Ka = QgsRasterLayer(str(doss)+'/Ka_factor.tif', "Ka factor")
    rCarte_R = QgsRasterLayer(str(doss)+'/R_factor.tif', "R factor")
    print(rCarte_I.isValid(), rCarte_P.isValid(), rCarte_Ka.isValid(), rCarte_R.isValid())
    if rCarte_I.isValid() == False:
        print ("probleme pour ouvrir la carte I, verifiez votre raster")
    else:
        print ("Raster Carte I valide")
        pass

    if rCarte_P.isValid() == False:
        print ("probleme pour ouvrir la carte P, verifiez votre raster")
    else:
        print("Raster carte P valide")
        pass

    if rCarte_Ka.isValid() == False:
        print ("probleme pour ouvrir la carte Ka, verifiez votre raster")
    else:
        print("Raster carte Ka valide")
        pass

    if rCarte_R.isValid() == False:
        print ("probleme pour ouvrir la carte R, verifiez votre raster")
    else:
        print("Raster carte R valide")
        pass

    if rCarte_I.isValid() == True and rCarte_P.isValid() == True and rCarte_Ka.isValid() == True and rCarte_R.isValid() == True:
        print ("Chargement des rasters reussi!")

    #creation des entrees pour le calculateur de raster
    entries = []
    LayI = QgsRasterCalculatorEntry()
    LayI.ref = "LayI@1"
    LayI.raster = rCarte_I
    LayI.bandNumber = 1
    entries.append(LayI)

    LayK = QgsRasterCalculatorEntry()
    LayK.ref = "LayK@1"
    LayK.raster = rCarte_Ka
    LayK.bandNumber = 1
    entries.append(LayK)

    LayR = QgsRasterCalculatorEntry()
    LayR.ref = "LayR@1"
    LayR.raster = rCarte_R
    LayR.bandNumber = 1
    entries.append(LayR)

    LayP = QgsRasterCalculatorEntry()
    LayP.ref = "LayP@1"
    LayP.raster = rCarte_P
    LayP.bandNumber = 1
    entries.append(LayP)

    #creation du calcul a realiser
    Formula = "LayI@1*%s+LayK@1*%s+LayR@1*%s+LayP@1*%s" % (pI, pKa, pR,pP)
    print(Formula)

    #realisation du calcul et affichage de la Carte Vg non reclassee
    calc = QgsRasterCalculator(Formula, str(doss)+'/Carte_Vg.tif', 'Gtiff', rCarte_I.extent(), rCarte_I.width(), rCarte_I.height(), entries)
    test = calc.processCalculation()
    print (test)

        #reclassement
    #recuperation de l'extension en string pour le r:reclass
    extension = gdal.Open(Carte_I.source())
    ExtentInfo = extension.GetGeoTransform()
    Xmin = str(ExtentInfo[0])
    Ymin = str(ExtentInfo[3])
    Xmax = str(ExtentInfo[0] + ExtentInfo[1] * extension.RasterXSize)
    Ymax = str(ExtentInfo[3] + ExtentInfo[5] * extension.RasterYSize)
    Extent =(Xmin, Xmax, Ymax, Ymin)
    StrExtent = ','.join(Extent)

    #reclassement de la Carte Vg et affichage de la carte
    if QGis.QGIS_VERSION_INT > 21800 :
        processing.runalg("grass7:r.reclass", str(doss)+'/Carte_Vg.tif', os.path.dirname(os.path.abspath(__file__))+ '/reclass_rules/reclass_rules_carteVg.txt',"", StrExtent, int(ExtentInfo[1]), str(doss)+'/rVulnerability_Map.tif')
    else:
        processing.runalg("grass7:r.reclass", str(doss)+'/Carte_Vg.tif', os.path.dirname(os.path.abspath(__file__))+ '/reclass_rules/reclass_rules_carteVg.txt', StrExtent, int(ExtentInfo[1]), str(doss)+'/rVulnerability_Map.tif')

    src_ds_Carte_Finale = gdal.Open(str(doss)+'/rVulnerability_Map.tif')
    driver_Carte_Finale = gdal.GetDriverByName("GTiff") 
    dst_ds_Carte_Finale = driver_Carte_Finale.CreateCopy(str(doss)+'/Vulnerability_Map.tif', src_ds_Carte_Finale, 0 )
    src_ds_Carte_Finale = None
    dst_ds_Carte_Finale = None
    os.remove(str(doss)+'/rVulnerability_Map.tif')
    os.remove(str(doss)+'/rVulnerability_Map.tfw')
    #rCarte_Finale = QgsRasterLayer(str(doss)+'/Vulnerability_Map.tif', "Vulnerability Map")
    
    #fermeture des connexions
    rCarte_I = None
    rCarte_P = None
    rCarte_Ka = None
    rCarte_R = None
    
