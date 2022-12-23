'''
    Functions related to processing the pointcloud.
'''
import os

import numpy as np
import pandas as pd
from plyfile import PlyData


def tiling(file_path: str, store_path: str = '.', block_num: int = 2):
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
            


if __name__ == '__main__':

    path_dir = 'E:\{}olumetric_data\{}olumetric_data\{}-12-02-07-59-19_Vive\{}-12-02-07-59-19_Vive'.format('v', 'v', '22', '22')
    path_list = os.listdir(path_dir)
    store_path = '{}\{}blocks'.format(path_dir, '2')
    
    if not os.path.exists(store_path):
        os.mkdir(store_path)
    for each_path in path_list:
        tiling('{}\{}'.format(path_dir, each_path), store_path)
            