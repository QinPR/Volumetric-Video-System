'''
    Functions related to processing the pointcloud.
'''
import os
import math
import sys

import numpy as np
import pandas as pd
from plyfile import PlyData


def tiling_rectangle(file_path: str, store_path: str = '.', block_num: int = 2):
    '''
        Given a path of a point-cloud, cut it into the specific number of blocks.
    '''
    try:
        filename = file_path.split('\\')[-1][:-4]
        print('The file path is {}'.format(file_path))
        plydata = PlyData.read(file_path)
        rawdata = plydata.elements[0].data
        data_pd = pd.DataFrame(rawdata)
        data_np = np.zeros(data_pd.shape, dtype=np.float32)
        property_names = rawdata[0].dtype.names
        for i, name in enumerate(property_names):
            data_np[:, i] = data_pd[name]

        if block_num == 2:
            for block_index in range(2):
                if os.path.exists('{}/{}/block{}.ply'.format(store_path, filename, block_index)):
                    continue   # to avoid calcualte repeatly

                if block_index == 1:
                    new_data_df = data_pd.loc[data_pd['z'] <= 0.3]
                else:
                    new_data_df = data_pd.loc[data_pd['z'] > 0.3]

                if not os.path.exists('{}/{}'.format(store_path, filename)):
                    os.mkdir('{}\\{}'.format(store_path, filename))
                # append the header of the ply file.
                f = open(file_path)
                line = ''
                while (line != 'end_header\n'):
                    line = f.readline()
                    if not os.path.exists('{}/{}/block{}.ply'.format(store_path, filename, block_index)):
                        with open('{}/{}/block{}.ply'.format(store_path, filename, block_index), 'w') as ply_file:
                            ply_file.write(line)
                    else:
                        with open('{}/{}/block{}.ply'.format(store_path, filename, block_index), 'a') as ply_file:
                            if line[:7] == 'element':
                                ply_file.write('element vertex {}\n'.format(new_data_df.shape[0]))

                            else:
                                ply_file.write(line)
                # append all the points in certain block
                merge_result_tuples = [tuple(xi) for xi in new_data_df.values]

                with open('{}/{}/block{}.ply'.format(store_path, filename, block_index), 'a') as ply_file:
                    for each_tuple in merge_result_tuples:
                        for element_i in range(len(each_tuple)):
                            if element_i >= 3:
                                ply_file.write(str(int(each_tuple[element_i])))
                            else: 
                                ply_file.write(str(each_tuple[element_i]))
                            if element_i == len(each_tuple) - 1:
                                ply_file.write('\n')
                            else:
                                ply_file.write(' ')
    except Exception as e:
        print(e)


center = None

def calculate_angle(df):

    angle = math.atan((df['z'] - center[2]) / (df['x'] - center[0]))

    if df['z'] - center[2] >= 0 and df['x'] - center[0] > 0:
        return angle
    elif df['z'] - center[2] > 0 and df['x'] - center[0] <= 0:
        return math.pi + angle
    elif df['z'] - center[2] <= 0 and df['x'] - center[0] < 0:
        return math.pi + angle
    elif df['z'] - center[2] < 0 and df['x'] - center[0] >= 0:
        return 2 * math.pi + angle


def tiling_cylinder(file_path: str, store_path: str = '.', sector_num: int = 6, height_num: int = 2):
    '''
        Given a path of a point-cloud, cut it into the specific number of sectors.
    '''
    global center
    try:
        filename = file_path.split('\\')[-1][:-4]
        print('The file path is {}'.format(file_path))
        plydata = PlyData.read(file_path)
        rawdata = plydata.elements[0].data
        data_pd = pd.DataFrame(rawdata)
        data_np = np.zeros(data_pd.shape, dtype=np.float32)
        property_names = rawdata[0].dtype.names
        for i, name in enumerate(property_names):
            data_np[:, i] = data_pd[name]

        # Find the certer point
        copy_data_pd = data_pd.copy(deep=True)
        copy_data_pd = copy_data_pd.loc[(copy_data_pd['y'] > -0.6) & (copy_data_pd['y'] < 1)]    # remove the upper noise and ground
        center = (np.mean(copy_data_pd['x']), np.mean(copy_data_pd['y']), np.mean(copy_data_pd['z']))
        print(center)
        data_pd['angle'] = data_pd.apply(calculate_angle, axis = 1)
        alpha = 2 * math.pi / sector_num
    
        for sector_index in range(sector_num):
            for height_index in range(height_num):
                new_data_df = data_pd.loc[(data_pd['angle'] >= sector_index * alpha) & (data_pd['angle'] < (sector_index + 1) * alpha)]
                if height_index == 0:
                    new_data_df = new_data_df.loc[new_data_df['y'] > center[1]]
                elif height_index == 1:
                    new_data_df = new_data_df.loc[new_data_df['y'] <= center[1]]

                directory_path = '{}\\{}'.format(store_path, filename)
                if not os.path.exists(directory_path):
                    os.mkdir(directory_path)
                # append the header of the ply file.
                ply_file_path = '{}\\sector{}_{}.ply'.format(directory_path, sector_index, height_index)
                if os.path.exists(ply_file_path):
                    print('Already exist!')
                    continue    # avoid calculate repeatly.
                f = open(file_path)
                line = ''
                while (line != 'end_header\n'):
                    line = f.readline()
                    if not os.path.exists(ply_file_path):
                        with open(ply_file_path, 'w') as ply_file:
                            ply_file.write(line)
                    else:
                        with open(ply_file_path, 'a') as ply_file:
                            if line[:7] == 'element':
                                ply_file.write('element vertex {}\n'.format(new_data_df.shape[0]))
                            else:
                                ply_file.write(line)
                # append all the points in certain block
                merge_result_tuples = [tuple(xi) for xi in new_data_df.values]

                with open(ply_file_path, 'a') as ply_file:
                    for each_tuple in merge_result_tuples:
                        for element_i in range(7):    # -1 is to avoid append the slope
                            if element_i >= 3:
                                ply_file.write(str(int(each_tuple[element_i])))
                            else: 
                                ply_file.write(str(each_tuple[element_i]))
                            if element_i == 6:
                                ply_file.write('\n')
                            else:
                                ply_file.write(' ')
    except Exception as e:
        print(e)
    


if __name__ == '__main__':

    # # For cutting into rectangles
    # path_dir = 'E:\{}olumetric_data\{}olumetric_data\{}-12-02-07-59-19_Vive\{}-12-02-07-59-19_Vive'.format('v', 'v', '22', '22')
    # path_list = os.listdir(path_dir)
    # store_path = '{}\{}blocks'.format(path_dir, '2')
    
    # if not os.path.exists(store_path):
    #     os.mkdir(store_path)
    # for each_path in path_list:
    #     tiling_rectangle('{}\{}'.format(path_dir, each_path), store_path)

    # For cutting into cylinders
    path_dir = 'E:\{}olumetric_data\{}olumetric_data\{}-12-02-07-59-19_Vive\{}-12-02-07-59-19_Vive'.format('v', 'v', '22', '22')
    path_list_tmp = os.listdir(path_dir)
    path_list = []
    for i in path_list_tmp:
        if i[-4:] == '.ply':
            path_list.append(i)
    sector_num = 8
    store_path = '{}\{}cylinders'.format(path_dir, sector_num)
    
    if not os.path.exists(store_path):
        os.mkdir(store_path)
    for each_path in path_list:
        tiling_cylinder('{}\{}'.format(path_dir, each_path), store_path, 8)



        
            