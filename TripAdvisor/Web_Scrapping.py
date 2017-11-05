## author : Shi Cangyuan (A0050882E)

import time
import requests
import csv
import math
import threading
import uuid
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from googletrans import Translator
from googletrans import LANGUAGES as LangurageDic
from pymongo import MongoClient
import TripAdvisor.StringUtils as Utils
import TripAdvisor.Convert_Helper as ConHelper
import TripAdvisor.TextAnalytics_Utils as TextAUtils
import TripAdvisor.MongoDB_Helper as MongoHelper
import TripAdvisor.DateUtils as DateUtils

allPageUrls = []

## execute click action on the given id control with PhantomJS
def Click_On_Control(id, driver):
    try:
        driver.find_element_by_id(id).click()
    except:
        logging.exception('Can not find control id' + id + ' to click')
        print('click on control raise exception')

## return Review block container
def Review_Container_ID(touristFunction_Type):
    baseId = 'taplc_location_reviews_list'
    suffix = '_0'
    typeIndicator = ''

    if touristFunction_Type == Utils.TouristFunction_Type_Hotel:
        typeIndicator = '_hotels'
    return baseId + typeIndicator + suffix

## return All language filter control name
def AllLanguage_Filter_Label_For(touristFunction_Type):
    baseLabel = 'taplc_location_review_filter_controls'
    suffix = '_0_filterLang_ALL'
    typeIndicator = ''
    if touristFunction_Type == Utils.TouristFunction_Type_Hotel:
        typeIndicator = '_hotels'
    return baseLabel + typeIndicator + suffix

## return Total Review ID
def Total_Review_Label_ID(touristFunction_Type):
    baseId = 'taplc_location_reviews_list'
    suffix = '_0'
    typeIndicator = ''
    if touristFunction_Type == Utils.TouristFunction_Type_Hotel:
        typeIndicator = '_hotels'
    return baseId + typeIndicator + suffix

## return Overlay Url to query user profile information
def Member_Overlay_Url_Query_Key(touristFunction_Type):
    baseQuery = '&fus=false&partner=false&LsoId=&metaReferer='
    suffix = '_Review'
    return baseQuery + touristFunction_Type +suffix

## return Two Column table control ID
def Topic_Location_Two_Column_ID(touristFunction_Type):
    baseID = 'taplc_location_detail_two_column_top'
    suffix = '_0'
    typeIndicator = ''
    if touristFunction_Type == Utils.TouristFunction_Type_Hotel:
        typeIndicator = '_hotels'
    return baseID + typeIndicator + suffix

## return locaiton detail header ID
def Taplc_Location_Detail_Header(touristFunctionType):
    baseID = 'taplc_location_detail_header'
    suffix = '_0'
    typeIndicator = ''
    if touristFunctionType == Utils.TouristFunction_Type_Hotel:
        typeIndicator = '_hotels'
    if touristFunctionType == Utils.TouristFunction_Type_Restaurant:
        typeIndicator = '_restaurants'
    if touristFunctionType == Utils.TouristFunction_Type_Attraction:
        typeIndicator = '_attractions'
    return baseID + typeIndicator + suffix

# check whether string is none or empty
# return boolean
def Is_NoneOrEmpty_String(strValue):
    return strValue is None or strValue == ''

# translate the text to destination language, default is english
# return a dictionary which use Google_TranslatedKey as key to store translated text, user Google_SourceLangKey as key to store source language
def Translate_Text(srcText, destLang = 'en'):
    try:
        if Is_NoneOrEmpty_String(srcText) == False:
            if len(srcText) > 4999: ## to avoid string overflow
                srcText = srcText[:4999]
            translator = Translator()
            tranlation = translator.translate(srcText, destLang)
            detect = translator.detect(srcText)
            lang = detect.lang
            if lang =='jazh-CN':
                lang = 'ja'
            return { Utils.Google_TranslatedKey : tranlation.text, Utils.Google_SourceLangKey : LangurageDic[lang]}
        else:
            return { Utils.Google_TranslatedKey : '', Utils.Google_SourceLangKey : ''}
    except:
        return { Utils.Google_TranslatedKey : srcText, Utils.Google_SourceLangKey : ''}

## return total review for one tourist function name
def Get_Total_Record_Number(soup, touristFunction_Type):
    container = soup.find('div', {'id': Total_Review_Label_ID(touristFunction_Type)})
    reviewStastic = container.find('p', {'class', 'pagination-details'})
    reviewNum = reviewStastic.findAll('b')
    if reviewNum is not None:
        totalReview = int(reviewNum[2].text.replace(',', ''))
        print(totalReview)
        return totalReview
    else:
        return '0'

