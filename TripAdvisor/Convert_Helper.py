from datetime import datetime
import calendar

## only accept the date string with 'mm/dd/yyyy' or 'dd MMM yyyy' format
def Convert_To_DateObject(dateText):
    dateV = ''
    monthV = ''
    yearV = ''
    if '/' in dateText:
        strArray = dateText.split('/')
        dateV = strArray[1]
        monthV = strArray[0]
        yearV = strArray[2]
    else:
        strArray = dateText.split( )
        dateV = strArray[0]
        monthV = str(Convert_Month_To_Integer(strArray[1]))
        yearV = strArray[2]
    return datetime(int(yearV),int(monthV),int(dateV))

## return integer value with short name Month. For example, 'Jan' will return 1
def Convert_Month_To_Integer(monthString):
    for i in range(len(calendar.month_name)):
        if calendar.month_name[i] == monthString:
            return i
    return 0