import asyncio
import unittest

import pytest
from eth_account import Account

from ethrcrudpy.did_ethr import EthDidService


@pytest.mark.asyncio
class TestEthrDidCrud:

    async def test_get_did_by_address(self):
        account = Account.create()

        service = EthDidService()
        await service.connect()

        try:
            did = await service.get_did_by_address(account.address, 'polygon')
            assert did == f'did:ethr:polygon:{account.address}'

        finally:
            await service.disconnect()


    async def test_get_did_doc(self):
        service = EthDidService()
        await service.connect()

        try:
            did = 'did:ethr:polygon:0xf14BED645685447D295159E26e5F634e7a1154F1'
            did_doc = await service.get_did_doc(did)
            assert '@context' in did_doc
            assert did_doc['id'] == did
            assert 'verificationMethod' in did_doc
            assert 'authentication' in did_doc
            assert 'assertionMethod'in did_doc

        finally:
            await service.disconnect()


    async def test_change_owner(self):
        current_owner = Account.create()
        new_owner = Account.create()

        service = EthDidService()
        await service.connect()

        try:
            did = await service.get_did_by_address(current_owner.address, 'polygon')
            lookup_owner = await service.lookup_owner(did)
            assert lookup_owner == current_owner.address
            await service.change_owner(did, current_owner, new_owner.address)
            lookup_owner2 = await service.lookup_owner(did)
            assert lookup_owner != lookup_owner2

        finally:
            await service.disconnect()

    async def test_set_attribute(self):
        owner = Account.create()

        service = EthDidService()
        await service.connect()

        try:
            did = await service.get_did_by_address(owner.address, 'polygon')
            await service.set_attribute(owner, did, 'did/svc/HubService', 'https://hubs.uport.me', 86400)
            did_doc = await service.get_did_doc(did)
            assert 'service' in did_doc

        finally:
            await service.disconnect()