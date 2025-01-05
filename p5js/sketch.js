let zcrIndex = 0; // Start fetching ZCR from index 0
let bgColor;
let fontColor;

//const SERVER_URL = "http://192.168.1.182:5050"; // Update to match your Python server address
const SERVER_URL = "http://127.0.0.1:5050";

function setup() {
    createCanvas(400, 400); // Canvas size
    bgColor = color(255); // Default background color (white)
    fontColor = color(0); // Default font color (black)
    setInterval(fetchZCR, 100); // Fetch ZCR every 100ms
}

function draw() {
    background(bgColor);

    fill(fontColor);
    textAlign(CENTER, CENTER);
    textSize(48);
    text("Demo", width / 2, height / 2);
}

function fetchZCR() {
    fetch(`${SERVER_URL}/get_zcr/${zcrIndex}`) // Dynamically request ZCR for current index
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then((data) => {
            if (data.zcr !== undefined) {
                // console.log("ZCR:", data.zcr); // Log the ZCR value
                if ( 0.06 < data.zcr < 0.08) {
                    bgColor = color(0); // Change background to black
                    fontColor = color(255); // Change font color to white
                } else {
                    bgColor = color(255); // Default background color (white)
                    fontColor = color(0); // Default font color (black)
                }
                zcrIndex++; // Increment index to fetch next value
            } else if (data.error) {
                console.error(`Error from server: ${data.error}`); // Log server error
            }
        })
        .catch((err) => {
            console.error("Fetch error:", err); // Log fetch error
        });
}