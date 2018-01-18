# -*- coding: utf-8 -*-
import copy

import requests
import scrapy
from scrapy import Request
import re
from muke import settings
import logging
from pyquery import PyQuery as pq

from muke.items import UserItem
from pymongo import MongoClient

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]


class MukespiderSpider(scrapy.Spider):
    name = 'mukespider'
    allowed_domains = ['www.imooc.com']
    # start_urls = ['http://www.imooc.com/']
    base_url = 'https://www.imooc.com/u/{id}/{kind}?page={page}'
    start_id = '2945290' #大V的id 起始id
    # start_id = '1098050' #有问题的id
    # start_id = '141256'  #特殊的id 性别保密 没学习时长
    # start_id = '4536274'  #女性id

    # start_id = '2132946' #小量的id
    # start_id = '2705746' #讲师的id 读取不到信息的
    # start_id = '10000'  #GM的id

    kind = ['courses','follows','fans']

    def start_requests(self):
        #这里第一个用户不在第一次进入parse_user，这样会造成多次启动多次录入第一个用户，因为parse_user并没有去重功能，
        # 不过初始账号是大V，有粉丝就会被循环到的，不用担心
        # yield  Request(self.base_url.format(id=self.start_id,kind=self.kind[0],page=1),self.parse_user)
        yield  Request(self.base_url.format(id=self.start_id,kind=self.kind[1],page=1),self.parse_follows)
        yield  Request(self.base_url.format(id=self.start_id,kind=self.kind[2],page=1),self.parse_fans)

    def parse_user(self, response):
        try:
            id = re.search('\/u\/(\d+)\/courses',response.url).group(1)
            name = response.css('.user-name > span ::text').extract_first()
            gender = response.css('.about-info>span ::attr(title)').extract_first()
            try:
                # 有问题 位置
                info = re.search('title=.*?><\/span>(.*?)<span ',response.css('.about-info').extract_first(),re.S).group(1).strip()
            except:
                info = None
            info=info.replace('\n','').replace('\r','').replace(' ','')
            learn_time = response.css('.u-info-learn em ::text').extract_first()
            if learn_time == None:
                learn_time = '0'
            credit = response.css('.u-info-credit em ::text').extract_first()
            mp = response.css('.u-info-mp em ::text').extract_first()
            follows_num = response.css('.item.follows em ::text').extract_first()
            followers_num =response.css('.item.followers em ::text').extract_first()
            courses_infos = []
                #for 直接用requests访问每一页课程并解析信息
            try:
                max_page = int(re.search('page=(\d+)">尾页</a>',response.text).group(1))
            except:
                max_page = 1
            # current_page = int(response.css('div.qa-comment-page > div > a.active.text-page-tag ::text').extract_first())
            for i in range(1,max_page+1):
                url = re.match(r'https.*page=', response.url)[0] + str(i)
                r = requests.get(url,headers=settings.DEFAULT_REQUEST_HEADERS)
                r = pq(r.text)
                courses_list = r('.clearfix.tl-item .course-list.course-list-m .clearfix ').children()
                course_name = courses_list('.course-list-cont h3 a')
                course_state = courses_list('.course-list-cont h3 span')
                learn_state = courses_list('.study-points .i-left.span-common')
                during_time = courses_list('.study-points .i-mid.span-common')
                learn_to = courses_list('.study-points .i-right.span-common')
                for j in range(0,len(courses_list)):
                    courses_info = {'course_name':course_name[j].text,
                                    'course_state':course_state[j].text,
                                    'learn_state':learn_state[j].text,
                                    'during_time':during_time[j].text,
                                    'learn_to':learn_to[j].text}
                    courses_infos.append(courses_info)
            item = UserItem()
            for field in item.fields:
                try:
                    item[field]=eval(field)
                except NameError:
                    print('Field is Not Defined', field)
            yield item
            # print(self.base_url.format(id=id,kind=self.kind[1],page=1))
            # print(self.base_url.format(id=id, kind=self.kind[2], page=1))
            yield Request(self.base_url.format(id=id,kind=self.kind[1],page=1),self.parse_follows)
            yield Request(self.base_url.format(id=id, kind=self.kind[2], page=1), self.parse_fans)
        except:
            return None

    def parse_follows(self, response):
        try:
            try:
                #读取尾页和当前页，如果不存在则只有一页，设为1
                max_page = int(re.findall('page=(\d+)\">尾页</a>',response.text)[0])
                current_page = int(response.css('#pagenation > div > a.active.text-page-tag ::text').extract_first())

            except:
                max_page = 1
                current_page = 1

            ids = response.css('div.concern-list ul div.title a::attr("href")').extract()
            for i in range(0,len(ids)):
                ids[i]=ids[i][3:]

            # //从数据库读取已收录的id（用于去重）
            db_id = db.user.find({},{'_id':0,'id':1})
            db_id_list = []
            for i in db_id:
                db_id_list.append(i['id'])


            # #判断id是否在数据库中，不在则调用Requests并回调parse_user，否则丢弃
            for id in ids:
                if id not in db_id_list:
                    yield Request(self.base_url.format(id=id,kind=self.kind[0],page=1),self.parse_user)
            #判断当前页是否为最后一页，不是的话则构造下一页的url，并重新调用调用Requests并回调parse_follows
            if current_page<max_page:
                next_page = current_page+1
            else:
                return None
            url = re.match(r'https.*page=',response.url)[0]+str(next_page)
            # print('+++++++++++++++++++++++',current_page,url)
            yield Request(url,self.parse_follows)
        except:
            return None


    def parse_fans(self, response):
        try:
            try:
                max_page = int(re.findall('page=(\d+)\">尾页</a>',response.text)[0])
                current_page = int(response.css('#pagenation > div > a.active.text-page-tag ::text').extract_first())

            except:
                max_page = 1
                current_page = 1

            ids = response.css('div.concern-list ul div.title a::attr("href")').extract()
            # //从数据库读取已收录的id（用于去重）
            db_id = db.user.find({},{'_id':0,'id':1})
            db_id_list = []
            for i in db_id:
                db_id_list.append(i['id'])

            for id in ids:
                if id not in db_id_list:
                   yield Request(self.base_url.format(id=id,kind=self.kind[0],page=1),self.parse_user)
            if current_page<max_page:
                next_page = current_page+1
            else:
                return None
            url = re.match(r'https.*page=',response.url)[0]+str(next_page)
            # print('+++++++++++++++++++++++',current_page+1,url)
            yield Request(url,self.parse_fans)
        except:
            return None