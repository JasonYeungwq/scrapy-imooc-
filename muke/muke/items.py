# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class UserItem(scrapy.Item):
    id = Field()
    name = Field()
    gender = Field()
    info = Field()
    learn_time = Field()
    credit = Field()
    mp = Field()
    follows_num = Field()
    followers_num = Field()
    courses_infos = Field()


