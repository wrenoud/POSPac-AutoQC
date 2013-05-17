#-------------------------------------------------------------------------------
# Name:     geodetic
# Purpose:  Calculates geodetic distance between two points specified by
#           latitude/longitude using Vincenty inverse formula for ellipsoids
# Author:   Chris Veness, Weston Renoud
# From:     Vincenty inverse formula - T Vincenty, "Direct and Inverse
#           Solutions of Geodesics on the Ellipsoid with application of nested
#           equations", Survey Review, vol XXII no 176, 1975
#           http://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf
# Note:     Original code written in Javascript by Chris Veness
#           http://www.movable-type.co.uk/scripts/latlong-vincenty.html
#           Adapted to python By Weston Renoud
#
# Created:  02/06/2011
# Copyright: (c) Chris Veness 2002-2010, (c) Weston Renoud
# Licence:  <your licence>
#-------------------------------------------------------------------------------
import math

#-------------------------------------------------------------------------------

# http://www.movable-type.co.uk/scripts/latlong-vincenty.html
# @param   {Number} lat1, lon1: first point in radians
# @param   {Number} lat2, lon2: second point in radians
# @returns (Number} distance in metres between points
#-------------------------------------------------------------------------------

def distVincenty (lat1, lon1, lat2, lon2):
    # GRS80 ellipsoid params
    a = 6378137
    b = 6356752.31414
    f = 1/298.257222101
    L = lon2 - lon1
    U1 = math.atan((1-f) * math.tan(lat1))
    U2 = math.atan((1-f) * math.tan(lat2))
    sinU1 = math.sin(U1)
    cosU1 = math.cos(U1)
    sinU2 = math.sin(U2)
    cosU2 = math.cos(U2)

    lmda = L
    lmdaP = 0
    iterLimit = 100

    while (abs(lmda-lmdaP) > 1e-12 and --iterLimit>0):
        sinlmda = math.sin(lmda)
        coslmda = math.cos(lmda)
        sinSigma = math.sqrt((cosU2*sinlmda) * (cosU2*sinlmda) + (cosU1*sinU2-sinU1*cosU2*coslmda) * (cosU1*sinU2-sinU1*cosU2*coslmda))
        if (sinSigma==0): return 0  # co-incident points
        cosSigma = sinU1*sinU2 + cosU1*cosU2*coslmda
        sigma = math.atan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinlmda / sinSigma
        cosSqAlpha = 1 - sinAlpha*sinAlpha
        cos2SigmaM = cosSigma - 2*sinU1*sinU2/cosSqAlpha
        #if (isNaN(cos2SigmaM)): cos2SigmaM = 0  # equatorial line: cosSqAlpha=0 (?6)
        C = f/16*cosSqAlpha*(4+f*(4-3*cosSqAlpha))
        lmdaP = lmda
        lmda = L + (1-C) * f * sinAlpha * (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)))

    if (iterLimit==0): return NaN  # formula failed to converge

    uSq = cosSqAlpha * (a*a - b*b) / (b*b)
    A = 1 + uSq/16384*(4096+uSq*(-768+uSq*(320-175*uSq)))
    B = uSq/1024 * (256+uSq*(-128+uSq*(74-47*uSq)))
    deltaSigma = B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM) - B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)))
    s = b*A*(sigma-deltaSigma)

    s = round(s,3) # round to 1mm precision

    # note: to return initial/final bearings in addition to distance, use something like:
    fwdAz = math.atan2(cosU2*sinlmda,  cosU1*sinU2-sinU1*cosU2*coslmda)
    revAz = math.atan2(cosU1*sinlmda, -sinU1*cosU2+cosU1*sinU2*coslmda)
    return [ s, fwdAz, revAz]

def toRad(deg):
    return deg/180*math.pi
def toDeg(rad):
    return rad/math.pi*180

if __name__ == "__main__":
#
# Test case:
#
    ret = distVincenty(toRad(50.06632222222222),toRad(-5.71475),toRad(58.64402222222222),(-3.0700944444444445))
    print ret['distance'] # 969954.114
    print toDeg(ret['initialBearing']) # 9.14186190832