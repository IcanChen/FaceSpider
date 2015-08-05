import json
import shutil

import requests
import os

import sys
import os
import time
import threading
import cProfile
import pstats
from Queue import Queue
reload(sys)
sys.setdefaultencoding("utf-8")


# make script runable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from spider.name_spider.ent_qq_com import get_names

__author__ = 'akira'

urls_queue = Queue()


class UrlsProducer(threading.Thread):
    def run(self):
        names = get_names()
        range_ = [names.next() for _ in range(1000)][-60:]
        print range_
        for name in range_:
            if isinstance(name, unicode):
                name = name.encode('utf-8')
            for url in get_image_urls(self.__get_json_data(name)):
                urls_queue.put([name, url])

    def __get_json_data(self, name):
        # json_url = image_baidu_json_api(name)
        json_url = baidu_image_api(name, 60)
        try:
            parsed_json = json.loads(requests.get(json_url).text)
        except (ValueError, requests.RequestException) as e:
            parsed_json = {'imgs': []}
        return parsed_json


class UrlsConsumer(threading.Thread):
    def __init__(self):
        super(UrlsConsumer, self).__init__()
        self.__start_flag = False

    def run(self):
        while True:
            if urls_queue.empty():
                time.sleep(0.5)
                if urls_queue.empty():
                    if self.__start_flag:
                        break
                    else:
                        continue
            url_name = urls_queue.get()
            download_image(url_name[0], url_name[1])
            self.__start_flag = True


def baidu_image_api(search_name, image_numbers=60, image_size='large', face_picture=True, category='star'):
    if image_size == 'large':
        img_size = 3
    elif image_size == 'medium':
        img_size = 2
    elif image_size == 'small':
        img_size = 1
    elif image_size == 'xlarge':
        img_size = 9
    else:
        img_size = 3
    if face_picture:
        face = 1
    else:
        face = 0

    if not isinstance(image_numbers, int):
        try:
            image_numbers = int(image_numbers)
        except ValueError:
            image_numbers = 60

    if not isinstance(face_picture, bool):
        face_picture = True

    if not isinstance(category, (str, unicode)):
        category = 'star'

    base_api = 'http://image.baidu.com/search/avatarjson?tn=resultjsonavatarnew&ie=utf-8\
&word={search_name}&cg={category}&pn=1&rn={image_numbers}&itg=0&z={img_size}&face={face}\
&fr=&width=&height=&lm=-1&ic=0&s=0&st=-1&gsm=3c'
    return base_api.format(**locals())

baidu_image_api_old = lambda name: '''http://image.baidu.com/search/avatarjson\
?tn=resultjsonavatarnew&ie=utf-8&word={}\
&cg=star&pn=1&rn=60&itg=0&z=3&face=1&fr=&width=&height=&lm=-1&ic=0&s=0&st=-1&gsm=3c'''.format(name)

base_dir = os.path.expanduser("~/Pictures/baidu_face/")

error_num = 0


def download_image(name, url):
    global error_num
    name_dir = os.path.join(base_dir, name)
    _, ext_name = os.path.splitext(url)
    print name_dir, url, ext_name

    try:
        response = requests.get(url, stream=True, timeout=5)
    except Exception:
        error_num += 1
        return
    if not response.status_code == 200 or ext_name is None:
        error_num += 1
        return

    if not os.path.isdir(name_dir):

        try:
            os.mkdir(name_dir)
        except Exception, ex1:
            print ex1
            pass
        idx = 0
    else:
        idx = len(os.listdir(name_dir))

    filename = os.path.join(name_dir, "{name}_{idx:04}{ext}".format(name=name,
                                                                    idx=idx,
                                                                    ext=ext_name))
    try:
        with open(filename, 'w') as fp:
            # response.raw.decode_content = True
            shutil.copyfileobj(response.raw, fp)
    except Exception, ex2:
        print ex2
        pass


def get_image_urls(json_data):
    return [img_dict['objURL'] for img_dict in json_data['imgs']]


def main():
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)
    consumers = []
    producers = []


    p = UrlsProducer()
    p.start()

    for i in xrange(60):
        c = UrlsConsumer()
        c.start()
        consumers.append(c)

    # for producer in producers:
    #     producer.join()
    for consumer in consumers:
        consumer.join()


if __name__ == '__main__':
    #main()
    cProfile.run('main()', os.path.expanduser('~/image.txt'))
    p = pstats.Stats(os.path.expanduser("~/image.txt"))
    p.sort_stats("time").print_stats()