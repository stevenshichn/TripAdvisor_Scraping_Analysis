import pandas as pd
import re
import datetime
import matplotlib
import numpy
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from pymongo import MongoClient
from porter2stemmer import Porter2Stemmer as stemmer
from wordcloud import WordCloud
import TripAdvisor.StringUtils as Utils
import TripAdvisor.DateUtils as DateUtils
import TripAdvisor.MongoDB_Helper as MongoUtils

client = MongoClient("localhost", 27017)
db = client[Utils.TripAdvisor_DB]
collection = db[Utils.Reviews_Table]

stopword = ['hotel', 'Singapor', 'great', 'nan', 'room', 'good', 'of', 'staff', 'locat', 'swissotel', 'clark', 'quay',
             'merchant', 'court']

cursor = collection.find()
#
# #pointing the cursor to the query statement, we can modify the mongodb query here to specify the data to load in.
df = pd.DataFrame(list(cursor))

def One_Day_Before(dateV):
    return Get_Past_Date_Object(dateV,1)

def One_Year_Before(dateV):
    return Get_Past_Date_Object(dateV,365)

def One_Day_After(dateV):
    return Get_Past_Date_Object(dateV,-1)

def One_Year_After(dateV):
    return Get_Past_Date_Object(dateV,-365)

def Get_Past_Date_Object(baseDate, days):
    return DateUtils.parserDate(Get_Past_Date(baseDate,days))

def Get_Display_DateRange(start, end):
    try:
        st = str(start).split( )[0] if isinstance(start, datetime.datetime) else start
        ed = str(end).split( )[0] if isinstance(end, datetime.datetime) else end
        return st + ' ~ ' + ed
    except:
        return ''

## positive days, return before baseDate string, negative return after baseDate string
def Get_Past_Date(baseDate, days):
    if isinstance(baseDate, datetime.datetime):
        return str(baseDate - datetime.timedelta(days)).split( )[0]
    else:
        return str(DateUtils.parserDate(baseDate) - datetime.timedelta(days)).split( )[0]

def Get_Append_Keyword_Title(keyword):
    withKeyWord = '' if keyword == '' else ' with keyword \"' + keyword +'\"'
    return withKeyWord

    # The percent symbol needs escaping in latex
    if matplotlib.rcParams['text.usetex'] is True:
        return s + r'$\%$'
    else:
        return s + '%'


def Show_Avg_Review_Rating_DateRange(renovateStart, renovationEnd, functionName, keyword = '', daysBefore = 365, daysAfter = 365):
    renovateStart_Date = DateUtils.parserDate(renovateStart)
    oneDayBefore = One_Day_Before(renovateStart_Date)
    oneYearBefore = Get_Past_Date_Object(oneDayBefore, daysBefore)
    renovateEnd_Date = DateUtils.parserDate(renovationEnd)
    oneDayAfter = One_Day_After(renovateEnd_Date)
    oneYearAfter = Get_Past_Date_Object(oneDayAfter, -daysAfter)
    latestRecord = MongoUtils.getLatestDate(collection, functionName)
    if oneYearAfter > latestRecord:
        oneYearAfter = latestRecord
    before_renovation = MongoUtils.averageReviewRating_DateRange(collection, oneYearBefore, oneDayBefore, functionName, keyword)
    undergoing_renovation = MongoUtils.averageReviewRating_DateRange(collection, renovateStart_Date, renovateEnd_Date, functionName, keyword)
    after_renovation = MongoUtils.averageReviewRating_DateRange(collection, oneDayAfter, oneYearAfter, functionName,keyword)
    df_before = pd.DataFrame(list(before_renovation))
    df_undergoing = pd.DataFrame(list(undergoing_renovation))
    df_after = pd.DataFrame(list(after_renovation))
    Raw_Data = {Utils.TimeLine_Col : [1, 2, 3],
                Utils.Average_Rating_Col : [Utils.FormatFloatWithTwoDecimalPlace(df_before['avgRating'][0]), Utils.FormatFloatWithTwoDecimalPlace(df_undergoing['avgRating'][0]), Utils.FormatFloatWithTwoDecimalPlace(df_after['avgRating'][0])]}
    plt.figure(1)
    plt.subplot(211)
    plt.xticks(Raw_Data[Utils.TimeLine_Col],[Get_Display_DateRange(oneYearBefore, oneDayBefore), Get_Display_DateRange(renovateStart, renovationEnd), Get_Display_DateRange(oneDayAfter, oneYearAfter)])
    plt.axhline(y=Raw_Data[Utils.Average_Rating_Col][0], xmin=0, xmax=1 / 6, c=Utils.Orange_Color, linestyle='dashed')
    plt.axhline(y=Raw_Data[Utils.Average_Rating_Col][1], xmin=0, xmax=0.5, c=Utils.Light_Green_Color, linestyle='dashed')
    plt.axhline(y=Raw_Data[Utils.Average_Rating_Col][2], xmin=0, xmax=5 / 6, c=Utils.Blue_Color, linestyle='dashed')
    plt.ylabel('Rating Mean')
    plt.plot(Raw_Data[Utils.TimeLine_Col], Raw_Data[Utils.Average_Rating_Col],'bo')
    kw = Get_Append_Keyword_Title(keyword)
    plt.title(functionName + ('\n Rating Mean'+kw if kw != '' else ''),loc='center')
    plt.axis([0.5,3.5,min(Raw_Data[Utils.Average_Rating_Col])-0.5,max(Raw_Data[Utils.Average_Rating_Col])+0.5])
    plt.show()


