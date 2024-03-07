#!/usr/bin/env node
const argv = require('yargs/yargs')(process.argv.slice(2))
    .usage('Usage: $0 -w [num] -h [num]')
    .demandOption(['b', 'p'])
    .option('breathPath', {
        description: 'Path to Breath data json.',
        alias: 'b',
        type: 'string'
    })
    .option('imagePath', {
        description: 'Output filename with path. i.e. ./images/1',
        alias: 'p',
        type: 'string'
    })
    .argv;

const p5 = require('node-p5');
const {resolve} = require("path");

let breathData;
let breathFilePath;
let imageFilePath;
try {
    breathFilePath = resolve(argv.breathPath);
    breathData = require(breathFilePath);
    imageFilePath = resolve(argv.imagePath);
    p5.loadFont("./RobotoCondensed-Regular.ttf")
} catch (err) {
    let message = {
        "success": false,
        "error": `Could not load file on path ${breathFilePath}. Check for correct linux or windows paths.`
    };
    console.log(JSON.stringify(message));
    process.exit(1);
}

// const breath = JSON.parse(argv.breath);
const canvasWidth = 1500;
const canvasHeight = 1500;

// DEFINES eCO2 SPRAYS CHARACTERS USED - white stars & tail
const alphabet = ".¨˙•:";
// DEFINES eCO2 SPRAYS SPECIAL CHARACTER - white stars & tail
// Please use long & lat to choose one special character
const alphabet_special = "∆∞◊+×>÷#ΠΔΓФo*ΞθI[/";
const deltaTemp = breathData.data.breath.temp - breathData.data.ref1.temp;
const breathTemp = breathData.data.breath.temp;
const CO2 = breathData.data.breath.CO2;
const ethanol = breathData.data.breath.ethanol;
const h2 = breathData.data.breath.h2;
const eCO2 = breathData.data.breath.eCO2;
const humidity = breathData.data.breath.hum;
const hash =  breathData.data.hash;
const id =  breathData.id;
const lat =  breathData.data.coord.latitude;
const lon =  breathData.data.coord.longitude;
const selected_char = alphabet_special[Math.floor(Math.abs(lat+lon) % alphabet_special.length)]
// DEFINE STARTING DRAWING POSITION AND THUS IMG DIST
const CENTER = Math.floor(humidity % 2) == true;
// CO-DEFINES UNIQUE PATTERN (shuffels the deck to draw cards)
let seed = Math.abs(breathData.data.rfid ^ hash);
// console.log(deltaTemp, breathTemp, CO2, ethanol, h2, eCO2, humidity, seed, hash, CENTER, selected_char, Math.floor((lat+lon) % alphabet_special.length));
const chaos = require('./chaosLib')(seed, canvasWidth, canvasHeight);

const {BLACK, WHITE, WHITE1, WHITE2, WHITE3, MS_01, MS_02, MS_03, MS_04 , MS_05, MS_06, TOP, BOT} =
    require("./envvars")(chaos.random_range(deltaTemp^breathTemp), chaos.random_range(breathTemp));

// DEFINES STEP SIZE (distance grid points (output:10-18)) basend on CO2 input
let stepSize = chaos.range_scale(CO2, 200, 5000, 13, 17);
// DEFINE IF THE PICTURE WILL HAVE REDUCED CLOUDS
let centered_reduction = 1;
if (CENTER && Math.floor(id % 2) == true) {
    centered_reduction = 0.88;
}
// DEFINES NUMBER OF CIRCLES
const ratio_clouds_ethanol = ((19.7 - stepSize)/3.35) * centered_reduction;
const ratio_clouds_h2 = ((30.0 - stepSize)/14.1) * centered_reduction;

// DRAWS eCO2 LINES - white lines on top
const total_lines = chaos.range_scale(eCO2, 9000, 11000, 9000, 11000);
// DRAWS eCO2 STARS - white characters on top
const total_stars = chaos.range_scale(eCO2, 9000, 11000, 7000, 20000);



let posX, posY;
if (CENTER) {
    posX = canvasWidth / 2;
    posY= canvasHeight / 2;
} else {
    posX = chaos.random_range(canvasWidth);
    posY = chaos.random_range(canvasHeight);
}

// Updates module vars
chaos.seed = seed;
chaos.posX = posX;
chaos.posY = posY;
chaos.stepSize = stepSize;

// Updates values for both the chaos and current modules
// REQUIRED AFTER ALL RANDOM CALLS
function _updateCursorPosition() {
    posX = chaos.posX;
    posY = chaos.posY;
    chaos.stepSize = stepSize;
}

let resourcesToPreload = {
    logo: p5.loadImage('logo.png')
}

