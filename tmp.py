import json
import pandas as pd
import config as config

path = '{}\\9\\video_0.csv'.format(config.Viewpoint_Dataset)

df = pd.read_csv(path)
return_dict = {}
return_dict['x'] = df['HmdPosition.x'].tolist()
return_dict['y'] = df['HmdPosition.y'].tolist()
return_dict['z'] = df['HmdPosition.z'].tolist()

with open('./js/viewport_change.json', 'w') as f:
    json.dump(return_dict, f)