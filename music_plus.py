import requests     #发送网络请求
import json
import prettytable as pt
import pymysql as mysql
import pandas as pd

name = input('请输入歌手或歌曲名：')
#1. 发送请求 向搜索功能接口发送请求 注意前面的f
url = f'https://c.y.qq.com/soso/fcgi-bin/client_search_cp?p=1&n=10&w={name}'
response = requests.get(url)
#<response [200]：请求成功

#2. 获取数据 获取所有歌曲信息数据
json_str = response.text
# print(response.text)

#3. 解析数据 如歌曲 歌手名 专辑 歌曲mid
#字符串切片,去掉callback ()的无用信息,-1为倒数第二位
json_str = json_str[9:-1]
# print(json_str)

#4. str转为json/字典
json_dict = json.loads(json_str)

#python字典取值
#通过['键']获取值，键值对
song_list = json_dict['data']['song']['list']
tb = pt.PrettyTable()
tb.field_names = ['序号','歌名','歌id','歌mid','歌手','歌手id','歌手mid','专辑','专辑id','专辑mid','流派','语种','发行时间','链接']

#待插入的信息
album_info_list = []
music_album = []
music_info_list = []
music_singer = []
singer_info_list = []
count = 0

#数据库连接
con = mysql.connect(host="127.0.0.1",port=3306,user="root",passwd="123456",db="music_plus",charset="utf8")
#生成游标对象
cur = con.cursor()
#sql语句
a_insert_sql = "insert ignore into album values (%s,%s,%s)"
ma_insert_sql = "insert into music_album values (null,%s,%s)"
m_insert_sql = "insert ignore into music values (%s,%s,%s,%s,%s)"
ms_insert_sql = "insert into music_singer values (null,%s,%s)"
s_insert_sql = "insert ignore into singer values (%s,%s,%s)"
l_inser_sql = "insert into language(id, language) select null, %s from DUAL where not exists (select id from language where language = %s)"
t_inser_sql = "insert into type(id, typename) select null, %s from DUAL where not exists (select id from type where typename = %s)"
ml_insert_sql = "insert into music_language values (null,%s,%s)"
mt_insert_sql = "insert into music_type values (null,%s,%s)"

#5. 格式化输出
for song in song_list:
    albumname = song['albumname']
    albumid = song['albumid']
    albummid = song['albummid']
    singername = song['singer'][0]['name']
    singerid = song['singer'][0]['id']
    singermid = song['singer'][0]['mid']
    songname = song['songname']
    songid = song['songid']
    songmid = song['songmid']
    url2 = f'http://localhost:3200/getSongInfo?songmid={songmid}'
    url3 = f'http://localhost:3200/getMusicPlay?songmid={songmid}'
    response2 = requests.get(url2)
    response3 = requests.get(url3)
    json_str2 = response2.text
    json_str2 = json_str2[12:-1]
    json_str3 = response3.text
    json_str3 = json_str3[8:-1]
    json_dict2 = json.loads(json_str2)
    json_dict3 = json.loads(json_str3)
    # print(len(json_dict3['playUrl'][songmid]['url']))
    songurl = json_dict3['playUrl'][songmid]['url']     #播放地址
    info = json_dict2['songinfo']['data']['info']
    genre = info['genre']['content'][0]['value']        #流派
    lan = info['lan']['content'][0]['value'].replace(' ','')   #语种
    pub_time = info['pub_time']['content'][0]['value']  #发行
    # print(songmid,songname,singer,albumname)
    tb.add_row([count, songname,songid, songmid, singername, singerid, singermid, albumname,albumid,albummid,genre,lan,pub_time,songurl])
    cur.execute(a_insert_sql, [albumid, albummid, albumname])
    cur.execute(m_insert_sql, [songid, songmid, songname, pub_time, songurl])
    cur.execute(s_insert_sql, [singerid, singermid, singername])
    cur.execute(ms_insert_sql, [songid, singerid])
    cur.execute(ma_insert_sql, [songid, albumid])

    cur.execute(l_inser_sql, [lan, lan])
    l_query_sql = "select id from language where language = %s"
    cur.execute(l_query_sql, [lan])
    lanid = cur.fetchall()[0][0]
    cur.execute(ml_insert_sql, [songid, lanid])

    cur.execute(t_inser_sql, [genre, genre])
    t_query_sql = "select id from type where typename = %s"
    cur.execute(t_query_sql, [genre])
    typeid = cur.fetchall()[0][0]
    cur.execute(mt_insert_sql,[songid,typeid])

    album_info_list.append([albumid,albummid,albumname])
    music_album.append([songid,albumid])
    music_info_list.append([songid,songmid,songname,genre,lan,pub_time])
    music_singer.append([songid,singerid])
    singer_info_list.append([singerid, singermid, singername])
    count += 1

print(tb)
# print(album_info_list)
# print(music_album)
# print(music_info_list)
# print(music_singer)
# print(singer_info_list)

cur.close()
con.commit()
con.close()