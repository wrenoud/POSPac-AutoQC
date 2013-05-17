import os, math, struct
import pylab as pl

PROJECT_FILETYPE_MASK = "*.pospac"

class project():
    """
    Encapsulates an Applanix POSPac Project to provide objects for access to various
    data files and 
    """
    EXTRACTED_DIR = "Extract"
    PROCESSED_DIR = "Proc"
    
    def __init__(self, projectFile, version = "5.4 SP1"):
        if ".pospac" in projectFile:
            self.projectFile = projectFile
            #get the project path (minus .pospac extension)
            self.path = os.path.splitext(projectFile)[0]
            #get project name
            self.name = os.path.basename(self.path)
    
            # Detect Kernel
            if not self.detectKernel():
                raise IOError(0, "Unable to determine kernel name.", projectFile)
            
            
            self.version = version
            
            if self.version == "5.4 SP1":
                self.dataFileFieldCounts = {"sbet": 17, # Post-Processed Solution File
                                            "vnav": 17, # Real-Time Navigation Solution File
                                            "iin": 17, # Intermediate Post-Processed Navigation Solution File
                                            "smrmsg": 10, # Post-Processed Solution Accuracy File
                                            "smers": 50, # Smoothed Estimated Errors File
                                            #"iincal": 19, # Calibrated Installation Parameters File
                                            "iinkaru": 5, # Solution Status File
                                            "gamsu": 5, # GAMS Solution File
                                            "navdif_bet": 14, # Smoothed ? Reference Data (NAVDIF results)
                                            "g111": 5} # Real-time Heave Data
            elif self.version == "5.4":
                self.dataFileFieldCounts = {"sbet": 17, # Post-Processed Solution File
                                            "vnav": 17, # Real-Time Navigation Solution File
                                            "iin": 17, # Intermediate Post-Processed Navigation Solution File
                                            "smrmsg": 10, # Post-Processed Solution Accuracy File
                                            "smers": 53, # Smoothed Estimated Errors File
                                            "iincal": 19, # Calibrated Installation Parameters File
                                            "iinkaru": 5, # Solution Status File
                                            "gamsu": 5, # GAMS Solution File
                                            "navdif_bet": 14, # Smoothed ? Reference Data (NAVDIF results)
                                            "g111": 5} # Real-time Heave Data
            else: #pre 5.4
                 self.dataFileFieldCounts = {"sbet": 17, # Post-Processed Solution File
                                            "vnav": 17, # Real-Time Navigation Solution File
                                            "iin": 17, # Intermediate Post-Processed Navigation Solution File
                                            "smrmsg": 10, # Post-Processed Solution Accuracy File
                                            "smers": 53, # Smoothed Estimated Errors File
                                            "iincal": 19, # Calibrated Installation Parameters File
                                            "iinotfu": 5, # Solution Status File
                                            "gamsu": 5, # GAMS Solution File
                                            "betdif": 14} # Smoothed ? Reference Data (NAVDIF results)
        else:
            raise IOError(0, "Wrong filetype.", projectFile)
        
    def detectKernel(self):
        dirs = os.listdir(self.path)
        kernel = False
        
        for folder in dirs:
            folderPath = os.path.join(self.path,folder)
            if os.path.isdir(folderPath) and self.EXTRACTED_DIR in os.listdir(folderPath):
                self.kernel = folder
                return True

        return False
            
    def detectDataFileObjectFieldCount(self,filepath):
        for fieldCount in range(5,100):
            try:
                # data file class wil raise an Exception if it can't detect start and end time
                # or if the message length doesn't divide equaly into the file size.
                # Auto detect can in rare cases select erronious fieldcounts
                dataObject = dataFile(filepath, fieldCount)
                print "Field count detected: %s" % fieldCount
                return dataObject
            except IOError:
                pass
        raise Exception("Can't detect message field count.")


    def getDataFileObject(self, fileTypePrefix, dataTypeDir):
        """
        Returns a POSPacDataFile object for access to the data file
        """
        filepath = self.getDataFilePath(fileTypePrefix, dataTypeDir)

        if os.path.exists(filepath):
            if fileTypePrefix in self.dataFileFieldCounts:
                fieldCount = self.dataFileFieldCounts[fileTypePrefix]
                try:
                    dataObject = dataFile(filepath, fieldCount)
                except:
                    print "Warning: Know file type \"%s\" field count incorrect. Trying auto detect message field count." % fileTypePrefix
                    dataObject = self.detectDataFileObjectFieldCount(filepath)

            else:
                print "Warning: File type prefix \"%s\" unrecognized. Auto detecting message field count." % fileTypePrefix
                dataObject = self.detectDataFileObjectFieldCount(filepath)
        else:
            raise IOError(0,"Data file does not exist.",filepath)

        return dataObject
    
    def getExtractedDataObject(self,fileTypePrefix):
        """Convenience function"""
        return self.getDataFileObject(fileTypePrefix, self.EXTRACTED_DIR)
    
    def getProcessedDataObject(self,fileTypePrefix):
        """Convenience function"""
        return self.getDataFileObject(fileTypePrefix, self.PROCESSED_DIR)
    
    def getDataFilePath(self, fileTypePrefix, dataTypeDir):
        return os.path.join(self.path, self.kernel, dataTypeDir, self.getDataFileName(fileTypePrefix))
    
    def getDataFileName(self, fileTypePrefix):
        return "%s_%s.out" % (fileTypePrefix, self.kernel)
    
    def __str__(self):
        string = ""
        for key in self.__dict__:
            value = self.__dict__[key]
            string += "%s: %s\n" %(key, value)
        return string


