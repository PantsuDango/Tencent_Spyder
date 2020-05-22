'''
file: Tencent_Spyder.py
encoding: utf-8
data: 2019.12.25
name: xxx
email: xxx
introduction: 爬取腾讯视频-电影-电影片库的电影信息，并根据电影评分生成柱状图
url: https://v.qq.com/channel/movie?listpage=1&channel=movie&sort=18&_all=1
'''


import pymysql
import requests
import re
import sys,os
import time
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


def mysql_preset(password):

    '''
       Mysql预设
       使用root用户本地连接mysql，新建一个Tencent库，并在该库中新建一张movies表，
       用于存储之后爬取到的所有电影数据
       Args:
            password：登录root用户用的密码
       Returns：
               cur：创建好的游标对象
               db：与mysql建立连接的对象
    '''

    # root用户登录与mysql建立连接
    db = pymysql.connect(host='localhost', user='root', password=password, charset='UTF8MB4')
    # 创建游标对象
    cur = db.cursor()
    # 新建Tencent库
    cur.execute('create database Tencent character set UTF8MB4')
    # 进入Tencent库
    cur.execute('use Tencent')
    print('\n>>> 创建Tencent库成功\n')

    # 新建movies表
    cur.execute('create table movies\
    (id int primary key auto_increment,\
    电影名称 varchar(30),\
    主演 varchar(100),\
    播放量 varchar(30))\
    character set UTF8MB4;')

    print('>>> 在Tencent库中创建movies表成功\n')
    return cur,db


def respone(url):

    '''
       目标页面发起请求并获取响应
       Args:
            url：目标页面
       Returns：
               html：目标页面返回的源码
    '''

    # 模拟谷歌浏览器请求头
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"}
    # 发请求并获取响应
    res = requests.get(url, headers=headers ,timeout=10)
    # 改变编码格式
    res.encoding = 'utf-8'
    # 获取源码
    html = res.text

    return html


def re_html(html,movies_name,actors_name,view_counts):

    '''
       正则匹配页面源码获取关键数据
       Args:
            html：用于匹配的源码数据
            movies_name：存所有电影名称
            actors_name：存所有主演名单
            view_counts：存所有播放量
       Returns：
               movies_name：存所有电影名称
               actors_name：存所有主演名单
               view_counts：存所有播放量
    '''

    # 正则匹配目标页面
    datas = re.findall(r'html" target="_blank" title="(.+?)".+?"figure_desc" title="(.+?)">.+?svg_icon_play_sm"></use></svg>(.+?)</div>',html,re.S)

    for data in datas:
        movies_name.append(data[0])  # 存电影名称
        actors_name.append(data[1][3:])  # 存主演
        view_counts.append(data[2])  # 存播放量

    return movies_name,actors_name,view_counts


def mysql_insert(cur,movies_name,actors_name,view_counts):

    '''
       将所有数据写入Mysql数据库中
       Args:
            cur：与数据库建立连接的游标对象
            movies_name：存所有电影名称
            actors_name：存所有主演名单
            view_counts：存所有播放量
       Returns：
               failure_count：写入失败的记录数
    '''

    failure_count = 0  # 存写入失败的记录
    # 将电影信息逐个写入movies表中
    for movie_name,actor_name,view_count in zip(movies_name,actors_name,view_counts):
        try:
            cur.execute("insert into movies values(null,'''%s''','''%s''','''%s''');"%(movie_name,actor_name,view_count))
        except Exception as error:
            print('>>> %s %s %s 写入movies表中失败'%(movie_name,actor_name,view_count))
            print('>>> 原因：%s\n'%error)
            failure_count += 1

    return failure_count