def Show_Sentiment_Stacked_Bar_DateRange(renovateStart, renovationEnd, functionName, keyword='', daysBefore = 365, daysAfter = 365):
    renovateStart_Date = DateUtils.parserDate(renovateStart)
    oneDayBefore = One_Day_Before(renovateStart)
    oneYearBefore = Get_Past_Date_Object(oneDayBefore, daysBefore)
    renovateEnd_Date = DateUtils.parserDate(renovationEnd)
    oneDayAfter = One_Day_After(renovateEnd_Date)
    oneYearAfter = Get_Past_Date_Object(oneDayAfter, -daysAfter)
    latestRecord = MongoUtils.getLatestDate(collection, functionName)
    if oneYearAfter > latestRecord:
        oneYearAfter = latestRecord
    before_renovation = MongoUtils.aggregateSentiment(collection, oneYearBefore, oneDayBefore, functionName, keyword)
    undergoing_renovation = MongoUtils.aggregateSentiment(collection, renovateStart_Date, renovateEnd_Date, functionName, keyword)
    after_renovation = MongoUtils.aggregateSentiment(collection, oneDayAfter, oneYearAfter, functionName, keyword)
    df_before = pd.DataFrame(list(before_renovation))
    df_before = df_before.sort_values(by = ['_id'])
    df_undergoing = pd.DataFrame(list(undergoing_renovation))
    df_undergoing = df_undergoing.sort_values(by=['_id'])
    df_after = pd.DataFrame(list(after_renovation))
    df_after = df_after.sort_values(by=['_id'])
    if df_before.empty != True and df_undergoing.empty != True and df_after.empty != True:
        name_Value = [Utils.Negative_Col.lower(),Utils.Neutral_Col.lower(),Utils.Positive_Col.lower()] # after sort the dataframe, the name should be in this order
        before_V = [0,0,0]
        undergoing_V = [0,0,0]
        after_V = [0,0,0]
        for index, row in df_before.iterrows():
            p = name_Value.index(row['_id']) ## to adapt dataframe doesn't have all the columns
            if p != -1:
                before_V[p] = row['total']
        for index, row in df_undergoing.iterrows():
            p = name_Value.index(row['_id'])  ## to adapt dataframe doesn't have all the columns
            if p != -1:
                undergoing_V[p] = row['total']
        for index, row in df_after.iterrows():
            p = name_Value.index(row['_id'])  ## to adapt dataframe doesn't have all the columns
            if p != -1:
                after_V[p] = row['total']

        raw_data = {Utils.TimeLine_Col : [Get_Display_DateRange(oneYearBefore, oneDayBefore), Get_Display_DateRange(renovateStart, renovationEnd), Get_Display_DateRange(oneDayAfter, oneYearAfter)],
                    Utils.Negative_Col : [before_V[0] ,undergoing_V[0],after_V[0]],
                    Utils.Neutral_Col : [before_V[1],undergoing_V[1],after_V[1]],
                    Utils.Positive_Col : [before_V[2],undergoing_V[2],after_V[2]]}

        df = pd.DataFrame(raw_data, columns = [Utils.TimeLine_Col, Utils.Negative_Col, Utils.Neutral_Col, Utils.Positive_Col])

        # Create a figure with a single subplot
        f, ax = plt.subplots(1, figsize=(6,3))

        # Set bar width at 1
        bar_width = 1

        # positions of the left bar-boundaries
        bar_l = [i for i in range(len(df[Utils.Negative_Col]))]

        # positions of the x-axis ticks (center of the bars as bar labels)
        tick_pos = [i+(bar_width/2) for i in bar_l]

        # Create the total score for each participant
        totals = [i+j+k for i,j,k in zip(df[Utils.Negative_Col], df[Utils.Neutral_Col], df[Utils.Positive_Col])]

        # Create the percentage of the total score the negative value for each participant was
        negative_R = [i / j * 100 for  i,j in zip(df[Utils.Negative_Col], totals)]

        # Create the percentage of the total score the neutral value for each participant was
        neutral_R = [i / j * 100 for  i,j in zip(df[Utils.Neutral_Col], totals)]

        # Create the percentage of the total score the positive value for each participant was
        positive_R = [i / j * 100 for  i,j in zip(df[Utils.Positive_Col], totals)]

        # Create a bar chart in negative
        p1=ax.bar(bar_l,
               # using negative_R data
               negative_R,
               # labeled
               label=Utils.Before_Renovation_Col,
               # with alpha
               alpha=0.9,
               # with color orange
               color=Utils.Orange_Color,
               # with bar width
               width=bar_width,
               # with border color
               edgecolor='white'
               )

        # Create a bar chart in position bar_1
        p2 = ax.bar(bar_l,
               # using neutral_R data
               neutral_R,
               # with negative_R
               bottom=negative_R,
               # labeled
               label=Utils.Undergoing_Renovation_Col,
               # with alpha
               alpha=0.9,
               # with color light green
               color=Utils.Light_Green_Color,
               # with bar width
               width=bar_width,
               # with border color
               edgecolor='white'
               )

        # Create a bar chart in position bar_1
        p3 = ax.bar(bar_l,
               # using positive_R data
               positive_R,
               # with negative_R and neutral_R on bottom
               bottom=[i+j for i,j in zip(negative_R, neutral_R)],
               # labeled
               label=Utils.After_Renovation_Col,
               # with alpha
               alpha=0.9,
               # with color blue
               color=Utils.Blue_Color,
               # with bar width
               width=bar_width,
               # with border color
               edgecolor='white'
               )

        # Set the ticks to be Stages
        plt.xticks(tick_pos, df[Utils.TimeLine_Col])

        def to_percent(y, position):
            # Ignore the passed in position. This has the effect of scaling the default
            # tick locations.
            s = str(y)

            # The percent symbol needs escaping in latex
            if matplotlib.rcParams['text.usetex'] is True:
                return s + r'$\%$'
            else:
                return s + '%'
        formatter = FuncFormatter(to_percent)
        # Set the formatter
        plt.gca().yaxis.set_major_formatter(formatter)
        for i,v in enumerate(df[Utils.Negative_Col]):
            ax.text(v, i, str(v), color = 'blue', fontweight = 'bold')
        kw = Get_Append_Keyword_Title(keyword)
        plt.title(functionName + ('\nSentiment Comparison' + kw if kw != '' else ' Sentiment Comparison'),loc = 'center')
        # Let the borders of the graphic
        plt.xlim([min(tick_pos)-bar_width*1.1, max(tick_pos)+bar_width*0.4])
        plt.ylim(-5, 105)
        plt.text(x = -0.1, y=negative_R[0]/2, text = Utils.Format_To_Percentage_With_OneFloatPoint(negative_R[0]), ha='left', s=40)
        plt.text(x=0.9, y=negative_R[1]/2, text= Utils.Format_To_Percentage_With_OneFloatPoint(negative_R[1]), ha='left', s=40)
        plt.text(x=2, y=negative_R[2]/2, text=Utils.Format_To_Percentage_With_OneFloatPoint(negative_R[2]), ha='left', s=40)

        # rotate axis labels
        plt.setp(plt.gca().get_xticklabels(), rotation=0, horizontalalignment='right')

        plt.legend((p3[0],p2[0],p1[0]),(Utils.Positive_Col,Utils.Neutral_Col,Utils.Negative_Col), loc='center right')

        # shot plot
        plt.show()
    else:
        print('no record found')

