let bgColor;
let fontColor;
let canvas;
let sampleRate = 44100;
let frameLength = 2048;
let zcrIndex = 0; // Start fetching from the first index
let particles = []; // Array to store particle objects
let noiseScale = 0.01; // Scale for Perlin noise
let maxParticles = 200; // Number of particles

// Server URL
const SERVER_URL = "http://127.0.0.1:5050";

function setup() {
    canvas = createCanvas(1600, 1000); // Canvas size
    centerCanvas();
    bgColor = color(255); // Default background color (white)
    fontColor = color(0); // Default font color (black)

    // Initialize particles
    for (let i = 0; i < maxParticles; i++) {
        particles.push(createParticle());
    }

    // Start fetching ZCR values
    setInterval(fetchZCR, sampleRate / frameLength); // Fetch ZCR every ~46ms
}

function createParticle() {
    return {
        x: random(width),
        y: random(height),
        size: random(5, 15),
        speed: random(1, 3),
        dirX: random([-1, 1]),
        dirY: random([-1, 1]),
    };
}

function centerCanvas() {
    let x = (windowWidth - width) / 2; // Center horizontally
    let y = (windowHeight - height) / 2; // Center vertically
    canvas.position(x, y); // Set the canvas position
}

function windowResized() {
    centerCanvas();
}

function draw() {
    background(bgColor);

    // Draw particles
    for (let p of particles) {
        let n = noise(p.x * noiseScale, p.y * noiseScale);
        let angle = TAU * n;

        // Update particle position based on Perlin noise
        p.x += cos(angle) * p.dirX * p.speed;
        p.y += sin(angle) * p.dirY * p.speed;

        // Calculate color based on position
        let d = dist(width / 2, height / 2, p.x, p.y) / (width / 2);
        let colorValue = lerpColor(color(0, 100, 255), color(255, 0, 150), d);
        fill(colorValue);
        noStroke();
        ellipse(p.x, p.y, p.size);

        // Reset particle if it goes off-screen
        if (!onScreen(p)) {
            p.x = random(width);
            p.y = random(height);
            p.dirX *= -1;
            p.dirY *= -1;
        }
    }

    fill(fontColor);
    textAlign(CENTER, CENTER);
    textSize(48);
    text("ZCR Visualization", width / 2, height - 50);
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
                console.log(`ZCR: ${data.zcr}`); // Log the ZCR value
                if (data.zcr >= 0.02 && data.zcr <= 0.08) {
                    // Trigger particle noise effect
                    noiseScale = random(0.005, 0.02); // Adjust noise scale dynamically
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

function onScreen(p) {
    return p.x > 0 && p.x < width && p.y > 0 && p.y < height;
}
