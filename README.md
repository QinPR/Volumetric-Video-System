### Volumentric Video System  
---  
#### Introduction   
+ This is a system for Volumetric Video Streaming. Now an implementation of 'End to End' transmision equiped with point-cloud tiling and viewpoint prediction is completed. The system now can transmit the pointcloud data from server end to user end through WebRTC and measure the transmitting time of each ply file, as well as the total transmission time.  

#### How to Run the Code  
+ Please run this code in server end, and open the port(default: 42345) so that the user end can access the server end.  
+ Please first  modify the `config.py` to specify the path of volumetric data.  
+ Then, run code by `python3 main.py`. The records of each file's transmission time will be stored in `Transmit_Log.txt`.  
+ After all the ply files are transmitted, a summary of transission time of each ply file as well as the upload speed before transmitting each ply file will be recorded in `result1.json` and `result.csv`.  
