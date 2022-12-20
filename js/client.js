var current_cache_store_index = 0;
let caught = 0;


// 1. Handle the WebRTC transmit logic.
var pc = null;
var clear = 0;  // if it clear == 1, the scene should be cleared.

function negotiate () {
	// Create the user end's SDP
	return pc.createOffer().then(function (offer) {
	// Record the local SDP
		return pc.setLocalDescription(offer);
	}).then(function () {
		// wait for ICE gathering to complete
		return new Promise(function (resolve) {
			if (pc.iceGatheringState === 'complete') {
				resolve();
			} else {
				function checkState () {
					if (pc.iceGatheringState === 'complete') {
						pc.removeEventListener('icegatheringstatechange', checkState);
						resolve();
					}
				}
				pc.addEventListener('icegatheringstatechange', checkState);
			}
		});
	}).then(function () {
		var offer = pc.localDescription;
	// Return the local SDP to 信令服务
		return fetch('/offer', {
			body: JSON.stringify({
				sdp: offer.sdp,
				type: offer.type,
			}),
			headers: {
				'Content-Type': 'application/json'
			},
			method: 'POST'
		});
	}).then(function (response) {
	// Get and parse the SDP of server
		return response.json();
	}).then(function (answer) {
	// Record the SDP of server
		return pc.setRemoteDescription(answer);
	}).catch(function (e) {
		alert(e);
	});
}

function start () {
	// User End
	// The connection params of WebRTC
	var config = {
		sdpSemantics: 'unified-plan',
		iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }]
	};

	// Create WebRTC connection object
	pc = new RTCPeerConnection(config);

	// Create the Channel to transmit data.
	var sendChannel = pc.createDataChannel('sendDataChannel');

	// Send the file to server end through RTC
	sendChannel.onopen = (_) => {
		sendChannel.send('User End Establish Data Channel');
		console.log('The flag of establishing data channel is sent out!');
	}

	// Handle the returned data from user end.
	sendChannel.onmessage = (event) => {
		if (event.data == 'Server End Establish Data Channel'){
			console.log('Receive Estabalish Channel');
			sendChannel.send('Start Transmit');    // Start transmit the data.
		}
		else if (event.data == 'over'){      // All the data has been transmitted.
			console.log('All the files has been transmitted.')
		}
		// else if (event.data == 'start frame'){
		// 	console.log('Receive start frame');
		// }
		else if (event.data == 'end frame'){
			console.log('Receive end frame');
			// THREE.Cache.add(current_cache_store_index.toString(), new Float32Array(send_array));
			// current_cache_store_index += 1
			// caught += 1;
			clear = 1;
			sendChannel.send('Start Transmit');    // Start transmit the data.
		}
		else{
			console.log('Receive chunk');
			clear = 0;
			THREE.Cache.add(current_cache_store_index.toString(),event.data);
			current_cache_store_index += 1
			caught += 1;
		}
	}

	document.getElementById('start').style.display = 'none';
	document.getElementById('transmitting').style.display = 'inline-block';
	console.log('Start to negotiate!');
	negotiate();
}


function return_caught(){
	return caught;
}

function return_clear(){
	return clear;
}


start();

export { return_caught, return_clear };
