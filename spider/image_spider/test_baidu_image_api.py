#-*- coding:utf-8 -*-
import json
from unittest import TestCase
import requests
from image_baidu_com import baidu_image_api, get_image_urls

__author__ = 'akira'


class TestBaidu_image_api(TestCase):
    def test_baidu_image_api(self):
        names_without_result = ['！！！！！！！！', 92347527340958273094572, 10848247279349, '!@#$@!#']
        names_with_result = ['张学友', 'Tom Hanks', '新垣 結衣']
        names_invalid = ['', ' ', '/', '&', '=', ':']

        num = 10

        # url_without_result = map(lambda name: baidu_image_api(name, num), names_without_result)
        # url_with_result = map(lambda name: baidu_image_api(name, num), names_with_result)
        # url_invalid = map(lambda name: baidu_image_api(name, num), names_invalid)
        url_without_result, url_with_result, url_invalid = map(lambda nl: map(lambda name: baidu_image_api(name, num),
                                                                              nl),
                                                               [names_without_result, names_with_result, names_invalid])

        def do_test(url_list, predicate):
            for url in url_list:
                parsed_json = json.loads(requests.get(url).text)
                img_urls = get_image_urls(parsed_json)
                assert predicate(len(img_urls))

        do_test(url_without_result, lambda len_of_urls: len_of_urls == 0)
        do_test(url_with_result, lambda len_of_urls: len_of_urls > 0)

        try:
            do_test(url_invalid, lambda len_of_urls: len_of_urls)
        except (requests.RequestException, ValueError):
            pass
