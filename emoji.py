# !/usr/bin/python
# encoding: utf-8

import sys
from workflow import Workflow3, web
from multiprocessing.pool import ThreadPool
import urllib.request
import requests
import os
import re
from bs4 import BeautifulSoup

ICON_DEFAULT = 'icon.png'

user_home_dir = os.path.expanduser('~') + "/.emoji"
cache_path = os.getenv('cache_path', user_home_dir)
if cache_path == "":
    cache_path = user_home_dir

int_number = re.compile(r'[0-9]')

if cache_path[len(cache_path) - 1] != '/':
    cache_path = cache_path + '/'


def list_emoji_doutub(query=None, page=1):
    url = "https://www.doutub.com/search/{}/{}".format(query, page)

    headers = {"Referer": "https://www.doutub.com"}
    r = requests.get(url, headers=headers)

    # throw an error if request failed, Workflow will catch this and show it to the user
    r.raise_for_status()

    emojis = []
    data = r.text

    soup = BeautifulSoup(data)
    imgs = soup.css.select('img[data-src]')

    if not os.path.exists(cache_path):
        os.makedirs(cache_path)

    count = len(imgs)
    if count == 0:
        return emojis
    pool = ThreadPool(processes=count)

    for d in imgs:

        src = d['data-src']
        r = re.compile('(\d+)\.\w+$')
        match = r.search(src)
        title = d['alt']
        if match:
            image_name = match.group(1)
        else:
            image_name = title
        key_name = cache_path + image_name
        e = {'url': src, 'path': key_name, 'title': title}
        emojis.append(e)

        if os.path.exists(key_name):
            continue

        pool.apply_async(func=download, args=(src, key_name, headers))
    pool.close()
    pool.join()
    return emojis


def list_emoji_dbbqb(query=None, page=1):
    start = (page - 1) * 100
    url = "https://www.dbbqb.com/api/search/json?start={}&w={}".format(
        start, query)

    headers = {
        "Referer":
        "https://www.dbbqb.com/api/search/json?start=0&w=%E5%9C%A8%E5%90%97",
        "Content-Type": "application/json",
        "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Web-Agent": "web"
    }
    r = requests.get(url, headers=headers)

    # throw an error if request failed, Workflow will catch this and show it to the user
    r.raise_for_status()

    emojis = []
    data = r.json()

    if not os.path.exists(cache_path):
        os.makedirs(cache_path)

    count = len(data)
    if count == 0:
        return emojis
    pool = ThreadPool(processes=count)

    for d in data:

        src = 'https://image.dbbqb.com/' + d['path']
        image_name = d['hashId']
        key_name = cache_path + image_name
        e = {'url': src, 'path': key_name, 'title': image_name}
        emojis.append(e)

        if os.path.exists(key_name):
            continue

        pool.apply_async(func=download, args=(src, key_name, headers))
    pool.close()
    pool.join()
    return emojis


def download(url, out_dir, headers):

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(out_dir, "wb") as f:
            f.write(response.content)
    else:
        logger.debug("图片下载失败")


def main(wf):
    if len(wf.args):
        query = wf.args[0]
    else:
        query = None
    # print('%s', query)
    key = query
    page = 1
    try:
        last_space_index = query.rindex(' ')
        # 用户在末尾输入空格
        if last_space_index == len(query) - 1:
            wf.add_item(title=u'请输入关键词或页码', valid=True, icon=ICON_DEFAULT)
            wf.send_feedback()
            return
        # 用户在末尾输入的是空格和页码数字
        if int_number.match(query[last_space_index + 1:]):
            key = query[0:last_space_index]
            page = int(query[last_space_index + 1:])
        else:
            # 用户在末尾输入的是空格和关键词
            key = query

    except ValueError:
        pass

    def wrapper():
        return list_emoji_dbbqb(key, page)

    # 使用缓存，以查询参数（包括查询关键字和页码）作为缓存的 key，缓存 2 小时
    emojis = wf.cached_data(query, wrapper, max_age=7200)
    # emojis = list_emoji(key, page)

    if len(emojis) <= 0:
        wf.add_item(title=u'未找到表情包', valid=True, icon=ICON_DEFAULT)

    # 添加 item 到 workflow 列表
    for emoji in emojis:
        if 'title' in emoji:
            title = emoji['title']
        else:
            title = emoji['path']
        wf.add_item(title=title,
                    subtitle=emoji['path'],
                    arg=emoji['path'],
                    valid=True,
                    icon=emoji['path'],
                    quicklookurl=emoji['path'])

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3()

    logger = wf.logger

    sys.exit(wf.run(main))