#Displaying the number of reviews and mean review rating
def displayinfo(sortedBy = 1):
    df.head()
    df.Review_Rating.mean()
    sortK = 'count' if sortedBy == 1 else 'mean'
    count = df.groupby(Utils.DicTouristFunctionKey).Review_Rating.agg(['count','mean']).sort_index()
    return (count)

#Displaying the number of reviews and mean review rating for the comment with a specific word
def displayinfo_word(word, sortedBy = 1):
    df[word] = df.Comment.str.contains(word,flags=re.IGNORECASE,regex=True,na=False)
    sortK = 'count' if sortedBy == 1 else 'mean'
    countcomment = df[df[word]].groupby(Utils.DicTouristFunctionKey).Review_Rating.agg(['count','mean']).sort_index()
    return (countcomment)


#function to return a new dataframe with another column that specify whether it contains the word
def dfwithword(df,word):
    df[word] = df.Comment.str.contains(word,flags=re.IGNORECASE,regex=True,na=False)
    return(df)



def Generate_Interval_Number(start, qty, interval):
    limit = start + (qty-1)*interval+1
    if isinstance(start, int):
        return list(range(start, limit, interval))
    else:
        return list(numpy.arange(start, limit, interval))

#plotting the count of renovation related versus the total
def plotcount(topic):
    fig = plt.figure()
    names=[]
    displayInfo = displayinfo().copy()
    countList = list(displayinfo()['count'])
    wordList = list(displayinfo_word(topic)['count'])
    lenCount = len(countList)
    print(list(displayInfo))
    newFrame = pd.DataFrame(index=displayInfo.index)
    newFrame['count'] = countList
    newFrame[topic + '-count'] = wordList
    print(newFrame)
    newFrame = newFrame.sort('count',ascending = True)
    print(newFrame)
    keyBar = plt.bar(Generate_Interval_Number(1, lenCount, 2), newFrame[topic + '-count'],
                     label='Reviews with Keyword-' + topic, color=Utils.Orange_Color)
    barList = plt.bar(Generate_Interval_Number(2, lenCount, 2), newFrame['count'], label='Total Reviews',
                      color=Utils.Blue_Color)


    for s in list(newFrame.index):
        names.append(s.replace('Singapore','SG'))
    plt.xticks(Generate_Interval_Number(1.5, lenCount,2), names, rotation=20)
    plt .legend()
    plt.title('Count of Reviews by Hotel')
    plt.show()

