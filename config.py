'''
    Configure the Folder of Volmentric Data to be transmitted here.
'''
Full_Data_Path = 'E:\{}olumetric_data\{}olumetric_data\{}-12-02-07-59-19_Vive\{}-12-02-07-59-19_Vive\{}blocks'.format('v', 'v', '22', '22', '2')
# Full_Data_Path = 'E:\{}olumetric_data\{}olumetric_data\{}-12-02-07-59-19_Vive\{}-12-02-07-59-19_Vive'.format('v', 'v', '22', '22')
# Full_Data_Path = 'E:\{}olumetric_data\{}olumetric_data\{}-12-02-08-00-51_Vivesit\Dump\colored_pointcloud'.format('v', 'v', '22')


# Dataset to train the model for predicting viewpoint
Viewpoint_Dataset = 'E://viewpoint-dataset//Experiment_1'
train_window = 30
pred_window = 1
trainining_validation_split = 0.8