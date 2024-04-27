import json
import re
import time
import pandas as pd
import numpy as np
import requests
from requests.exceptions import RequestException


def procode(x):
    if x[0] == '6':
        return x + '.SH'
    elif x[0] == '8':
        return x + '.BJ'
    else:
        return x + '.SZ'


def get_page(url, ec):
    '''抓取网页'''

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/70.0.3538.77 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers)
        response.encoding = ec  # 编码
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None


'''第x季度机构持仓详情'''


def parse_jigou(page=1, jigoutype=3, zjc=0, tseason='2021-03-31'):
    '''爬取各机构持仓详情'''

    '''
    st 按某一列排序：SCode股票代码 Count持有家数 ShareHDNum持股总数 TabRate占总股本比例(基金是持股市值) ShareHDNumChange持股变动数 RateChange持股变动比例
    sd 排列顺序：1降序 0升序
    jigoutype 机构类型：1基金 2QFII 3社保 4券商 5保险 6信托
    zjc 持仓变动方向：0全部 1增仓 2减仓
    '''
    url = 'http://data.eastmoney.com/dataapi/zlsj/list?date=' + tseason + '&type=' + str(jigoutype) + '&zjc=' + str(
        zjc) + '&sortField=HOLDCHA_RATIO&sortDirec=1&pageNum=' + str(page) + '&pageSize=50&p=' + str(
        page) + '&pageNo=' + str(page)
    html = get_page(url, 'utf-8')
    respJson = json.loads(html)
    codes = [x['SECUCODE'] for x in respJson['data']]  # 代码
    names = [x['SECURITY_NAME_ABBR'] for x in respJson['data']]  # 名称
    types = [x['ORG_TYPE_NAME'] for x in respJson['data']]  # 机构类型
    counts = [x['HOULD_NUM'] for x in respJson['data']]  # 持有家数
    directs = [x['HOLDCHA'] for x in respJson['data']]  # 变动方向
    ratechange = [x['HOLDCHA_RATIO'] for x in respJson['data']]  # 变动比例
    countnum = [float(x['TOTAL_SHARES']) / 10000 for x in respJson['data']]  # 持股总数
    tabrate = [x['TOTALSHARES_RATIO'] for x in respJson['data']]  # 占总股本比例

    result = pd.DataFrame({'证券代码': codes, '证券简称': names, '机构类型': types, '持有家数': counts, '变动方向': directs,
                           '变动比例（%）': ratechange, '持股总数（万股）': countnum, '占总股本比例（%）': tabrate})
    maxpage = respJson['pages']  # 最大页数

    return result, maxpage


def get_jigou(jigoutype=3, zjc=0, tseason='2021-03-31'):
    pagesize = 1
    resultdf, maxpage = parse_jigou(page=pagesize, jigoutype=jigoutype, zjc=zjc, tseason=tseason)
    while pagesize <= maxpage:
        # print(pagesize)
        temp, temppage = parse_jigou(page=pagesize, jigoutype=jigoutype, zjc=zjc, tseason=tseason)
        resultdf = pd.concat([resultdf, temp])
        pagesize += 1
        time.sleep(2)
    return resultdf


def parse_jigou_stock(market='SZ', code='000049', tseason='2021-03-31', last_tseason='2020-12-31'):
    '''爬取各股票某季度十大流通详情'''

    url1 = 'http://emweb.securities.eastmoney.com/ShareholderResearch/PageSDLTGD?code=' + market + str(
        code) + '&date=' + last_tseason
    html1 = get_page(url1, 'utf-8')
    # html1 = ('{' + re.findall('data:.*\]', html1, re.S)[0] + '}').replace('data', '"data"')
    respJson1 = json.loads(html1)
    if len(respJson1['sdltgd']) > 0:
        last_tseason_min = float(respJson1['sdltgd'][-1]['HOLD_NUM']) / 10000  # 上季度十大流通股东最少的持股数量（万股）
        time.sleep(1)
        url2 = 'http://data.eastmoney.com/dataapi/zlsj/detail?SHType=3&SHCode=&SCode=' + str(
            code) + '&ReportDate=' + tseason + '&sortField=HOLDER_CODE&sortDirec=1&pageNum=1&pageSize=30'
        html2 = get_page(url2, 'utf-8')
        respJson2 = json.loads(html2)
        if len(respJson2['data']) > 0:
            if ((max([float(x['TOTAL_SHARES']) for x in
                      respJson2['data']])) / 10000) > last_tseason_min:  # 本季度社保机构最多的持股数量（万股）
                return 1
            else:
                return 0
        else:
            return np.nan
    else:
        return 1