function sketch(p, preloaded) {

    let logo = preloaded.logo;
    // Paints a random sized square once or twice
    function _draw_rnd_circle(max_size, bkg, color) {
        p.noStroke();
        p.fill(bkg);
        let size = chaos.random_range(max_size);
        p.circle(posX, posY, size);
        if(color){
            p.fill(color);
            p.circle(posX, posY, size);
        }
    }

    // Paint a random character once or twice
    function _draw_rnd_text(text_size, char_set, color, color2, text_size_increment) {
        p.noStroke();
        p.fill(color);
        p.textSize(text_size);
        let selChar = char_set.length> 1 ? chaos.rand_char(char_set) : char_set
        p.text(selChar, posX, posY);
        if(color2){
            p.fill(color2);
            p.textSize(text_size+text_size_increment);
            p.text(selChar, posX, posY);
            p.fill(color2);
            p.textSize(text_size+text_size_increment*text_size_increment);
            p.text(selChar, posX, posY);
        }
    }

    // Draw circles in a cloud pattern
    function drawCloud(dataInput, ratio, dotMaxSize, firstColor, secondColor=undefined, stepIncrease=0, center=false, faster= false) {
        stepSize += stepIncrease;
        for (let i = 0; i <= (dataInput) * ratio; i++) {
            if (faster) {
                chaos.drunkard_walk_faster(center);
            } else {
                chaos.drunkard_walk(1, 1, center);
            }
            _updateCursorPosition();
            _draw_rnd_circle(dotMaxSize, firstColor, secondColor);
        }
    }

    // Draw lines based on dot matrix and distance
    function drawGeometricalLines(dataInput, ratio, strokeWeight, strokeColor, lineMaxDistance=canvasWidth/2, stepSizeMultiX=1, stepSizeMultiY=1, center=false) {
        let matrix = [];
        for (let i = 0; i <= (dataInput) * ratio; i++) {
            chaos.drunkard_walk(stepSizeMultiX, stepSizeMultiY, center);
            _updateCursorPosition();
            matrix.push([posX, posY]);
            if (matrix.length > 2) {
                let previous = matrix[i - 1];
                let current = matrix[i];
                let distance = Math.hypot(previous[0] - current[0], previous[1] - current[1]);
                if (distance < lineMaxDistance) {
                    p.strokeWeight(strokeWeight);
                    p.stroke(strokeColor);
                    p.line(current[0], current[1], previous[0], previous[1]);
                }
            }
        }
    }

    // Draws waves of sprayed characters with one or two colors
    function drawCharacterSpray(ratioStars, dataInput, textSize, charSet, firstColor, secondColor, textSizeIncrement, center = false, sparse = false) {
        for (let i = 0; i <= ratioStars; i++) {
            if (sparse) {
                chaos.random_pos();
            } else {
                chaos.drunkard_walk(1,1, center);
                p.rotate(dataInput);
            }
            _updateCursorPosition();
            _draw_rnd_text(textSize, charSet, firstColor, secondColor, textSizeIncrement);
        }
        p.resetMatrix();
    }

    let canvas;

    p.setup = function setup() {
        canvas = p.createCanvas(canvasWidth, canvasHeight);
        p.noLoop();
        p.background(BLACK);
    };

    p.draw = function draw() {

        // ETHANOL CLOUD 001
        drawCloud(ethanol, ratio_clouds_ethanol, 20, WHITE, BOT, -1, CENTER, true);
        // ETHANOL CLOUD 002
        drawCloud(ethanol, ratio_clouds_ethanol, 20, WHITE, BOT, -1, CENTER, true);
        drawCloud(ethanol, ratio_clouds_ethanol, 20, WHITE, MS_04, -1, CENTER, true);

        // DRAWS H2 CLOUDS - colored circles "perimeter"
        drawCloud(h2, ratio_clouds_h2, 20, WHITE, MS_05, -1, CENTER);
        drawCloud(h2, ratio_clouds_h2, 20, WHITE, MS_03, -1, CENTER);
        drawCloud(h2, ratio_clouds_h2, 20, WHITE, MS_06, -1, CENTER);
        drawCloud(h2, ratio_clouds_h2, 20, WHITE, MS_01, -1, CENTER);
        drawCloud(h2, ratio_clouds_h2, 20, WHITE, MS_02, 6, CENTER);
        drawCloud(h2, ratio_clouds_h2, 20, WHITE, TOP, 3.5, CENTER);

        // DRAWS eCO2 LINES - white lines on top
        drawGeometricalLines(total_lines, 1/64, 1.5, WHITE3, 500, 8, 8);
        // DRAWS eCO2 LINES - white lines on top
        drawGeometricalLines(total_lines, 1/8, 1, WHITE2, 500, 4, 4);
        // DRAWS eCO2 LINES - white lines on top
        drawGeometricalLines(total_lines, 1/32, 1, WHITE2, 500, 2, 2);
        // DRAWS eCO2 LINES - white lines on top
        drawGeometricalLines(total_lines, 1/32, 1, WHITE2, 500, 1, 1);



        // DRAWS eCO2 SPRAYS - white stars & tail (breath.eCO2) * ratio_stars
        drawCharacterSpray(total_stars, humidity, 20, alphabet, WHITE1, WHITE2, 2);
        p.resetMatrix();
        drawCharacterSpray(total_stars*0.02, humidity, 14 , selected_char, WHITE1, WHITE2, 2,);
        p.resetMatrix();
        drawCharacterSpray(chaos.random_range(6), humidity, 10 , "φ", WHITE1, WHITE2, 2, false, true);

        // // DRAWS LOPHI LOGO
        p.noStroke();

        p.fill('rgba(255,255,255, 1)');
        // // //textFont(use something which is similarly thin to white lines or check with design guidelines?!);
        p.textSize(17);
        // p.textStyle(p.BOLD);
        // p.blendMode(p.DIFFERENCE);
        p.image(logo, canvasWidth-189, canvasHeight-54, 143, 11);

        p5Instance.saveCanvas(canvas, imageFilePath, 'png').then(f => {
            let message = {"success": true, "path": f};
            console.log(JSON.stringify(message));
            // console.timeEnd("total");
            process.exit(0);
        }).catch((err) => {
            let message = {"success": false, "error": err.message};
            console.log(JSON.stringify(message));
            // console.timeEnd("total");
            process.exit(1);
        });
    };
}


// console.time("total");
let p5Instance = p5.createSketch(sketch, resourcesToPreload);

