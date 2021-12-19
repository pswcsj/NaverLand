from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys

type_dict = {
    '매매':'A1',
    '전세':'A2',
    '월세':'B1',
    '단기임대':'B2'
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
gun = gun_dict[input("원하는 건물을 입력하세요 >")]

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

driver.get(url+'/'+gun+'/'+type_key+price)
print(driver.current_url)
time.sleep(1)

# https://m.land.naver.com/cluster/clusterList?view=atcl&cortarNo=4127300000&rletTpCd=OPST&tradTpCd=A1%3AB1%3AB2&z=13&lat=37.319537&lon=126.811832&pCortarNo=%20Request%20Method:%20GET

#매물 보기 클릭
try: driver.find_element(By.XPATH, '//*[@id="_mapSection"]/div[2]').click()
except: time.sleep(0.1)






# user_agent = driver.execute_script("return navigator.userAgent;") #useragent 정보 네이버가 봇감지하는 것을 방지하기 위해 사용
# print(user_agent)
#
# header = {
#     'User-Agent': user_agent,
#     'Referer' : 'https://m.land.naver.com/'
# }


# driver.close()