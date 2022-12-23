'''
    GBDT model to predict the viewpoint of camera
'''

import os
import sys

from sklearn.ensemble import GradientBoostingRegressor
import pandas as pd
import logging
import joblib

import config as config


logging.basicConfig(filename = 'Train_Log.txt', level=logging.INFO)  # Log file 
logger = logging.getLogger(__name__)


def load_dataset() -> dict:
    '''
        Load traning dataset
        output a dict of dataset {exp_index: time_series}
    '''
    returned_dict_train = {}
    returned_dict_validation = {}
    traning_exp_tmp = os.listdir(config.Viewpoint_Dataset)
    training_exp_list = []
    for i in traning_exp_tmp:
        if i[-4:] != '.csv':     # Exclude the metadata
            training_exp_list.append(i)
    # append training_set
    for each_traning_exp_group_i in range(len(training_exp_list)):
        train = 1
        if each_traning_exp_group_i > len(training_exp_list) * config.trainining_validation_split:
            train = 0     # for validation
        each_traning_exp_group = training_exp_list[each_traning_exp_group_i]
        exp_path = '{}\\{}'.format(config.Viewpoint_Dataset, each_traning_exp_group)
        detailed_exp_list = os.listdir(exp_path)
        for each_detailed_exp in detailed_exp_list:
            detailed_exp_path = '{}\\{}'.format(exp_path, each_detailed_exp)
            detailed_exp_df = pd.read_csv(detailed_exp_path)[['HmdPosition.x', 'HmdPosition.y', 'HmdPosition.z']]
            store_name = "{}_{}".format(each_traning_exp_group, each_detailed_exp)
            if train == 1:
                returned_dict_train[store_name] = detailed_exp_df
            else:
                returned_dict_validation[store_name] = detailed_exp_df
    
    return returned_dict_train, returned_dict_validation


class GBDT:
    '''
        Gradient Boosting Decision Tree for viewpoint prediction
    '''
    def __init__(self, trainset: dict, valset: dict):

        self.trainset = trainset
        self.valset = valset
        self.train_window = config.train_window
        self.pred_window = config.pred_window
        self.GBDT_Model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.5, max_depth=2, random_state=0)
        
    def train(self):

        reorganize_dataset_x = []
        reorganize_dataset_y = []
        for each_exp in self.trainset.keys():
            each_dataset = self.trainset[each_exp]
            start_index = 0
            while start_index + self.train_window + self.pred_window < each_dataset.shape[0]:
                train_x = each_dataset[start_index:start_index + self.train_window]
                train_x = train_x.to_numpy().flatten()
                train_y = each_dataset[start_index + self.train_window: start_index + self.train_window + self.pred_window]['HmdPosition.x']
                train_y = train_y.to_numpy().flatten()
                reorganize_dataset_x.append(train_x[:])
                reorganize_dataset_y.append(train_y[:])
                start_index = start_index + self.train_window + self.pred_window
        self.GBDT_Model.fit(reorganize_dataset_x, reorganize_dataset_y)
        logger.info('Training score = {}'.format(self.GBDT_Model.score(reorganize_dataset_x, reorganize_dataset_y)))

        joblib.dump(self.GBDT_Model, 'Trained_GBDT_Model.pkl')

    def valiate(self):

        self.GBDT_Model = joblib.load('Trained_GBDT_Model.pkl')
        reorganize_dataset_x = []
        reorganize_dataset_y = []
        for each_exp in self.valset.keys():
            each_dataset = self.valset[each_exp]
            start_index = 0
            while start_index + self.train_window + self.pred_window < each_dataset.shape[0]:
                train_x = each_dataset[start_index:start_index + self.train_window]
                train_x = train_x.to_numpy().flatten()
                train_y = each_dataset[start_index + self.train_window: start_index + self.train_window + self.pred_window]['HmdPosition.x']
                train_y = train_y.to_numpy().flatten()
                reorganize_dataset_x.append(train_x[:])
                reorganize_dataset_y.append(train_y[:])
                start_index = start_index + self.train_window + self.pred_window
        val_score = self.GBDT_Model.score(reorganize_dataset_x, reorganize_dataset_y)
        logger.info('Validation Score = {}'.format(val_score))
            



if __name__ == '__main__':

    train, val = load_dataset()

    logger.info('Begin to train GBDT model!')

    GBDT_instance = GBDT(train, val)

    # GBDT_instance.train()

    GBDT_instance.valiate()