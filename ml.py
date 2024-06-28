import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from nltk.corpus import stopwords
import nltk 
import numpy as np
import re
import random

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


nltk.download('punkt')
nltk.download("stopwords")
nltk.download('wordnet')
nltk.download('omw-1.4')

body= pd.read_csv("DB/news.csv")

Summary=body["Summary"]

def clean_lowercase(review_text):
    return str(review_text).lower()
body['CleanReview']=Summary.apply(clean_lowercase)

def clean_non_alphanumeric(review_text):
    return re.sub('[^a-zA-Z]',' ',review_text)   
body['CleanReview']=body['CleanReview'].apply(clean_non_alphanumeric)

from nltk.tokenize import word_tokenize   
def clean_tokenization(review_text):    
    return word_tokenize(review_text)      
body['CleanReview']=body['CleanReview'].apply(clean_tokenization)

from nltk.stem import PorterStemmer  
stemmer = PorterStemmer()   
def clean_stem(token):
    return [stemmer.stem(i) for i in token]   
body['CleanReview']=body['CleanReview'].apply(clean_stem)

from nltk.stem import WordNetLemmatizer   
lemma=WordNetLemmatizer()
def clean_lemmatization(token):
    return [lemma.lemmatize(word=w,pos='v') for w in token]    
body['CleanReview']=body['CleanReview'].apply(clean_lemmatization)

def Clean_length(token):
    return [i for i in token if len(i)>2]    
body['CleanReview']=body['CleanReview'].apply(Clean_length)

def convert_to_string(listReview):
    return ' '.join(listReview)
body['CleanReview']=body['CleanReview'].apply(convert_to_string)    

my_stopwords= stopwords.words("english")
vectorizer = CountVectorizer(stop_words=my_stopwords)
bag_of_words = vectorizer.fit_transform(body['CleanReview'])
news_vector=bag_of_words.todense()

from sklearn.metrics.pairwise import cosine_similarity
sw=list(body.groupby("Category"))
def recommender(x):
    L=[]
    M=[]
    n=x.shape[0]
    nn=np.shape(news_vector)[0]
    for i in range (0,n):
        for j in range(0,np.shape(news_vector)[0]):
            L.append(float(cosine_similarity(news_vector[j,:], news_vector[int(x.iloc[i][0]),:])[0][0])*x.iloc[i][1])
    if n<=3:
      for k in range(0,3*n+1):
        a=L.index(max(L))
        M.append(int(a%nn))
        for s in range(0,n):
            L[(a%nn)+(s*nn)]=0
      for i in random.sample(list(range(0,len(sw))),10-(3*n+1)):
        X=np.random.randint(len(sw[i][1]),size=1)
        M.append((sw[i][1].iloc[int(X)][0])-1)
        
    else:
      for k in range(0,10):      
          a=L.index(max(L))
          M.append(int(a%nn))
          for s in range(0,n):
              L[(a%nn)+(s*nn)]=0
    return M

def get_news(df):
    return body.iloc[recommender(df)]