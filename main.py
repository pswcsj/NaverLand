from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys
import json
import pandas as pd

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

def get_values(url):
    info_list = url.split('/')
    lan = info_list[4].split(':')[0]
    lon = info_list[4].split(':')[1]
    z = info_list[4].split(':')[2]
    cortarNo = info_list[4].split(':')[3]
    return lan, lon, z, cortarNo

driver = webdriver.Chrome('./chromedriver')

loc = input("지역을 입력하세요 > ")
driver.get('https://m.land.naver.com/search/result/'+loc)
while driver.current_url.split('/')[3] != 'map':
    loc = input("지역을 더 자세히 입력하세요 > ")
    driver.get('https://m.land.naver.com/search/result/' + loc)
    time.sleep(0.1)

#url로 조건 설정
url_divide = driver.current_url.split('/'); url_divide.pop(); url_divide.pop();
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
driver.get(url+'/'+gun+'/'+type_key+price)

#단지 정보를 받아옴
lan, lon, z, cortaNo = get_values(driver.current_url)
url_info = 'cortarNo='+str(cortaNo)+'&rletTpCd='\
    +gun+'&tradTpCd='+type_key+'&z='+str(z)+'&lat='+str(lan)+'&lon='+str(lon)+'&'+price
url_dan = 'https://m.land.naver.com/cluster/clusterList?view=atcl&'+url_info
driver.get(url_dan)

time.sleep(1)
json_datar = driver.find_element(By.XPATH, '/html/body/pre').text
json_data = json.loads(json_datar)

total_cnt = 0
for data in json_data['data']['ARTICLE']:
    total_cnt += data['count']
print(total_cnt)

url_house = 'https://m.land.naver.com/cluster/ajax/articleList?'+url_info+'sort=rank&page='
df = pd.DataFrame(columns=['거래 방식', '지역', '매물 종류', '가격대', '면적', '특징'])

for i in range(1, int((total_cnt)/20)+2):
    driver.get(url_house+str(i))
    json_data = json.loads(driver.find_element(By.XPATH, '/html/body/pre').text)['body']
    if (type == '매매') | (type == '전세'):
        for data in json_data:
            try:
                df.loc[len(df)] = [type, loc+' '+data['atclNm']+' '+data['bildNm']+' '+data['flrInfo'], gunn, data['prc'], str(data['spc1'])+'/'+str(data['spc2']), data['atclFetrDesc']]
            except KeyError:
                df.loc[len(df)] = [type, loc+' '+data['atclNm']+' '+data['bildNm']+' '+data['flrInfo'], gunn, data['prc'], str(data['spc1'])+'/'+str(data['spc2']), '-']
    elif (type == '월세') | (type == '단기임대'):
        for data in json_data:
            try:
                df.loc[len(df)] = [type, loc+' '+data['atclNm']+' '+data['bildNm']+' '+data['flrInfo'], gunn, str(data['prc'])+'/'+str(data['rentPrc']), str(data['spc1'])+'/'+str(data['spc2']), data['atclFetrDesc']]
            except KeyError:
                df.loc[len(df)] = [type, loc+' '+data['atclNm']+' '+data['bildNm']+' '+data['flrInfo'], gunn, str(data['prc'])+'/'+str(data['rentPrc']), str(data['spc1'])+'/'+str(data['spc2']), '-']
    # print(json_data)
    print(df)

df.to_csv('result.csv')
time.sleep(1)

driver.quit()






# user_agent = driver.execute_script("return navigator.userAgent;") #useragent 정보 네이버가 봇감지하는 것을 방지하기 위해 사용
# print(user_agent)
#
# header = {
#     'User-Agent': user_agent,
#     'Referer' : 'https://m.land.naver.com/'
# }


# driver.close()