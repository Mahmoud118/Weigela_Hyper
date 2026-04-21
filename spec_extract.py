"""
For newer GDAL that can read rotation angle from ENVI


"""
# python C:/mydata/test_potato_spec_extract.py -r "C:/mydata/cosi_timeseries_bin"    -p C:/mydata/test_shp_epsg32610.shp -f uid -l aaa -c C:/mydata/test_out_606.csv


import numpy as np
import os, math, sys,argparse
import time
try:
    import gdal
except:
    try:
        from osgeo import gdal
    except:
        print ("Import of gdal failed.")
        sys.exit(1)

        
from osgeo import gdal, ogr, osr

import envi_header_handler as EHH



def tran_coord(GeoTransform,indices):

    xp = GeoTransform[0] + (indices[1]+0.5)*GeoTransform[1] + (indices[0]+0.5)*GeoTransform[2]   
    yp = GeoTransform[3] + (indices[1]+0.5)*GeoTransform[4] + (indices[0]+0.5)*GeoTransform[5]  

    return xp,yp




def rasterize_polygon(img_fn,polygon_fn,key_id):
  inenvi = os.path.abspath(img_fn)    

  if os.path.exists(img_fn+".hdr"):
    hdrinfo=EHH.ENVI_Header(img_fn+".hdr")
    print (img_fn+".hdr")
  else:
    if os.path.exists(os.path.splitext(img_fn)[0]+".hdr"):
      hdrinfo=EHH.ENVI_Header(os.path.splitext(img_fn)[0]+".hdr")
      print (os.path.splitext(img_fn)[0]+".hdr")
    else:
      print ("Cannot find .hdr file")
      sys.exit(1)

  rot_angle = hdrinfo.get_rotation()

  in_ds=gdal.Open(img_fn,gdal.GA_ReadOnly)
  geotransform=in_ds.GetGeoTransform()
  ds_nband=in_ds.RasterCount
  ds_rows=in_ds.RasterYSize
  ds_cols=in_ds.RasterXSize
  
  print (geotransform)
  
  pixel_size=np.sqrt(geotransform[1]**2+geotransform[2]**2)
  
  #polygon
  source_ds = ogr.Open(polygon_fn)

  source_layer = source_ds.GetLayer()
  print (source_layer.GetFeatureCount())
  field_list = []
  ldefn = source_layer.GetLayerDefn()
  for n in range(ldefn.GetFieldCount()):
    fdefn = ldefn.GetFieldDefn(n)
    field_list.append(fdefn.name)

  if not (key_id in field_list):
    print ('Field "',key_id,'" is not in the shapefile!')
    sys.exit(1)
    
  tmp_mem_driver=ogr.GetDriverByName('MEM')

  dest = tmp_mem_driver.CreateDataSource('tempData')

  mem_lyr = dest.CopyLayer(source_layer,'newlayer',['OVERWRITE=YES'])
  FeatureCount= mem_lyr.GetFeatureCount()
  # Add a new field
  new_field = ogr.FieldDefn('tempFID', ogr.OFTInteger)  
  mem_lyr.CreateField(new_field)

  lookup_dict={}
  for i, feature in enumerate(mem_lyr):
    feature.SetField('tempFID', i+1)  # key step1
    lookup_dict[str(i+1)]=feature.GetField(key_id)
    mem_lyr.SetFeature(feature)  # key step 2


  if FeatureCount<255:
    target_ds = gdal.GetDriverByName('MEM').Create('', ds_cols, ds_rows, 1, gdal.GDT_Byte)
    #target_ds = gdal.GetDriverByName('GTiff').Create('/home/ye6/hys_test/test_ftps/data/temp8bit.tif', ds_cols, ds_rows, 1, gdal.GDT_Byte)
    nodata_val=255
  else:
    if (FeatureCount>255 and FeatureCount < 32767):
      target_ds = gdal.GetDriverByName('MEM').Create('', ds_cols, ds_rows, 1, gdal.GDT_Int16)
      #target_ds = gdal.GetDriverByName('GTiff').Create('/home/ye6/hys_test/test_ftps/data/tempData.tif', ds_cols, ds_rows, 1, gdal.GDT_Int16)
      nodata_val=-9999
    else:    # >32767
      target_ds = gdal.GetDriverByName('MEM').Create('', ds_cols, ds_rows, 1, gdal.GDT_Int32)
      nodata_val=-9999    

  target_ds.SetGeoTransform(geotransform)
  
  target_ds.SetProjection(in_ds.GetProjection())
  band = target_ds.GetRasterBand(1)
  band.SetNoDataValue(nodata_val)

  gdal.RasterizeLayer(target_ds, [1], mem_lyr, options=["ATTRIBUTE=tempFID" ,"ALL_TOUCHED=FALSE"])
  in_ds=None
  return (target_ds,lookup_dict)


