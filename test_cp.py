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
def get_li(doc):
    soup = BeautifulSoup(doc, 'html.parser')
    ol = soup.find('ol', class_='grid_view')
    name = []  # 名字
    star_con = []  # 评价人数
    score = []  # 评分
    info_list = []  # 短评
    for i in ol.find_all('li'):
        detail = i.find('div', attrs={'class': 'hd'})
        movie_name = detail.find(
            'span', attrs={'class': 'title'}).get_text()  # 电影名字
        level_star = i.find(
            'span', attrs={'class': 'rating_num'}).get_text()  # 评分
        star = i.find('div', attrs={'class': 'star'})
        star_num = star.find(text=re.compile('评价'))  # 评价

        info = i.find('span', attrs={'class': 'inq'})  # 短评
        if info:  # 判断是否有短评
            info_list.append(info.get_text())
        else:
            info_list.append('无')
        score.append(level_star)

        name.append(movie_name)
        star_con.append(star_num)
    page = soup.find('span', attrs={'class': 'next'}).find('a')  # 获取下一页
    if page:
        return name, star_con, score, info_list, DOWNLOAD_URL + page['href']
    return name, star_con, score, info_list, None

def connectDb():
    db = MySQLdb.connect("localhost", "root", "", "PythonTest", charset='utf8')
    if db:
        print 'connect success!'
    return db

def intoTable(db,sql):
    # SQL 插入语句
    cursor = db.cursor
    sql = "select version();"
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
    while url:
        doc = download_page(url)
        movie, star, level_num, info_list, url = get_li(doc)
        name = name + movie
        star_con = star_con + star
        score = score + level_num
        info = info + info_list
    dataSrc = connectDb()
    # for (i, m, o, p) in zip(name, star_con, score, info):
    #     col_A = 'A%s' % (name.index(i) + 1)
    #     col_B = 'B%s' % (name.index(i) + 1)
    #     col_C = 'C%s' % (name.index(i) + 1)
    #     col_D = 'D%s' % (name.index(i) + 1)
    #     ws1[col_A] = i
    #     ws1[col_B] = m
    #     ws1[col_C] = o
    #     ws1[col_D] = p
    #    wb.save(filename=dest_filename)

    for i in range(len(name)):
        content1 = name[i]
        content2 = float(score[i])
        content3 = info[i]
        cursor = dataSrc.cursor()
        # 使用execute方法执行SQL语句
        content1 = unicode(content1)  # "u'"+content1+"'"
        content3 = unicode(content3)  # "u'"+content3+"'"
        # cursor.execute("INSERT INTO movietmp(moviename,score, comment)VALUES ('%s',%.1f,'%s')" % (eval(content1),content2,eval(content3)))
        try:
            cursor.execute("INSERT INTO movietmp(moviename,score, comment)VALUES ('%s',%.1f,'%s')" % (MySQLdb.escape_string(content1),content2,MySQLdb.escape_string(content3)))
            dataSrc.commit()
        except:
            # Rollback in case there is any error
            # print ('insert error!',Exception)
            err_info = sys.exc_info()
            print(err_info[0], ":", err_info[1])
            # 如果发生异常，则回滚
            dataSrc.rollback()

        # 使用 fetchone() 方法获取一条数据
        # data = cursor.fetchone()

        # intoTable(dataSrc,intosql)
    dataSrc.close()
if __name__ == '__main__':
    main()