## return header object
def Get_Current_Total_Reviews_AtHeader(soup):
    reviewContainer = soup.find('div', {'id' : 'REVIEWS'})
    headerContainer = reviewContainer.find('div', {'class' : 'prw_rup prw_common_location_content_header'})
    headerClass = headerContainer.find('div',{'class' : 'header_group block_header'})
    headerTitle = headerClass.find('span',{'class' : 'reviews_header_count block_title'}).text.replace('(','').replace(')','').replace(',','')
    return int(headerTitle)

## Generate all the page URLs for one tourist function name
## baseURL should include the tourist function id given by tripadvisor
## touristFunction_Type : Hotel, Restaurant, Attraction
def Get_All_Page_Url(baseUrl, touristFunction_Type):
    pageUrls = []
    url = baseUrl
    driver = webdriver.PhantomJS(executable_path=Utils.PhantomJsPath)
    driver.get(baseUrl)
    Click_On_Control(AllLanguage_Filter_Label_For(touristFunction_Type), driver)
    time.sleep(2)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    container = soup.find('div', {'id': Review_Container_ID(touristFunction_Type)})
    reviewStastic = container.find('p', {'class', 'pagination-details'})
    reviewNum = reviewStastic.findAll('b')
    driver.quit()
    if reviewNum is not None:
        reviewPageInterval = int(reviewNum[1].text)
        totalReview = Get_Current_Total_Reviews_AtHeader(soup)
        print(totalReview)
        totalPage = math.ceil(totalReview / reviewPageInterval)
        for i in range(totalPage):
            if i == 0:
                pageUrls.append(url)
            else:
                pageUrls.append(baseUrl + '-or' + str(i * reviewPageInterval))
        return {Utils.UrlKey : pageUrls, Utils.TotalNumKey : totalReview}
    else:
        return {Utils.UrlKey : [] , Utils.TotalNumKey : 0}

def Ensure_Click_AllLanguage_RadioButton(driver, pUrl, touristFunction_Type):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    recordNum = Get_Total_Record_Number(soup, touristFunction_Type)
    if int(recordNum) < Get_Current_Total_Reviews_AtHeader(soup):
        Click_On_Control(AllLanguage_Filter_Label_For(touristFunction_Type), driver)
        time.sleep(2)  # give the time to allow execute the javascript
        driver.get(pUrl)
        time.sleep(1)
        return Ensure_Click_AllLanguage_RadioButton(driver, pUrl, touristFunction_Type)
    else:
        return driver

## Token gender from Age additional information
def Get_Gender_From_Text(text):
    if 'female' in text or 'Female' in text:
        return 'female'
    elif 'male' in text or 'Male' in text:
        return 'male'
    else:
        return ''

## Token age from Age additional information
def Get_Age_From_Text(text):
    keyword = 'year old'
    if keyword in text:
        index = text.find(keyword)
        return text[:index].strip()
    else:
        return ''

