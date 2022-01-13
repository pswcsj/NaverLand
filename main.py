import time
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup

type_dict = {
    '매매':'A1',
    '전세':'B1',
    '월세':'B2',
    '단기임대':'B3'
}
gun_dict = {
    '아파트':'APT',
    '빌라':'VL',
    '단독/다가구':'DDDGG',
    '상가주택':'SGJT',
    '원룸':'OR',
    '상가':'SG',
    '토지':'TJ',
    '공장/창고':'GJCG',
    '지식산업센터':'APTHGJ',
    '건물':'GM',
    '오피스텔':'OPST',
    '아파트분양권':'ABYG',
    '오피스텔분양권':'OBYG',
    '재건축':'JGC',
    '전원주택':'JWJT',
    '한옥주택':'HOJT',
    '재개발':'JGB',
    '고시원':'GSW',
    '사무실':'SMS'
}
header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
    'Referer' : 'https://m.land.naver.com/'
}


def get_values(url):
    info_list = url.split('/')
    lan = info_list[4].split(':')[0]
    lon = info_list[4].split(':')[1]
    z = info_list[4].split(':')[2]
    try: cortarNo = info_list[4].split(':')[3]
    except IndexError: cortarNo = ''
    return lan, lon, z, cortarNo


def get_loc(data):
    url = 'https://map.naver.com/v5/api/geocode?request=coordsToaddr&version=1.0&sourcecrs=epsg:4326&output=json&orders=addr&coords='+ str(data['lng'])+','+str(data['lat'])
    res = requests.get(url, headers=header)
    soop = BeautifulSoup(res.text, 'html.parser')

    json_ju = json.loads(soop.contents[0])['results'][0]
    location = json_ju['region']['area1']['name']+' '+json_ju['region']['area2']['name']+' '+json_ju['region']['area3']['name']+' '+json_ju['region']['area4']['name']+\
        json_ju['land']['number1']+'-'+json_ju['land']['number2']
    return location


loc = input("지역을 입력하세요 > ")
response = requests.get('https://m.land.naver.com/search/result/'+loc, headers = header)
print(response.url)

while response.url.split('/')[3] != 'map':
    loc = input("지역을 더 자세히 입력하세요 > ")
    response = requests.get('https://m.land.naver.com/search/result/'+loc, headers = header)
    # time.sleep(0.1)

#url로 조건 설정
url_divide = response.url.split('/'); url_divide.pop(); url_divide.pop();
url = '/'.join(url_divide)
print(list(type_dict.keys()))
type = input("원하는 거래 방식을 입력하세요 >")
type_key = type_dict[type]

print(list(gun_dict.keys()))
gunn = input("원하는 건물을 입력하세요 >")
gun = gun_dict[gunn]

if type=='매매':
    priceMin = input("매매가의 최솟값을 입력하세요(만) >")
    priceMax = input("매매가의 최댓값을 입력하세요(만) >")
    price = '?dprcMin='+str(priceMin)+'&dprcMax='+str(priceMax)+'&'
elif type=='전세':
    priceMin = input("보증금의 최솟값을 입력하세요(만) >")
    priceMax = input("보증금의 최댓값을 입력하세요(만) >")
    price = '?wprcMin='+str(priceMin)+'&wprcMax='+str(priceMax)+'&'
elif (type=='월세') | (type=='단기임대'):
    priceWMin = input("보증금의 최솟값을 입력하세요(만) >")
    priceWMax = input("보증금의 최댓값을 입력하세요(만) >")
    priceMMin = input("월세의 최솟값을 입력하세요(만) >")
    priceMMax = input("월세의 최댓값을 입력하세요(만) >")
    price = '?wprcMin='+str(priceWMin)+'&wprcMax='+str(priceWMax)+\
            '&rprcMin='+str(priceMMin)+'&rprcMax='+str(priceMMax)+'&'

#위의 입력한 조건들 만족시키는 url로 접속
response = requests.get(url+'/'+gun+'/'+type_key+price, headers = header)

#단지 정보를 받아옴
lan, lon, z, cortaNo = get_values(response.url)
url_info = 'cortarNo='+str(cortaNo)+'&rletTpCd='\
    +gun+'&tradTpCd='+type_key+'&z='+str(z)+'&lat='+str(lan)+'&lon='+str(lon)+'&'+price[1:]
url_dan = 'https://m.land.naver.com/cluster/clusterList?view=atcl&'+url_info
response = requests.get(url_dan, headers = header)
soup = BeautifulSoup(response.text, 'html.parser')
# time.sleep(1)
json_data = json.loads(soup.contents[0])

total_cnt = 0
for data in json_data['data']['ARTICLE']:
    total_cnt += data['count']
print(total_cnt)

url_house = 'https://m.land.naver.com/cluster/ajax/articleList?'+url_info+'sort=rank&page='
df = pd.DataFrame(columns=['거래 방식', '지역', '매물 종류', '가격대', '면적', '특징', '매물번호', '부동산', '상세정보 링크'])