def extract_point(img_file,target_ds, lookup_dict,key_id, outcsv_f,flightline):  
  
  in_ds=gdal.Open(img_file,gdal.GA_ReadOnly)
  ds_nband=in_ds.RasterCount
  ds_rows=in_ds.RasterYSize
  ds_cols=in_ds.RasterXSize
 
  poly_raster=target_ds.GetRasterBand(1).ReadAsArray()
  
  geotrans=target_ds.GetGeoTransform()
  data_type=target_ds.GetRasterBand(1).DataType

  if (data_type == gdal.GDT_Byte):
    ind=np.where((poly_raster>0) & (poly_raster<255)  )
  else:
    if (data_type == gdal.GDT_Int16):
      ind=np.where((poly_raster>0) & (poly_raster<32767)  )
    else:
      ind=np.where(poly_raster>0  )

  x_list,y_list=tran_coord(geotrans,ind)
  total_point=len(ind[1])

  print (total_point,' points')

  if total_point==0:
    print ("No intersection.")
    sys.exit(1)

  latlon_wgs84 = osr.SpatialReference()
  latlon_wgs84.ImportFromEPSG ( 4326 )

  img_sr=osr.SpatialReference(wkt=in_ds.GetProjection())
  tx2 = osr.CoordinateTransformation (  img_sr ,latlon_wgs84)

  
  band_list_str=''
  for x in range(ds_nband):
    band_list_str+=',Band_'+str(x+1)

  header_str='flightline,id,img_row,img_col,lon,lat,x_coord,y_coord,polygon_order,'+key_id+','+band_list_str[1:]

  with open(outcsv_f,'wb') as outcsv:
    outcsv.write(bytes(header_str,'UTF-8'))
    outcsv.write('\n'.encode('utf-8'))

    for i in range(total_point):
      row=int(ind[0][i])
      col=int(ind[1][i])
      poly_id=poly_raster[row,col]
      poly_id_code=lookup_dict[str(poly_id)]

      #lon,lat,z0=tx2.TransformPoint(x_list[i],y_list[i]) # gdal version<3
      lat,lon,z0=tx2.TransformPoint(x_list[i],y_list[i])  # gdal version>=3

      val_list=''
      for iband in range(ds_nband):
        band=in_ds.GetRasterBand(iband+1)
        val=band.ReadAsArray(col,row,1,1)[0,0]
        val_list+=','+'{0:g}'.format(val)

      #print i,row,col,lon,lat, x_list[i],y_list[i],poly_id,poly_id_code,val_list
      outcsv.write('{},{},{},{},{},{},{},{},{},{},{}'.format(flightline,i+1,row,col,lon,lat, x_list[i],y_list[i],poly_id,poly_id_code,val_list[1:]).encode('utf-8'))
      outcsv.write('\n'.encode('utf-8'))


def go_extract(img_fn, polygon_fn, outcsv, key_id,flightline):

  target_ds, lookup_dict=rasterize_polygon(img_fn,polygon_fn,key_id)

  extract_point(img_fn,target_ds, lookup_dict, key_id, outcsv,flightline)

def main(argv):

  parser = argparse.ArgumentParser(description='This code is to extract data across third dimension using polygon shapefiles')
  parser.add_argument('-r','--raster',type=str, help='Input multiband image file full name',required=True)
  parser.add_argument('-p','--polygon',type=str, help='Input polygon shapefile full name',required=True)
  parser.add_argument('-f','--field',type=str, help='field in SHP to be ID',required=True)
  parser.add_argument('-c','--csv',  type=str, help='Output csv', required=True)
  parser.add_argument('-l','--flightline',  type=str, help='flightline', required=True)

  args = parser.parse_args()
  

  img_fn=args.raster 
  outcsv=args.csv
  polygon_fn=args.polygon
  key_id=args.field
  flightline=args.flightline
  
  start_time = time.time()
  go_extract(img_fn, polygon_fn, outcsv, key_id, flightline)
  end_time = time.time()
  print("{} sec.".format(end_time-start_time))


if __name__ == "__main__":
  main(sys.argv)