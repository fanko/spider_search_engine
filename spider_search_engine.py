# encoding: utf-8
# author: fanko24@gmail.com

import sys
import time
import random
import re
import urllib2
from bs4 import BeautifulSoup


# 每次搜索返回的100条结果
RN = 100

# 最多只解析10页
MAX_PAGE = 10

# 伪装不同的user_agent，避免被搜索引擎封掉
user_agent_list = ['Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0',
                   'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533+',
                   '(KHTML, like Gecko) Element Browser 5.0',
                   'IBM WebExplorer /v0.94',
                   'Galaxy/1.0 [en] (Mac OS X 10.5.6; U; en)',
                   'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
                   'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
                   'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko)',
                   'Version/6.0 Mobile/10A5355d Safari/8536.25',
                   'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko)',
                   'Chrome/28.0.1468.0 Safari/537.36',
                   'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; TheWorld)']


# 提取关键词的搜索结果条数
def get_result_number(soup):
    # 构造正则表达式对象
    regex = "百度为您找到相关结果约(.*)个"

    # findall匹配
    link = re.findall(regex, str(soup))
    # 返回搜索结果条数
    number = "".join(link[0].strip().split(","))
    if number.isdigit():
        return int(number)
    return -1


# 提取特定关键词搜索结果的第n页
def get_soup(query, page):
    # 第page页的百度搜索url
    url='http://www.baidu.com/s?wd=%s&rn=%d&pn=%d' %(query, RN, (page-1)*RN)

    # 将url写入request对象，并伪造user-agent避免被百度封
    request = urllib2.Request(url)
    index = random.randint(0, len(user_agent_list)-1)
    user_agent = user_agent_list[index]
    request.add_header('User-agent', user_agent)

    # 抓取url
    html=urllib2.urlopen(request).read()
    time.sleep(1.5)

    # 将返回的html对象利用BeautifulSoup对象解析
    soup=BeautifulSoup(html)

    return soup


# 搜索制定的关键词，返回(url, title, abstract)列表
def search(query):
    query_result = []

    # 抓取搜索结果的第一页
    first_page = 1
    first_soup = get_soup(query, first_page)

    # 获取第一页中的搜索结果条数，以此计算页数
    result_number = get_result_number(first_soup)
    page = (result_number - 1)/RN + 1

    # 逐页抓取并解析
    for i in range(1, page+1):
        soup = None
        if i == 1:
            soup = first_soup
        else:
            soup = get_soup(query, i)

        # 通过BeautifulSoup的find_all函数以及百度的xml页面结构解析出url,title和abstract
        for item in soup.find_all("div", "result c-container "):
            # 解析出abstract
            abstract =  item.div.get_text().encode("utf-8")

            # 解析出title
            regex = u"data-tools='\{\"title\":\"(.*)\",\"url\":\"(.*)\"\}'"
            div = item.find_all("div", "c-tools")
            link = re.findall(regex, str(div[0]))
            title = link[0][0]

            # 解析出url片段和最后更新日期
            span = item.find_all("span", "g")
            content = span[0].get_text()
            lst = content.strip().split()
            url = ""
            day = ""
            if len(lst) == 2:
                url = lst[0].strip().encode("utf-8")
                day = lst[1].strip().encode("utf-8")

            # 更新query_result
            query_result.append([url, title, abstract, day])

    return query_result

if __name__=='__main__':
    fout = open("debug.log", "a")
    for line in sys.stdin:
        key = line.strip()
        search_result = []
        repeat_number = 10
        while repeat_number > 0:
            begin = time.time()
            try:
                search_result = search(key)
                end = time.time()
                fout.write("%s\tis  OK\t%4.3f\n" %(key, end-begin))
            except:
                repeat_number -= 1
                end = time.time()
                fout.write("%s\trepeat\t%4.3f\n" %(key, end-begin))
            if search_result:
                break

        if len(search_result) == 0:
            print key
        else:
            for i in range(len(search_result)):
                print "\001".join([key, str(i+1)]+search_result[i])
