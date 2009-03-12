"""
Allows for text logging to a logfile.
"""

import datetime

LARGE_BARRIER = "\n-------\n"
SMALL_BARRIER = "\n\n"
LOG_FILE_NAME = "log.txt"
ASSERT_FILE_NAME = "log.txt"

def log(logstring, logtitle = None, logfilename = LOG_FILE_NAME):
    logfile = open(logfilename, 'a')
    logfile.write(LARGE_BARRIER)
    logfile.write(str(datetime.datetime(2007, 04, 24).now()))
    logfile.write(SMALL_BARRIER)
    if logtitle is not None:
        logfile.write(logtitle)
        logfile.write(SMALL_BARRIER)
    logfile.write(str(logstring))
    logfile.close()

def pasAss(boolean_value, logstring, logtitle = None, logfilename = ASSERT_FILE_NAME):
    """
    Passive assertion.  If the boolean value provided is true, log something.
    
    This is distinguished from the active assertion built into Python, which
    actually raises an exception if the assertion is true.
    """
    
    if boolean_value:
        log(logstring, logtitle, logfilename)

if __name__ == "__main__":
    log("Hello, world!")
    log("Goodbye, world!")