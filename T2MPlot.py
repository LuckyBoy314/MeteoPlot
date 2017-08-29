# -*- coding:utf-8 -*-

import datetime
import os, time
from math import sqrt, fabs

import cPickle as pickle
from collections import OrderedDict

import pandas as pd

from bokeh.plotting import figure, output_file, save, ColumnDataSource  # ,show
from bokeh.models import Range1d, Span, BoxAnnotation, HoverTool, DatetimeTicker, DatetimeTickFormatter
from bokeh.models.widgets import Panel, Tabs

from pyMicaps import Diamond4

def searchProductFiles(date_time, directories):
    """
    按照起报时间搜索相应文件
    :param date_time: 起报时间
    :param directories: 搜索目录，要提供产品的最终目录
    :return:
    """
    files_list = []  # os.path.join(root,f)
    for dir in directories:
        for root, dirs, files in os.walk(dir, topdown=True):
            if files:  # 当files不为空的时候，root为存储数据的最终目录
                files_list.extend(
                    [os.path.join(root, f) for f in files
                     if f.startswith(date_time) and f not in [os.path.basename(each) for each in files_list]]
                )  # 前面目录中的模式产品文件优先

    return files_list


def plot_2T(date_time, stations, models):
    """

    :param date_time: 必须是'YYMMDDHH'形式
    :param stations:
    :param models:
    :return:
    """
    tabs = []
    output_file('D:/MICAPSData/TempForecast/2T_Forecast.html', title=u'2米温度预报', mode='inline')

    names = [name for name in stations] + ['date_time_X', 'date_time_str']
    tools_to_show = 'hover,box_zoom,pan,save,resize,reset,wheel_zoom'
    colors = ['red', 'blue', 'green', 'orange', 'yellow', 'purple', 'pink']

    for model in models:

        # 处理u'河南WRF_RUC'的'YYYYMMDDHH'形式
        if model == u'河南WRF_RUC':
            date_time_condition = (
            datetime.datetime.strptime('20' + date_time, '%Y%m%d%H') - datetime.timedelta(hours=8)).strftime(
                '%Y%m%d%H')
        else:
            date_time_condition = date_time

        data = []
        files_list = searchProductFiles(date_time_condition, models[model])

        for each in files_list:
            d = Diamond4(each)
            lon_lat_s = [stations[name][1] for name in stations]
            extracted_values = d.IDW(lon_lat_s)

            # 处理时间索引
            date_time_index = d.valid_time
            if model in [u'河南WRF_RUC', u'GRAPES_GFS', u'GRAPES_MESO', u'T639粗']:
                date_time_index += datetime.timedelta(hours=8)

            # 注意bokeh在将时间对象作为X轴时会将本地时间转换为世界时，为了避免这种转换，需要再本地时间上再加上8h（北京时比世界时快8h）
            extracted_values.extend(
                [date_time_index + datetime.timedelta(hours=8), date_time_index.strftime("%m/%d %Hh")])
            data.append(pd.DataFrame(extracted_values, index=names).T)

        # 如果没有数据，则返回，防止出错
        if not data:
            continue

        df = pd.concat(data).sort_values('date_time_X', ascending=False)
        del data

        n_series = len(df)

        p = figure(plot_width=1920 - 140, plot_height=1200 - 250,
                   x_axis_type="datetime", tools=tools_to_show, active_scroll="wheel_zoom")

        # 分别为每个站点绘制时间序列变化曲线
        for name, color in zip(stations, colors):
            source = ColumnDataSource(data={
                'dateX': df['date_time_X'],
                'v': df[name],
                'dateX_str': df['date_time_str'],
                'name': [name for n in xrange(n_series)]
            })

            p.line('dateX', 'v', color=color, legend=name, source=source)
            circle = p.circle('dateX', 'v', fill_color="white", size=8, color=color, legend=name, source=source)
            p.tools[0].renderers.append(circle)

        # 图例显示策略
        p.legend.click_policy = "hide"
        # 显示标签
        hover = p.select(dict(type=HoverTool))
        hover.tooltips = [(u"温度", "@v{0.0}"), (u"站点", "@name"), (u"时间", "@dateX_str")]
        hover.mode = 'mouse'

        # 标题设置
        if model == u'EC细 2TMax_3h':
            title = ' '.join([date_time, u'EC细', u'过去3小时2米最高温度预报'])
        elif model == u'EC细 2TMin_3h':
            title = ' '.join([date_time, u'EC细', u'过去3小时2米最低温度预报'])
        else:
            title = ' '.join([date_time, model, u'2米温度预报'])
        p.title.text = title

        p.title.align = "center"
        p.title.text_font_size = "25px"
        # p.title.background_fill_color = "#aaaaee"
        # p.title.text_color = "orange"
        p.xaxis.axis_label = u'日期/时间'
        p.yaxis.axis_label = u'温度(℃)'

        p.xaxis[0].formatter = DatetimeTickFormatter(hours=['%m/%d %Hh', '%m/%d %H:%M'], days=['%m/%d %Hh'])
        p.xaxis[0].ticker = DatetimeTicker(desired_num_ticks=20, num_minor_ticks=4)

        # todo.根据上午还是下午确定不同的日界线
        # location使用实数表示，所以必须把时间转换成时间戳，但不清楚为什么要乘以1000
        dateX = df['date_time_X'].tolist()
        n_days = (dateX[-1] - dateX[0]).days + 1
        forecast_span = [
            Span(location=time.mktime(
                (dateX[0] + datetime.timedelta(days=i) + datetime.timedelta(hours=12)).timetuple()) * 1000,
                 dimension='height', line_color='red', line_dash='dashed', line_width=2)
            for i in xrange(n_days)]
        for span in forecast_span:
            p.add_layout(span)

        tab = Panel(child=p, title=model)
        tabs.append(tab)
    tabs = Tabs(tabs=tabs)
    save(tabs)  # 直接保存就行


