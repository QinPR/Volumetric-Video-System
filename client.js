var pc = null;

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
	sendChannel = pc.createDataChannel('sendDataChannel');

	// Send the file to server end through RTC
	sendChannel.onopen = (_) => {
		sendChannel.send('User End Establish Data Channel');
		console.log('The flag of establishing data channel is sent out!');
	}

	// Handle the returned data from user end.
	sendChannel.onmessage = (event) => {
		if (event.data == 'Server End Establish Data Channel'){
			sendChannel.send('Start Transmit');    // Start transmit the data.
		}
		else if (event.data == 'over'){      // All the data has been transmitted.
			console.log('All the files has been transmitted.')
		}
		else{
			sendChannel.send('Start Transmit');    // Start transmit the data.
		}
	}

	document.getElementById('start').style.display = 'none';
	document.getElementById('transmitting').style.display = 'inline-block';
	console.log('Start to negotiate!');
	negotiate();
}