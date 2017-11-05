from datetime import datetime
import calendar

# accept yyyy-mm-dd
def parserDate(dateString):
    dateArray = dateString.split('-')
    yearV = dateArray[0].strip()
    monthV = dateArray[1].strip()
    dateV = dateArray[2].strip()
    return datetime(int(yearV),int(monthV),int(dateV))

def getMonthIndex(monthName):
    for i in range(len(calendar.month_name)):
        if calendar.month_name[i] == monthName:
            return i
    return 0

def parserDateString(dataString):
    dataArray = dataString.split( )
    if len(dataArray)>2:
        month = dataArray[1]
        m = getMonthIndex(month)
        if m != 0:
            y = int(dataArray[2].strip())
            d = int(dataArray[0].strip())
            return datetime(y,m,d)
        else:
            return None
    else:
        return None