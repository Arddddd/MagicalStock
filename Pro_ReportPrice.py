import pandas as pd
import numpy as np


def last_nyear(date, n, keywords=''):
    '''
    返回date第前n年报告期
    只针对格式如'2020-12-31'的date
    keywords：''或者'扣非'
    '''
    return keywords + str(int(date[:4]) - n) + '-' + date[-5:]


def last_season(date, keywords=''):
    '''
    返回date上一季报告期
    只针对格式如'2020-12-31'的date
    keywords：''或者'扣非'
    '''

    seasons = ['03-31', '06-30', '09-30', '12-31']
    if date[-5:] != '03-31':
        return keywords + date[:4] + '-' + seasons[seasons.index(date[-5:]) - 1]
    else:
        return keywords + str(int(date[:4]) - 1) + '-12-31'


def last_nlist(date, n, keywords=''):
    '''
    返回date前n个报告期到现在的日期序列
    只针对格式如'2020-12-31'的date
    keywords：''或者'扣非'
    '''

    datecopy = date
    datelist = [keywords + datecopy]
    for nn in range(1, n + 1):
        datecopy = last_season(datecopy)
        datelist.append(keywords + datecopy)
    datelist.reverse()
    return datelist


def init_seasons(date, keywords=''):
    '''
    返回从年初到date的日期序列
    只针对格式如'2020-12-31'的date
    keywords：''或者'扣非'
    '''
    seasons = ['03-31', '06-30', '09-30', '12-31']
    if date[-5:] != '03-31':
        date_list = []
        for i in range(seasons.index(date[-5:]), 0, -1):
            date_list.append(keywords + date[:4] + '-' + seasons[seasons.index(date[-5:]) - i])
        return date_list
    else:
        return [keywords + date]


# ### now_period = '2023-06-30'