def plotcount_word(word):
    fig = plt.figure()
    names = []

    displayInfo = displayinfo().copy()
    countList = list(displayinfo()['mean'])
    wordList = list(displayinfo_word(word)['mean'])
    lenCount = len(countList)
    print(list(displayInfo))
    newFrame = pd.DataFrame(index=displayInfo.index)
    newFrame['mean'] = countList
    newFrame[word + '-mean'] = wordList
    print(newFrame)
    newFrame = newFrame.sort('mean', ascending=True)
    lenCount = len(countList)
    print(newFrame)
    for s in list(newFrame.index):
        names.append(s.replace('Singapore','SG'))
    plt.bar(Generate_Interval_Number(1, lenCount, 2), newFrame[word + '-mean'],
                label='Reviews with Keyword-' + word,
                color=Utils.Orange_Color)
    plt.bar(Generate_Interval_Number(2, lenCount, 2),newFrame['mean'], label = 'Total Reviews', color =Utils.Blue_Color)


    plt.xticks(Generate_Interval_Number(1.5, lenCount,2),names, rotation=20)
    # plt.yticks(Generate_Interval_Number(0.5,lenCount,1),['','','','','','','',3.5,4,4.5,5,'',''])
    plt.legend()
    plt.title('Rating Mean by Hotel')
    plt.show()

#generate a histogram of the review rating distribution
def reviewplot(df):
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    v = df.sort('Review_Rating')
    ax.hist(v['Review_Rating'],bins = 5,color=Utils.Blue_Color)
    plt.title('Review Distribution')
    plt.xlabel('Review Rating')
    ax.set_xticks([1,2,3,4,5])
    plt.ylabel('# Reviews')
    plt.show()

