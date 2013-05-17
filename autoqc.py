import os
import sys
import pylab as pl
import ApplanixPOSPacModule as pos
import navdif

def countLessThan (data, value):
    cnt = 0
    for i in data:
        if i < value:
            cnt += 1
    return cnt

def countMoreThan (data, value):
    cnt = 0
    for i in data:
        if i > value:
            cnt += 1
    return cnt

def printHeader(text,printHandle):

    printHandle("________________________________________________________________________________")
    printHandle(text + " -")
    printHandle(" ")

#-------------------------------------------------------------------------------
# Tolerances
#-------------------------------------------------------------------------------

# RMS tolerances
RMS_blanking = 60 # seconds to ignore at beginning and end of solution
# position
RMS_north_tolerance = ['<',0.07] # meters
RMS_east_tolerance = ['<',0.07] # meters
RMS_down_tolerance = ['<',0.07] # meters
# orientation
RMS_roll_tolerance = ['<',1.2] # arc-minutes = 0.02 degrees
RMS_pitch_tolerance = ['<',1.2] # arc-minutes = 0.02 degrees
RMS_heading_tolerance = ['<',1.2] # arc-minutes = 0.02 degrees

# Error estimate tolerenaces and ranges
error_accel_bias_range = 500 # micro-g
error_accel_scale_range = 500 # ppm
error_gyro_bias_tolerance = ['<',5] # deg/hr
error_gyro_scale_range = 500 # ppm
error_lever_arm_tolerance = ['<',0.01] # meters

# Solution status tolerances
SV_count_tolerance = 4 # no less than
PDOP_tolerance = 3 # no greater than
Baseline_length_tolerance = ['<',20000] # meters, no greater than

# Sustained tolerances
GAMS_not_in_use = 60 # seconds
processing_mode = 60 # seconds

#-------------------------------------------------------------------------------
# Get Project Path
#-------------------------------------------------------------------------------

