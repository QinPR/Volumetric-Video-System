'''
    Main Implementation of server end.
    Modified from https://github.com/tsonglew/webrtc-stream
'''
import argparse
import asyncio
import json
import logging
import os
import platform
import ssl
import time
import json
import sys
import math

from aiohttp import web
from aiortc import (
    RTCDataChannel,
    RTCPeerConnection,
    RTCSessionDescription,
)
import psutil
import pandas as pd
import numpy as np
import ujson
import joblib
from plyfile import PlyData, PlyElement

import config as config

# Some Global Vars
ROOT = os.path.dirname(__file__)
Timer = -1
current_file_index = 0
total_spend_time = 0
spend_time_list = []
vertical_indices = [4, 5, 6, 7]
hori_indices = [0, 1]
# PLY_Data_List = os.listdir(config.Full_Data_Path)
# PLY_Data_List = []
# for i in PLY_Data_Dir_List: 
#     if i[-4:] == '.ply':
#         PLY_Data_List.append(i)
PLY_Data_List = os.listdir(config.Full_Data_Path)


# GBDT Model
x_GBDT_Model = joblib.load('x_Trained_GBDT_Model.pkl')
z_GBDT_Model = joblib.load('z_Trained_GBDT_Model.pkl')
    # We let alone y axis for future work
viewpoint_queue = []
center = (-0.09303445, 0.1593566, 0.2598027)
alpha = 2 * math.pi / config.horizontal_tiling