#generate a review distribution histogram by sentiment
def reviewplotsentiment(df):
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.hist(df[df.Sentiment=='positive']['Review_Rating'],bins = 5,label='positive',alpha=0.5, color=Utils.Blue_Color)
    ax.hist(df[df.Sentiment=='negative']['Review_Rating'],bins = 5,label='negative',alpha=0.5,color=Utils.Orange_Color)
    plt.title('Review Distribution')
    plt.xlabel('Review Rating')
    ax.set_xticks([1,2,3,4,5])
    plt.ylabel('# Reviews')
    plt.legend()
    plt.show()

# a function to plot the time series with the rolling mean rating
def dftimeplot(df,tfname):
    df= df[df.TouristFunction_Name == tfname]
    df['Review_Date'] = pd.to_datetime(df['Review_Date'])
    df = df.sort_values(by='Review_Date',ascending =False)
    df['Rolling_Mean'] = df['Review_Rating'].rolling(window = 100).mean()
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot(df['Review_Date'],df['Rolling_Mean'],label='Average Rating')
    plt.ylabel('Rolling Mean Rating')
    plt.xlabel('Year')
    plt.title('Rating over Time')
    plt.legend()
    plt.show()

## Word Cloud

def Format_Output_Image_Name(startDate, endDate, functionName, keyword = ''):
    return functionName + '-' + Get_Display_DateRange(startDate, endDate) + ((' keyword-' + keyword) if keyword != '' else keyword)+ '.png'

