# _*_ coding: utf-8 _*_

# Copyright (c) 2020 NMC Developers.
# Distributed under the terms of the GPL V3 License.

"""
  Miscellaneous magics funcations.
"""

import sys
import math
import numpy as np

try:
    from Magics import macro as magics
except ImportError:
    print("""Magics not installed. Please refer to 
      https://anaconda.org/conda-forge/magics""")
    sys.exit(1)


def get_skip_vector(lon, lat, map_region):
    """
    Calculate default skip vector for magics vector map.
    """
    if map_region is not None:
        lon1 = lon[ (lon >= map_region[0]) & (lon <= map_region[1])]
        lat1 = lat[ (lat >= map_region[2]) & (lat <= map_region[3])]
    else:
        lon1 = lon
        lat1 = lat
    skip_vector = max(math.ceil(len(lon1)/60.0), math.ceil(len(lat1)/30.0))
    
    return skip_vector


def minput_2d(data, lon, lat, metadata):
    """
    Put the data into magics minput function.
    minput is used 2 define matrices as input for contouring or
    list of values as input of curve or symbol plotting.

    Args:
        data (np.float64): 2D array, [nlat, nlon]
        lon (np.float64): 1D vector, [nlon]
        lat (np.float64): 1D vector, [nlat]
        metadata (dictionary): variable name and units information, 
            like {'units': 'K', 'long_name': '2 metre temperature'}. Defaults to None.
    """
    
    lat = np.squeeze(lat.astype(np.float64))
    lon = np.squeeze(lon.astype(np.float64))
    input_field_values = np.squeeze(data.astype(np.float64))

    # put values into magics
    return magics.minput(
        input_type = "geographical",
        input_field = input_field_values,
        input_latitudes_list = lat,
        input_longitudes_list = lon,
        input_metadata = metadata)


def minput_2d_vector(udata, vdata, lon, lat, skip=1, metadata=None):
    """
    Put the data into magics minput function.
    minput is used 2 define matrices as input for contouring or
    list of values as input of curve or symbol plotting.

    Args:
        udata (np.array): 2D array, [nlat, nlon]
        vdata (np.array): 2D array, [nlat, nlon]
        lon (np.array): 1D vector, [nlon]
        lat (np.array): 1D vector, [nlat]
        skip (int, optional): grid skip point number. Defaults to 1.
        metadata (dictionary): variable name and units information, 
            like {'units': 'm/s', 'long_name': 'wind field'}. Defaults to None.
    """

    # extract values
    lat = np.squeeze(lat.astype(np.float64))    # 1D vector
    lon = np.squeeze(lon.astype(np.float64))    # 1D vector
    uwind_field = np.squeeze(udata.astype(np.float64))    # 2D array, [nlat, nlon]
    vwind_field = np.squeeze(vdata.astype(np.float64))    # 2D array, [nlat, nlon]
    lon, lat = np.meshgrid(lon, lat)

    # skip values and flatten
    uwind_field = uwind_field[::skip, ::skip].flatten()
    vwind_field = vwind_field[::skip, ::skip].flatten()
    lat = lat[::skip, ::skip].flatten()
    lon = lon[::skip, ::skip].flatten()

    # remove nan values
    index = (~np.isnan(uwind_field)) & (~np.isnan(vwind_field))
    uwind_field = uwind_field[index]
    vwind_field = vwind_field[index]
    if uwind_field.size == 0:
        return None
    lat = lat[index]
    lon = lon[index]

    # check meta information
    if metadata is None:
        metadata = {'units': 'm/s', 'long_name': 'wind field'}

    # put into magics minput function
    return magics.minput(
            input_type = "geographical",
            input_x_component_values = uwind_field,
            input_y_component_values = vwind_field,
            input_latitude_values = lat,
            input_longitude_values = lon,
            input_metadata = metadata)


def minput_xarray(data, varname='data', metadata=None):
  """
  Put xarray grid into magics minput data.
  refer to: https://github.com/ecmwf/magics-python/blob/master/Magics/macro.py
            https://confluence.ecmwf.int/display/MAGP/Input+Data
  
  Args:
      data (object): xarray dataset which retrieve 
                     from micaps cassandra server directory.
      vwind (object): xarray dataset which retrieve 
                      from micaps cassandra server directory.
                      if set, data is uwind.
      metadata(dict, optional): data meta information. Defaults to {'units': 'm/s', 'long_name': 'Wind field'}.
  Examples:
      from nmc_met_io.retrieve_micaps_server import get_model_grid
      dataset = get_model_grid("ECMWF_HR/TMP/850", varattrs={'units':'C', 'long_name':'temperature'})
      data = minput_grid(dataset)
  """
  # flatten an nD matrix into a 2d matrix
  for dim in data.dims:
    if dim in ['lon', 'lat']:
      continue
    else:
      d = data[dim].values[0]
      data = data.loc[{dim: d}]

  # extract values
  lat = data['lat'].values.astype(np.float64)    # 1D vector
  lon = data['lon'].values.astype(np.float64)    # 1D vector
  input_field_values = np.squeeze(data[varname].values.astype(np.float64))    # 2D array, [nlat, nlon]

  # set data meta data
  if metadata is None:
    metadata = dict(data[varname].attrs)

  # put values into magics
  return magics.minput(
    input_field = input_field_values,
    input_latitudes_list = lat,
    input_longitudes_list = lon,
    input_metadata = metadata)


def minput_xarray_vector(uwind, vwind, u_varname='data', v_varname='data', skip=1,
                       metadata={'units': 'm/s', 'long_name': 'Wind field'}):
  """
  Put u and v xarray grid into magics minput data.
  refer to: https://github.com/ecmwf/magics-python/blob/master/Magics/macro.py
            https://confluence.ecmwf.int/display/MAGP/Input+Data
  
  Args:
      uwind (object): u wind xarray dataset which retrieve 
                      from micaps cassandra server directory.
      vwind (object): v wind xarray dataset which retrieve 
                      from micaps cassandra server directory.
      skip (int, optional): grid skip point number. Defaults to 1.
      metadata(dict, optional): data meta information. Defaults to {'units': 'm/s', 'long_name': 'Wind field'}.
  """

  # flatten an nD matrix into a 2d matrix
  for dim in uwind.dims:
    if dim in ['lon', 'lat']:
      continue
    else:
      d = uwind[dim].values[0]
      uwind = uwind.loc[{dim: d}]
      d = vwind[dim].values[0]
      vwind = vwind.loc[{dim: d}]

  # extract values
  lat = uwind['lat'].values.astype(np.float64)    # 1D vector
  lon = uwind['lon'].values.astype(np.float64)    # 1D vector
  uwind_field = np.squeeze(uwind['u_varname'].values.astype(np.float64))    # 2D array, [nlat, nlon]
  vwind_field = np.squeeze(vwind['v_varname'].values.astype(np.float64))    # 2D array, [nlat, nlon]
  lon, lat = np.meshgrid(lon, lat)

  # skip values and flatten
  uwind_field = uwind_field[::skip, ::skip].flatten()
  vwind_field = vwind_field[::skip, ::skip].flatten()
  lat = lat[::skip, ::skip].flatten()
  lon = lon[::skip, ::skip].flatten()

  # put into magics minput function
  return magics.minput(
        input_type = "geographical",
        input_x_component_values = uwind_field,
        input_y_component_values = vwind_field,
        input_latitude_values = lat,
        input_longitude_values = lon,
        input_metadata = metadata)
