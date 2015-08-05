__author__ = 'akira'
import requests
import re

urls = [
        'http://ent.qq.com/c/gangtai_star.shtml',
        'http://ent.qq.com/c/dalu_star.shtml',
        'http://ent.qq.com/c/yazhou_star.shtml'
        ]
re_names = re.compile(r'''<td width=.+?<a href="(http:\/\/datalib\.ent\.qq\.com\/star\/\d+?\/index.shtml)" title=.+? target="_blank">(.+?)</a></div></td>''', re.DOTALL)
def __get_html(url):
    return requests.get(url).text

def __get_name_from_page(html_text):
    results = re_names.findall(html_text)
    return results

def __get_all_url_name_pair():
    star_names = []
    for url in urls:
        html_text = __get_html(url)
        star_names.extend(__get_name_from_page(html_text))
    return star_names

def get_names():
    url_name_pairs = __get_all_url_name_pair()
    for (_, _name) in url_name_pairs:
        yield _name

if __name__ == '__main__':
    for name in get_names():
        print name