def autoqc (projectFile,navdifRefFile,printHandle,progressHandle):

    project = pos.project(projectFile)
    
    printHandle("Processing %s" % project.name)

    #-----------------------------------------------------------------------
    # Smoothed Performance Metrics
    #-----------------------------------------------------------------------
    printHeader("Smoothed Performance Metrics",printHandle)

    rms = project.getProcessedDataObject("smrmsg")

    msgStart = rms.getMsgNumByTime(rms.startTime + RMS_blanking)
    msgInc = 5 # seconds
    msgEnd = rms.getMsgNumByTime(rms.startTime + rms.messages*rms.timeInc - RMS_blanking)

    fields = [1,2,3,4,8,9,10]

    messages = range(msgStart,msgEnd,msgInc) # entire series at 5 seconds
    rms_data = rms.getData(messages,fields)

    printHandle('\tMax\t(StDev) - Tolerance')
    printHandle('North:\t%s\t(%s) - %s m' % (round(max(rms_data[:,1]),3),round(pl.std(rms_data[:,1]),3),RMS_north_tolerance[1]))
    printHandle('East:\t%s\t(%s) - %s m' % (round(max(rms_data[:,2]),3),round(pl.std(rms_data[:,2]),3),RMS_east_tolerance[1]))
    printHandle('Down:\t%s\t(%s) - %s m' % (round(max(rms_data[:,3]),3),round(pl.std(rms_data[:,3]),3),RMS_down_tolerance[1]))
    printHandle('Roll:\t%s\t(%s) - %s arc-min' % (round(max(rms_data[:,4]),3),round(pl.std(rms_data[:,4]),3),RMS_roll_tolerance[1]))
    printHandle('Pitch:\t%s\t(%s) - %s arc-min' % (round(max(rms_data[:,5]),3),round(pl.std(rms_data[:,5]),3),RMS_pitch_tolerance[1]))
    printHandle('Heading:\t%s\t(%s) - %s arc-min' % (round(max(rms_data[:,6]),3),round(pl.std(rms_data[:,6]),3),RMS_heading_tolerance[1]))

    del rms
    del rms_data

    #-----------------------------------------------------------------------
    # Calibration Installation Parameters
    #-----------------------------------------------------------------------
    printHeader("Calibration Installation Parameters",printHandle)

    cal = project.getProcessedDataObject("iincal")

    msgStart = cal.messages - 10*60 # last 10 minutes
    if msgStart <= cal.arrayStart: # make sure the file is at least 10 minutes long
        msgStart = cal.arrayStart
    msgEnd = cal.messages

    fields = [1,2,3,4,5]
    messages = range(msgStart,msgEnd,1)

    cal_data = cal.getData(messages,fields)

    printHandle('\tAvg.\t(StDev)')
    printHandle('X Ref Pri:\t%s\t(%s)' % (round(sum(cal_data[:,1])/len(cal_data[:,1]),3),round(pl.std(cal_data[:,1]),4)))
    printHandle('Y Ref Pri:\t%s\t(%s)' % (round(sum(cal_data[:,2])/len(cal_data[:,2]),3),round(pl.std(cal_data[:,2]),4)))
    printHandle('Z Ref Pri:\t%s\t(%s)' % (round(sum(cal_data[:,3])/len(cal_data[:,3]),3),round(pl.std(cal_data[:,3]),4)))
    printHandle(' ')
    printHandle('Max Figure of Merit: %s' % max(cal_data[:,4]))

    del cal
    del cal_data

    #-----------------------------------------------------------------------
    # Solution Status
    #-----------------------------------------------------------------------
    printHeader("Solution Status",printHandle)

    status = project.getProcessedDataObject("iinkaru")

    msgStart = status.arrayStart
    msgInc = 1
    msgEnd = status.messages

    fields = [1,2,3,4,5]
    messages = range(msgStart,msgEnd,msgInc) # entire series at 1 second

    status_data = status.getData(messages,fields)

    # Min SV Count
    min_SV = min(status_data[:,1])
    if min_SV <= SV_count_tolerance:
        timeOutOfTolerance = countLessThan(status_data[:,1],SV_count_tolerance + 1)
        printHandle('Min # SVs:    %s (out of tolerance for %s minutes)' % (min_SV,round(timeOutOfTolerance/60.0,1)))
    else:
        printHandle('Min # SVs:    %s' % min_SV)

    # Max PDOP
    max_PDOP = round(max(status_data[:,2]),2)
    if max_PDOP > PDOP_tolerance:
        timeOutOfTolerance = countMoreThan(status_data[:,2],PDOP_tolerance)
        printHandle('Max PDOP:     %s (out of tolerance for %s minutes)' % (max_PDOP,round(timeOutOfTolerance/60.0,1)))
    else:
        printHandle('Max PDOP:     %s' % max_PDOP)

    printHandle('Max Baseline: %s m' % round(max(status_data[:,3]),0))
    printHandle(' ')
    printHandle('Processing Mode:')

    proc_mode = pl.zeros(9)
    for _mode in status_data[:,4]:
        proc_mode[_mode] += 1

    printHandle('\tFixed NL/WL (0/1):\t%s minutes' % round((proc_mode[0] + proc_mode[1])/60,1))
    if proc_mode[2] > 60:
        printHandle('\tFloat Mode (2):\t%s minutes' % round(proc_mode[2]/60,1))
    if proc_mode[3] > 5:
        printHandle('\tDGPS Mode (3):\t%s minutes' % round(proc_mode[3]/60,1))
    if proc_mode[4] > 5:
        printHandle('\tRTCM Mode (4):\t%s minutes' % round(proc_mode[4]/60,1))
    if proc_mode[5] > 1:
        printHandle('\tIAPPP Mode (5):\t%s minutes' % round(proc_mode[5]/60,1))
    if proc_mode[6] > 1:
        printHandle('\tC/A Mode (6):\t%s minutes' % round(proc_mode[6]/60,1))
    if proc_mode[7] > 1:
        printHandle('\tGNSS Mode (7):\t%s minutes' % round(proc_mode[7]/60,1))
    if proc_mode[8] > 1:
        printHandle('\tDR Mode (8):\t%s minutes' % round(proc_mode[8]/60,1))

    del status
    del status_data

    #-----------------------------------------------------------------------
    # Smoothed Reference Data (Realtime Difference)
    #-----------------------------------------------------------------------
    printHeader("Smoothed-Reference Data (Realtime Difference)",printHandle)

    sbet = pos.dataFile(navdifRefFile,project.dataFileFieldCounts["sbet"])

    vnav = project.getExtractedDataObject("vnav")

    navdif_filename = project.getDataFilePath("autoqc_navdif_bet",project.PROCESSED_DIR)
    navdif.navdif(sbet,vnav,navdif_filename,5,progressHandle)

    diff = pos.dataFile(navdif_filename,project.dataFileFieldCounts["navdif_bet"])

    msgStart = diff.arrayStart
    msgInc = 1
    msgEnd = diff.messages

    fields = [1,2,3,4]
    messages = pl.arange(msgStart,msgEnd,msgInc) # entire series at 1 second

    diff_data = diff.getData(messages,fields)

    printHandle('\t\tAvg.\t(StDev)')
    printHandle('North Pos. Diff:\t%s\t(%s) m' % (round(sum(diff_data[:,1])/len(diff_data[:,1]),3),round(pl.std(diff_data[:,1]),3)))
    printHandle('East Pos. Diff:\t%s\t(%s) m' % (round(sum(diff_data[:,2])/len(diff_data[:,2]),3),round(pl.std(diff_data[:,2]),3)))
    printHandle('Down Pos. Diff:\t%s\t(%s) m' % (round(sum(diff_data[:,3])/len(diff_data[:,3]),3),round(pl.std(diff_data[:,3]),3)))

