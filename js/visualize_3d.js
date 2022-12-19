import { PCDLoader } from './pcd_loader.js'
import { return_caught } from './client.js'
import { PLYLoader } from 'https://unpkg.com/three@0.138.0/examples/jsm/loaders/PLYLoader.js'

// 0. Enable a cache to store the ply file
THREE.Cache.enabled = true;
export var current_cache_display_index = 0

// 2. Visualize the ply files
var scene = new THREE.Scene();
var camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);

var renderer = new THREE.WebGLRenderer();
renderer.setSize( window.innerWidth, window.innerHeight );
document.body.appendChild( renderer.domElement );

// The demo before is creating a cube and display
// var geometry = new THREE.BoxGeometry( 1, 1, 1 );
// var material = new THREE.MeshBasicMaterial( { color: 0x00ff00 } );
// var cube = new THREE.Mesh( geometry, material );

// Now, we would like to display the ply file that got from webrtc channel

// scene.add( cube );

camera.position.z = 5;
var display_object = null;
var loader = new PLYLoader();


var render = function () {
	requestAnimationFrame( render );
	// cube.rotation.x += 0.1;
	// cube.rotation.y += 0.1;
	if (return_caught() == 1){
		
		// display_object = JSON.parse(THREE.Cache.get(current_cache_display_index.toString()));
        display_object = THREE.Cache.get(current_cache_display_index.toString());

		loader.load(display_object, function (geometry) {
            console.log('OK here');
			// const material = new THREE.PointsMaterial({
            //     color: 0xffffff,
            //     size: 0.4,
            //     opacity: 0.6,
            //     transparent: true,
            //     blending: THREE.AdditiveBlending,
            // });
            var mesh = new THREE.Points(geometry);
            console.log('hello there!');
            scene.add( mesh );
        });
        current_cache_display_index = current_cache_display_index + 1;
	}

	renderer.render(scene, camera);
};

render();