def pro_report(now_period):
    cols = ['2017-12-31',
            '2018-03-31', '2018-06-30', '2018-09-30', '2018-12-31', '2019-03-31', '2019-06-30', '2019-09-30',
            '2019-12-31', '2020-03-31', '2020-06-30', '2020-09-30', '2020-12-31', '2021-03-31', '2021-06-30',
            '2021-09-30', '2021-12-31', '2022-03-31', '2022-06-30', '2022-09-30', '2022-12-31', '2023-03-31']
    cols_no = ['扣非' + x for x in cols]

    his_pro = pd.read_excel(r'单季度净利润.xlsx', index_col=0, skipfooter=2)
    his_pro_no = pd.read_excel(r'单季度扣非净利润.xlsx', index_col=0, skipfooter=2)

    del his_pro['名称'], his_pro_no['名称']
    his_pro.columns = cols
    his_pro_no.columns = cols_no

    his_pro = his_pro.replace('--', np.nan)
    his_pro_no = his_pro_no.replace('--', np.nan)

    # his_pro = his_pro / 100000000
    # his_pro_no = his_pro_no / 100000000

    his_pro = his_pro.reset_index()
    his_pro.rename(columns={'代码': '证券代码'}, inplace=True)
    his_pro_no = his_pro_no.reset_index()
    his_pro_no.rename(columns={'代码': '证券代码'}, inplace=True)

    pro = pd.read_excel(r'业绩.xlsx', skipfooter=2)  # , engine='xlrd')
    pro = pro.replace('--', np.nan)
    pro.columns = ['证券代码', '证券简称', '最新报告期', '实际披露期', 'Pettm', '扣非' + now_period,
                   now_period, '预告披露期', '预告报告期', '预告净利润上限', '预告净利润下限', '快报披露期', '快报净利润']
    pro['最新报告期'] = [x if pd.isna(x) else (pd.to_datetime(x)).strftime('%Y-%m-%d') for x in pro['最新报告期']]
    pro['实际披露期'] = [x if pd.isna(x) else (pd.to_datetime(x)).strftime('%Y-%m-%d') for x in pro['实际披露期']]
    pro['预告披露期'] = [x if pd.isna(x) else (pd.to_datetime(x)).strftime('%Y-%m-%d') for x in pro['预告披露期']]
    pro['预告报告期'] = [x if pd.isna(x) else (pd.to_datetime(x)).strftime('%Y-%m-%d') for x in pro['预告报告期']]
    pro['快报披露期'] = [x if pd.isna(x) else (pd.to_datetime(x)).strftime('%Y-%m-%d') for x in pro['快报披露期']]

    for i in ['Pettm', '扣非' + now_period, now_period, '预告净利润上限', '预告净利润下限', '快报净利润']:
        if len(pro[i].value_counts() > 0):
            if ((type(pro[i].value_counts().sort_index().index[0]) != str) and (
                    not (pd.isna(pro[i].value_counts().sort_index().index[0])))):
                pass
            else:
                pro[i] = pro[i].str.replace(',', '').astype(float)
        else:
            pass

    '''############################## pro可以分为 有正式公告 有快报 有预告 没有预告 四个部分 ####################################'''

    # ### 有正式公告 last_nyear(now_period, 1) 直接更新单季度净利润同比、扣非净利润同比、扣非ttm
    pro1 = pro[pro['最新报告期'] == now_period].copy()
    if len(pro1) > 0:
        pro1temp = pro1.merge(his_pro, on='证券代码', how='left')
        pro1temp = pro1temp.merge(his_pro_no, on='证券代码', how='left')
        pro1temp = pro1temp.set_index('证券代码')

        # # 前两年的单季度净利润
        pro_temp = pro1temp[last_nlist(now_period, 8)].T
        pro_temp_ratio = (pro_temp - pro_temp.shift(4)) / abs(pro_temp.shift(4))
        pro_temp_ratio = pro_temp_ratio.iloc[-2:, :].T
        pro_temp_ratio.columns = ['上一期净利润同比', '本期净利润同比']
        pro_temp_ratio = pro_temp_ratio.reset_index()  # 近两季度同比

        # # 前两年的单季度扣非净利润
        pro_no_temp = pro1temp[last_nlist(now_period, 8, '扣非')].T
        pro_no_temp_ratio = (pro_no_temp - pro_no_temp.shift(4)) / abs(pro_no_temp.shift(4))
        pro_no_temp_ratio = pro_no_temp_ratio.iloc[-2:, :].T
        pro_no_temp_ratio.columns = ['上一期扣非净利润同比', '本期扣非净利润同比']
        pro_no_temp_ratio = pro_no_temp_ratio.reset_index()  # 近两季度同比
        pro_no_temp_ttm = pd.DataFrame(pro_no_temp.rolling(4).sum().loc['扣非' + now_period])
        pro_no_temp_ttm.columns = ['扣非净利润ttm（亿）']
        pro_no_temp_ttm = pro_no_temp_ttm.reset_index()  # 扣非ttm

        # # 合并
        pro1 = pro1[['证券代码', '证券简称', '最新报告期', '实际披露期', 'Pettm', '预告披露期', '预告报告期', '快报披露期', '快报净利润']].merge(
            pro_temp_ratio, on='证券代码', how='left')
        pro1 = pro1.merge(pro_no_temp_ratio, on='证券代码', how='left')
        pro1 = pro1.merge(pro_no_temp_ttm, on='证券代码', how='left')
        pro1['正式报告/快报/预告'] = 1
    else:
        pro1 = pd.DataFrame(
            columns=['证券代码', '证券简称', '最新报告期', '实际披露期', 'Pettm', '预告披露期', '预告报告期', '快报披露期', '快报净利润',
                     '上一期净利润同比', '本期净利润同比', '上一期扣非净利润同比', '本期扣非净利润同比', '扣非净利润ttm（亿）', '正式报告/快报/预告'])

    # ### 有快报 init_seasons(now_period) 先算出单季度净利润数据，再更新单季度净利润同比
    pro2 = pro[(pro['最新报告期'] != now_period) & (pro['快报披露期'].notnull())].copy()
    if len(pro2) > 0:
        pro2['最新报告期'] = now_period
        pro2['实际披露期'] = pro2['快报披露期']
        pro2[now_period] = pro2['快报净利润']
        pro2temp = pro2.merge(his_pro, on='证券代码', how='left')
        pro2temp = pro2temp.set_index('证券代码')

        # # 前两年的单季度净利润
        pro_temp = pro2temp[last_nlist(now_period, 8)].T
        pro_temp.loc[now_period] = pro_temp.loc[now_period] - pro_temp.loc[init_seasons(now_period)].sum()
        pro_temp_ratio = (pro_temp - pro_temp.shift(4)) / abs(pro_temp.shift(4))
        pro_temp_ratio = pro_temp_ratio.iloc[-2:, :].T
        pro_temp_ratio.columns = ['上一期净利润同比', '本期净利润同比']
        pro_temp_ratio = pro_temp_ratio.reset_index()  # 近两季度同比

        # # 合并
        pro2 = pro2[['证券代码', '证券简称', '最新报告期', '实际披露期', 'Pettm',
                     '预告披露期', '预告报告期', '快报披露期', '快报净利润']].merge(pro_temp_ratio, on='证券代码', how='left')
        pro2['上一期扣非净利润同比'] = np.nan
        pro2['本期扣非净利润同比'] = np.nan
        pro2['扣非净利润ttm（亿）'] = np.nan
        pro2['正式报告/快报/预告'] = 2
    else:
        pro2 = pd.DataFrame(
            columns=['证券代码', '证券简称', '最新报告期', '实际披露期', 'Pettm', '预告披露期', '预告报告期', '快报披露期', '快报净利润',
                     '上一期净利润同比',
                     '本期净利润同比', '上一期扣非净利润同比', '本期扣非净利润同比', '扣非净利润ttm（亿）', '正式报告/快报/预告'])

    # ### 有预告 init_seasons(now_period) 先算出单季度净利润数据，再更新单季度净利润同比
    pro3 = pro[(pro['最新报告期'] != now_period) & (pro['预告报告期'] == now_period) & (
            pro['快报披露期'].isnull() & (pro['预告净利润上限'].notnull()))].copy()
    if len(pro3) > 0:
        pro3['最新报告期'] = now_period
        pro3['实际披露期'] = pro3['预告披露期']
        pro3[now_period] = (pro3['预告净利润上限'] + pro3['预告净利润下限']) / 2
        pro3temp = pro3.merge(his_pro, on='证券代码', how='left')
        pro3temp = pro3temp.set_index('证券代码')

        # # 前两年的单季度净利润
        pro_temp = pro3temp[last_nlist(now_period, 8)].T
        pro_temp.loc[now_period] = pro_temp.loc[now_period] - pro_temp.loc[init_seasons(now_period)].sum()
        pro_temp_ratio = (pro_temp - pro_temp.shift(4)) / abs(pro_temp.shift(4))
        pro_temp_ratio = pro_temp_ratio.iloc[-2:, :].T
        pro_temp_ratio.columns = ['上一期净利润同比', '本期净利润同比']
        pro_temp_ratio = pro_temp_ratio.reset_index()  # 近两季度同比

        # # 合并
        pro3 = pro3[['证券代码', '证券简称', '最新报告期', '实际披露期', 'Pettm',
                     '预告披露期', '预告报告期', '快报披露期', '快报净利润']].merge(pro_temp_ratio, on='证券代码', how='left')
        pro3['上一期扣非净利润同比'] = np.nan
        pro3['本期扣非净利润同比'] = np.nan
        pro3['扣非净利润ttm（亿）'] = np.nan
        pro3['正式报告/快报/预告'] = 3
    else:
        pro3 = pd.DataFrame(
            columns=['证券代码', '证券简称', '最新报告期', '实际披露期', 'Pettm', '预告披露期', '预告报告期', '快报披露期', '快报净利润',
                     '上一期净利润同比',
                     '本期净利润同比', '上一期扣非净利润同比', '本期扣非净利润同比', '扣非净利润ttm（亿）', '正式报告/快报/预告'])

    # ### 合并
    pro_ = pd.concat([pro1, pro2, pro3])

    # ### 没预告 不更新
    pro0 = pro[~pro['证券代码'].isin(pro_['证券代码'])].copy()
    if len(pro0) > 0:
        pro0temp = pro0.merge(his_pro, on='证券代码', how='left')
        pro0temp = pro0temp.merge(his_pro_no, on='证券代码', how='left')
        pro0temp = pro0temp.set_index('证券代码')
        last_period = last_season(now_period)

        # # 前两年的单季度净利润
        pro_temp = pro0temp[last_nlist(last_period, 8)].T
        pro_temp_ratio = (pro_temp - pro_temp.shift(4)) / abs(pro_temp.shift(4))
        pro_temp_ratio = pro_temp_ratio.iloc[-2:, :].T
        pro_temp_ratio.columns = ['上一期净利润同比', '本期净利润同比']
        pro_temp_ratio = pro_temp_ratio.reset_index()  # 近两季度同比

        # # 前两年的单季度扣非净利润
        pro_no_temp = pro0temp[last_nlist(last_period, 8, '扣非')].T
        pro_no_temp_ratio = (pro_no_temp - pro_no_temp.shift(4)) / abs(pro_no_temp.shift(4))
        pro_no_temp_ratio = pro_no_temp_ratio.iloc[-2:, :].T
        pro_no_temp_ratio.columns = ['上一期扣非净利润同比', '本期扣非净利润同比']
        pro_no_temp_ratio = pro_no_temp_ratio.reset_index()  # 近两季度同比
        pro_no_temp_ttm = pd.DataFrame(pro_no_temp.rolling(4).sum().loc['扣非' + last_period])
        pro_no_temp_ttm.columns = ['扣非净利润ttm（亿）']
        pro_no_temp_ttm = pro_no_temp_ttm.reset_index()  # 扣非ttm

        # # 合并
        pro0 = pro0[['证券代码', '证券简称', '最新报告期', '实际披露期', 'Pettm', '预告披露期', '预告报告期', '快报披露期', '快报净利润']].merge(
            pro_temp_ratio, on='证券代码', how='left')
        pro0 = pro0.merge(pro_no_temp_ratio, on='证券代码', how='left')
        pro0 = pro0.merge(pro_no_temp_ttm, on='证券代码', how='left')
        pro0['正式报告/快报/预告'] = 0
    else:
        pro0 = pd.DataFrame(
            columns=['证券代码', '证券简称', '最新报告期', '实际披露期', 'Pettm', '预告披露期', '预告报告期', '快报披露期', '快报净利润',
                     '上一期净利润同比',
                     '本期净利润同比', '上一期扣非净利润同比', '本期扣非净利润同比', '扣非净利润ttm（亿）', '正式报告/快报/预告'])

    '''############################################ pro_new 处理业绩类型 ##################################################'''

    df = pd.concat([pro_, pro0])
    df['yj_type1'] = [1 if ((x > 0.7) and (y > 0.7)) else 0 for x, y in
                      zip(df['本期净利润同比'], df['上一期净利润同比'])]
    df['yj_type1_nan'] = [1 if ((x > 0.7) and (y > 0.7)) else 0 for x, y in
                          zip(df['本期扣非净利润同比'], df['上一期扣非净利润同比'])]
    df['yj_type2'] = [2 if ((x > 0.4) and (y > 0.4) and (z > 0) and (w < 30)) else 0 for x, y, z, w in
                      zip(df['本期净利润同比'], df['上一期净利润同比'], df['扣非净利润ttm（亿）'], df['Pettm'])]
    df['yj_type2_nan'] = [2 if ((x > 40) and (y > 40) and (z > 0) and (w < 30)) else 0 for x, y, z, w in
                          zip(df['本期扣非净利润同比'], df['上一期扣非净利润同比'], df['扣非净利润ttm（亿）'], df['Pettm'])]

    df1 = pd.read_excel(r'预告.xlsx', skipfooter=2)
    df1.columns = ['证券代码', '证券简称', '最新业绩预告报告期', '业绩预告首次披露日期', '业绩预告最新披露日期', '预告净利润同比增长上限',
                   '预告净利润同比增长下限', '业绩预告类型', '业绩预告变动原因']
    df1 = df1.replace('--', np.nan)
    df1 = df1[(df1['预告净利润同比增长下限']>0) & (df1['业绩预告首次披露日期']!=df1['业绩预告最新披露日期'])]
    df1 = df1[df1['业绩预告类型'] != '续亏']
    df = df.merge(df1[['证券代码', '业绩预告变动原因']], on='证券代码', how='left')
    df['yj_type3'] = [4 if not (pd.isna(x)) else 0 for x in df['业绩预告变动原因']]
    df['yj_type'] = df['yj_type1'] + df['yj_type2'] + df['yj_type3']
    df['yj_type_nan'] = df['yj_type1_nan'] + df['yj_type2_nan'] + df['yj_type3']

    df['扣非净利润ttm（亿）'] = df['扣非净利润ttm（亿）']/100000000
    df = df[['证券代码', '证券简称', '最新报告期', '实际披露期', '预告报告期', '预告披露期', '快报披露期', '正式报告/快报/预告',
             '上一期净利润同比', '本期净利润同比', '上一期扣非净利润同比', '本期扣非净利润同比',
             '扣非净利润ttm（亿）', 'Pettm', 'yj_type', 'yj_type_nan']]
    df = df.sort_values('证券代码')
    df.to_excel(r'yj.xlsx', index=False)

    return df


