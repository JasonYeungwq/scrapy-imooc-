# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo


class MukePipeline(object):
    def process_item(self, item, spider):
        return item

class MongoPipiline(object):
    def __init__(self,mongo_uri,mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls,cralwer):
        return cls(
            mongo_uri = cralwer.settings.get('MOGO_URI'),
            mongo_db = cralwer.settings.get('MONGO_DB')
        )


    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db['user'].update({'id':item['id']},dict(item),True)
        # self.db['user'].insert(dict(item))
        return item
