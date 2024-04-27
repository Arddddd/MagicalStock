import json
import re
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
from requests.exceptions import RequestException

cookie = 'qgqp_b_id=3e1faecd5293f0d60ea45f6de94e6aab; em-quote-version=topspeed; em_hq_fls=js; _qddaz=QD.mn7w0m.kw6hwy.kvzer3t4; ' \
         'xsb_history=870446%7CST%u6052%u6CF0; intellpositionL=652px; intellpositionT=455px; emhq_picfq=1; ' \
         'HAList=a-sh-603816-%u987E%u5BB6%u5BB6%u5C45%2Cty-116-06199-%u8D35%u5DDE%u94F6%u884C%2Cty-1-000001-%' \
         'u4E0A%u8BC1%u6307%u6570%2Ca-sh-603866-%u6843%u674E%u9762%u5305%2Ca-sz-002179-%u4E2D%u822A%u5149%u7535%2Ca-sh-600057-%' \
         'u53A6%u95E8%u8C61%u5C7F%2Ca-sh-601156-%u4E1C%u822A%u7269%u6D41%2Ca-sz-002673-%u897F%u90E8%u8BC1%u5238%2Ca-sz-000538-%' \
         'u4E91%u5357%u767D%u836F%2Cty-1-000300-%u6CAA%u6DF1300%2Ca-sh-601162-%u5929%u98CE%u8BC1%u5238; st_si=74119052993981; ' \
         'st_asi=delete; JSESSIONID=5567287D4979D3CEE73742B353C0919D; st_pvi=16602812083173; st_sp=2021-06-28%2008%3A00%3A18; ' \
         'st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; st_sn=4; st_psi=20220913143654515-113300302015-6975486531'

def get_page(url, ec):
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip,deflate,br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Cookie': cookie,
        'Host': 'datacenter-web.eastmoney.com',
        'Referer': 'https://data.eastmoney.com/',
        'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'script',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.encoding = ec  # 编码
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None


def procode(x):
    if x[0] == '6':
        return x + '.SH'
    else:
        return x + '.SZ'


def sumdf(df, cols):
    for col in cols:
        df[col + '_sum'] = sum(df[col].astype(int))
    return df


'''近一个月龙虎榜机构席位买卖详情'''


def parse_longhu(page=1):
    # url = 'http://data.eastmoney.com/DataCenter_V3/stock2016/DailyStockListStatistics/' \
    #       'pagesize=50,page=' + str(page) + ',sortRule=-1,sortType=PBuy,startDate=' + begindate + \
    #       ',endDate=' + enddate + ',gpfw=0,js=var%20data_tab_2.html'

    url = 'https://datacenter-web.eastmoney.com/api/data/v1/get?callback=jQuery112305224044302812088_1663051014245&' \
          'sortColumns=BILLBOARD_TIMES%2CLATEST_TDATE%2CSECURITY_CODE&sortTypes=-1%2C-1%2C1&' \
          'pageSize=50&pageNumber=' + str(page) + '&reportName=RPT_BILLBOARD_TRADEALL&columns=ALL&' \
                                                  'source=WEB&client=WEB&filter=(STATISTICS_CYCLE%3D%2201%22)' # STATISTICS_CYCLE%3D%2201%22 近一个月

    html = get_page(url, 'utf-8')
    html1 = re.findall('\{.*\}', html, re.S)[0] # + '}'
    html1 = html1.replace("\n", "\\n").replace("\r", "\\r").replace("\n\r", "\\n\\r").replace("\r\n", "\\r\\n").replace(
        "\t", "\\t").replace("\t\r", "\\t\\r").replace("\r\t", "\\r\\t").replace("\\", "\\\\")
    respJson = json.loads(html1)
    codes = [x['SECUCODE'] for x in respJson['result']['data']]  # 代码
    names = [x['SECURITY_NAME_ABBR'] for x in respJson['result']['data']]  # 名称
    highdate = [x['LATEST_TDATE'] for x in respJson['result']['data']]  # 上榜日期
    buyers = [x['ORG_BUY_TIMES'] for x in respJson['result']['data']]  # 买方机构数
    sellers = [x['ORG_SELL_TIMES'] for x in respJson['result']['data']]  # 卖方机构数
    netbuy = [float(x['ORG_NET_BUY']) / 10000 for x in respJson['result']['data']]  # 买入净额（万元）
    # pbrate = [x['PBRate'] for x in respJson['data']]  # 机构净买入额占总成交额占比（%）

    result = pd.DataFrame({'证券代码': codes, '证券简称': names, '上榜日期': highdate, '买方机构数': buyers, '卖方机构数': sellers,
                           '买入净额（万元）': netbuy})
    maxpage = respJson['result']['pages']  # 最大页数
    return result, maxpage


def get_longhu(page=1):
    pagesize = 1
    resultdf, maxpage = parse_longhu(page=pagesize)
    while pagesize <= maxpage:
        temp, temppage = parse_longhu(page=pagesize)
        resultdf = pd.concat([resultdf, temp])
        pagesize += 1
        time.sleep(2)

    return resultdf


########################################################################################################################


def get_today_longhu():
    # enddate = datetime.today().strftime('%Y-%m-%d')
    # begindate = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')

    df = get_longhu()
    # df['证券代码'] = [procode(x) for x in df['证券代码']]
    df = df.drop_duplicates()
    df = df[df['买入净额（万元）'] != 0]
    df = df.sort_values(['证券代码', '上榜日期', '买方机构数'], ascending=False).reset_index(drop=True)

    # df = df.groupby(['证券代码']).apply(lambda x: sumdf(x, ['买方机构数', '卖方机构数', '买入净额（万元）']))
    # df = df[['证券代码', '证券简称', '上榜日期', '买方机构数_sum', '卖方机构数_sum', '净买入金额（万元）']].drop_duplicates(['证券代码']).reset_index(
    #     drop=True)
    df.to_excel(r'lh.xlsx', index=False)

    return df
