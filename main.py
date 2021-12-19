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
driver.get(url='https://m.land.naver.com')
time.sleep(0.1)
driver.find_element(By.XPATH, '//*[@id="ct"]/div/div[2]/div/div[2]/div[2]/div[2]/a').click()
time.sleep(0.1)

# 시/동 선택
lists = []
while not lists:
    lists = driver.find_elements(By.CSS_SELECTOR, ".region_inner._region_item")
    loc_f_list = [list.text for list in lists]
    time.sleep(0.1)
print(loc_f_list)
loc_f = input("위에 제시된 목록 중 거래 지역을 입력하세요 >")
lists[loc_f_list.index(loc_f)].click()
time.sleep(1)

# 시/군/구 선택
lists = []
while not lists:
    lists = driver.find_elements(By.CSS_SELECTOR, ".region_inner._region_item")
    loc_s_list = [list.text for list in lists]
    time.sleep(0.1)
# loc_p = [text if text != '' else None for text in loc_s_list]
print(loc_s_list)
loc_s = input("위에 제시된 목록 중 거래 지역을 입력하세요 >")
lists[loc_s_list.index(loc_s)].click()
time.sleep(1)

# 읍/면/동 선택
choice = input("읍/면/동까지 입력하시겠습니까?(O/X)")
if (choice == 'o') | (choice == 'O'):
    lists = []
    while not lists:
        lists = driver.find_elements(By.CSS_SELECTOR, ".region_inner._region_item")
        loc_t_list = [list.text for list in lists]
        time.sleep(0.1)
    print(loc_t_list)
    loc_t = input("위에 제시된 목록 중 거래 지역을 입력하세요 >")
    lists[loc_t_list.index(loc_t)].click()

#검색 클릭
try: driver.find_element(By.XPATH, '//*[@id="mapSearch"]/div[2]/div[1]/section/div[2]/a').click()
except: time.sleep(0.1)
time.sleep(1)

#url로 조건 설정
url_divide = driver.current_url.split('/'); url_divide.pop(); url_divide.pop();
url = '/'.join(url_divide)
print(list(type_dict.keys()))
type = type_dict[input("원하는 거래 방식을 입력하세요 >")]
print(list(gun_dict.keys()))
gun = gun_dict[input("원하는 건물을 입력하세요 >")]
driver.get(url+'/'+gun+'/'+type)
time.sleep(1)



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