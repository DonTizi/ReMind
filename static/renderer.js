document.addEventListener("DOMContentLoaded", function () {
    const chatInput = document.querySelector("#chat-input");
    const sendButton = document.querySelector("#send-btn");
    const chatContainer = document.querySelector(".chat-container");
    const themeButton = document.querySelector("#theme-btn");
    const deleteButton = document.querySelector("#delete-btn");


    // Load and manage theme and chat history
    const loadDataFromLocalstorage = () => {
        const themeColor = localStorage.getItem("themeColor");
        document.body.classList.toggle("light-mode", themeColor === "light_mode");
        themeButton.innerText = document.body.classList.contains("light-mode") ? "dark_mode" : "light_mode";

        const defaultText = `<div class="default-text">
            <h1>Recall AI</h1>
            <p>Start a conversation with your locally Artificial Memory.<br> Display the power of Artificial Memory.</p>
        </div>`;

        chatContainer.innerHTML = localStorage.getItem("all-chats") || defaultText;
        chatContainer.scrollTo(0, chatContainer.scrollHeight);
    };

    loadDataFromLocalstorage();


        // Three.js setup for 3D Object
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('three-container').appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(0, 1, 0);
    scene.add(directionalLight);

    // GLTF Loader
    let gltfModel;
    const loader = new THREE.GLTFLoader();
    loader.load(
        '../assets/brain_hologram.glb',  // Update the path to your model
        function (gltf) {
            gltfModel = gltf.scene;
            gltfModel.scale.set(20, 20, 20);  // Scale the model
            gltfModel.position.set(0, 110, 0); // Position the model
            scene.add(gltfModel);
        },
        undefined,
        function (error) {
            console.error('An error happened:', error);
        }
    );

    // Adjust camera position and orientation
    camera.position.set(0, 150, 100);
    camera.lookAt(new THREE.Vector3(0, 30, 0));

    function animate() {
        requestAnimationFrame(animate);
        if (gltfModel) {
            gltfModel.rotation.y += 0.01;
        }
        renderer.render(scene, camera);
    }

    animate();

    // Handle window resize
    // Handle window resize
    // Handle window resize
    window.addEventListener('resize', () => {
        renderer.setSize(window.innerWidth, window.innerHeight);
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
    });

    let currentIncomingMessageDiv = null;
    let typingAnimationDiv = null;

    const socket = io('http://localhost:8000');

    socket.on('response_message', function(data) {
        const { message, isFirstChunk, isIncomplete } = data;
    
        if (isFirstChunk) {
            // Start with typing animation
            if (typingAnimationDiv) {
                chatContainer.removeChild(typingAnimationDiv);
            }
            displayTypingAnimation();
            currentIncomingMessageDiv = createChatElement('', 'incoming');
            chatContainer.appendChild(currentIncomingMessageDiv);
        } else {
            // Remove typing animation after the first chunk
            if (typingAnimationDiv) {
                chatContainer.removeChild(typingAnimationDiv);
                typingAnimationDiv = null;
            }
        }
    
        if (currentIncomingMessageDiv) {
            const pElement = currentIncomingMessageDiv.querySelector('p');
            pElement.textContent += message;  // Append the chunk directly
        }
    
        if (!isIncomplete) {
            currentIncomingMessageDiv = null;
            chatInput.disabled = false;
            sendButton.disabled = false;
        }
    });
    

    function createChatElement(content, className) {
        const chatDiv = document.createElement("div");
        chatDiv.classList.add("chat", className);
        chatDiv.innerHTML = `<div class="chat-details"><p>${content}</p></div>`;
        return chatDiv;
    }

    function displayTypingAnimation() {
        typingAnimationDiv = document.createElement("div");
        typingAnimationDiv.classList.add("chat", "incoming");
        typingAnimationDiv.innerHTML = `<div class="loader"></div>`;
        chatContainer.appendChild(typingAnimationDiv);
    }

    const handleOutgoingChat = () => {
        const userText = chatInput.value.trim();
        if (!userText) return;
        chatInput.disabled = true;
        sendButton.disabled = true;
    
        chatInput.value = "";
        const outgoingChatDiv = createChatElement(userText, 'outgoing');
        chatContainer.appendChild(outgoingChatDiv);
        chatContainer.scrollTo(0, chatContainer.scrollHeight);
    
        socket.emit('send_message', {message: userText});
    };

    sendButton.addEventListener("click", handleOutgoingChat);
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleOutgoingChat();
        }
    });

    deleteButton.addEventListener("click", () => {
        if (confirm("Are you sure you want to delete all the chats?")) {
            localStorage.removeItem("all-chats");
            loadDataFromLocalstorage();
        }
    });

    themeButton.addEventListener("click", () => {
        document.body.classList.toggle("light-mode");
        localStorage.setItem("themeColor", document.body.classList.contains("light-mode") ? "dark_mode" : "light_mode");
        themeButton.innerText = document.body.classList.contains("light-mode") ? "dark_mode" : "light_mode";
    });
});