## Scrapping detail process
def Scraping_Procedure(processUrl, reviewDic, userDic, touristFunctionName, touristFunction_Type, lock, dbClient):
    for pUrl in processUrl:
        try:
            print(pUrl)
            driver = webdriver.PhantomJS(executable_path=Utils.PhantomJsPath)
            time.sleep(2)
            driver.get(pUrl)
            time.sleep(1)
            link = Ensure_Click_AllLanguage_RadioButton(driver, pUrl, touristFunction_Type).find_element_by_xpath("//*[@class='taLnk ulBlueLinks']")
            try:
                if link is not None and link.text == 'More':
                    link.click()
                    time.sleep(2)
            except:
                logging.exception('fail to click more link in ' + pUrl)
                print('link can not click')
            pHtml = driver.page_source
            pSoup = BeautifulSoup(pHtml, 'html.parser')
            driver.quit()
            pContain = pSoup.find('div',{'id' : Topic_Location_Two_Column_ID(touristFunction_Type)}).find('div',{'id' : Review_Container_ID(touristFunction_Type)}).findAll('div', {
                'class': 'review-container'})
            for con in pContain:
                userName = ''
                reviewDate = ''
                quoteTitle = ''
                langUsed = ''
                memberInfoUrl = ''
                badgeLevel = ''
                ageSinceValue = ''
                hometownValue = ''
                ageAdditionalInfo = ''
                age = ''
                gender = ''
                commentText = ''
                rating = 0
                tagBlockValue = []
                contribution = 0
                cityVisited = 0
                helpfulVotes = 0
                photos = 0
                ratingsGiven = 0
                forumPosts = 0
                excellentNum = 0
                veryGoodNum = 0
                averageNum = 0
                poorNum = 0
                terribleNum = 0
                numHelp = 0
                userInfoDiv = con.find('div', {'class': 'ui_column is-2'}).find('div',{'class' : 'prw_rup prw_reviews_member_info_hsx'})
                commentInfoDiv = con.find('div', {'class': 'ui_column is-9'})
                memberInfoDiv = userInfoDiv.find('div', {'class': 'member_info'})
                memberOverlay = memberInfoDiv.find('div',{'class' : 'memberOverlayLink'})
                if memberOverlay is None:
                    print(pUrl)
                    print(memberInfoDiv)
                else:
                    userId = memberOverlay.get('id')
                    splitIndex = userId.index('-')
                    memberIdStr = userId[:splitIndex]
                    memberId = memberIdStr[4:]
                    srcStr = userId[splitIndex + 1:]
                    src = srcStr[4:]
                    memberInfoUrlEncode = 'Uid=' + str(memberId) + '&c=&src=' + str(src)
                    memberInfoUrl = 'https://www.tripadvisor.com.sg/MemberOverlay?Mode=owa&' + memberInfoUrlEncode + Member_Overlay_Url_Query_Key(touristFunction_Type)
                    print(memberInfoUrl)
                # get rating
                ratingInfo = commentInfoDiv.find('div', {'class': 'rating reviewItemInline'})
                ratingIcon = ratingInfo.find('span').get('class')
                if len(ratingIcon) == 2:
                    ratingText = ratingIcon[1]
                    ratingText = ratingText.replace('bubble_', '')[:1]
                    rating = int(ratingText)
                # get rating date
                reviewDate = ratingInfo.find('span', {'class': 'ratingDate relativeDate'}).get('title')
                quoteDiv = commentInfoDiv.find('div', {'class': 'quote'})
                quoteUrl = quoteDiv.find('a').get('href')
                quoteSpan = quoteDiv.find('a').find('span', {'class': 'noQuotes'})
                quoteTitle = Translate_Text(quoteSpan.text)[Utils.Google_TranslatedKey]
                # if is_utf8(quoteTitle) == True:
                #     quoteTitle = quoteTitle.encode('utf-8')
                # get review comment
                commentTextContainer = commentInfoDiv.find('div',{'class' : 'prw_rup prw_reviews_text_summary_hsx'})
                if commentTextContainer is not None:
                    commentTextField = commentTextContainer.find('p',{'class' : 'partial_entry'})
                    commentText = commentTextField.text
                    moreLink = commentTextField.find('span', {'class' : 'taLnk ulBlueLinks'})
                    if moreLink is not None:
                        if moreLink.text == 'More':
                            print(commentText)
                translationC = Translate_Text(commentText.replace('<br>', '\r\n'))
                commentText = translationC[Utils.Google_TranslatedKey]
                langUsed = translationC[Utils.Google_SourceLangKey]
                sentiment = TextAUtils.Get_Sentiment_Result(commentText)
                keyPhrases = TextAUtils.Get_KeyPhrases_From_Comment(commentText)
                # get number of thumbsup
                helpfulContentDiv = commentInfoDiv.find('div', {'class': 'helpful redesigned hsx_helpful'})
                numHelpSpan = helpfulContentDiv.find('span', {'class': 'numHelp emphasizeWithColor'})
                numHelpText = numHelpSpan.text.strip()
                if numHelpText == '':
                    numHelp = 0
                else:
                    numHelp = int(numHelpText)
                if memberInfoUrl != '':
                    memberInfoHtml = requests.get(memberInfoUrl)
                    mSoup = BeautifulSoup(memberInfoHtml.content, 'html.parser')
                    mOverlayDiv = mSoup.find('div', {'class': 'memberOverlayRedesign g10n'})
                    userSection = mOverlayDiv.find('a')
                    userLink = userSection.get('href')
                    userName = userSection.find('h3', {'class': 'username reviewsEnhancements'}).text
                if Is_NoneOrEmpty_String(userName):
                    userName = str(uuid.uuid1())
                memberReviewBadgeDiv = mOverlayDiv.find('div', {'class': 'memberreviewbadge'})
                if memberReviewBadgeDiv is not None:
                    badgeInfoDiv = memberReviewBadgeDiv.find('div', {'class': 'badgeinfo'})
                    if badgeInfoDiv is not None:
                        badgeLevel = badgeInfoDiv.text.replace('Level','').replace('Contributor','').strip()
                reviewCountContainer = mOverlayDiv.find('ul', {'class': 'countsReviewEnhancements'})
                # temporary remove this part, will get them from the member profile page
                if reviewCountContainer is not None:
                    reviewEnhancementList = reviewCountContainer.findAll('li')
                    if reviewEnhancementList is not None:
                        for list in reviewEnhancementList:
                            spanValue = list.find('span', {'class': 'badgeTextReviewEnhancements'}).text
                            if list.find('span', {'class', 'ui_icon globe-world iconReviewEnhancements'}) is not None:
                                cityVisited = int(spanValue.replace('Cities visited','').replace('City visited','').strip())
                reviewContributionWrap = mOverlayDiv.find('div', {'class': 'wrap container histogramReviewEnhancements'})

                if reviewContributionWrap is not None:
                    reviewContributionDiv = reviewContributionWrap.find('ul')
                    if reviewContributionDiv is not None:
                        for chartRowDiv in reviewContributionDiv.findAll('div', {'class': 'chartRowReviewEnhancements'}):
                            reviewCategory = chartRowDiv.find('span', {'class',
                                                                       'rowLabelReviewEnhancements rowCellReviewEnhancements'}).text.strip()
                            number = chartRowDiv.find('span', {'class': 'rowCountReviewEnhancements rowCellReviewEnhancements'}).text
                            if reviewCategory == 'Excellent':
                                excellentNum = int(number)
                            if reviewCategory == 'Very good':
                                veryGoodNum = int(number)
                            if reviewCategory == 'Average':
                                averageNum = int(number)
                            if reviewCategory == 'Poor':
                                poorNum = int(number)
                            if reviewCategory == 'Terrible':
                                terribleNum = int(number)
                userDetailHtml = requests.get(Utils.WebsiteUrl + userLink)
                userDetailSoup = BeautifulSoup(userDetailHtml.content, 'html.parser')
                userDetailDiv = userDetailSoup.find('div',{'class' : 'modules-membercenter-member-profile '})
                userMembershipDiv = userDetailDiv.find('div',{'class' : 'profInfo'})

                if userMembershipDiv is not None:
                    ageSinceDiv = userMembershipDiv.find('div',{'class','ageSince'})
                    if ageSinceDiv is not None:
                        ageSinceValue = ageSinceDiv.find('p',{'class':'since'}).text.replace('Since','').strip()
                        if ageSinceValue == 'this month' or ageSinceValue == 'this week' or ageSinceValue == 'today':
                            ageSinceValue = Utils.Get_Current_Month_Year_String()
                        else:
                            ageSinceValue = Utils.Parser_Month_Year_String(ageSinceValue)
                        allAgeInfo = ageSinceDiv.findAll('p')
                        if len(allAgeInfo) >1:
                            ageAdditionalInfo = allAgeInfo[1].text
                            age = Get_Age_From_Text(ageAdditionalInfo)
                            gender = Get_Gender_From_Text(ageAdditionalInfo)
                    hometownDiv = userMembershipDiv.find('div',{'class':'hometown'})
                    if hometownDiv is not None:
                        homeTownP = hometownDiv.find('p')
                        if homeTownP is not None:
                            hometownValue = homeTownP.text
                memberTagDiv = userDetailSoup.find('div',{'class' : 'modules-membercenter-member-tag '})
                if memberTagDiv is not None:
                    tagBlock = memberTagDiv.find('div',{'class' : 'tagBlock'})
                    if tagBlock is not None:
                        for tagBubble in tagBlock.findAll('div', {'class' : 'tagBubble unclickable'}):
                            tagBlockValue.append(tagBubble.text)
                    else:
                        tagBlockValue.append('')
                else:
                    tagBlockValue.append('')
                # profile summary
                profileSummaryDiv = userDetailSoup.find('div',{'class' : 'modules-membercenter-content-summary '})
                if profileSummaryDiv is not None:
                    memberPointDiv = profileSummaryDiv.find('div',{'class' : 'member-points'})
                    if memberPointDiv is not None:
                        for pointLi in memberPointDiv.findAll('li',{'class' : 'content-info'}):
                            pointLiReview = pointLi.find('a',{'name' : 'reviews'})
                            if pointLiReview is not None:
                                contribution = int(pointLiReview.text.replace('Reviews','').replace('Review','').strip())
                            pointLiRatings = pointLi.find('a',{'name' : 'ratings'})
                            if pointLiRatings is not None:
                                ratingsGiven = int(pointLiRatings.text.replace('Ratings','').replace('Rating','').strip())
                            pointLiForumPosts = pointLi.find('a', {'name' : 'forums'})
                            if pointLiForumPosts is not None:
                                forumPosts = int(pointLiForumPosts.text.replace('Forum Posts','').replace('Forum Post','').strip())
                            pointLiPhotos = pointLi.find('a',{'name' : 'photos'})
                            if pointLiPhotos is not None:
                                photos = int(pointLiPhotos.text.replace('Photos','').replace('Photo','').strip())
                            pointLiHelpfulVotes = pointLi.find('a',{'name' : 'lists'})
                            if pointLiHelpfulVotes is not None:
                                helpfulVotes = int(pointLiHelpfulVotes.text.replace('Helpful votes','').replace('Helpful vote','').strip())

                reviewDocument = {Utils.DicUserNameKey : userName, Utils.DicTouristFunctionKey : touristFunctionName, Utils.DicReviewDateKey : DateUtils.parserDateString(reviewDate), Utils.DicTitleKey : quoteTitle, Utils.DicCoomentKey : commentText, Utils.DicCommentLangKey : langUsed,
                                  Utils.DicSentimentKey : sentiment, Utils.DicKeyPhrasesKey : keyPhrases, Utils.DicReviewRatingKey : rating, Utils.DicNumerOfHelpKey : numHelp}
                userDocument = {Utils.DicUserNameKey: userName, Utils.DicBadgeLevelKey: badgeLevel, Utils.DicTagsKey: tagBlockValue,
                                Utils.DicHomeTownKey: hometownValue, Utils.DicAgeSinceKey: ageSinceValue,
                                Utils.DicAgeRangeKey : age, Utils.DicGenderKey : gender, Utils.DicUserContributionKey: contribution,
                                Utils.dicCitiesVisitedKey: cityVisited, Utils.DicHelpfulVotesKey: helpfulVotes, Utils.DicPhotosKey: photos,
                                Utils.DicForumPostKey: forumPosts, Utils.DicRatingGivenKey: ratingsGiven,
                                Utils.DicExcellentNumKey: excellentNum, Utils.DicVeryGoodNumKey: veryGoodNum,
                                Utils.DicAverageNumKey: averageNum, Utils.DicPoorNumKey: poorNum, Utils.DicTerribleNumKey: terribleNum}
                with lock:
                    try:
                        MongoHelper.Insert_Data_IntoMongoDB(Utils.TripAdvisor_DB, Utils.Reviews_Table, dbClient, reviewDocument)
                        MongoHelper.Insert_Data_IntoMongoDB(Utils.TripAdvisor_DB, Utils.Users_Table, dbClient, userDocument, Utils.DicUserNameKey, userName)
                    except Exception as e:
                        logging.exception('error in insert into database : ' + e.__str__())
                reviewDic.append(reviewDocument)
                userDic.append(userDocument)
        except Exception as e:
            logging.exception('Error' + e.__str__() +' in : '  + pUrl)
            pass
    return reviewDic, userDic

