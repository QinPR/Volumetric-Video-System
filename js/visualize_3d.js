import { return_caught, return_clear } from './client.js';

// 0. Enable a cache to store the ply file
THREE.Cache.enabled = true;
var current_cache_display_index = 0

// 2. Visualize the ply files
var scene = new THREE.Scene();
var camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);

var renderer = new THREE.WebGLRenderer();
renderer.setSize( window.innerWidth, window.innerHeight );
renderer.setClearColor('rgb(255,255,255)', 0);
document.body.appendChild( renderer.domElement );

camera.position.set(0.535 * 4, 0, 0.575 * 4);
camera.lookAt(new THREE.Vector3(0, 0, 0));
var display_object = null;
var pointcloud = null;
var expected_caught = 1;

function return_scene(){
    return scene;
};

function animate() {
    //requestAnimationFrame( animate );
    if (return_clear() == 1){
        if (return_caught() >= expected_caught){
            if(scene.children.length > 0){ 
                scene.remove(scene.children[0]); 
            }
            var array = []
            while (current_cache_display_index < return_caught()){
                array = array.concat(JSON.parse(THREE.Cache.get(current_cache_display_index.toString())));
                THREE.Cache.remove(current_cache_display_index.toString());
                current_cache_display_index += 1;
                expected_caught += 1;
            }
            display_object = new Float32Array(array);
            const geometry = new THREE.BufferGeometry();
            var attribute = new THREE.BufferAttribute(display_object, 3);      // 3 means axis-xyz
            geometry.addAttribute( 'position' , attribute);  
            const material = new THREE.PointsMaterial( { color: 0x00ff00, size: 0.005 } );
            pointcloud = new THREE.Points(geometry, material);
            scene.add( pointcloud );
            console.log('Successfule add pointcloud!');
        }
    }
    renderer.render(scene, camera);
};

// animate();
setInterval(function () {
    animate();
}, 50);


var current_time_index = 1;    // every one means 10ms
var current_view_point = null;
var viewpoint_testset = null;
var get_dataset = 0;   // A flag indicating whether the dataset is loaded.
var url = './js/viewport_change.json';
var request = new XMLHttpRequest();
request.open('get', url)
request.send(null);
request.onload = function() {
    if (request.status == 200) {
        viewpoint_testset = JSON.parse(request.responseText);
        get_dataset = 1;
    }
}

function change_view() {
    if (get_dataset == 1){
        current_view_point = [viewpoint_testset['x'][current_time_index]  * 4, 0, viewpoint_testset['z'][current_time_index] * 4];
        camera.position.set(viewpoint_testset['x'][current_time_index] * 4, 0, viewpoint_testset['z'][current_time_index] * 4);
        current_time_index = current_time_index + 1;
    }
};

setInterval(function () {
    change_view();
}, 10);



export { return_scene };