def last_season_period(date):
    '''
    返回date上一季报告期
    '''
    seasons = ['03-31', '06-30', '09-30', '12-31']
    if date[-5:] != '03-31':
        return date[:4] + '-' + seasons[seasons.index(date[-5:]) - 1]
    else:
        return str(int(date[:4]) - 1) + '-12-31'


def get_today_jigou(tseason='2023-06-30'):
    df = pd.DataFrame()
    for stat in [3]:  # range(1, 7)
        df = pd.concat([df, get_jigou(tseason=tseason, jigoutype=stat)])
    df = df.drop_duplicates()
    df = df[
        (df['机构类型'] == '社保') & ((df['变动方向'] != '减仓'))].sort_values('证券代码').reset_index(drop=True)
    df.to_excel(r'机构持仓' + tseason + '.xlsx', index=False)
    # # 本季度新进
    df = pd.read_excel(r'机构持仓' + tseason + '.xlsx', dtype={'证券代码': str})
    test_codes = df[df['变动方向'] == '新进'][
        '证券代码'].sort_values().to_list()  # ####################################### 待测试股票列表
    # # 本季度增持
    dff = pd.read_excel(r'机构增持' + tseason + '.xlsx', dtype={'证券代码': str})
    dff_codes = dff[dff['变动方向'] == '新进']['证券代码'].to_list()
    test_codes = list(set(test_codes) - set(dff_codes))  # ############################################ 剔除已经验证过的股票
    test_codes.sort()
    if len(test_codes) > 0:
        last_tseason = last_season_period(tseason)
        test_codes1 = [x[:6] for x in test_codes]
        test_codes2 = [x[7:] for x in test_codes]
        no_codes = []  # 本季度应该剔除的
        nan_codes = []  # 有出现空值的
        for code, market in zip(test_codes1, test_codes2):
            if parse_jigou_stock(market=market, code=code, tseason=tseason, last_tseason=last_tseason) == 0:
                no_codes.append(code)
                time.sleep(5)
            elif pd.isna(parse_jigou_stock(market=market, code=code, tseason=tseason, last_tseason=last_tseason)):
                nan_codes.append(code)
                time.sleep(5)
        no_codes = [procode(x) for x in no_codes]
        df = df[~(df['证券代码'].isin(no_codes))].copy()
        df1 = pd.concat([df, dff]).drop_duplicates().reset_index(drop=True)
    else:
        df1 = pd.concat([df[df['变动方向'] != '新进'], dff]).drop_duplicates().reset_index(drop=True)
    df1.to_excel(r'机构增持' + tseason + '.xlsx', index=False)
    # df1['证券代码'] = [procode(x) for x in df1['证券代码']]
    # df1['jg_type'] = [1 if x == '社保' else 0 for x in df1['机构类型']]
    # df['jg_type2'] = [2 if x == '保险' else 0 for x in df['机构类型']]
    # df['jg_type'] = df['jg_type1'] + df['jg_type2']
    # df1 = df1[['证券代码', '证券简称', 'jg_type']].drop_duplicates().reset_index(drop=True)
    # df1 = df1.groupby(['证券代码', '证券简称']).sum().reset_index()
    df1 = df1[['证券代码', '证券简称', '持有家数', '变动方向']].drop_duplicates().reset_index(drop=True)
    df1.rename(columns={'持有家数': 'jg_num', '变动方向': 'jg_chg'}, inplace=True)
    df1.to_excel(r'jg.xlsx', index=False)
    return df1
