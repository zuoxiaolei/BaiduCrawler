#coding:utf-8
'''
@author: aitech
@email:
'''
import time
from splinter import Browser
from settings import settings
from bs4 import BeautifulSoup
import requests
import os
import re
import datetime
import urllib
import csv


class Coordinate():
    def __init__(self,x,y):
        self.x = x
        self.y = y

class BaiDuIndex():
    def __init__(self):
        self.browser = self.get_cookie()

    def get_cookie(self):
        '''
        从网页登录获取cookie
        '''
        browser = Browser("phantomjs")
        url = "http://index.baidu.com/"
        browser.visit(url)
        browser.click_link_by_partial_text(u"登录")
        browser.find_by_id("TANGRAM_12__userName").fill(settings.username)
        browser.find_by_id("TANGRAM_12__password").fill(settings.passwd)
        browser.find_by_id("TANGRAM_12__submit").click()
        time.sleep(5)
        #return browser
        return browser

    def close(self):
        self.browser.quit()

    def get_trend_Yimg(self,src,cookies,filename):
        res = requests.get(src,cookies=cookies)
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(filename,"wb") as fh:
            fh.write(res.content)


    def my_ocr_online(self,filename):
        '''
        ocr识别图片信息
        '''
        filename = os.path.abspath(filename)
        print filename
        with Browser("phantomjs") as browser:
            browser.visit("http://www.i2ocr.com/")
            browser.attach_file("i2ocr_uploadedfile",filename)
            time.sleep(2)

            browser.find_by_id("submit_i2ocr").click()
            time.sleep(5)
            html = browser.html

            pattern = re.compile(ur"\$\(\"\#ocrTextBox\"\)\.val\(\"(.*?)\"\)")
            text = pattern.findall(html)[0]
            return text

    def get_date(self,cor):
        end_date = []
        start_date = []
        firstDate = datetime.datetime(2011,1,1)
        for ele in range(len(cor)):
            end_date.append(firstDate+datetime.timedelta(days=7*ele))
            start_date.append(firstDate+datetime.timedelta(days=7*ele-6))
        return start_date,end_date

    def transfer_cor(self,rel_dist,hight,cor,start_point,nums):
        '''
        坐标数值转化
        '''
        real_value = []
        for ele in cor:
            #print ele.y
            real_value.append(int((start_point.y-ele.y)/hight*rel_dist)+nums[-1]-rel_dist+0.05*rel_dist)
        return real_value

    def get_response(self,url):
        '''
        从url获取信息
        '''
        browser =self.browser
        browser.visit(url)
        time.sleep(2)
        browser.find_by_text('全部').click()
        time.sleep(3)
        html = browser.html
        soup = BeautifulSoup(html,'lxml')

        src = "http://index.baidu.com"+soup.find(id="trendYimg").get('src')
        cookies = browser.cookies.all()
        filename = "./image/temp.png"
        self.get_trend_Yimg(src,cookies,filename)
        text = self.my_ocr_online(filename)
        #print text
        text = text.strip().replace(u",",u"").replace(u".",u"").replace(u" ",u"")
        numbers = [int(line.strip()) for line in text.split(u"\\n") if len(line.strip())!=0]
        #print numbers

        #获取数据
        paths = soup.find(id="trend").find_all("path")
        grids = paths[0].get('d').split(u"L")
        #print "length grids"
        #print len(grids)
        height = float(grids[1].split(u",")[-1])- float(grids[0].split(u",")[1])
        #print "height:"
        #print height

        #print "start_point"

        start_point = Coordinate(0,float(paths[2].get('d').split(u"L")[0].split(u",")[-1]))
        #print start_point.y
        #坐标
        data = paths[5].get('d').split(u"C")
        #print "data:"
        #print len(data)
        del data[0]

        cor = []
        for ele in data:
            temp = ele.split(u",")
            cor.append(Coordinate(float(temp[0]),float(temp[1])))
            #cor.append(Coordinate(float(temp[2]),float(temp[3])))
            #cor.append(Coordinate(float(temp[4]),float(temp[5])))
        #获取时间
        start_date,end_date = self.get_date(cor)
        #获取坐标
        rel_dist = numbers[0]-numbers[1]
        #print "rel_dist"
        #print rel_dist
        real_cor = self.transfer_cor(rel_dist,height,cor,start_point,numbers)
        browser.quit()
        return start_date,end_date,real_cor

    def output_to_csv(self,keyworld):
        filename = u'./result/'+keyworld+u".csv"
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        strings = urllib.quote(keyworld.encode('gb2312'))
        url = "https://index.baidu.com/?tpl=trend&type=0&area=0&time=13&word="+strings
        start_date,end_date,real_cor = self.get_response(url)

        #write to csv
        csvfile = open(filename,"wb")
        writter = csv.writer(csvfile)
        writter.writerow(["start date","end date","value"])
        for i,j,k in zip(start_date,end_date,real_cor):
            start = i.strftime("%Y-%m-%d")
            end = j.strftime("%Y-%m-%d")
            writter.writerow([start,end,k])
        csvfile.close()

if __name__=="__main__":
    keyword = "百度"
    baidu = BaiDuIndex()
    baidu.output_to_csv(keyword)