def pro_price():
    pro = pd.read_excel(r'价格.xlsx', skipfooter=2)
    pro = pro.replace('--', np.nan)
    pro.columns = ['证券代码', '证券简称', '总市值（亿）', '十大流通股比例（%）', '当日收盘价', '120天前收盘价', '250天前收盘价',
                   'MA50D', 'MA150D', 'MA200D', 'MAX250D', 'MIN250D', 'HL20D', 'HL60D', '中信二级']
    pro[ '总市值（亿）'] = pro[ '总市值（亿）']/100000000
    for i in ['总市值（亿）', '当日收盘价', '120天前收盘价', '250天前收盘价', 'MA50D', 'MA150D', 'MA200D', 'MAX250D', 'MIN250D']:
        if ((type(pro[i].value_counts().sort_index().index[0]) != str) and (
                not (pd.isna(pro[i].value_counts().sort_index().index[0])))):
            pass
        else:
            pro[i] = pro[i].str.replace(',', '').astype(float)
    # #　股价强度
    pro['120天前收盘价'] = pro['120天前收盘价'].replace(0, np.nan)
    pro['250天前收盘价'] = pro['250天前收盘价'].replace(0, np.nan)
    pro['strength120'] = pro['当日收盘价'] / pro['120天前收盘价'] - 1
    x = pd.qcut(pro['strength120'].dropna(), 100, labels=False)
    pro['strength120'] = np.nan
    pro.loc[x.index, 'strength120'] = x
    pro['strength250'] = pro['当日收盘价'] / pro['250天前收盘价'] - 1
    x = pd.qcut(pro['strength250'].dropna(), 100, labels=False)
    pro['strength250'] = np.nan
    pro.loc[x.index, 'strength250'] = x
    # # 形态
    pro['qs_type'] = [
        1 if ((a > b) and (a > c) and (a > d) and (b > c) and (b > d) and (a > 1.3 * e) and (a > 0.7 * f)) else 0 for
        a, b, c, d, e, f in
        zip(pro['当日收盘价'], pro['MA50D'], pro['MA150D'], pro['MA200D'], pro['MIN250D'], pro['MAX250D'])]
    pro['sl_type'] = [1 if a > b else 0 for a, b in zip(pro['HL60D'], pro['HL20D'])]

    pro = pro[['证券代码', '证券简称', '中信二级', '十大流通股比例（%）', '总市值（亿）', 'strength120', 'strength250', 'qs_type', 'sl_type']]
    pro = pro.sort_values('证券代码')
    pro.to_excel(r'pr.xlsx', index=False)

    return pro
