from ast import IsNot
from distutils.log import error
from msilib.schema import Class
from flask import Flask, render_template, jsonify, request
from flask_restful import Resource, Api
from flask_mysqldb import MySQL
import tweepy
import pandas as pd
from textblob import TextBlob
from wordcloud import WordCloud
import numpy as np
import matplotlib.pyplot as plt
from pytrends.request import TrendReq
from datetime import timedelta, date
import skfuzzy as fuzz
from skfuzzy import control as ctrl

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'iziyobisi'
mysql = MySQL(app)
api = Api(app)

app.secret_key = 'abcdefghijklmnopqrstuvwxyz'


def fuzzy(tw, twt, twtr):
    google = ctrl.Antecedent(np.arange(0, 101, 5), 'google')
    twitter = ctrl.Antecedent(np.arange(0, 101, 5), 'twitter')
    twitter2 = ctrl.Antecedent(np.arange(0, 101, 5), 'twitter2')
    rating = ctrl.Consequent(np.arange(0, 101, 5), 'rating')

    google['low'] = fuzz.trapmf(google.universe, [0, 0, 40, 45])
    google['medium'] = fuzz.trapmf(google.universe, [40, 45, 70, 75])
    google['high'] = fuzz.trapmf(google.universe, [70, 75, 101, 101])
    twitter['low'] = fuzz.trapmf(twitter.universe, [0, 0, 40, 45])
    twitter['medium'] = fuzz.trapmf(twitter.universe, [40, 45, 70, 75])
    twitter['high'] = fuzz.trapmf(twitter.universe, [70, 75, 101, 101])
    twitter2['low'] = fuzz.trapmf(twitter2.universe, [0, 0, 40, 45])
    twitter2['medium'] = fuzz.trapmf(twitter2.universe, [40, 45, 70, 75])
    twitter2['high'] = fuzz.trapmf(twitter2.universe, [70, 75, 101, 101])
    rating['low'] = fuzz.trapmf(rating.universe, [0, 0, 30, 35])
    rating['medium'] = fuzz.trapmf(rating.universe, [30, 35, 70, 75])
    rating['high'] = fuzz.trapmf(rating.universe, [70, 75, 101, 101])

    rule1 = ctrl.Rule(google['low'] & twitter['low']
                      & twitter2['low'], rating['low'])
    rule2 = ctrl.Rule(google['low'] & twitter['low'] &
                      twitter2['medium'], rating['low'])
    rule3 = ctrl.Rule(google['low'] & twitter['low'] &
                      twitter2['high'], rating['low'])
    rule4 = ctrl.Rule(google['low'] & twitter['medium']
                      & twitter2['low'], rating['low'])
    rule5 = ctrl.Rule(google['low'] & twitter['medium']
                      & twitter2['medium'], rating['low'])
    rule6 = ctrl.Rule(google['low'] & twitter['medium']
                      & twitter2['high'], rating['medium'])
    rule7 = ctrl.Rule(google['low'] & twitter['high']
                      & twitter2['low'], rating['medium'])
    rule8 = ctrl.Rule(google['low'] & twitter['high']
                      & twitter2['medium'], rating['medium'])
    rule9 = ctrl.Rule(google['low'] & twitter['high']
                      & twitter2['high'], rating['medium'])
    rule10 = ctrl.Rule(google['low'] & twitter['low']
                       & twitter2['low'], rating['low'])
    rule11 = ctrl.Rule(google['low'] & twitter['low']
                       & twitter2['medium'], rating['low'])
    rule12 = ctrl.Rule(google['low'] & twitter['low']
                       & twitter2['high'], rating['low'])
    rule13 = ctrl.Rule(google['medium'] & twitter['medium']
                       & twitter2['low'], rating['medium'])
    rule14 = ctrl.Rule(google['medium'] & twitter['medium']
                       & twitter2['medium'], rating['medium'])
    rule15 = ctrl.Rule(google['medium'] & twitter['medium']
                       & twitter2['high'], rating['medium'])
    rule16 = ctrl.Rule(google['medium'] & twitter['high']
                       & twitter2['low'], rating['high'])
    rule17 = ctrl.Rule(google['medium'] & twitter['high']
                       & twitter2['medium'], rating['high'])
    rule18 = ctrl.Rule(google['medium'] & twitter['high']
                       & twitter2['high'], rating['high'])
    rule19 = ctrl.Rule(google['high'] & twitter['low']
                       & twitter2['low'], rating['medium'])
    rule20 = ctrl.Rule(google['high'] & twitter['low']
                       & twitter2['medium'], rating['medium'])
    rule21 = ctrl.Rule(google['high'] & twitter['low']
                       & twitter2['high'], rating['medium'])
    rule22 = ctrl.Rule(google['high'] & twitter['medium']
                       & twitter2['low'], rating['high'])
    rule23 = ctrl.Rule(google['high'] & twitter['medium']
                       & twitter2['medium'], rating['high'])
    rule24 = ctrl.Rule(google['high'] & twitter['medium']
                       & twitter2['high'], rating['high'])
    rule25 = ctrl.Rule(google['high'] & twitter['high']
                       & twitter2['low'], rating['high'])
    rule26 = ctrl.Rule(google['high'] & twitter['high']
                       & twitter2['medium'], rating['high'])
    rule27 = ctrl.Rule(google['high'] & twitter['high']
                       & twitter2['high'], rating['high'])

    rating_ctrl = ctrl.ControlSystem(
        [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12, rule13, rule14, rule15, rule16, rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25, rule26, rule27])
    rat = ctrl.ControlSystemSimulation(rating_ctrl)

    rat.input['google'] = tw
    rat.input['twitter'] = twt
    rat.input['twitter2'] = twtr
    rat.compute()
    return rat.output['rating']

