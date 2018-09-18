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

reload(sys)
sys.setdefaultencoding('utf8')

wb = Workbook()
dest_filename = '电影.xlsx'
ws1 = wb.active
ws1.title = u"电影top250"
DOWNLOAD_URL = 'http://movie.douban.com/top250/'

dataSrcName = 'movietmp'
def download_page(url):
    """获取url地址页面内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36'
    }
    data = requests.get(url, headers=headers).content
    return data


def get_brief(item):
    hyperlink = item.find('div',attrs={'class':'pic'}).find('a')['href']
    hyperlink_page = download_page(hyperlink)
    content = BeautifulSoup(hyperlink_page, 'html.parser')
    brief_para = str(content.find('div',attrs={'id':'link-report'}).find('span',attrs={'class':''}).get_text())
    # if (brief_para.find('<br />')) <0:
    #
    #     print 'yes！'
    #     b = brief_para
    # else:
    b = brief_para.split('<br/>')[0]
    return b.strip()[0:100]


def get_li(doc):
    soup = BeautifulSoup(doc, 'html.parser')
    ol = soup.find('ol', class_='grid_view')
    print '11111111'
    name = []  # 名字
    star_con = []  # 评价人数
    score = []  # 评分

    info_list = []  # 短评
    area_list = []  # 地区
    tags_list = []  # 标签
    brief_list = [] # 简介

    for i in ol.find_all('li'):
        # # # #       #       #            #       #        #
        brief = get_brief(i)
        # print brief

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
        brief_list.append(brief)
        star_con.append(star_num)

    page = soup.find('span', attrs={'class': 'next'}).find('a')  # 获取下一页
    if page:
        return name, star_con, score, info_list, area_list,tags_list,brief_list, DOWNLOAD_URL + page['href']
    return name, star_con, score, info_list, area_list, tags_list, brief_list, None

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
    moviebrief = []

    while url:
        doc = download_page(url)
        movie, star, level_num, info_list, area, tags, brief, url = get_li(doc)
        name = name + movie
        star_con = star_con + star
        score = score + level_num
        info = info + info_list
        moviearea = moviearea + area
        movietags = movietags + tags
        moviebrief = moviebrief + brief

    dataSrc = connectDb()

    for i in range(len(name)):
        content1 = name[i]
        content2 = float(score[i])
        content3 = info[i]
        content4 = moviearea[i]
        content5 = movietags[i]
        content6 = moviebrief[i]

        cursor = dataSrc.cursor()
        # 使用execute方法执行SQL语句
        content1 = unicode(content1)  # "u'"+content1+"'"
        content3 = unicode(content3)  # "u'"+content3+"'"

        content4 = unicode(content4)
        content5 = unicode(content5)
        content6 = unicode(content6)

        intosql = "INSERT INTO movietmp(moviename,score, comment,area,tags,brief)VALUES ('%s',%.1f,'%s','%s','%s','%s')" \
                  % (MySQLdb.escape_string(content1),content2,MySQLdb.escape_string(content3),\
                     MySQLdb.escape_string(content4),MySQLdb.escape_string(content5),MySQLdb.escape_string(content6))
        intoTable(dataSrc,intosql)

    dataSrc.close()
if __name__ == '__main__':
    main()