for i in range(1, int((total_cnt)/20)+2):
    response = requests.get(url_house+str(i), headers = header)
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        json_data = json.loads(soup.contents[0])['body']
    except json.decoder.JSONDecodeError:
        print("https://m.land.naver.com 에 접속해서 로봇 인증을 해주세요")
        while response.url == 'https://m.land.naver.com/error/abuse':
            response = requests.get(url_house + str(i), headers=header)
            soup = BeautifulSoup(response.text, 'html.parser')
            time.sleep(0.1)
        json_data = json.loads(soup.contents[0])['body']

    if (type == '매매') | (type == '전세'):
        for data in json_data:
            sameCnt = data['sameAddrCnt']
            if sameCnt >= 2:
                url_jung = 'https://m.land.naver.com/article/getSameAddrArticle?articleNo='+str(data['atclNo'])
                response = requests.get(url_jung, headers=header)
                soup = BeautifulSoup(response.text, 'html.parser')

                try:
                    json_jung = json.loads(soup.contents[0])
                except json.decoder.JSONDecodeError:
                    print("https://m.land.naver.com/error/abuse에 접속해 로봇 인증을 하세요")
                    while response.url == 'https://m.land.naver.com/error/abuse':
                        response = requests.get(url_jung, headers=header)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        time.sleep(0.1)
                    json_jung = json.loads(soup.contents[0])

                for data in json_jung:
                    location = get_loc(data)
                    try:
                        df.loc[len(df)] = [type,
                                           location + ' ' + data['atclNm'] + ' ' + data['bildNm'] + ' ' + data['flrInfo'],
                                           gunn, data['prc'], str(data['spc1']) + '/' + str(data['spc2']),
                                           data['atclFetrDesc'], data['atclNo'], data['rltrNm'], 'https://m.land.naver.com/article/info/'+str(data['atclNo'])]

                    except KeyError:
                        df.loc[len(df)] = [type,
                                           location + ' ' + data['atclNm'] + ' ' + data['bildNm'] + ' ' + data['flrInfo'],
                                           gunn, data['prc'], str(data['spc1']) + '/' + str(data['spc2']), '-', data['atclNo'], data['rltrNm'], 'https://m.land.naver.com/article/info/'+str(data['atclNo'])]

            else:
                try:
                    df.loc[len(df)] = [type, location+' '+data['atclNm']+' '+data['bildNm']+' '+data['flrInfo'], gunn, data['prc'], str(data['spc1'])+'/'+str(data['spc2']), data['atclFetrDesc'], data['atclNo'], data['rltrNm'], 'https://m.land.naver.com/article/info/'+str(data['atclNo'])]
                except KeyError:
                    df.loc[len(df)] = [type, location+' '+data['atclNm']+' '+data['bildNm']+' '+data['flrInfo'], gunn, data['prc'], str(data['spc1'])+'/'+str(data['spc2']), '-', data['atclNo'], data['rltrNm'], 'https://m.land.naver.com/article/info/'+str(data['atclNo'])]

    elif (type == '월세') | (type == '단기임대'):
        for data in json_data:
            sameCnt = data['sameAddrCnt']
            if sameCnt >= 2:
                url_jung = 'https://m.land.naver.com/article/getSameAddrArticle?articleNo=' + str(data['atclNo'])
                response = requests.get(url_jung, headers=header)
                soup = BeautifulSoup(response.text, 'html.parser')
                try:
                    json_jung = json.loads(soup.contents[0])
                except json.decoder.JSONDecodeError:
                    print("https://m.land.naver.com/error/abuse에 접속해 로봇 인증을 하세요")
                    while response.url == 'https://m.land.naver.com/error/abuse':
                        response = requests.get(url_jung, headers=header)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        time.sleep(0.1)
                    json_jung = json.loads(soup.contents[0])
                for data in json_jung:
                    try:
                        df.loc[len(df)] = [type,
                                           location + ' ' + data['atclNm'] + ' ' + data['bildNm'] + ' ' + data['flrInfo'],
                                           gunn, str(data['prc']) + '/' + str(data['rentPrc']),
                                           str(data['spc1']) + '/' + str(data['spc2']), data['atclFetrDesc'], data['atclNo'], data['rltrNm'], 'https://m.land.naver.com/article/info/'+str(data['atclNo'])]
                    except KeyError:
                        df.loc[len(df)] = [type,
                                           location + ' ' + data['atclNm'] + ' ' + data['bildNm'] + ' ' + data['flrInfo'],
                                           gunn, str(data['prc']) + '/' + str(data['rentPrc']),
                                           str(data['spc1']) + '/' + str(data['spc2']), '-', data['atclNo'], data['rltrNm'], 'https://m.land.naver.com/article/info/'+str(data['atclNo'])]
            else:
                try:
                    df.loc[len(df)] = [type, location+' '+data['atclNm']+' '+data['bildNm']+' '+data['flrInfo'], gunn, str(data['prc'])+'/'+str(data['rentPrc']), str(data['spc1'])+'/'+str(data['spc2']), data['atclFetrDesc'], data['atclNo'], data['rltrNm'], 'https://m.land.naver.com/article/info/'+str(data['atclNo'])]
                except KeyError:
                    df.loc[len(df)] = [type, location+' '+data['atclNm']+' '+data['bildNm']+' '+data['flrInfo'], gunn, str(data['prc'])+'/'+str(data['rentPrc']), str(data['spc1'])+'/'+str(data['spc2']), '-', data['atclNo'], data['rltrNm'], 'https://m.land.naver.com/article/info/'+str(data['atclNo'])]
    print(df)
df.to_csv('result.csv', encoding='utf-8-sig')