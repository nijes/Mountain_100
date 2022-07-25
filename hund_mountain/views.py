from django.shortcuts import render, redirect
from .models import Coordinate, Mountain1, Mountain2, Mountain3, LiveWeather, Subway, Train, Bus
from tkinter import messagebox
import requests
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from django.http import JsonResponse

custom_header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}



def index(request):
    return render(request, 'index.html')


def map(request, areacode):
    area = Coordinate.objects.get(areacode=areacode)
    mountain = Mountain1.objects.all()
    return render(request, 'map.html', {'area': area, 'mountain': mountain})


def nifos(request, id):

    url = f'http://mtweather.nifos.go.kr/famous/mountainOne?stnId={id}'
    req = requests.get(url, headers=custom_header).text
    document = json.loads(req)

    nowWeather = int(document['others']['iconCode'])
    nowTemp = document['famousMTSDTO']['forestAWS10Min']['tm2m']
    sunriseTime = document['others']['sunriseTime']
    sunsetTime = document['others']['sunsetTime']
    w_info = document['hr3List'][0]
    today_weather = {'wcond': w_info['wcond'], 'temp': w_info['temp'], 'humi': w_info['humi'], 'wspd': w_info['wspd'], 'rainp': w_info['rainp']}
    w_info = document['hr3List'][-14]
    tommorow_weather = {'wcond': w_info['wcond'], 'temp': w_info['temp'], 'humi': w_info['humi'], 'wspd': w_info['wspd'], 'rainp': w_info['rainp']}
    w_info = document['hr3List'][-6]
    after_tommorow_weather =  {'wcond': w_info['wcond'], 'temp': w_info['temp'], 'humi': w_info['humi'], 'wspd': w_info['wspd'], 'rainp': w_info['rainp']}

    mtw = {
        'nowWeather': nowWeather,
        'nowTemp': nowTemp,
        'sunriseTime': sunriseTime,
        'sunsetTime': sunsetTime,
        'today_weather': today_weather,
        'tommorow_weather': tommorow_weather,
        'after_tommorow_weather': after_tommorow_weather
    }

    return JsonResponse(mtw)



def list(request):
    mountains = Mountain1.objects.all()
    return render(request, 'list.html', {'mountains': mountains})



def detail(request, id):
    if request.method == 'GET':
        mountain1 = Mountain1.objects.get(id=id)
        mountain2 = Mountain2.objects.get(id=id)
        mountain3 = Mountain3.objects.get(id=id)
        return render(request, 'detail.html', {'mountain1':mountain1, 'mountain2': mountain2, 'mountain3': mountain3, 'id':id})

    else:
        mt_name = request.POST['mt_name']
        try:
            mountain1 = Mountain1.objects.get(name=mt_name)
            id = mountain1.id
            mountain2 = Mountain2.objects.get(id=id)
            mountain3 = Mountain3.objects.get(id=id)
            return render(request, 'detail.html', {'mountain1': mountain1, 'mountain2': mountain2, 'mountain3': mountain3, 'id':id})
        except:
            messagebox.showinfo('Error', '해당 산이 목록에 없습니다')
            return redirect('/list/')


def analyze_2(request):
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)

    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    tm = str(tomorrow)
    tmr = tm[:4] + tm[5:7] + tm[8:10] + '09'

    lW = LiveWeather.objects.filter(day=tmr)
    df = pd.DataFrame(columns=['name', 'temp', 'hum', 'di', 'num'])
    j = 0
    for i in lW:
        df.loc[j] = [str(i.name), float(i.temp), float(i.hum), float(i.di), float(i.num)]
        j += 1

    conditionlist = [
        (df['di'] <= 68),
        (df['di'] <= 70) & (df['di'] > 68),
        (df['di'] <= 75) & (df['di'] > 70),
        (df['di'] <= 80) & (df['di'] > 75),
        (df['di'] <= 83) & (df['di'] > 80),
        (df['di'] <= 86) & (df['di'] > 83)]
    choicelist = ["매우 쾌적", "쾌적", "조금 쾌적", "조금 불쾌", "불쾌", "매우 불퇘"]
    df['di_count'] = np.select(conditionlist, choicelist)

    color = ['#008080']
    sns.set_palette(color)

    sns.displot(x='hum', y='temp', data=df, kind='hist', binwidth=(3, 1))
    plt.savefig('./hund_mountain/static/assets/img/graph.png')

    colors = ['#0100FF', '#00D8FF', "#B2EBF4", '#FFC19E', '#FFA7A7']
    #colors = ['#FFA7A7', '#FFC19E', "#B2EBF4", '#00D8FF', '#0100FF']

    sns.set_palette(sns.color_palette(colors))
    ax = sns.countplot(data=df, y='di_count', order=['매우 쾌적', '쾌적', '조금 쾌적', '조금 불쾌', '불쾌'])
    plt.yticks(rotation=90)
    plt.ylabel('불쾌 지수')
    ax.figure.savefig('./hund_mountain/static/assets/img/graph2.png')

    cf1 = LiveWeather.objects.filter(di__lt = 68) & LiveWeather.objects.filter(day=tmr)
    cf2 = LiveWeather.objects.filter(di__lt = 70) & LiveWeather.objects.filter(di__gt =68) & LiveWeather.objects.filter(day=tmr)
    cf3 = LiveWeather.objects.filter(di__lt = 75) & LiveWeather.objects.filter(di__gt =70) & LiveWeather.objects.filter(day=tmr)

    return render(request, 'analyze_2.html', {'cf1':cf1, 'cf2':cf2, 'cf3':cf3})


def transit(request, id):
    subway = Subway.objects.all()
    train = Train.objects.all()
    bus = Bus.objects.all()
    mountain = Mountain1.objects.all()
    center = Mountain1.objects.get(id=id)
    return render(request, 'transit.html', {'subway': subway, 'train': train, 'bus': bus, 'mountain': mountain, 'id': id, 'center':center})


def recommend(request):
    return render(request, 'recommend.html')


def analyze_1(request):
    return render(request, 'analyze_1.html')
