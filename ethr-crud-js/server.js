import { WebSocketServer } from 'ws';
import fs from 'fs';
import yaml from 'js-yaml';
import {InfuraProvider, Wallet} from "ethers";
import {getResolver} from "ethr-did-resolver";
import {Resolver} from "did-resolver";
import {EthrDID} from "ethr-did";

// Load the YAML configuration
const config = yaml.load(fs.readFileSync('./config.yaml', 'utf8'));
const providerConfig = {
    networks: [
        { name: "mainnet", provider: new InfuraProvider('mainnet', config.providers.infura) },
        { name: "polygon", provider: new InfuraProvider('matic', config.providers.infura) }
    ]
}
const ethrDidResolver = getResolver(providerConfig)
const didResolver = new Resolver(ethrDidResolver)

// Create a WebSocket server with the port from the config file
const wss = new WebSocketServer({ port: config.server.port });

function getEthrDid(did) {
    const splitted_did = did.split(':')
    const netname = (splitted_did.length === 4) ? splitted_did[2] : 'mainnet'
    const provider = providerConfig.networks.find(network => network.name === netname).provider
    const txSigner = new Wallet(config.signerPrivateKey, provider)
    return new EthrDID({
        identifier: did,
        chainNameOrId: netname,
        provider: provider,
        txSigner: txSigner
    })
}

wss.on('connection', (ws) => {
    console.log('Client connected');

    ws.on('message', async (message) => {
        const data = JSON.parse(message);
        const { method, args } = data;

        try {
            let result;
            if (method === 'getDidByAddress') {
                const ethrDid = new EthrDID({identifier: args['address'], chainNameOrId: args['chainName']})
                result = ethrDid.did
            } else if (method === 'getDidDoc') {
                result = await didResolver.resolve(args['did'])
            } else if (method === 'createChangeOwnerHash') {
                const ethrDid = getEthrDid(args['did'])
                result = await ethrDid.createChangeOwnerHash(args['newOwnerAddress'])
            } else if (method === 'lookupOwner') {
                const ethrDid = getEthrDid(args['did'])
                result = await ethrDid.lookupOwner(false)
            } else if (method === 'changeOwnerSigned') {
                const ethrDid = getEthrDid(args['did']);
                result = await ethrDid.changeOwnerSigned(args['newOwnerAddress'], {
                    sigV: args['signature']['v'],
                    sigR: args['signature']['r'],
                    sigS: args['signature']['s'],
                })
            } else if (method === 'createSetAttributeHash') {
                const ethrDid = getEthrDid(args['did'])
                result = await ethrDid.createSetAttributeHash(args['attrName'], args['attrValue'], Number(args['exp']))
            } else if (method === 'setAttributeSigned') {
                const ethrDid = getEthrDid(args['did']);
                result = await ethrDid.setAttributeSigned(args['attrName'], args['attrValue'], Number(args['exp']), {
                    sigV: args['signature']['v'],
                    sigR: args['signature']['r'],
                    sigS: args['signature']['s'],
                })
            }

            ws.send(JSON.stringify({ success: true, result }));
        } catch (error) {
            ws.send(JSON.stringify({ success: false, error: error.message }));
        }
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

console.log('WebSocket server is running on ws://localhost:8080');
