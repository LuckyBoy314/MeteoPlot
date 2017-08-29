# -*- coding:utf-8 -*-

from pyMicaps import Diamond4
import datetime, os
import arcpy

if __name__ == "__main__":

    start_time = '17082908'  # 起报时间
    micaps_source_dir = 'Y:\\'
    temp_dir = 'D:/rain_model/%s/' % start_time
    product_dir = 'Z:/model_rain/'
    mxd_path = os.getcwd() + u'/data/多模式降水对比模板.mxd'
    print mxd_path
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    for valid_h in range(12, 132, 12):

        if valid_h == 12:
            fs = [r'%sECMWF_HR\RAIN12\999\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sGERMAN_HR\APCP\999\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sGRAPES_GFS\RAIN12_4\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sGRAPES_MESO\RAIN_4\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sJAPAN_HR\APCP\0\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sJAPAN_LR\RAIN12\999\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sT639_HR\RAIN12\999\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sT639_LR\RAIN_4\%s.%03d' % (micaps_source_dir, start_time, valid_h)
                  ]
        else:
            fs = [r'%sECMWF_HR\RAIN12\999\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sGERMAN_HR\RAIN12\999\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sGRAPES_GFS\RAIN12_4\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sGRAPES_MESO\RAIN12_4\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sJAPAN_HR\RAIN12\0\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sJAPAN_LR\RAIN12\999\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sT639_HR\RAIN12\999\%s.%03d' % (micaps_source_dir, start_time, valid_h),
                  r'%sT639_LR\RAIN12_4\%s.%03d' % (micaps_source_dir, start_time, valid_h)
                  ]
        for f in fs:
            if os.path.exists(f):
                f_cut_source = f[len(micaps_source_dir):]
                out = ''.join(
                    [temp_dir, f_cut_source[0:f_cut_source.find('\\')], '_', '%03d' % valid_h, '.asc'])
                if not os.path.exists(out):
                    d = Diamond4(f)
                    d.convert_to_EsriAscii(out)

    #
    mxd = arcpy.mapping.MapDocument(mxd_path)

    txts = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT")
    start_time_datetime = datetime.datetime.strptime(start_time, '%y%m%d%H')
    for valid_h, i in zip(range(0, 120, 12), range(23, 13, -1)):
        beg = (start_time_datetime + datetime.timedelta(hours=valid_h)).strftime('%m%d%H')
        end = (start_time_datetime + datetime.timedelta(hours=valid_h + 12)).strftime('%m%d%H')
        txts[i].text = beg + '-' + end

    mxd.replaceWorkspaces('D:/rain_model/17082320', "RASTER_WORKSPACE", temp_dir, "RASTER_WORKSPACE", False)
    broken_lyrs = arcpy.mapping.ListBrokenDataSources(mxd)
    for broken_lyr in broken_lyrs:
        broken_lyr.visible = False
        broken_dfs = arcpy.mapping.ListDataFrames(mxd, broken_lyr.name)
        if len(broken_dfs) > 0:
            region_lyrs = arcpy.mapping.ListLayers(mxd, "", broken_dfs[0])
        if len(region_lyrs) > 0:
            region_lyrs[0].visible = False

    arcpy.mapping.ExportToJPEG(mxd, product_dir + start_time, resolution=200)
