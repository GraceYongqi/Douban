#!/usr/bin/env python
# _*_coding:utf-8_*_
# Author: wuqi

import requests
import re
import codecs
from bs4 import BeautifulSoup
from openpyxl import Workbook
import MySQLdb
import sys
import random
import time

reload(sys)
sys.setdefaultencoding('utf8')

user_agent_list = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
]
UA = random.choice(user_agent_list)
user_agent = UA

wb = Workbook()

dest_filename = '电影.xlsx'
ws1 = wb.active
ws1.title = u"电影top250"
DOWNLOAD_URL = 'http://movie.douban.com/top250/'

dataSrcName = 'movietmp'
def download_page(url):
    """获取url地址页面内容"""
    headers = {
      #  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36'
        'User-Agent':UA,
        'Referer':'https://www.douban.com/'
    }
    data = requests.get(url, headers=headers).content
    return data


def get_li(doc):
    #待补充爬取图片
    #referer UA随机待验证

    soup = BeautifulSoup(doc, 'html.parser')
    ol = soup.find('ol', class_='grid_view')
    name = []  # 名字
    star_con = []  # 评价人数
    score = []  # 评分

    info_list = []  # 短评
    area_list = []  # 地区
    tags_list = []  # 标签

    for i in ol.find_all('li'):

        detail = i.find('div', attrs={'class': 'hd'})
        movie_name = detail.find(
            'span', attrs={'class': 'title'}).get_text()  # 电影名字
        level_star = i.find(
            'span', attrs={'class': 'rating_num'}).get_text()  # 评分
        star = i.find('div', attrs={'class': 'star'})
        star_num = star.find(text=re.compile('评价'))  # 评价

        basic = i.find('div',attrs={'class':'bd'})
        specific = unicode(str(basic.find('p',attrs={'class':''})))
        splitres = specific.split('<br/>')[1]
        area = splitres.split('/')[1].strip()
        tags = splitres.split('/')[2].strip('<').strip()

        info = i.find('span', attrs={'class': 'inq'})  # 短评

        name.append(movie_name)
        score.append(level_star)
        if info:  # 判断是否有短评
            info_list.append(info.get_text())
        else:
            info_list.append('无')
        area_list.append(area)
        tags_list.append(tags)
        star_con.append(star_num)

    page = soup.find('span', attrs={'class': 'next'}).find('a')  # 获取下一页
    if page:
        return name, star_con, score, info_list, area_list,tags_list,DOWNLOAD_URL + page['href']
    return name, star_con, score, info_list, area_list, tags_list,  None

def connectDb():
    db = MySQLdb.connect("localhost", "root", "", "PythonTest", charset='utf8')
    if db:
        print 'connect success!'
    return db

def intoTable(db,sql):
    # SQL 插入语句
    cursor = db.cursor()
    try:
        # 执行sql语句
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except:
        # Rollback in case there is any error
        # print ('insert error!',Exception)
        info = sys.exc_info()
        print(info[0], ":", info[1])
        # 如果发生异常，则回滚
        db.rollback()


def main():
    url = DOWNLOAD_URL
    name = []
    star_con = []
    score = []
    info = []
    moviearea = []
    movietags = []

    while url:
        doc = download_page(url)
        movie, star, level_num, info_list, area, tags, url = get_li(doc)
        name = name + movie
        star_con = star_con + star
        score = score + level_num
        info = info + info_list
        moviearea = moviearea + area
        movietags = movietags + tags
        # time.sleep(random.uniform(5,20))

    dataSrc = connectDb()

    for i in range(len(name)):
        content1 = name[i]
        content2 = float(score[i])
        content3 = info[i]
        content4 = moviearea[i]
        content5 = movietags[i]

        cursor = dataSrc.cursor()
        # 使用execute方法执行SQL语句
        content1 = unicode(content1)  # "u'"+content1+"'"
        content3 = unicode(content3)  # "u'"+content3+"'"

        content4 = unicode(content4)
        content5 = unicode(content5)

        intosql = "INSERT INTO movies(moviename,score, comment,area,tags)VALUES ('%s',%.1f,'%s','%s','%s')" \
                  % (MySQLdb.escape_string(content1),content2,MySQLdb.escape_string(content3),\
                     MySQLdb.escape_string(content4),MySQLdb.escape_string(content5))
        intoTable(dataSrc,intosql)

    dataSrc.close()
if __name__ == '__main__':
    main()