## Core function
def Crawl_TouristFunction(baseUrl, touristFunctionName, touristFunction_Type, dbClient):
    reviewCollection = ''
    userCollection = ''
    lock = threading.Lock()
    userWholeList = []
    reviewWholeList = []
    userRes1 = []
    reviewRes1 = []
    userRes2 = []
    reviewRes2 = []
    try:

        dic = Get_All_Page_Url(baseUrl, touristFunction_Type)
        allPageUrls = dic[Utils.UrlKey]
        totalRecord = dic[Utils.TotalNumKey]
        halfNum = round(len(allPageUrls)/2)
        t1 = threading.Thread(target=Scraping_Procedure, args=(allPageUrls[:halfNum], reviewRes1, userRes1, touristFunctionName, touristFunction_Type, lock, dbClient))
        t2 = threading.Thread(target=Scraping_Procedure, args=(allPageUrls[halfNum:], reviewRes2, userRes2, touristFunctionName, touristFunction_Type, lock, dbClient))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        print(touristFunctionName + ' finish')

        userWholeList.extend(userRes1)
        userWholeList.extend(userRes2)
        reviewWholeList.extend(reviewRes1)
        reviewWholeList.extend(reviewRes2)
    except Exception as e:
        logging.exception('Exception : ' + e.__str__())
        pass
    userProfileCSVFile = Utils.Get_Result_CSV_File(touristFunctionName, Utils.Result_Type_User_Profile)
    reviewCSVFile = Utils.Get_Result_CSV_File(touristFunctionName, Utils.Result_Type_Reviews)
    with open(userProfileCSVFile,'w', newline='', encoding='utf-8') as profileCSV:
        try:
            profileWriter = csv.writer(profileCSV)
            profileWriter.writerow([Utils.DicUserNameKey, Utils.DicBadgeLevelKey, Utils.DicTagsKey, Utils.DicHomeTownKey, Utils.DicAgeSinceKey, Utils.DicAgeRangeKey, Utils.DicGenderKey, Utils.DicUserContributionKey,
                                    Utils.dicCitiesVisitedKey, Utils.DicHelpfulVotesKey, Utils.DicPhotosKey, Utils.DicForumPostKey, Utils.DicRatingGivenKey,
                                    Utils.DicExcellentNumKey, Utils.DicVeryGoodNumKey, Utils.DicAverageNumKey, Utils.DicPoorNumKey, Utils.DicTerribleNumKey])
            num = len(userWholeList)
            for i in range(num):
                user = userWholeList[i][Utils.DicUserNameKey]
                badge = userWholeList[i][Utils.DicBadgeLevelKey]
                hometown = userWholeList[i][Utils.DicHomeTownKey]
                membership = userWholeList[i][Utils.DicAgeSinceKey]
                ageValue = userWholeList[i][Utils.DicAgeRangeKey]
                genderValue = userWholeList[i][Utils.DicGenderKey]
                userContribution = userWholeList[i][Utils.DicUserContributionKey]
                cityVisit = userWholeList[i][Utils.dicCitiesVisitedKey]
                helpfulV = userWholeList[i][Utils.DicHelpfulVotesKey]
                postPhotos = userWholeList[i][Utils.DicPhotosKey]
                forumPosted = userWholeList[i][Utils.DicForumPostKey]
                ratingGivenN = userWholeList[i][Utils.DicRatingGivenKey]
                excellent = userWholeList[i][Utils.DicExcellentNumKey]
                veryGood = userWholeList[i][Utils.DicVeryGoodNumKey]
                average = userWholeList[i][Utils.DicAverageNumKey]
                poor = userWholeList[i][Utils.DicPoorNumKey]
                terrible = userWholeList[i][Utils.DicTerribleNumKey]
                tags = userWholeList[i][Utils.DicTagsKey]
                profileWriter.writerow([user, badge, tags, hometown, membership, ageValue, genderValue, userContribution,
                                        cityVisit, helpfulV, postPhotos, forumPosted, ratingGivenN,
                                        excellent, veryGood, average, poor, terrible])
            profileCSV.close()
        except:
            logging.exception('Fail to insert data to ' + userProfileCSVFile)
            pass

    with open(reviewCSVFile, 'w', newline='', encoding='utf-8') as csvfile:
        try:
            spamwriter = csv.writer(csvfile)
            spamwriter.writerow([Utils.DicUserNameKey, Utils.DicTouristFunctionKey, Utils.DicReviewDateKey, Utils.DicTitleKey, Utils.DicCoomentKey, Utils.DicCommentLangKey, Utils.DicSentimentKey, Utils.DicKeyPhrasesKey, Utils.DicReviewRatingKey, Utils.DicNumerOfHelpKey])
            num = len(reviewWholeList)
            for i in range(num):
                user = reviewWholeList[i][Utils.DicUserNameKey]
                hotel = reviewWholeList[i][Utils.DicTouristFunctionKey]
                date = reviewWholeList[i][Utils.DicReviewDateKey]
                title = reviewWholeList[i][Utils.DicTitleKey]
                text = reviewWholeList[i][Utils.DicCoomentKey]
                sourceLang = reviewWholeList[i][Utils.DicCommentLangKey]
                sentimentValue = reviewWholeList[i][Utils.DicSentimentKey]
                keyPhrasesValue = reviewWholeList[i][Utils.DicKeyPhrasesKey]
                rate = reviewWholeList[i][Utils.DicReviewRatingKey]
                numberOfHelp = reviewWholeList[i][Utils.DicNumerOfHelpKey]
                spamwriter.writerow([user, hotel, date, title, text, sourceLang, sentimentValue, keyPhrasesValue, rate, numberOfHelp])
            csvfile.close()
        except:
            logging.exception('Fail to insert record to ' + reviewCSVFile)
            pass
    print('finished')

