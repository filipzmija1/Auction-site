import pytest

from datetime import datetime

from django.test import Client
from django.contrib.auth import get_user_model

from auctions.models import Auction, Item, Category


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user_create():
    user = get_user_model().objects.create_user(username='testuser', password='12345')
    return user


@pytest.fixture
def auctions_create():
    buyer = get_user_model().objects.create_user(username='testuser2', password='12345')
    seller = get_user_model().objects.create_user(username='testuser3', password='12345')
    category = Category.objects.create(name='testname', description='ttest')
    item = Item.objects.create(name='test', description='test', category=category)
    for _ in range(5):
        Auction.objects.create(
            name='random_name',
            item=item,
            min_price=20,
            buy_now_price=100,
            end_date=datetime.now(),
            seller=seller,
            buyer=buyer)


@pytest.fixture
def items_create():
    category = Category.objects.create(name='testname', description='ttest')
    Item.objects.create(name='test1', description='test', category=category)
    Item.objects.create(name='test2', description='test', category=category)
    Item.objects.create(name='test3', description='test', category=category)


@pytest.fixture
def item():
    category = Category.objects.create(name='testname', description='ttest')
    item = Item.objects.create(name='test1', description='test', category=category)
    return item


@pytest.fixture
def auction():
    buyer = get_user_model().objects.create_user(username='testuser2', password='12345')
    seller = get_user_model().objects.create_user(username='testuser3', password='12345')
    category = Category.objects.create(name='testname', description='ttest')
    item = Item.objects.create(name='test', description='test', category=category)
    auction = Auction.objects.create(
            name='random_name',
            item=item,
            min_price=20,
            buy_now_price=100,
            end_date=datetime.now(),
            seller=seller,
            buyer=buyer)
    return auction