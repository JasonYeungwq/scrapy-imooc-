# *_*coding:utf-8 *_*
from pyquery import PyQuery as pq
import re
import requests
url = 'https://www.imooc.com/u/2945290/follows'
r = requests.get(url)
max_page = re.findall('page=(\d+)\">尾页</a>',r)[0]
print(max_page)
requests.get(url,)