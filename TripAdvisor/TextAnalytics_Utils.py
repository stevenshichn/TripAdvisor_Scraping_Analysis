import TripAdvisor.StringUtils as Utils
import urllib
import json
import logging

logging.basicConfig(filename='text_'+Utils.LOG_FILENAME, level=logging.Error)

def Get_Text_Analytics_API_Header():
    headers = {}
    headers['Ocp-Apim-Subscription-Key'] = Utils.Text_Analytics_APIKey
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'
    return headers

# return sentiment, threshold : greater than 0.6 means positive, less than 0.45 means negative, in between means neutral
def Get_Sentiment_Result(text, language = 'en'):
    sentiment = 0
    try:
        if len(text) > 4999: ## to avoid string overflow
            text = text[:4999]
        headers = Get_Text_Analytics_API_Header()
        postData = json.dumps({"documents": [{"id": "1", "language": language, "text": text}]}).encode('utf-8')
        request2 = urllib.request.Request(Utils.Sentiment_URI, postData, headers)
        response2 = urllib.request.urlopen(request2)
        response2json = json.loads(response2.read().decode('utf-8'))
        if len(response2json['documents']) > 0:
            sentiment = response2json['documents'][0]['score']  # Sample json: {'errors': [], 'documents': [{'id': '1', 'score': 0.946106320818458}]}
            return Parser_Sentiment_Score_Into_String(sentiment)
        else:
            print(str(response2json['documents']))
            return ''
    except:
        if sentiment > 0:
            return Parser_Sentiment_Score_Into_String(sentiment)
        else:
            logging.exception('Fail to sentiment with ' + text)
            print('sentiment error')
            return ''

def Parser_Sentiment_Score_Into_String(score):
    if score < 0.45:
        return 'negative'
    elif score > 0.6:
        return 'positive'
    else:
        return 'neutral'

def Get_KeyPhrases_From_Comment(text, language = 'en'):
    keyPhrasesV = []
    try:
        if len(text) > 4999: ## to avoid string overflow
            text = text[:4999]
        headers = Get_Text_Analytics_API_Header()
        postData = json.dumps({"documents": [{"id": "1", "language": language, "text": text}]}).encode('utf-8')
        request3 = urllib.request.Request(Utils.KeyPhrases_URI, postData, headers)
        response3 = urllib.request.urlopen(request3)
        response3json = json.loads(response3.read().decode('utf-8'))
        if response3json['documents'] is None:
            print('try to get key phrases')
            return Get_KeyPhrases_From_Comment(text)
        keyPhrasesV = response3json['documents'][0]['keyPhrases']  # Sample json: {'documents': [{'keyPhrases': ['Azure'], 'id': '1'}], 'errors': []}
    except IndexError as message:
        print(message.__str__())
        logging.exception('fail to extract key phrases with ' + text)
        print("error occurs when get Key Phrases from Comment : " + text)
    else:
        if len(keyPhrasesV) == 0:
            logging.exception('unknow error in ')
            print('error occurs in get Key Phases from Comment : ' + text)
    finally:
        return keyPhrasesV