class dataFile():
    """
    Class for accessing data in POSPAC data files
    """
    fieldLength = 8
    # the class was originally designed in MATLAB so the initial array
    # index was 1 in my code for message and field numbers, this allows for a
    # simple switch to using 0 as the starting index number

    arrayStart = 1

    def __init__(self, filename, fields):
    # Description: class constructor
    #
    # Inputs: filename - path to POSPAC file to open
    #         fields - number of double fields in the POSPAC file

        self.filename = filename
        self.fid = open(self.filename,'rb')
        self.fields = fields
        self.messageLength = self.fieldLength * self.fields
        self.size = os.path.getsize(filename)
        
        # compute the number of messages in the file
        messages = float(self.size) / self.messageLength
        if round(messages,0) == messages: # make sure the length divides evenly, otherwise there are malformed messages
            self.messages = int(messages)
        else:
            raise IOError(0,"Filesize is not an integer multiple of the message length.",self.filename)
        
        # get time data
        self.startTime = round(self.getField(self.arrayStart,self.arrayStart),3)
        self.endTime = round(self.getField(self.arrayStart + self.messages - 1,self.arrayStart),3)
        # divide the difference of first and last time by the number of messages
        # this is more precise than the difference between two messages because
        # the exact time can float slightly
        self.timeInc = round((self.getField(self.messages,self.arrayStart) - self.getField(self.arrayStart,self.arrayStart))/self.messages, 3)
        self.timeLength = self.endTime - self.startTime
        if self.timeLength <= 0:
            raise IOError(0,"File start time (%.3f) is greater than end time (%.3f)." % (self.startTime,self.endTime),filename)

    def __del__(self):
        self.fid.close()

    def getField(self,message,field):
    # Description: get a single value from the file at the designated message
    # and field number. Note that the count starts at 1 for both indexes.
    #
    # Inputs: message - message number (1 is first message)
    #         field - field number (1 is first field)
    #
    # Output: value - float value stored at (message,field)
        if message <= self.messages and field <= self.fields and message >= self.arrayStart:
            offset = (message - self.arrayStart) * self.messageLength + (field - self.arrayStart) * self.fieldLength;

            self.fid.seek(offset);
            data = self.fid.read(self.fieldLength);
            value = struct.unpack("=1d",data)
            return value[0]
        else:
            # throw out of range error
            print 'out of range'
            return False

    def getMsgNumByTime(self, time):
        return int(round(self.getPreciseMsgNumByTime(time),0))

    def getPreciseMsgNumByTime(self,time):
    # Description: finds the nearest message number in the file that corresponds
    # to the input time, performs a file read to determine the frequency bias. A more
    # sophisticated approach would be a frequency bias lookup table, but because of possible
    # non-linearity in the bias drift a file read would still be required as a check.
    # Observed drift has been anywhere from -0.05 to 0.12 seconds per hour (generally
    # slightly faster than target frequency), a reference bias within
    # 60 seconds of the target time is usually sufficient to predict the actual message
    # number. The drift doesn't usually exceed 1 second.
    #
    # Inputs: time - time to find the message number for
    #
    # Output: messageNumber - message number in the file
        if time >= self.startTime and time <= self.endTime:
            predictedMsgNum = self.getPredictedMsgNumByTime(time)
            timeAtPredictedMsg = self.getField(predictedMsgNum,self.arrayStart)
            drift = time - timeAtPredictedMsg
            actualMsgNum = predictedMsgNum + drift/self.timeInc
            return actualMsgNum
        else:
            # throw time outside file error
            raise IOError('Time (%.1f) not within bounds of file: %s' % (time,self.filename))

    def getPredictedMsgNumByTime(self, time):
    # Description: finds the nearest predicted message number in the file that based on
    # the time increment between messages and the start time
    #
    # Inputs: time - time to find the message number for
    #
    # Output: messageNumber - predicted message number in the file
        
        if time >= self.startTime and time <= self.startTime + self.timeLength / 2:
            messageNumber = int(round((time - self.startTime) / self.timeInc, 0) + self.arrayStart)
            return messageNumber
        elif time <= self.endTime and time > self.endTime - self.timeLength / 2:
            """closer to the end... we'll work backwards to avoid predicting past the end"""
            messageNumber = int(self.messages - round((self.endTime - time) / self.timeInc, 0) + self.arrayStart - 1)
            return messageNumber
        else:
            # throw time outside file error
            print 'time not within bounds of file'

    def getDataByTime(self, times, fields, interp = 0):
    # Description: gets data by times instead of message numbers
    #
    # Inputs: times - list of times to return
    #         fields - list of fields to return for selected times
    #
    # Output: value - 2D list of fields at given times
        value = [] # initialize return

        for time in times:
            msgData = []
            for field in fields:
                if not interp:
                    msgData += [self.getField(self.getMsgNumByTime(time),field)]
                else:
                    msgData += [self.interpByTime(time,field)]

            value += [msgData]
        return value

    def getData (self, messages, fields):
    # Description: gets a large chunk of data by message and field numbers
    #
    # Inputs: messages - list of messages to return
    #         fields - list of fields to return for selected messages
    #
    # Output: values - 2D list of fields at given messages
        rows = len(messages)
        cols = len(fields)

        values = pl.zeros((rows,cols),dtype=pl.float64) # initialize return

        for row in xrange(rows):
            for col in xrange(cols):
                values[row,col] = self.getField(messages[row],fields[col])
        return values

    def getCommonIntStart(self,dblfile):
    # Description: gets the earliest common whole integer time
    #
    # Inputs: dblfile - a double file to find a common time with
    #
    # Output: time - common start time
        if math.ceil(round(self.startTime, 3)) > math.ceil(round(dblfile.startTime, 3)):
            time = int(math.ceil(round(self.startTime, 3)))
        else:
            time = int(math.ceil(round(dblfile.startTime, 3)))
        return time

    def getCommonIntEnd(self,dblfile):
    # Description: gets the latest common whole integer time
    #
    # Inputs: dblfile - a double file to find a common time with
    #
    # Output: time - common start time
        if math.floor(round(self.endTime, 3)) > math.floor(round(dblfile.endTime, 3)):
            time = int(math.ceil(round(dblfile.endTime, 3)))
        else:
            time = int(math.ceil(round(self.endTime, 3)))
        return time

    def interpByTime(self, time, field):
    # Description: finds the nearest message number in the file that corresponds
    # to the input time
    #
    # Inputs: time - time to interpolate the value for
    #
    # Output: value - the interpolated value
        # fractional (float) message number
        exactMsg = self.getPreciseMsgNumByTime(time)
        # get the message number before and after
        leftMsg = math.floor(exactMsg)
        rightMsg = math.ceil(exactMsg)

        if leftMsg >= self.arrayStart and rightMsg <= self.messages:
            if leftMsg == rightMsg:
                return self.getField(leftMsg,field)
            else:
                leftData = [self.getField(leftMsg,1),self.getField(leftMsg,field)]
                rightData = [self.getField(rightMsg,1),self.getField(rightMsg,field)]

                if rightData[0] >= time and leftData[0] <= time:
                    # slope of the line, time is x, field is y
                    m = (rightData[1] - leftData[1])/(rightData[0] - leftData[0])

                    value = rightData[1] - m * (rightData[0] - time)
                    # print "    y1: %s (%s)" % (leftData[1],leftData[0])
                    # print "    y2: %s (%s)" % (rightData[1],rightData[0])
                    # print "interp: %s (%s)"% (value,time)
                    return value
                else:
                    # throw error
                    # but this is a class issue, wrong messages selected
                    print "Time outside interpolation bounds."
        else:
            # throw error
            print "can't interpolate, time outside file extents."

    def __str__(self):
        string = ""
        for key in self.__dict__:
            string += key + ": " + str(self.__dict__[key]) + "\n"

        return string

def trueVelocity(velocityX, velocityY, velocityZ, wanderAngle):
    """
    "The standard navigation record casts the computed velocity in a
    wander angle frame that is locally level but not necessarily aligned
    with true North. If the X-axis of the wander angle frame points North
    then the Y-axis points West and the Z-axis points Up. The standard
    navigation record includes the wander angle that allows
    transformation of the computed velocity components to North, East
    and Down."
    """
    velocityNorth = velocityX * math.cos(wanderAngle) - velocityY * math.sin(wanderAngle)
    velocityEast = - velocityX * math.sin(wanderAngle) - velocityY * math.cos(wanderAngle)
    velocityDown = - velocityZ
    return [velocityNorth, velocityEast, velocityDown]

def trueHeading(platformHeading, wanderAngle):
    """
    "The indicated heading is the heading of the wander angle frame.
    Again, this avoids a computational singularity at the poles. The true
    heading is computed as shown below"
    """
    return (platformHeading - wanderAngle) % (2 * math.pi)

def groundSpeed(velocityX, velocityY):
    return math.sqrt(velocityX**2 + velocityY**2)
