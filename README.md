
# Breath4.sale Backend server 🖼️

## How to install the dependencies ⚒
Install Python 3.10.
Using the terminal `cd` into the root folder and run:
```
python3 -m venv -p python3 venv
source venv/activate
pip install -r requirements.txt
```

Install Node.js and [NVM](https://github.com/nvm-sh/nvm).
Using the terminal `cd` into `scripts` and run:
```
nvm install 16 && nvm use 16
npm install
node ./scripts/generate.js -b ./collections/PH_8747/breath/0.json -w 3000 -h 3000 -p ./collections/PH_8747/images/0
```

## How to launch the applications 🚀
Get help message:
```sh
node ./scripts/generate.js
```
Run the image generator:
```
uvicorn api:breath_test
node ./scripts/generate.js -b ./collections/PH_8747/breath/0.json -w 3000 -h 3000 -p ./collections/PH_8747/images/0
```


# Breath4.sale  🖼️

## How to install ⚒
Install Node.js and [NVM](https://github.com/nvm-sh/nvm).
Using the terminal `cd` into this folder and run:
```
nvm install 16
npm install
node ./scripts/generate.js -b ./collections/PH_8747/breath/0.json -w 3000 -h 3000 -p ./collections/PH_8747/images/0
```

## How to launch 🚀
Get help message:
```sh
node ./scripts/generate.js
```
Run the image generator:
```
node ./scripts/generate.js -b ./collections/PH_8747/breath/0.json -w 3000 -h 3000 -p ./collections/PH_8747/images/0
```
