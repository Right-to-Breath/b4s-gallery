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


const {OpenSeaSDK, Chain} = require("opensea-js");
// const { WyvernSchemaName } = require('opensea-js/lib/types');
const { ethers } = require("ethers");

const OWNER_ADDRESS = "0xae83C177aC4c83a198f03775992DF5BC0c44EB9f";
const ACCOUNT_PRIVATE_KEY = '0x83325a2d81bbf971f66acf59465d51d7589f68b12f678fd94ebe99ab86bc7714';
const API_KEY = "efd24029cd3e40abb6af9dae6631e623";
// SELECTED_NETWORK = "main"; // noobs should have used mainnet...
// SELECTED_NETWORK_CHAIN_ID = "1";
const RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/sH1CBo7l611TyvPLqKRbPimvHMIdqIjI";
const NFT_CONTRACT_ADDRESS = "0x98a1ffdb36079ca1c243276676fda5bb49277d26";
const START_PRICE = "0.013";
const AUCTION_DAYS = 14;
const AUCTION_HOURS = 24;
const IS_AUCTION = true;


const provider = new ethers.JsonRpcProvider(RPC_URL);
const wallet = new ethers.Wallet(ACCOUNT_PRIVATE_KEY, provider);
  
const openseaSDK = new OpenSeaSDK(wallet, {
    chain: Chain.Mainnet,
    apiKey: API_KEY
    },
    null
);


const expirationTime = Math.round(Date.now() / 1000 + 60 * 60 * AUCTION_HOURS * AUCTION_DAYS);
//  for 'rinkeby' 0xc778417e063141139fce010982780140aa0cd5ab for mainnet use "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
let wethAddress = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2";
//let daiAddress = "0x6B175474E89094C44Da98b954EedeAC495271d0F";

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
    try {
        const { nft } = await openseaSDK.api.getNFT(NFT_CONTRACT_ADDRESS, argv.tokenId)
        const refresh_msg = await openseaSDK.api.refreshNFTMetadata(nft.contract, nft.identifier)
        const asset = {
            "tokenId": nft.identifier,
            "tokenAddress": nft.contract
        }
        
        return await openseaSDK.createListing({
            asset: asset,
            accountAddress: wallet.address,
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
        "message": `https://opensea.io/assets/ethereum/0x98a1ffdb36079ca1c243276676fda5bb49277d26/${argv.tokenId}`
    };
    console.log(JSON.stringify(message));
    process.exit(0);
});
