#!usr/bin/env python3
# @File:Hot_Song_List.py
# @Date:2018/05/22
# Author:Cat.1
# encoding:utf-8
import io  
import sys  
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') 

import requests
import re, random
import redis, time
import config
import AES

Page_Start_Url = "/discover/playlist/?order=hot&cat=%E5%85%A8%E9%83%A8&limit=35&offset="
Page_Start     = 35
Raw_Page_Sum   = 0
class Hot_Song_List(object):
    requ_date        = {}
    """
    This is a base sarwl , include class, and use requests.session 
    and requests.get/post
    """
    def __init__(self):
        self.session = requests.session()
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13;rv:57.0) Gecko/20100101 Firefox/57.0',
            'Referer':"http://music.163.com"
        }
        self.post_headers = {
                            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13;rv:57.0) Gecko/20100101 Firefox/57.0',
                            'Referer':"http://music.163.com", 
                            'Content-Type':"application/x-www-form-urlencoded"
                        }
        self.User_List_All = ["用户热门歌单", "/discover/playlist"]
        host               = config.getConfig("database", "dbhost")
        port               = config.getConfig("database", "dbport")
        self.r             = redis.Redis(host=host, port=int(port), decode_responses=True, db = 1)  
        # 连接到1号数据库, 用于储存网易云音乐的用户热门歌单信息
        self.NEMurl        = "http://music.163.com"

    def pre_request(self, url):
        global Page_Start_Url, Page_Start, Raw_Page_Sum

        resp           = self.session.get(url = self.NEMurl + url, headers = self.headers)
        regex          = re.compile(r"\<img class=\"[\w0-9\-]+\" src=\"(.+)\"\/>\n<a title=\"([\｜\✞\♪\(\)\？\?\♡\【\¼\】\/\[\]\丨\s\「\」\|\『\』\——\•\★\"\u4e00-\u9fa5\w\d\s\，\.]+)\" href=\"(.+)\" class=")
        result         = regex.findall(resp.text)
        for i in range(Raw_Page_Sum, Raw_Page_Sum + len(result)):
            self.r.set(str(i), result[i - Raw_Page_Sum][0] + "user_song_list" + result[i - Raw_Page_Sum][1] + "user_song_list" + result[i - Raw_Page_Sum][2])
            self.r.expire(str(i), 3600*12)
        print("Update")
        Raw_Page_Sum   += len(result)
        print(Raw_Page_Sum)
        regex          = re.compile(r"<a href=\"(.+)\" class=\"zpgi\">\d{1,3}</a>")
        Page_Url       = regex.findall(resp.text)

        Limit_Max_Page = int(re.findall(r'offset=(\d{2,5})', Page_Url[-1])[0])
        if Page_Start <= Limit_Max_Page:
            Page_Start += 35
            url = Page_Start_Url + str(Page_Start)
            time.sleep(1)
            print("这是page = ", Page_Start)
            test.pre_request(url)
        else:
            return 1

    def Random_Return_func(self):
        global re_date
        self.requ_date = {}
        Random_Max = self.r.dbsize()
        for i in range(0, 6):
            music_data = {}
            
            User_Song_List = self.r.get(str(random.sample(range(0, Random_Max), 1)[0]))
            music_data.update({
                                "image_url":User_Song_List.split("user_song_list")[0],\
                                 "title": User_Song_List.split("user_song_list")[1], \
                                 "song_list_url": self.NEMurl + User_Song_List.split("user_song_list")[2]
                                 })
            self.requ_date.update({str(i) : music_data})
        return self.requ_date
    
    def top_songlist(self, url):

        self.requ_date = {}
        """
        这是用来下载top_songlist的热门排行版的方法
        并向前端返回歌曲的id,歌手, 歌名的信息
        """
        date = "{\'id\': %s, \'total\': \'true\',\'csrf_token\
        \':\"\", \'limit\': 1000, \'n\': 1000, \'offset\': 0}"
        Song_List_Id = re.findall(r"id=(\d{1,15})", url)
        date = AES.encrypted_request(date %(Song_List_Id[0]))
        try:
            connection = self.session.post(url = "http://music.163.com/weapi/v3/playlist/detail",
                                       data = date,
                                       headers=self.post_headers,
                                       )
        except:
            return 0
        else:
            try:
                music_data = {}
                connection = connection.json()
                num = len(connection["playlist"]['tracks'])
                music_data = {"creator":connection["playlist"]['creator'], "Songlist_detail":connection["playlist"]['tracks'], "description":connection["playlist"]['description'], "song_num":num}
            except:
                music_data = {"status":"没有该歌单!"}
            self.requ_date.update(music_data)
            return self.requ_date


if __name__ == "__main__":
    
    test = Hot_Song_List()
    while 1:
        test.pre_request(test.User_List_All[1])
        time.sleep(3600 * 12)

    # print(test.top_songlist("https://music.163.com/m/playlist?id=2196054076"))