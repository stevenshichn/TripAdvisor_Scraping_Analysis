import csv
import re
from datetime import datetime
import TripAdvisor.StringUtils as Utils
import TripAdvisor.Convert_Helper as ConHelper
import TripAdvisor.DateUtils as DateUtils

def Drop_DataBase(databaseName, client):
    client.drop_database(databaseName)

def Clear_AllRecords_In_Table(databaseName, tableName, client):
    db = client[databaseName]
    collection = db[tableName]
    collection.remove()

def Insert_Data_IntoMongoDB(databBaseName, tableName, client, valueDic, updateColumn = '', updateKey = ''):
    db = client[databBaseName]
    collection = db[tableName]
    if updateColumn == '':
        collection.insert_one(valueDic)
    else:
        queryFilter = {updateColumn : updateKey}
        record = collection.find_one(queryFilter)
        if record is not None:
            collection.update_one(queryFilter, {'$set': valueDic})
        else:
            collection.insert_one(valueDic)

def Insert_CSV_Reviews_Into_MongoDB(fileName, client):
    db = client[Utils.TripAdvisor_DB]
    collection = db[Utils.Reviews_Table]
    with open(fileName, 'r', encoding='utf-8') as f:
        line = csv.reader(f)
        firstRow = next(line)
        for row in line:
            col = len(firstRow)
            dict = {}
            for index in range(col):
                if firstRow[index] == Utils.DicReviewDateKey:
                    dict[firstRow[index].replace(' ', '_')] = ConHelper.Convert_To_DateObject(row[index])
                else:
                    dict[firstRow[index].replace(' ', '_')] = row[index]
            try:
                collection.insert_one(dict)
            except:
                print(row[0])

        f.close()

def Insert_CSV_Users_Into_MongoDB(fileName, client):
    db = client[Utils.TripAdvisor_DB]
    userCollection = db[Utils.Users_Table]
    with open(fileName, 'r', encoding='utf-8') as f:
        line = csv.reader(f)
        firstRow = next(line)
        for row in line:
            col = len(firstRow)
            dict = {}
            userName = ''
            for index in range(col):
                if firstRow[index] == Utils.DicUserNameKey:
                    userName = row[index]
                dict[firstRow[index].replace(' ', '_')] = row[index]
            try:
                queryFilter = {Utils.DicUserNameKey.replace(' ', '_'): userName}
                record = userCollection.find_one(queryFilter)
                if record is None:
                    userCollection.insert_one(dict)
                else:
                    print(userName)
                    userCollection.update_one(queryFilter, dict)
            except:
                print(row[0])

        f.close()

# accept yyyy-mm-dd
def getDateRangeData(biggerDate, smallerDate, dbCollection):
    biggerD = DateUtils.parserDate(biggerDate)
    smallerD = DateUtils.parserDate(smallerDate)
    return dbCollection.find({Utils.DicReviewDateKey : {"$lt" : biggerD, "$gt" : smallerD}})

def getDateRangeDataAcceptDateObject(big, small, col, functionName):
    return col.find({'$and': [{Utils.DicReviewDateKey : {"$lte" : big, "$gte" : small}}, {Utils.DicTouristFunctionKey : functionName}]},{Utils.DicSentimentKey : 1,'_id' :0})

def getRegexObject(pattern):
    return re.compile(pattern, re.I)

def getDataWithKeyword(dbCollection, column, keywordPattern):
    return dbCollection.find({column : {"$regex" : getRegexObject(keywordPattern)}})

def aggregateSentiment(col, startDate, endDate, functionName, keyword = ''):
    pipe = [{
        '$match': {'$and': [{Utils.DicTouristFunctionKey : functionName},
                            {Utils.DicReviewDateKey : {'$gte': startDate, '$lte': endDate}},
                            {'$or':[{'$and' : [{Utils.DicCoomentKey : {"$regex" : getRegexObject(keyword)}}]},{Utils.DicTitleKey:{'$regex' : getRegexObject(keyword)}}]}]}
    },
        {'$group': {'_id': '$' + Utils.Sentiment_Col, 'total': {'$sum': 1}}}]
    return col.aggregate(pipeline=pipe)

def getSortedDateRecord(col, functionName):
    pipe = [{'$match': {Utils.DicTouristFunctionKey : functionName}},{'$sort': {Utils.DicReviewDateKey : -1}}]
    return col.aggregate(pipeline = pipe)

def getLatesetDateRecordDateString(col, functionName):
    df = getSortedDateRecord(col,functionName)
    return str(df.next()[Utils.DicReviewDateKey]).split( )[0]

def getLatestDate(col, functionName):
    d = getLatesetDateRecordDateString(col,functionName).split('-')
    return datetime(int(d[0]),int(d[1]), int(d[2]))

def averageReviewRating_DateRange(col, startDate, endDate, functionName, keyword =''):
    pipe = [{'$match': {'$and':
            [  {Utils.DicReviewDateKey:
                {'$gte': startDate,
                 '$lte': endDate
                }},{'$or':[{'$and' : [{Utils.DicCoomentKey : {"$regex" : getRegexObject(keyword)}}]},{ Utils.DicTitleKey :{'$regex' : getRegexObject(keyword)}}]},
                {Utils.DicTouristFunctionKey : functionName}
            ]}},
        {'$group': {'_id':'$' + Utils.DicTouristFunctionKey, 'avgRating':{'$avg' : '$' + Utils.DicReviewRatingKey}}}]
    return col.aggregate(pipeline = pipe)