if __name__ == "__main__":
    # f = file('stations.pkl','rb')
    # stations = pickle.load(f)
    # models = pickle.load(f)
    # f.close()

    stations = OrderedDict([
        (u'封丘', ['53983', (114.4166667, 35.03333333)]),
        (u'辉县', ['53985', (113.8166667, 35.45)]),
        (u'新乡', ['53986', (113.8833333, 35.31666667)]),
        (u'获嘉', ['53988', (113.6666667, 35.26666667)]),
        (u'原阳', ['53989', (113.95, 35.05)]),
        (u'卫辉', ['53994', (114.0666667, 35.38333333)]),
        (u'延津', ['53997', (114.1833333, 35.15)])
    ])

    models = OrderedDict([
        (u'EC细', ['Y:/ECMWF_HR/2T/999', 'R:/MICAPS/ecmwf_thin/2T/999']),
        (u'EC细 2TMax_3h', ['Y:/ECMWF_HR/MX2T3/999']),
        (u'EC细 2TMin_3h', ['Y:/ECMWF_HR/MN2T3/999']),
        (u'GRAPES_GFS', ['Y:/GRAPES_GFS/T2M_4']),
        (u'GRAPES_MESO', ['Y:/GRAPES_MESO/T2M_4']),
        (u'GRAPES_MESO集合平均', ['Y:/SEVP/NWPR/SENGRA/ET0/L20']),
        (u'Japan细', ['Y:/JAPAN_HR/TMP/2']),
        (u'T639细', ['Y:/T639_HR/2T/2']),
        (u'T639粗', ['Y:/T639_LR/T2M_4', 'R:/MICAPS/T639/T2M_4']),
        (u'GERMAN细', ['Y:/GERMAN_HR/TMP_2M/2']),
        (u'河南WRF_RUC', ['W:/t2m'])
    ])

    now = datetime.datetime.now()
    today = now.strftime('%y%m%d')
    nowtime = now.strftime('%y%m%d%H')
    if nowtime < today + "12":
        yesterday = now - datetime.timedelta(days=1)
        start_predict = yesterday.strftime('%y%m%d') + '20'
    else:
        start_predict = today + '08'
    date =  start_predict  # "17020220"

    logfile = r'D:\MICAPSData\TempForecast\log.txt'
    f = open(logfile, 'a')
    f.write("now is:" + now.strftime('%Y_%m_%d %H:%M:%S') + '\n')
    start = time.clock()
    # ***********************测试程序*********************************"
    plot_2T(start_predict, stations, models)
    # ***********************测试程序*********************************"
    end = time.clock()
    elapsed = end - start

    f.write("start is:" + start_predict + '\n')
    f.write("Time used: %.6fs, %.6fms\n" % (elapsed, elapsed * 1000))
    f.write("*****************\n")
    f.close()
