#!/usr/bin/env node
const argv = require('yargs/yargs')(process.argv.slice(2))
    .usage('Usage: $0 -n [num]')
    .demandOption(['n'])
    .option('tokenId', {
      description: 'Token number or id',
      alias: 'n',
      type: 'number'
    })
    .argv;


const opensea = require("opensea-js");
const { WyvernSchemaName } = require('opensea-js/lib/types');
const OpenSeaPort = opensea.OpenSeaPort;
const RPCSubprovider = require("web3-provider-engine/subproviders/rpc");
const Web3ProviderEngine = require("web3-provider-engine");
const PrivateKeyWalletSubprovider = require("@0x/subproviders").PrivateKeyWalletSubprovider;

OWNER_ADDRESS = "0xAd276706c9FdfDD50556892d7C7469DA10639bEB";
ACCOUNT_PRIVATE_KEY = "0f40fda5fad430bc38d2b130367cb0bd992bbcbc7eb507486ec19eabbcc85d27";
SELECTED_NETWORK = "rinkeby";
RPC_URL = "https://eth-rinkeby.alchemyapi.io/v2/VOnGmudV5KcqbZEwe40Nks4CbyKe2rsh";
NFT_CONTRACT_ADDRESS = "0xD653694558aF69d09709768aFac9e35C9Fb984C8";
START_PRICE = "0.0001";
AUCTION_DAYS = 1;
AUCTION_HOURS = 1;
IS_AUCTION = Math.floor(Math.random()*2);

const privateKeyWalletSubprovider = new PrivateKeyWalletSubprovider(ACCOUNT_PRIVATE_KEY, 4);

const providerEngine = new Web3ProviderEngine();
providerEngine.addProvider(privateKeyWalletSubprovider);
const infuraRpcSubprovider = new RPCSubprovider({rpcUrl: RPC_URL,});
providerEngine.addProvider(infuraRpcSubprovider);
providerEngine.start();

const seaport = new OpenSeaPort(
providerEngine,
  {
    networkName: SELECTED_NETWORK,
    // apiKey: API_KEY,
  },
  (arg) => console.log(arg)
);

const expirationTime = Math.round(Date.now() / 1000 + 60 * 60 * AUCTION_HOURS * AUCTION_DAYS);
//  for 'rinkeby' 0xc778417e063141139fce010982780140aa0cd5ab for mainnet use "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
let wethAddress = "0xc778417e063141139fce010982780140aa0cd5ab";


let options = {};
if (IS_AUCTION) {
    options = {
        waitForHighestBid: true,
        paymentTokenAddress: wethAddress,
        expirationTime: expirationTime,
    }
} else {
    options = {
        endAmount: START_PRICE
    }
}

async function main() {
    // console.log(`Account ${OWNER_ADDRESS} selling ${NFT_CONTRACT_ADDRESS} token #${argv.tokenId} on ${SELECTED_NETWORK} for ${START_PRICE} payment ERC ${wethAddress}.`);
    try {
        return await seaport.createSellOrder({
            asset: {
                tokenId: argv.tokenId,
                tokenAddress: NFT_CONTRACT_ADDRESS,
                schemaName: WyvernSchemaName.ERC721
            },
            accountAddress: OWNER_ADDRESS,
            startAmount: START_PRICE,
            ...options,
        })

    } catch (error) {
        let message = {
            "success": false,
            "message": error.message
        };
        console.log(JSON.stringify(message));
        process.exit(1);
    }
}

main().then(r => {
    let message = {
        "success": true,
        "message": `${r.asset.openseaLink}`
    };
    console.log(JSON.stringify(message));
    process.exit(0);
});