def Get_Tourist_Function_Url(touristFunctionType, touristFunctionID):
    return Utils.Get_Base_Url(touristFunctionType) + touristFunctionID + '-Reviews'

def Run_Tourist_Function_Scraping_Save_CSV(dicToursitFunction, touristFunctionType, dbClient):
    for key, value in dicToursitFunction.items():
        try:
            _baseUrl = Get_Tourist_Function_Url(touristFunctionType, key)
            Crawl_TouristFunction(_baseUrl, value, touristFunctionType, dbClient)
        except Exception as e:
            logging.exception(e.__str__() + 'when scraping ' + value + ' web page')
            pass

def Store_Into_MongoDB(dicCrawl, client):
    for key, value in dicCrawl.items():
        MongoHelper.Insert_CSV_Users_Into_MongoDB(Utils.Get_Result_CSV_File(value, Utils.Result_Type_User_Profile), client)
        MongoHelper.Insert_CSV_Reviews_Into_MongoDB(Utils.Get_Result_CSV_File(value, Utils.Result_Type_Reviews), client)

def Scrap_TouristFunction_Information(touristFunctionDic, touristFunctionType, client):
    csvFileName = Utils.Get_Result_CSV_File(touristFunctionType, Utils.Result_Type_TouristFunction)
    dict = {}
    with open(csvFileName, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([Utils.TouristFunction_Name_Key, Utils.TouristFunction_Type_Key, Utils.TouristFunction_Overall_Rating_Key,
                         Utils.TouristFunction_Ranking_Key, Utils.TouristFunction_PriceRange_Key, Utils.TouristFunction_SubType_Key, Utils.TouristFunction_Address_Key, Utils.TouristFunction_Country_Key,
                         Utils.TouristFunction_Postal_Code_Key, Utils.TouristFunction_Phone_Key, Utils.TouristFunction_Websit_Key,
                         Utils.TouristFunction_Email_Key])
        f.close()
    for key, value in touristFunctionDic.items():
        try:
            websiteUrl = Get_Tourist_Function_Url(touristFunctionType, key)
            overlayUrl = Utils.WebsiteUrl + '/EmailHotel?detail=' + key.lstrip('d')  # for hotel email

            html = requests.get(websiteUrl)
            soup = BeautifulSoup(html.content, 'html.parser')

            html2 = requests.get(overlayUrl)
            soup2 = BeautifulSoup(html2.content, 'html.parser')

            bizInfo = soup.find('div', {'id': Taplc_Location_Detail_Header(touristFunctionType)})

            bizName = bizInfo.find('h1').text.strip()
            bizRating = bizInfo.find('span', {'class': 'ui_bubble_rating'})['alt'].split()[0]
            bizRankB = bizInfo.find('span', {'class': 'header_popularity'}).find('b')
            bizRank = ''
            bizSubType = []
            bizPriceRange = ''
            if bizRankB is not None:
                bizRankBSpan = bizRankB.find('span')
                if bizRankBSpan is not None:
                    bizRank = bizRankBSpan.text.lstrip('#')
                else:
                    bizRank = bizRankB.text.lstrip('#')
            bizStreetAddress = bizInfo.find('span', {'class': 'street-address'}).text
            bizPostalCode = bizInfo.find('span', {'class': 'locality'}).text.rstrip(', ')
            bizCountry = bizInfo.find('span',{'class' : 'country-name'}).text.strip()
            bizPriceRangeClass = bizInfo.find('span',{'class' :'header_tags'})
            if bizPriceRangeClass is not None:
                bizPriceRange = bizPriceRangeClass.text.strip()
            bizSubTypeClass = bizInfo.find('span',{'class' : 'header_links'})
            if bizSubTypeClass is not None:
                bizSubTypeLinkText = bizSubTypeClass.findAll('a')
                if bizSubTypeLinkText is not None:
                    for linkT in bizSubTypeLinkText:
                        bizSubType.append(linkT.text.strip())
            else:
                bizSubTypeClass = bizInfo.findAll('span',{'class' : 'header_detail'})
                if bizSubTypeClass is not None:
                    for span in bizSubTypeClass:
                        detailDiv = span.findAll('div',{'class' : 'detail'})
                        if detailDiv is not None:
                            for div in detailDiv:
                                details = div.findAll('a')
                                if details is not None:
                                    for detail in details:
                                        bizSubType.append(detail.text)
            bizPhone = ''
            bizEmail = ''
            # some tourist function does not list phone number
            try:
                bizPhoneObject = bizInfo.find('div', {'class': 'blEntry phone'})
                if bizPhoneObject is not None:
                    bizPhoneSpan = bizPhoneObject.findAll('span')
                    if bizPhoneSpan is not None:
                        length = len(bizPhoneSpan)
                        bizPhoneScript = bizPhoneSpan[length-1].find('script')
                        if bizPhoneScript is not None:
                            bizPhone = bizPhoneScript.text
                            bizPhone = Utils.RejoinPhoneNumber(bizPhone)# number sequence is scrambled in souce code
            except Exception as e:
                logging.exception('error in scrapping phone information : ' + e.__str__())

            # some tourist function does not list email
            try:
                emailObject = soup2.find('input', {'id': 'receiver'})
                if emailObject is not None:
                    bizEmail = emailObject['value']
            except Exception as e:
                logging.exception('error in scrapping email information : ' + e.__str__())
            bizWebsite = Query_Tourist_Function_Website_URL(value)
            with open(csvFileName, 'a', newline='', encoding='utf-8') as f:
                spamwriter = csv.writer(f)
                spamwriter.writerow(
                    [bizName, touristFunctionType, bizRating, bizRank, bizPriceRange, bizSubType, bizStreetAddress, bizCountry, bizPostalCode,
                     bizPhone, bizWebsite, bizEmail])
                f.close()
            dict = {Utils.TouristFunction_Name_Key : bizName, Utils.TouristFunction_Type_Key:touristFunctionType, Utils.TouristFunction_Overall_Rating_Key : bizRating,
            Utils.TouristFunction_Ranking_Key : bizRank, Utils.TouristFunction_PriceRange_Key : bizPriceRange, Utils.TouristFunction_SubType_Key : bizSubType,
            Utils.TouristFunction_Address_Key : bizStreetAddress, Utils.TouristFunction_Country_Key:bizCountry,
            Utils.TouristFunction_Postal_Code_Key : bizPostalCode, Utils.TouristFunction_Phone_Key : bizPhone, Utils.TouristFunction_Websit_Key: bizWebsite,
            Utils.TouristFunction_Email_Key : bizEmail}
            MongoHelper.Insert_Data_IntoMongoDB(Utils.TripAdvisor_DB, Utils.TouristFunction_Table, client, dict, Utils.DicTouristFunctionKey, bizName)
        except Exception as e:
            logging.exception('error in scrapping tourist function : ' + e.__str__())

def Query_Tourist_Function_Website_URL(name):
    try:
        googleSearchURL = 'https://google.com/search?q=' + name.replace(' ', '')
        googleResultHtml = requests.get(googleSearchURL)
        time.sleep(3)
        googleSoup = BeautifulSoup(googleResultHtml.content, 'html.parser')
        urlDiv = googleSoup.find('div',{'class' : 'kv'})
        if urlDiv is not None:
            cite = urlDiv.find('cite')
            if cite is not None:
                if '...' in cite.text:
                    hrefClass = urlDiv.find('a',{'class':'_Zkb'})
                    if hrefClass is not None:
                        hrefLink = hrefClass['href']
                        decodeLink = hrefLink.split(':')
                        dotIndex = cite.text.index('...')
                        subStringV = cite.text[:dotIndex]
                        for s in decodeLink:
                            if subStringV in s:
                                percentageSymbolIndex = s.index('%')
                                return s[:percentageSymbolIndex].replace('//','')
                    return cite.text
                return cite.text
        else:
            return ''
    except:
        return ''

if __name__ == '__main__':

    logging.basicConfig(filename=Utils.LOG_FILENAME, level=logging.Error)
    client = MongoClient('localhost', 27017)
    MongoHelper.Drop_DataBase(Utils.TripAdvisor_DB, client)
    DicRestaurantCrawl = {Utils.Tong_Le_ID : Utils.Tong_Le_Private_Dinning}
    DicAttractionCrawl = {Utils.Zoo_ID : Utils.Zoo_Singapore}

    DicHotelCrawl = {
        Utils.Grand_Hyatt_Singapore_ID : Utils.Grand_Hyatt_Singapore,
        Utils.Hilton_Singapore_ID : Utils.Hilton_Singapore,
        Utils.Singapore_Marriott_Tang_Plaza_ID : Utils.Singapore_Marriott_Tang_Plaza,
        Utils.Hard_Rock_Singapore_ID : Utils.Hard_Rock_Singapore,
        Utils.Swissotel_Merchant_Court_ID : Utils.Swissotel_Merchant_Court,
        Utils.Grand_Park_City_Hall_ID: Utils.Grand_Park_City_Hall,
        Utils.Four_Seasons_Hotel_ID: Utils.Four_Seasons_Hotel,
                           }
    Scrap_TouristFunction_Information(DicHotelCrawl, Utils.TouristFunction_Type_Hotel, client)
    Scrap_TouristFunction_Information(DicRestaurantCrawl, Utils.TouristFunction_Type_Restaurant, client)
    Scrap_TouristFunction_Information(DicAttractionCrawl, Utils.TouristFunction_Type_Attraction, client)
    Run_Tourist_Function_Scraping_Save_CSV(DicRestaurantCrawl, Utils.TouristFunction_Type_Restaurant, client)
    Run_Tourist_Function_Scraping_Save_CSV(DicAttractionCrawl, Utils.TouristFunction_Type_Attraction, client)
    Run_Tourist_Function_Scraping_Save_CSV(DicHotelCrawl, Utils.TouristFunction_Type_Hotel, client)


    # Store_Into_MongoDB(DicRestaurantCrawl, client)
    # Store_Into_MongoDB(DicAttractionCrawl, client)
    # Store_Into_MongoDB(DicHotelCrawl, client)
    client.close()
