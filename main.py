from flask import Flask, redirect, render_template, request, url_for
from csv import DictWriter
import pandas as pd
import numpy as np
import random
from datetime import datetime
import hashlib
from ml import *

from logging.config import dictConfig


initial_time = None
article_ID = None
final_time = None

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})



app = Flask(__name__, static_url_path='', static_folder='static')

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

authenticated = False
mobileGlobal = None

@app.route('/index', methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    
    if request.method == "GET":
        app.logger.info("Displaying index")
        return render_template("/index.html")
    
    else:
    
        if request.form['action'] == 'signup':
            return redirect(url_for("signup"))
    
        elif request.form['action'] == 'signin':

            app.logger.info("Attempting to log in")
            mobile = request.form['mobile']
            password_hash = hashlib.md5(request.form['password'].encode()).hexdigest()
            userDF = pd.read_csv("DB/user.csv")
            app.logger.info("DB Fetched")

            mobileList = list(map(int, userDF['Mobile'].to_list()))

            if int(mobile) in mobileList:
                # app.logger.info("Found mobile")
                # app.logger.info(userDF['Mobile'])
                # app.logger.info(mobile)
                # app.logger.info(type(mobile))
                if userDF.loc[userDF['Mobile']==np.int64(mobile)].PasswordHash.values[0] == password_hash:
                    app.logger.info("Redirecting to news")
                    global authenticated
                    global mobileGlobal
                    mobileGlobal = mobile
                    authenticated = True
                    return redirect(url_for("news", mobile=mobile))
                else:
                    return "Wrong password"
            else:
                return "User data not found"



def getNews(mobile):
    df = pd.read_csv("DB/UserPreferences/"+str(mobile)+".csv")
    app.logger.info(df)
    return body.iloc[recommender(df)]


@app.route("/winClose", methods=["GET", "POST"])
def winClose():
    app.logger.info(mobileGlobal)
    global initial_time
    global article_ID
    global final_time
    global authenticated
    if initial_time is not None:
        final_time = datetime.now()
        time_spent = (final_time - initial_time).total_seconds()
        field_names = ["Article ID", "Time Spent"]
        data_dict = {"Article ID": article_ID, "Time Spent": time_spent}
            
        with open("DB/UserPreferences/"+str(mobileGlobal)+".csv", 'a', newline='', encoding='utf-8') as f:
            app.logger.info("Writing to "+str(mobileGlobal))
            dictwriter_object = DictWriter(f, fieldnames=field_names)
            dictwriter_object.writerow(data_dict)
            f.close()
    authenticated = False
    mobileGlobal = None
    return ('', 204)


@app.route("/click", methods=["GET", "POST"])
def click():
    request_data_article_ID, mobile = list(map(int, request.data.decode("utf-8").split(",")))
    global initial_time
    global article_ID
    global final_time
    app.logger.info("In Click()")
    if initial_time is None:
        app.logger.info("Initial time is None")
        initial_time = datetime.now()
        article_ID = request_data_article_ID
    else:
        app.logger.info("Initial time is not None")
        final_time = datetime.now()
        time_spent = (final_time - initial_time).total_seconds()
        field_names = ["Article ID", "Time Spent"]
        data_dict = {"Article ID": article_ID, "Time Spent": time_spent}
            
        with open("DB/UserPreferences/"+str(mobile)+".csv", 'a', newline='', encoding='utf-8') as f:
            app.logger.info("Writing to "+str(mobile))
            dictwriter_object = DictWriter(f, fieldnames=field_names)
            dictwriter_object.writerow(data_dict)
            f.close()

        article_ID = request_data_article_ID
        initial_time = datetime.now()
        final_time = None

    return ('', 204)


@app.route("/news/<mobile>", methods=["GET", "POST"])
def news(mobile):
    global authenticated
    if authenticated == False or authenticated == None:
        return "You need to sign in first"
        
    if request.method == "GET":
        app.logger.info("Getting")
        app.logger.info("Redirected to news function")
        if pd.read_csv("DB/UserPreferences/"+mobile+".csv").empty:
            app.logger.info("Attempting to render news template for user without click data")
            
            body=pd.read_csv("DB/news.csv")
            sw=list(body.groupby("Category"))
            MM=[]
            for i in random.sample(list(range(0,len(sw))),10):
                X=np.random.randint(len(sw[i][1]),size=1)
                MM.append((sw[i][1].iloc[int(X)][0])-1)
            result=body.iloc[MM]
            #result = pd.read_csv("DB/news.csv").sample(n=10)
            return render_template("news.html", newsItems=result.values.tolist(), mobile=mobile)

        app.logger.info("Attempting to render news template for user with click stream data")
        result = getNews(mobile)
        return render_template("news.html", newsItems=result.values.tolist(), mobile=mobile)

    else:
        app.logger.info("Post")
        return "Post"


@app.route("/signup", methods=["POST", "GET"])
def signup():
    
    field_names = ['Username','Mobile','PasswordHash']
    
    if request.method == "GET":
        return render_template('/signup.html')
    
    else:

        if request.form['action'] == 'signup':
            
            username = request.form['username']
            mobile = request.form['mobile']
            password_hash = hashlib.md5(request.form['password'].encode()).hexdigest()
            data_dict = {'Username': username, 'Mobile': mobile, 'PasswordHash': password_hash}
            
            with open("DB/user.csv", 'a', newline='', encoding='utf-8') as f:
                dictwriter_object = DictWriter(f, fieldnames=field_names)
                dictwriter_object.writerow(data_dict)
                f.close()

            pd.DataFrame(columns=['Article ID', 'Time Spent']).to_csv("DB/UserPreferences/"+mobile+".csv", index=False)
            
            return redirect(url_for('index'))
        
        elif request.form['action'] == 'signin':
            return redirect(url_for('index'))



if __name__ == "__main__":
    app.run()