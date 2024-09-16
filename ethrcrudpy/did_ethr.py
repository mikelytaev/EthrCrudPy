import aiohttp
import asyncio
import json

from eth_account import Account


class EthDidService:
    def __init__(self, host='ws://localhost', port=8080):
        self.ws_url = f"{host}:{port}"

    async def connect(self):
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(self.ws_url)

    async def disconnect(self):
        await self.ws.close()
        await self.session.close()

    async def send_request(self, method, args):
        payload = json.dumps({
            "method": method,
            "args": args
        })
        await self.ws.send_str(payload)
        response = await self.ws.receive()

        if response.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(response.data)
            return data
        elif response.type == aiohttp.WSMsgType.ERROR:
            raise Exception(f"WebSocket error: {response.data}")

    async def get_did_by_address(self, address: str, chain_name):
        return (await self.send_request("getDidByAddress", {"address": address, "chainName": chain_name}))['result']

    async def get_did_doc(self, did: str):
        return (await self.send_request("getDidDoc", {"did": did}))['result']['didDocument']

    async def create_change_owner_hash(self, did: str, new_owner_address: str):
        return (await self.send_request("createChangeOwnerHash", {"did": did, "newOwnerAddress": new_owner_address}))['result']

    async def change_owner_signed(self, did: str, new_owner_address: str, signature):
        return (await self.send_request("changeOwnerSigned", {
            "did": did,
            "newOwnerAddress": new_owner_address,
            "signature": signature
        }))['result']

    async def change_owner(self, did: str, current_owner: Account, new_owner_address: str):
        hash = await self.create_change_owner_hash(did, new_owner_address)
        signed_hash = current_owner.unsafe_sign_hash(hash)
        return await self.change_owner_signed(did, new_owner_address, {"v": signed_hash.v, "r": hex(signed_hash.r), "s": hex(signed_hash.s)})


    async def create_set_attribute_hash(self, did: str, attr_name: str, attr_value: str, expired: int):
        return (await self.send_request("createSetAttributeHash", {
            "did": did,
            "attrName": attr_name,
            "attrValue": attr_value,
            "exp": expired
        }))['result']

    async def lookup_owner(self, did: str):
        return (await self.send_request("lookupOwner", {
            "did": did
        }))['result']

    async def set_attribute_signed(self, did: str, attr_name: str, attr_value: str, expired: int, signature):
        return (await self.send_request("setAttributeSigned", {
            "did": did,
            "attrName": attr_name,
            "attrValue": attr_value,
            "exp": expired,
            "signature": signature
        }))['result']

    async def set_attribute(self, owner: Account, did: str, attr_name: str, attr_value: str, expired: int):
        hash = await self.create_set_attribute_hash(did, attr_name, attr_value, expired)
        signed_hash = owner.unsafe_sign_hash(hash)
        return await self.set_attribute_signed(did, attr_name, attr_value, expired, {"v": signed_hash.v, "r": hex(signed_hash.r), "s": hex(signed_hash.s)})
