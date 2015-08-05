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
from Queue import Queue, Empty
from threading import Lock
reload(sys)
sys.setdefaultencoding("utf-8")


# make script runable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from spider.name_spider.ent_qq_com import get_names

__author__ = 'akira'

urls_queue = Queue(200)


class UrlsProducer(threading.Thread):
    def __init__(self, exit_event, name):
        super(UrlsProducer, self).__init__(name=name)
        self.exit_event = exit_event
        self.exit_event.clear()

    def run(self):
        names = get_names()
        range_ = [names.next() for _ in xrange(1000)][-60:]
        for name in range_:
            if isinstance(name, unicode):
                name = name.encode('utf-8')
            for url in get_image_urls(self.__get_json_data(name)):
                urls_queue.put([name, url])
        self.exit_event.set()
        print 'exit........thread name=%s' % self.name

    def __get_json_data(self, name):
        # json_url = image_baidu_json_api(name)
        json_url = baidu_image_api(name, 60)
        try:
            print 'get ->',
            parsed_json = json.loads(requests.get(json_url, timeout=10).text)
            print '<- get'
        except (ValueError, requests.RequestException) as e:
            parsed_json = {'imgs': []}
        except Exception, ex:
            parsed_json = {'imgs': []}
        return parsed_json


class UrlsConsumer(threading.Thread):
    def __init__(self, exit_event, name):
        super(UrlsConsumer, self).__init__(name=name)
        self.exit_event = exit_event

    def run(self):
        while True:
            try:
                url_name = urls_queue.get(block=False)
                download_image(*url_name)
            except Empty:
                if self.exit_event.is_set():
                    break
                pass
            except Exception, ex:
                print 'exception in UrlsConsumer:', ex
            threading._sleep(0.1)
        print 'exit........thread name=%s' % self.name


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
total_num = 0
error_lock = threading.Lock()
total_lock = threading.Lock()


def download_image(name, url):
    global error_num, total_num
    name_dir = os.path.join(base_dir, name)
    _, ext_name = os.path.splitext(url)
    print name_dir, url, ext_name

    try:
        # print 1,
        response = requests.get(url, stream=False, timeout=10)
    except Exception, ex:
        error_lock.acquire(1)
        error_num += 1
        error_lock.release()
        return

    if not response.status_code == 200 or ext_name is None:
        error_lock.acquire(1)
        error_num += 1
        error_lock.release()
        return

    if not os.path.isdir(name_dir):
        try:
            os.mkdir(name_dir)
        except Exception, ex1:
            print 'Exception in mkdir', ex1
            pass
        idx = 0
    else:
        idx = len(os.listdir(name_dir))

    filename = os.path.join(name_dir, "{name}_{idx:04}{ext}".format(name=name,
                                                                    idx=idx,
                                                                    ext=ext_name))
    try:
        with open(filename, 'w') as fp:
            shutil.copyfileobj(response.raw, fp)
        total_lock.acquire(1)
        total_num += 1
        total_lock.release()
        if total_num % 10 == 0:
            print 'total image num = %d, clock=%4.4f' % (total_num, time.clock())
    except Exception, ex2:
        print 'Exception in copy file obj', ex2
        pass



def get_image_urls(json_data):
    return [img_dict['objURL'] for img_dict in json_data['imgs']]


def main():
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)
    consumers = []
    # producers = []

    exit_event = threading.Event()

    p = UrlsProducer(exit_event, 'UrlsProducer_00')
    p.start()

    for i in xrange(120):
        c = UrlsConsumer(exit_event, 'UrlsConsumer_%02d' % i)
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