async def index(request):
    '''
        Static Resoruce of Main Page
    '''
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def client_js(request):
    '''
        js
    '''
    content = open('./js/client.js', "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def pcd_loader_js(request):
    '''
        js
    '''
    content = open("./js/pcd_loader.js", "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def visualize_3d(request):
    '''
        js
    '''
    content = open("./js/visualize_3d.js", "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def viewport_change(request):
    '''
        js
    '''
    content = open("./js/viewport_change.json", "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    '''
        提供信令服务
    '''
    # Get the request from user
    params = await request.json()

    # Extract SDP from request of user, generate SDP of server.
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    # Create the connection object of server
    pc = RTCPeerConnection()

    # Create the Data Channel for server end
    data_channel = pc.createDataChannel('sendDataChannel')

    # Save the server connection object to the global var `pcs`
    pcs.add(pc)

    await server(pc, offer, data_channel)   # waiting this to end, until it returns

    # Return the SDP of server back to the user 
    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


pcs = set()


def speed_test(test_gap: int = 10) -> float:
    '''
        Return the current Upload speed by Mbps
        Since the psutil.net_io_counters() records the throughput every 10s, the test_gap should be at least 10s. 
    '''
    sent_before = psutil.net_io_counters().bytes_sent
    time.sleep(test_gap)
    sent_now = psutil.net_io_counters().bytes_sent
    upload_speed = (sent_now - sent_before) / 1024 / 1024 / test_gap

    return upload_speed


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)



def determine_sectors():
    '''
        Determine the sectors to be sent based on the prediction of viewpoint(camera's position)
    '''
    
    vertical_indices = []
    hori_indices = [0, 1]

    input_array = np.array(viewpoint_queue).flatten().reshape(1, -1)
    x_result = x_GBDT_Model.predict(input_array)[0]
    z_result = z_GBDT_Model.predict(input_array)[0]
    y_result = 0  # we let alone y-axis as the future work
    
    angle = math.atan((z_result - center[2]) / (x_result - center[0]))
    if z_result - center[2] > 0 and x_result - center[0] <= 0:
        angle = math.pi + angle
    elif z_result - center[2] <= 0 and x_result - center[0] < 0:
        angle = math.pi + angle
    elif z_result - center[2] < 0 and x_result - center[0] >= 0:
        angle = 2 * math.pi + angle

    for sector_index in range(config.horizontal_tiling):
        if angle >= sector_index * alpha and angle < (sector_index + 1) * alpha:
            logger.info('The predict sector is {}'.format(sector_index))
            left_sector_index = sector_index + 1
            if left_sector_index >= config.horizontal_tiling:
                left_sector_index -= config.horizontal_tiling

            left_left_sector_index = sector_index + 2
            if left_left_sector_index >= config.horizontal_tiling:
                left_left_sector_index -= config.horizontal_tiling

            right_sector_index = sector_index - 1
            if right_sector_index < 0:
                right_sector_index += config.horizontal_tiling

            right_right_sector_index = sector_index - 2
            if right_right_sector_index < 0:
                right_right_sector_index += config.horizontal_tiling

            
            vertical_indices = [sector_index, left_sector_index, right_sector_index, right_right_sector_index, left_left_sector_index]
            break
            
    return vertical_indices, hori_indices



async def server(pc, offer, data_channel):
    # Listen the connection status of RTC
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        global Timer
        logger.info("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            Timer = -1
            await pc.close()
            pcs.discard(pc)

    # Listen the video stream sent by user end
    @pc.on("track")
    def on_track(track):
        logger.info("======= received track: ", track)
        if track.kind == "video":
            logger.info('Server End working!')

            # bind the video stream after replacement of face
            pc.addTrack(track)

    # Listen the Data from the user end, and start transmit the volumetric data to user end.
    @pc.on("datachannel")
    def on_message(channel, vertice_chunk_size: int = 60000):
        '''
            vertice_chunk_size: The maximum number of vertices to be transmitted in one time
        '''
        logger.info('Got the start message!')
        @channel.on("message")
        def on_message(message):
            global Timer
            global total_spend_time
            global current_file_index
            global spend_time_list
            global vertical_indices
            global hori_indices
            global viewpoint_queue
            if channel.readyState == 'open':
                if message == 'User End Establish Data Channel':    # The User end establish the data channel.
                    channel.send('Server End Establish Data Channel')
                elif message == 'Start Transmit':
                    if Timer != -1:
                        spent_time = time.time() - Timer     # Timer End!
                        total_spend_time += spent_time
                        spend_time_list.append(spent_time)
                        logger.info('{} spent {}s to transmit.'.format(PLY_Data_List[current_file_index], spent_time))
                        current_file_index += 1
                    if current_file_index >= len(PLY_Data_List):    # All the ply file has been sent out.
                        channel.send('over')
                        logger.info('Over! The total spend time is {}s'.format(total_spend_time))
                        try:
                            df = pd.DataFrame({'time': spend_time_list})
                            df.to_csv('./result.csv')    # Store the result
                        except:
                            pass
                        with open('./result1.json', 'w') as f:
                            json.dump({'time': spend_time_list}, f)
                    else:
                        file_size = 0
                        df_list = []
                        for ver_index in vertical_indices:
                            for hori_index in hori_indices:
                                file_path = '{}\{}\sector{}_{}.ply'.format(config.Full_Data_Path, PLY_Data_List[current_file_index], ver_index, hori_index)
                                file_size += os.path.getsize(file_path) / 1024 / 1024        
                                plydata = PlyData.read(file_path)
                                rawdata = plydata.elements[0].data
                                df_list.append(pd.DataFrame(rawdata))
                        data_pd = pd.concat(df_list)

                        logger.info('=' * 40)
                        logger.info('Begin to transmit {} (size = {}Mb)'.format(PLY_Data_List[current_file_index], file_size))    

                        data_np = np.zeros((data_pd.shape[0], 3), dtype=np.float32)
                        property_names = rawdata[0].dtype.names
                        for i, name in enumerate(('x', 'y', 'z')):
                            data_np[:, i] = data_pd[name]
                        Timer = time.time()    # Timer Start!
                        start_index = 0
                        while start_index < data_np.shape[0]:
                            if start_index + vertice_chunk_size > data_np.shape[0]:
                                send_string = ujson.dumps(data_np[start_index:].flatten().tolist())
                            else:
                                send_string = ujson.dumps(data_np[start_index:start_index + vertice_chunk_size].flatten().tolist())    # because channel.send only support transmitting string.
                            channel.send(send_string)
                            start_index += vertice_chunk_size
                            logger.info('OK here')
                        channel.send('end frame')

                elif message[:11] == '[viewpoint]':
                    # If tiling, determine which sector to be transmit
                    if config.vertical_tiling > 0 or config.horizontal_tiling > 0:
                        viewpoint_x = message[11:].split(' ')[0]
                        viewpoint_y = message[11:].split(' ')[1]
                        viewpoint_z = message[11:].split(' ')[2]
                        viewpoint = [viewpoint_x, viewpoint_y, viewpoint_z]
                        if len(viewpoint_queue) == 0:
                            viewpoint_queue = [viewpoint for _ in range(config.train_window)]
                        else:
                            viewpoint_queue.pop(0)
                            viewpoint_queue.append(viewpoint)
                        vertical_indices, hori_indices = determine_sectors()
                    
            else:
                logger.info('The State of DataChannel is not ready.')



    # Record the SDP of user end.
    await pc.setRemoteDescription(offer)      
    # Create the local SDP
    answer = await pc.createAnswer()
    # Record the local SDP
    await pc.setLocalDescription(answer)


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Volumentric Video System")
    # parser.add_argument(
    #     "--host", default="localhost", help="Host for HTTP server (default: 0.0.0.0)"
    # )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=42345, help="Port for HTTP server (default: 42345)"
    )
    args = parser.parse_args()

    logging.basicConfig(filename = 'Transmit_Log.txt', level=logging.INFO)  # Log file 
    logger = logging.getLogger(__name__)

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/js/client.js", client_js)
    app.router.add_get("/js/pcd_loader.js", pcd_loader_js)
    app.router.add_get("/js/visualize_3d.js", visualize_3d)
    app.router.add_get("/js/viewport_change.json", viewport_change)
    app.router.add_post("/offer", offer)
    web.run_app(app, host=args.host, port=args.port)
