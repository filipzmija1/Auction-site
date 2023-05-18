import pytest

from datetime import datetime, timedelta

from django.test import TestCase
from django.contrib.auth.models import User

from .models import Auction, Item

@pytest.mark.django_db
def test_home_page(client):
    url = '/home/'
    response = client.get(url)
    assert response.context['title'] == 'Auction house'
    assert response.status_code == 200
    assert response.context['users'] == 0
    assert response.context['auctions'] == 0


@pytest.mark.django_db
def test_home_page_with_objects(auctions_create, user_create, client):
    url = '/home/'
    response = client.get(url)
    assert User.objects.count() == 3
    assert response.context['users'] == 3
    assert Auction.objects.count() == 5
    assert response.status_code == 200


@pytest.mark.django_db
def test_item_list(items_create, client):
    url = '/items/'
    response = client.get(url)
    assert response.status_code == 200
    assert Item.objects.count() == 3
    items = response.context['object_list']
    assert items[0].name == 'test1'
    assert items[1].name == 'test2'
    assert items[2].name == 'test3'


@pytest.mark.django_db
def test_item_detail(item, client):
    url = f'/items/{item.pk}'
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['item'] == item


@pytest.mark.django_db
def test_item_detail_fail(item, client):
    invalid_pk = item.pk + 1
    url = f'/items/{invalid_pk}/'
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_auction_list(auctions_create, client):
    url = '/auctions/'
    response = client.get(url)
    assert response.status_code == 200
    assert Auction.objects.count() == 5
    auctions = response.context['auction_list']
    assert auctions[0].name == 'random_name'
    assert auctions[1].name == 'random_name'
    assert auctions[2].name == 'random_name'
    assert auctions[3].name == 'random_name'
    assert auctions[4].name == 'random_name'


@pytest.mark.django_db
def test_auction_list_filter(auctions_create, client):
    url = '/auctions/?status=expired'
    response = client.get(url)
    assert response.status_code == 200
    assert 'auctions/expired_auction_list.html' in [t.name for t in response.templates] # Check if good template is used


@pytest.mark.django_db
def test_auctions_list_update_status(auction, client):
    """Create auction that should be expired"""
    url = '/auctions/'
    response = client.get(url)
    expired_auction = Auction.objects.get(pk=auction.pk)
    expired_auction.end_date = datetime.now() - timedelta(days=1)
    expired_auction.save()
    assert response.status_code == 200
    assert expired_auction.status == 'expired'