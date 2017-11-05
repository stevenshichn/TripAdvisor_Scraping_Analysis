import re
from datetime import datetime

WebsiteUrl = 'https://www.tripadvisor.com.sg'
_baseUrl = WebsiteUrl + '/Hotel_Review-g294265-d306176-Reviews' # grand park city hall

Text_Analytics_APIKey = '2b7eaab22f934db4a685780fb649bc06'
Sentiment_URI = 'https://westus.api.cognitive.microsoft.com/text/analytics/v2.0/sentiment'
KeyPhrases_URI = 'https://westus.api.cognitive.microsoft.com/text/analytics/v2.0/keyPhrases'

PhantomJsPath = 'C:/Program Files/Python36/phantomjs-2.1.1-windows/bin/phantomjs'

Google_TranslatedKey = 'translated'
Google_SourceLangKey = 'source'
UrlKey = 'urls'
TotalNumKey = 'total'

DicUserNameKey = 'User_Name'
DicTitleKey = 'Title'
DicCoomentKey = 'Comment'
DicCommentLangKey = 'Language'
DicReviewDateKey = 'Review_Date'
DicReviewRatingKey = 'Review_Rating'
DicNumerOfHelpKey = 'Thumbs_Up'
DicUserContributionKey = 'Contributions'
dicCitiesVisitedKey = 'Cities_Visited'
DicHelpfulVotesKey = 'Helpful_Votes'
DicPhotosKey = 'Photos_Posted'
DicRatingGivenKey = 'Ratings_Given'
DicForumPostKey = 'Forum_Posted'
DicAgeSinceKey = 'Membership'
DicHomeTownKey = 'Home_Town'
DicAgeRangeKey = 'Age'
DicGenderKey = 'Gender'
DicExcellentNumKey = 'Excellent'
DicVeryGoodNumKey = 'Very_Good'
DicAverageNumKey = 'Average'
DicPoorNumKey = 'Poor'
DicTerribleNumKey = 'Terrible'
DicBadgeLevelKey = 'Badge_Level'
DicTagsKey = 'Tags'
DicSentimentKey = 'Sentiment'
DicKeyPhrasesKey = 'Key_Phrases'
DicTouristFunctionKey = 'TouristFunction_Name'
TouristFunction_Type_Hotel = 'Hotel'
TouristFunction_Type_Attraction = 'Attraction'
TouristFunction_Type_Restaurant = 'Restaurant'
## hotel section
Grand_Park_City_Hall = 'Grand Park City Hall'
Four_Seasons_Hotel = 'Four Seasons Hotel Singapore'
Hilton_Singapore = 'Hilton Singapore'
Singapore_Marriott_Tang_Plaza = 'Singapore Marriott Tang Plaza Hotel'
Hard_Rock_Singapore = 'Hard Rock Hotel Singapore'
Swissotel_Merchant_Court = 'Swissotel Merchant Court Singapore'
Grand_Hyatt_Singapore = 'Grand Hyatt Singapore'
## restaurant section
Tong_Le_Private_Dinning = 'Tong Le Private Dining'
## attraction section
Zoo_Singapore = 'Zoo Singapore'
## hotel section
Grand_Park_City_Hall_ID = 'd306176'
Four_Seasons_Hotel_ID = 'd301897'
Hilton_Singapore_ID = 'd306197'
Singapore_Marriott_Tang_Plaza_ID = 'd299774'
Hard_Rock_Singapore_ID = 'd1447339'
Swissotel_Merchant_Court_ID = 'd301577'
Grand_Hyatt_Singapore_ID = 'd306175'
## restaurant section
Tong_Le_ID = 'd4132272'
## attraction section
Zoo_ID = 'd324542'

## Tourist Function
TouristFunction_Type_Key = 'TouristFunction_Type'
TouristFunction_Address_Key = 'Address'
TouristFunction_Ranking_Key = 'Rank'
TouristFunction_Overall_Rating_Key = 'Overall_Rating'
TouristFunction_Email_Key = 'Email'
TouristFunction_Phone_Key = 'Phone'
TouristFunction_Websit_Key = 'Website'
TouristFunction_Postal_Code_Key = 'Postal'
TouristFunction_Country_Key = 'Country'
TouristFunction_PriceRange_Key = 'Price_Range'
TouristFunction_SubType_Key = 'Sub_Type'

Result_Type_User_Profile = 'user-profile'
Result_Type_Reviews = 'review'
Result_Type_TouristFunction = 'tourist-functions'

MonthDic = {'1' : 'Jan', '2' : 'Feb', '3' : 'Mar',
            '4' : 'Apr', '5' : 'May', '6' : 'Jun',
            '7' : 'Jul', '8' : 'Aug', '9' : 'Sep',
            '10' : 'Oct', '11' : 'Nov', '12' : 'Dec'}

LOG_FILENAME = 'log_root.log'

# database
TripAdvisor_DB= 'tripadvisor'
Reviews_Table = 'reviews'
Users_Table = 'users'
TouristFunction_Table = 'tourists_Functions'

Before_Renovation_Col = 'Before'
Undergoing_Renovation_Col = 'During'
After_Renovation_Col = 'After'
Negative_Col = 'Negative'
Neutral_Col = 'Neutral'
Positive_Col = 'Positive'
Sentiment_Col = 'Sentiment'
TimeLine_Col = 'Stage'
Average_Rating_Col = 'Average Rating'

Orange_Color = '#E8881A'
Light_Green_Color = '#25D195'
Blue_Color = '#2F3CAB'

def Get_Result_CSV_File(touristFunctionName, resultFileType):
    return resultFileType + '-' + touristFunctionName + '.csv'

def RejoinPhoneNumber(phoneText):
    try:
        if phoneText is not None and phoneText != '':
            temp = re.findall(r'\d+', phoneText)
            phone = temp[1] + temp[3] + temp[2] + temp[4]
            return str(phone)
        else:
            return ''
    except:
        return ''

def Get_Base_Url(touristFunction_Type):
    return WebsiteUrl + '/' + touristFunction_Type + '_Review-g294265-'

def Format_To_Percentage_With_OneFloatPoint(value):
    return '{:.1f}'.format(value)+'%'

def Format_To_Percentage_With_NoFloatPoint(y, position):
    s = '{:.0f}'.format(y)

def FormatFloatWithTwoDecimalPlace(value):
    st = '%.2f' % round(value,2)
    return float(st)

def Get_Current_Month_Year_String():
    return datetime.today().strftime('%m/%d/%Y')

def Parser_Month_Year_String(monthYear):
    myArray = monthYear.split(' ')
    m = myArray[0]
    y = myArray[1]
    for key, value in MonthDic.items():
        if value == m.strip():
            return key + '/15/' + y
