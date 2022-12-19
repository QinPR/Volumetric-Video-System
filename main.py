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

from aiohttp import web
from aiortc import (
    RTCDataChannel,
    RTCPeerConnection,
    RTCSessionDescription,
)
import psutil
import pandas as pd
import numpy as np

import config as config

# Some Global Vars
ROOT = os.path.dirname(__file__)
Timer = -1
current_file_index = 0
total_spend_time = 0
spend_time_list = []
PLY_Data_List = sorted(os.listdir(config.Full_Data_Path))


async def index(request):
    '''
        Static Resoruce of Main Page
    '''
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    '''
        js
    '''
    content = open(os.path.join(ROOT, "client.js"), "r").read()
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
    def on_message(channel):
        logger.info('Got the start message!')
        @channel.on("message")
        def on_message(message):
            global Timer
            global total_spend_time
            global current_file_index
            global spend_time_list
            if channel.readyState == 'open':
                if message == 'User End Establish Data Channel':    # The User end establish the data channel.
                    #logger.info('The current speed is {}Mbps'.format(speed_test()))
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
                        file_path = '{}\{}'.format(config.Full_Data_Path, PLY_Data_List[current_file_index])
                        file_size = os.path.getsize(file_path) / 1024 / 1024
                        logger.info('=' * 40)
                        logger.info('Begin to transmit {} (size = {}Mb)'.format(PLY_Data_List[current_file_index], file_size))
                        with open(file_path) as f:
                            Timer = time.time()    # Timer Start!
                            channel.send(f.read())
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
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    web.run_app(app, host=args.host, port=args.port)