def Generate_Word_Cloud(startDate, endDate, functionName, stopword, keyword = '', daysBefore = 365, daysAfter = 365):
    renovateStart_Date = DateUtils.parserDate(startDate)
    oneDayBefore = One_Day_Before(renovateStart_Date)
    oneYearBefore = Get_Past_Date_Object(oneDayBefore, daysBefore)
    renovateEnd_Date = DateUtils.parserDate(endDate)
    oneDayAfter = One_Day_After(renovateEnd_Date)
    oneYearAfter = Get_Past_Date_Object(oneDayAfter, -daysAfter)
    latestRecord = MongoUtils.getLatestDate(collection, functionName)

    # after oct 2016
    query_dateAfterReno = {'$and':
                                [{Utils.DicReviewDateKey: {'$lt': oneYearAfter}},
                                 {Utils.DicReviewDateKey: {'$gt': renovateEnd_Date}}
                                 ]
                            }
    # between oct 2016 and may 2015
    query_dateBeforeReno = {'$and':
                                [{Utils.DicReviewDateKey: {'$lt': renovateStart_Date}},
                                 {Utils.DicReviewDateKey: {'$gt': oneYearBefore}}
                                 ]
                            }
    # between apr 2015 and may 2014
    query_dateDuringReno = {'$and':
                                [{Utils.DicReviewDateKey: {'$lt': renovateEnd_Date}},
                                 {Utils.DicReviewDateKey: {'$gt': renovateStart_Date}}
                                 ]
                            }

    query_negative = {Utils.Sentiment_Col: Utils.Negative_Col.lower()}
    query_positive = {Utils.Sentiment_Col: Utils.Positive_Col.lower()}

    query_commentKeyword = {Utils.DicCoomentKey: {'$regex': keyword}}

    # queries for mongoDB find() are here
    query_datePeriod = [query_dateAfterReno, query_dateDuringReno, query_dateBeforeReno]
    query_sentiment = [query_negative, query_positive]

    # list of wordcloud filenames
    list_wordcloud = ['1.afterNeg.png',
                      '2.afterPos.png',
                      '3.duringNeg.png',
                      '4.duringPos.png',
                      '5.beforeNeg.png',
                      '6.beforePos.png']

    # generate standard wordcloud, keyword 'renovat' is not filtered
    list_wordcloud_counter = 0

    for period in query_datePeriod:
        for sentiment in query_sentiment:

            queryResult = collection.find({'$and': [period, sentiment, {Utils.DicTouristFunctionKey : functionName}]},
                                       {Utils.DicKeyPhrasesKey: 1})
            # this gives a quick indication of execution progress
            print(queryResult.count())

            wordList = ''
            for row in queryResult:  # result is rows of dict
                row = row.values()  # get dict values
                temp = list(row)[1]
                if isinstance(temp, list):
                    for s in temp:
                        wordList += s.lower() + ' '
                else:
                    row = temp.lower()  # [0] is object_ID
                    wordList += re.sub('[][\',]', '', row) + ' '

            stemlist = ''
            for eachWord in wordList.split():
                # print (type(i))
                stemlist = stemlist + (stemmer().stem(eachWord)) + ' '

            # generate wordcloud
            wordcloud = WordCloud(
                stopwords=stopword,
                max_words=30,
                width=2000,
                height=1000,
                prefer_horizontal=1.0
            ).generate(stemlist)

            # save wordcloud
            plt.figure(figsize=(20, 10))
            plt.title(functionName + '-' + list_wordcloud[list_wordcloud_counter])
            plt.imshow(wordcloud, interpolation="bilinear")
            plt.axis("off")
            # plt.show
            plt.savefig(functionName + '-' + list_wordcloud[list_wordcloud_counter])
            list_wordcloud_counter += 1
    plt.close('all')  # flush plots from memory
    print('All wordclouds have been generated.')

    #####filter by keyword 'renovat'#######
    list_wordcloud_counter = 0

    for period in query_datePeriod:
        for sentiment in query_sentiment:

            queryResult = collection.find({'$and': [period, sentiment, {Utils.DicTouristFunctionKey : functionName}, query_commentKeyword]},
                                       {Utils.DicKeyPhrasesKey: 1})

            # this gives a quick indication of execution progress
            print(queryResult.count())

            wordList = ''

            for row in queryResult:  # result is rows of dict
                row = row.values()  # get dict values
                temp = list(row)[1]
                if isinstance(temp, list):
                    for s in temp:
                        wordList += s.lower() + ' '
                else:
                    row = temp.lower()  # [0] is object_ID
                    row = list(row)[1].lower()  # [0] is object_ID
                    wordList += re.sub('[][\',]', '', row) + ' '

            stemlist = ''
            for eachWord in wordList.split():
                # print (type(i))
                stemlist = stemlist + (stemmer().stem(eachWord)) + ' '

            # generate wordcloud
            wordcloud = WordCloud(
                stopwords=stopword,
                max_words=30,
                width=2000,
                height=1000,
                prefer_horizontal=1.0
                # colormap='plasma' more options at https://matplotlib.org/examples/color/colormaps_reference.html
            ).generate(stemlist)

            # save wordcloud
            plt.figure(figsize=(20, 10))
            plt.title(functionName + '-' + keyword + list_wordcloud[list_wordcloud_counter])
            plt.imshow(wordcloud, interpolation="bilinear")
            plt.axis("off")
            # plt.show
            plt.savefig(functionName + '-' + keyword + list_wordcloud[list_wordcloud_counter])
            list_wordcloud_counter += 1
    plt.close('all')  # flush plots from memory
    print('All wordclouds have been generated.')


## Execution code

Show_Sentiment_Stacked_Bar_DateRange('2015-5-1', '2016-10-31','Swissotel Merchant Court Singapore', 'renovat')
Show_Avg_Review_Rating_DateRange('2015-5-1', '2016-10-31','Swissotel Merchant Court Singapore')
Show_Sentiment_Stacked_Bar_DateRange('2015-5-1', '2016-10-31','Swissotel Merchant Court Singapore')
Show_Avg_Review_Rating_DateRange('2015-5-1', '2016-10-31','Swissotel Merchant Court Singapore','renovat')
Generate_Word_Cloud('2015-5-1', '2016-10-31','Swissotel Merchant Court Singapore', stopword, 'renovat')

#loading the queried object into the dataframe
df.Review_Rating = df.Review_Rating.astype(int)
df.Thumbs_Up = df.Thumbs_Up.astype(int)
#changing the datatype in the dataframe

displayinfo_word('renovat')

dfwithword(df,'renovat')

plotcount('renovat')

plotcount_word('renovat')

reviewplot(df)

reviewplotsentiment(df)

reviewplotsentiment(df)

dftimeplot(df,'Swissotel Merchant Court Singapore')
#plotting the timeframe with the comment with the word renovat
dftimeplot(dfwithword(df,'renovat'),'Swissotel Merchant Court Singapore')

