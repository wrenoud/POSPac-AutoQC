import struct
import math
import geodetic
import pylab as pl
import ApplanixPOSPacModule as pos

################################################################################
## MAIN CODE
################################################################################
def navdif (solution, ref, navdif_filename, inc = 5, progressHandle = False):

    fid = open(navdif_filename,'wb')

    ## Get Times
    startTime = solution.getCommonIntStart(ref)
    endTime = solution.getCommonIntEnd(ref)

    fields = range(1,12)

    fld = {'time' : 0, 'lat' : 1, 'lon' : 2, 'alt' : 3, 'xVel' : 4, \
           'yVel' : 5, 'zVel' : 6, 'roll' : 7,'pitch' : 8, 'heading' : 9, \
           'wander' : 10 }

    times = range(startTime,endTime,inc)

    # progress bar stuff
    counter = 0
    goal = len(times)

    # walk through writing out file
    for time in times: # range(0,endTime-startTime,inc):

        # Progess bar stuff
        if progressHandle:
            counter += 1
            progressHandle(float(counter) / goal * 100.0)

        # print time
        solution_data = solution.getDataByTime([time],fields,0)[0]
        ref_data = ref.getDataByTime([time],fields,0)[0]

        message = pl.zeros(14,dtype=pl.float64)
        
        # time
        message[0] = time

        #position difference
        posDiff = geodetic.distVincenty(ref_data[fld['lat']], ref_data[fld['lon']], \
                                        solution_data[fld['lat']], solution_data[fld['lon']])
        
        northPosDiff = posDiff[0] * math.cos(posDiff[1])
        eastPosDiff = posDiff[0] * math.sin(posDiff[1])
        downPosDiff = ref_data[fld['alt']] - solution_data[fld['alt']]
        
        message[1] = northPosDiff
        message[2] = eastPosDiff
        message[3] = downPosDiff
        
        #velocity difference
        velNorthSol, velEastSol, velDownSol = pos.trueVelocity(solution_data[fld['xVel']],solution_data[fld['yVel']],solution_data[fld['zVel']], solution_data[fld['wander']])
        velNorthRef, velEastRef, velDownRef = pos.trueVelocity(ref_data[fld['xVel']],ref_data[fld['yVel']],ref_data[fld['zVel']], ref_data[fld['wander']])
        
        velNorthDiff = velNorthSol - velNorthRef
        velEastDiff = velEastSol - velEastRef
        velDownDiff = velDownSol - velDownRef
        
        message[4] = velNorthDiff
        message[5] = velEastDiff
        message[6] = velDownDiff

        # roll difference
        message[7] = solution_data[fld['roll']] - ref_data[fld['roll']]

        # pitch difference
        message[8] = solution_data[fld['pitch']] - ref_data[fld['pitch']]

        # heading difference
        solution_heading = pos.trueHeading(solution_data[fld['heading']],solution_data[fld['wander']])
        ref_heading = pos.trueHeading(ref_data[fld['heading']],ref_data[fld['wander']])
        message[9] = ref_heading - solution_heading

        # 2D radial position difference
        message[10] = math.sqrt(northPosDiff**2 + eastPosDiff**2)
        # 3D radial position difference
        message[11] = math.sqrt(northPosDiff**2 + eastPosDiff**2 + downPosDiff**2)
        # 2D radial velocity difference
        message[12] = math.sqrt(velNorthDiff**2 + velEastDiff**2)
        # 3D radial velocity difference
        message[13] = math.sqrt(velNorthDiff**2 + velEastDiff**2 + velDownDiff**2)

        fid.write(struct.pack("=14d",*message))


    fid.close()