def bar_chart(view_counts):

    # 正常显示中文标签
    mpl.rcParams["font.sans-serif"] = ["SimHei"]
    mpl.rcParams["axes.unicode_minus"] = False

    count_1 = 0 #存播放量5亿以上的电影数量
    count_2 = 0 #存播放量3-5亿的电影数量
    count_3 = 0 #存播放量1-3亿的电影数量
    count_4 = 0 #存播放量5千-1亿的电影数量
    count_5 = 0 #存播放量1千-5千的电影数量
    count_6 = 0 #存播放量1千以下的电影数量

    # 播放量数据分析
    for view_count in view_counts:
        if view_count[-1] == '亿':
            view = int(view_count.replace('亿',''))
            if view >= 5:
                count_1 += 1
            elif 3 <= view < 5:
                count_2 += 1
            elif 1 <= view < 3:
                count_3 += 1
        elif view_count[-1] == '万':
            view = int(view_count.replace('万',''))
            if 5000 <= view < 10000:
                count_4 += 1
            elif 1000 <= view < 5000:
                count_5 += 1
            elif view < 1000:
                count_6 += 1

    x = np.arange(6)  # x轴条形图个数
    # x轴说明文字
    tick_label = ['5亿以上','3-5亿','1-3亿','5千-1亿','1千-5千','1千以下']
    y = []  # y轴
    y.append(count_1)
    y.append(count_2)
    y.append(count_3)
    y.append(count_4)
    y.append(count_5)
    y.append(count_6)

    plt.figure(figsize=(10,12))  # 控制画布大小
    bar_width = 0.5  # 控制条形柱宽度

    # align控制条形柱位置
    # color控制条形柱颜色
    # label为该条形柱对应图示
    # alpha控制条形柱透明度
    plt.bar(x, y, bar_width, align="center", color="c", alpha=0.5)
    # 控制x轴显示什么
    plt.xticks(x, tick_label)
    # 控制x轴刻度距离
    plt.xlim(-0.5,6)
    plt.title('电影播放量统计图',fontsize=20)
    #plt.show()  # 是否打开图形输出器，如有需要再打开
    # 当前文件路径
    path = os.path.dirname(sys.argv[0])
    plt.savefig(path + '\\' + '电影播放量统计图.png')  # 保存为当前目录下的图片
    plt.clf()  #关闭图形编辑器


def main():

    '''主循环'''

    password = input('\n>>> 请输入root用户的密码：')
    try:
        cur,db = mysql_preset(password)
    except Exception as error1:
        print('\n>>> 数据库预设失败，请避免以下问题后重试：')
        print('>>> 1.root用户密码不正确')
        print('>>> 2.Mysql服务处于开启状态')
        print('>>> 3.已存在名为Tencent的库')
        print('>>> 4.CBA库中已存在名为movies的表')
        print('>>> 原因：%s\n'%error1)
        sys.exit()  # 结束程序

    movie_count = int(input(">>> 请输入你要爬取的电影数量："))
    pages = movie_count // 30
    print('\n>>> 开始爬取电影信息...  预计耗时：%d 秒\n'%((pages+1)*2))

    movies_name = []  # 存所有电影名称
    actors_name = []  # 存所有主演名单
    view_counts = []  # 存所有播放量
    success = 0  # 存爬取成功的电影数

    for page in range(pages+1):

        offset = page * 30
        url = 'https://v.qq.com/x/bu/pagesheet/list?_all=1&append=1&channel=movie&listpage=2&offset=%d&pagesize=30&sort=18'%offset

        try:
            html = respone(url)
        except Exception as error2:
            print('>>> %s 页面爬取失败'%url)
            print('>>> 原因：%s\n'%error2)
        else:
            movies_name,actors_name,view_counts = re_html(html,movies_name,actors_name,view_counts)
            print('>>> %s 页面爬取成功'%url)

            if page ==  pages:
                success += movie_count % 30
            else:
                success += 30

            #每次爬取睡眠2秒
            time.sleep(2)

    print('\n>>> 爬取完毕，成功爬取了%d部电影信息，失败%d部\n'%(success, movie_count-success))

    movies_name = movies_name[:movie_count]
    actors_name = actors_name[:movie_count]
    view_counts = view_counts[:movie_count]

    print('>>> 数据开始写入数据库...\n')
    failure_count = mysql_insert(cur,movies_name,actors_name,view_counts)
    print('>>> 数据已全部写入Tencent库中的movies表')
    print('>>> 成功写入%d条，失败%d条\n'%(success-failure_count,failure_count))

    print('>>> 开始生成统计图表...')
    bar_chart(view_counts)
    print('>>> 根据电影播放量的统计图表生成完毕 ---> 电影播放量统计图.png\n')

    #提交数据库
    db.commit()
    #关闭游标对象
    cur.close()
    #关闭数据库连接
    db.close()


if __name__ == '__main__':

    main()