###API###


def setup(pk):
    penyakit = str(pk)
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM ' + penyakit)
    rv = cur.fetchall()
    my_list = []  # berisikan data obat
    seen = set()
    mylist = list(rv)
    for i in mylist:
        temp = Twitter(i[0].split()[0])
        if i[0].split()[0] not in seen and temp > 0:
            seen.add(i[0].split()[0])
            my_list.append(i)
    return list(my_list)


class tesSetup(Resource):
    def get(self):
        return jsonify(fuzzy(10, 20, 20))


def Twitter_auth():
    myToken = []
    Token = pd.read_csv('token.csv', sep=',')
    for i in Token:
        myToken.append(i)
    consumer_key = myToken[0]
    consumer_secret = myToken[1]
    access_token = myToken[2]
    access_token_secret = myToken[3]
    # proses autentikasi.
    authenticate = tweepy.OAuthHandler(consumer_key, consumer_secret)
    authenticate.set_access_token(access_token, access_token_secret)
    api = tweepy.API(authenticate, wait_on_rate_limit=True)
    # mengambil data tweet.
    return api


def tesTwitter(pk):
    list = []
    for i in range(20):
        list.append(getTrendW('paracetamol'))
    return jsonify(list)


def Twitter(pk):
    api = Twitter_auth()
    # mengambil data tweet.
    topic = pk
    posts = api.search_tweets(
        q=topic,  lang="id", count=100, include_rts=False, since="2022-10-25", until="2022-10-26")
    temp = len(posts)
    #     tes1 = list(mylist[index])
    #     tes1.append(temp)
    #     tes.append(tes1)
    #     index = index + 1
    #     temp = 0
    # sorted_tes = sorted(tes, key=lambda x: x[2], reverse=True)
    return temp


def Twitter1(pk):
    api = Twitter_auth()
    # mengambil data tweet.
    topic = pk
    posts = api.search_tweets(
        q=topic,  lang="id", count=100, include_rts=False, since="2022-10-26", until="2022-10-27")
    temp = len(posts)
    #     tes1 = list(mylist[index])
    #     tes1.append(temp)
    #     tes.append(tes1)
    #     index = index + 1
    #     temp = 0
    # sorted_tes = sorted(tes, key=lambda x: x[2], reverse=True)
    return temp


def Trends(pk):
    api = Twitter_auth()
    # mengambil data tweet.
    topic = pk
    posts = api.search_tweets(
        q=topic,  lang="id", count=100, include_rts=False, since="2022-10-27", until="2022-10-28")
    temp = len(posts)
    #     tes1 = list(mylist[index])
    #     tes1.append(temp)
    #     tes.append(tes1)
    #     index = index + 1
    #     temp = 0
    # sorted_tes = sorted(tes, key=lambda x: x[2], reverse=True)
    return temp


