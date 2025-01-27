let bgColor;
let fontColor;
let canvas;
let sampleRate = 44100;
let frameLength = 2048;
let featureIndex = 0; // Start fetching from the first index
let particles = []; // Array to store particle objects
let noiseScale = 0.01; // Scale for Perlin noise
let maxParticles = 200; // Number of particles
let rmsValues = []; // Store fetched RMS values
let metallicMode = false; // Flag for metallic morphing liquid
let waterInkMode = false; // Flag for water ink texture
let shootingStarMode = false; // Flag for shooting star effects (from ZCR)
let metallicTimer = 0; // Timer for metallic mode (in frames)

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

    // Start fetching feature values
    setInterval(fetchFeatures, sampleRate / frameLength); // Fetch features every ~46ms
}

function createParticle() {
    return {
        x: random(width),
        y: random(height),
        size: random(5, 15),
        speed: random(1, 3),
        dirX: random([-1, 1]),
        dirY: random([-1, 1]),
        trail: [], // Array to store trail positions
        maxTrailLength: 10, // Length of the trail
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
    // ZCR shooting star mode takes priority
    if (shootingStarMode) {
        bgColor = color(0); // Black background for shooting star
        drawShootingStarEffect();
    } else if (metallicMode) {
        // Metallic mode, limited to 2 seconds
        bgColor = color(0); // Black background for metallic mode
        drawMetallicLiquidTexture();

        metallicTimer++;
        if (metallicTimer > 120) { // Limit to ~2 seconds (120 frames at 60fps)
            metallicMode = false; // Reset metallic mode
            metallicTimer = 0;
        }
    } else {
        // Default mode (water ink particles)
        bgColor = color(255); // White background
        drawWaterInkTexture();
    }

    // Display title text
    fill(fontColor);
    textAlign(CENTER, CENTER);
    textSize(48);
    text("Audio Feature Visualization", width / 2, height - 50);
}

function fetchFeatures() {
    fetch(`${SERVER_URL}/get_features/${featureIndex}`) // Fetch features for the current index
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then((data) => {
            if (data.zcr !== undefined && data.rms !== undefined) {
                // Store RMS value
                rmsValues.push(data.rms);

                // Analyze RMS behavior over the last 100 frames
                if (rmsValues.length >= 100) {
                    let last100 = rmsValues.slice(-100);
                    let avgRms = last100.reduce((a, b) => a + b, 0) / last100.length;
                    let fluctuation = Math.max(...last100) - Math.min(...last100);

                    if (fluctuation > 0.02) {
                        // Activate metallic mode if dramatic RMS changes
                        metallicMode = true;
                        waterInkMode = false;
                    } else {
                        // Stable RMS -> Default water ink
                        metallicMode = false;
                        waterInkMode = true;
                    }
                }

                // ZCR behavior (prioritized over RMS)
                if (data.zcr >= 0.02 && data.zcr <= 0.08) {
                    shootingStarMode = true; // Activate shooting star mode
                } else {
                    shootingStarMode = false; // Default mode
                }

                featureIndex++; // Increment feature index to fetch next values
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

function drawMetallicLiquidTexture() {
    // Draw morphing metallic liquid
    for (let i = 0; i < 10; i++) {
        let x = width / 2 + noise(frameCount * 0.01 + i) * 200;
        let y = height / 2 + noise(frameCount * 0.01 + i + 10) * 200;
        fill(0, 255, 150, 100);
        ellipse(x, y, 300 + sin(frameCount * 0.05) * 50, 200 + cos(frameCount * 0.05) * 50);
    }
}

function drawWaterInkTexture() {
    // Draw water ink-like particles
    for (let p of particles) {
        let n = noise(p.x * noiseScale, p.y * noiseScale);
        let angle = TAU * n;
        p.x += cos(angle) * p.speed * 0.5; // Slower, ink-like movement
        p.y += sin(angle) * p.speed * 0.5;

        fill(50, 50, 255, 150); // Blue ink color
        noStroke();
        ellipse(p.x, p.y, p.size * 2); // Larger, ink-like particles
    }
}

function drawShootingStarEffect() {
    // Shooting star effect
    for (let p of particles) {
        p.x += p.dirX * p.speed * 2; // Faster movement
        p.y += p.dirY * p.speed * 0.5; // Smaller vertical movement

        fill(color(0, 255, 0)); // Neon green particles
        noStroke();
        ellipse(p.x, p.y, p.size);

        // Reset particle if off-screen
        if (!onScreen(p)) {
            p.x = random(width);
            p.y = random(height);
        }
    }
}