# class simpanT(Resource):
#     def get(self):
#         penyakit = ['asma', 'batukdanflu', 'demam',
#                     'diabetes', 'hipertensi', 'kategorikulit']
#         my_list = []
#         for j in penyakit:
#             mylist = list(Twitter(j))
#             for i in mylist:
#                 my_list.append(i[2])
#             df = pd.DataFrame(my_list, columns=[j])
#             df.to_csv('data.csv', encoding='utf-8')
#             mylist.clear()
#             my_list.clear()
#             df = df.iloc[0:0]
#         return 'suskses'


def getTrendW(pk):
    penyakit = str(pk)
    hl = 'en-ID'
    tz = 420
    kw_list = [penyakit]
    geo = 'ID'
    start_date = date(year=2022, month=10, day=16)
    end_date = date(year=2022, month=10, day=23)
    timeframe = str(start_date) + ' ' + str(end_date)
    pytrends = TrendReq(hl=hl, tz=tz)
    pytrends.build_payload(kw_list=kw_list, timeframe=timeframe, geo=geo)
    df_monthly = pytrends.interest_over_time()
    list3 = list(df_monthly[penyakit])
    temp = 0
    for i in list3:
        temp = temp + i
    temp = temp/len(list3)
    return temp


def getTrendM(pk):
    penyakit = str(pk)
    hl = 'en-ID'
    tz = 420
    kw_list = [penyakit]
    geo = 'ID'
    start_date = date(year=2021, month=10, day=27)
    end_date = date(year=2021, month=11, day=27)
    timeframe = str(start_date) + ' ' + str(end_date)
    pytrends = TrendReq(hl=hl, tz=tz)
    pytrends.build_payload(kw_list=kw_list, timeframe=timeframe, geo=geo)
    df_monthly = pytrends.interest_over_time()
    return list(df_monthly[penyakit])


class simpanG(Resource):
    def get(self):
        penyakit = ['asma', 'batuk', 'flu', 'demam',
                    'diabetes', 'hipertensi', 'kulit']
        for i in penyakit:
            list = Sorting(i)
            df = pd.DataFrame(list)
            df.to_csv(i + '.csv', header=False)
        return 'sukses'


def Sorting(pk):
    penyakit = pk
    my_list = setup(penyakit)
    list_rating = []
    tes = []
    index = 0
    mylist = []
    for i in my_list:
        mylist.append(i[0].split()[0])
    for obat in mylist:
        gl = Trends(obat)
        tw = Twitter(obat)
        tw1 = Twitter1(obat)
        total = fuzzy(gl, tw, tw1)
        list_rating.append(total)
        tes1 = list(my_list[index])
        tes1.append(total)
        tes.append(tes1)
        index = index + 1
        total = 0
    sorted_tes = sorted(tes, key=lambda x: x[2], reverse=True)
    return list(sorted_tes)


@ app.route('/')
@ app.route('/start')
def start():
    return render_template('index.html')


@ app.route('/iziyobisi')
def iziyobisi():
    obj = pd.read_csv('rekomendasiawal.csv')
    obj = obj.values.tolist()
    return render_template('index2.html', ob=list(obj))


@ app.route('/simpan')
def simpan():
    return render_template('index1.html')

# class Recommendation1():
#     def get(self):
#         penyakit = request.form['penyakit']
#         cur = mysql.connection.cursor()
#         cur.execute(('SELECT * FROM ' + str(penyakit) +' LIMIT 10'))
#         obj = cur.fetchall()
#         return jsonify(obj)


@ app.route('/recommendation', methods=['POST', 'GET'])
def recommendation():
    if request.method == 'POST':
        penyakit = request.form['penyakit']
        obj = pd.read_csv(penyakit + '.csv')
        obj = obj.values.tolist()
        return render_template('index2.html', ob=list(obj))
    else:
        return render_template('index2.html')


# api.add_resource(Recommendation1, '/Recommendation1')
api.add_resource(simpanG, '/user')

if __name__ == '__main__':
    app.run(debug=True)
