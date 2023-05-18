import pytest

from datetime import datetime, timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Auction, Item, Category, Bid

@pytest.mark.django_db
def test_home_page(client):
    """Tests home view"""
    url = '/home/'
    response = client.get(url)
    assert response.context['title'] == 'Auction house'
    assert response.status_code == 200
    assert response.context['users'] == 0
    assert response.context['auctions'] == 0


@pytest.mark.django_db
def test_home_page_with_objects(auctions_create, user_create, client):
    """Tests home view"""
    url = '/home/'
    response = client.get(url)
    assert User.objects.count() == 3
    assert response.context['users'] == 3
    assert Auction.objects.count() == 5
    assert response.status_code == 200


@pytest.mark.django_db
def test_item_list(items_create, client):
    """Tests item list view"""
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
    """Tests item details view"""
    url = f'/items/{item.pk}'
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['item'] == item


@pytest.mark.django_db
def test_item_detail_fail(item, client):
    """Tests item details view"""
    invalid_pk = item.pk + 1
    url = f'/items/{invalid_pk}/'
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_auction_list(auctions_create, client):
    """Tests auction list view"""
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
    """Tests auction list view"""
    url = '/auctions/?status=expired'
    response = client.get(url)
    assert response.status_code == 200
    assert 'auctions/expired_auction_list.html' in [t.name for t in response.templates] # Check if good template is used


@pytest.mark.django_db
def test_auctions_list_update_status(auction, client):
    """Create auction that should be expired, tests auction list view"""
    url = '/auctions/'
    response = client.get(url)
    expired_auction = Auction.objects.get(pk=auction.pk)
    expired_auction.end_date = datetime.now() - timedelta(days=1)
    expired_auction.save()
    assert response.status_code == 200
    assert expired_auction.status == 'expired'


@pytest.mark.django_db
def test_auction_details(auction, client):
    """Tests auction details view"""
    url = f'/auction/{auction.pk}'
    response = client.get(url)
    assert response.status_code == 200
    assert 'auction' in response.context
    assert 'opinions' in response.context
    assert 'average_rating' in response.context


@pytest.mark.django_db
def test_auction_details_opinions(auction, client):
    """Test the opinions in the AuctionDetails view"""
    url = f'/auction/{auction.pk}'
    response = client.get(url)
    opinions = response.context['opinions']
    assert len(opinions) == 1
    opinion = opinions[0]
    assert opinion.auction == auction
    assert opinion.reviewer.username == 'testuser2'
    assert opinion.rating == 5
    assert opinion.comment == 'Average auction'


@pytest.mark.django_db
def test_auction_details_average_rating(auction, client):
    """Test the average rating in the AuctionDetails"""
    url = f'/auction/{auction.pk}'
    response = client.get(url)
    average_rating = response.context['average_rating']
    assert average_rating == 5.0 


@pytest.mark.django_db
def test_categories_list(categories_create, client):
    """Tests CategoryList view"""
    url = '/categories/'
    response = client.get(url)
    assert response.status_code == 200
    assert Category.objects.count() == 5
    categories = response.context['category_list']
    assert categories[0].name == 'test'
    assert categories[1].name == 'testtest'
    assert categories[2].name == 'testtesttest'
    assert categories[3].name == 'testtesttesttest'
    assert categories[4].name == 'testtesttesttesttest'


@pytest.mark.django_db
def test_category_details(category, client):
    """Tests CategoryDetails view"""
    url = f'/category/{category.name}'
    response = client.get(url)
    assert response.context['category'] == category
    assert response.status_code == 200
    assert response.context['items'].count() == 2


@pytest.mark.django_db
def test_add_auction_get(client, user_create):
    """Test the GET request of AddAuction view"""
    client.force_login(user_create)
    url = '/add-auction/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_add_auction_post_valid(client, user_create, item):
    """Test the POST request of AddAuction view with valid data"""
    client.force_login(user_create)
    end_date = datetime.now() + timedelta(days=7) 
    url = '/add-auction/'
    response = client.post(url, {
        'name': 'Test Auction',
        'item': item.pk,
        'min_price': 100,
        'buy_now_price': 200,
        'end_date': end_date.strftime('%Y-%m-%d %H:%M:%S'),
    })
    assert response.status_code == 302
    assert Auction.objects.count() == 1 


@pytest.mark.django_db
def test_add_auction_post_invalid(client, user_create, item):
    """Test the POST request of AddAuction view with invalid data"""
    client.force_login(user_create)
    url = '/add-auction/'
    end_date = datetime.now() - timedelta(days=1) 
    data = {
        'name': '',
        'item': item.pk,
        'min_price': 100,
        'buy_now_price': 50,
        'end_date': end_date.strftime('%Y-%m-%d %H:%M:%S'),  
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assert Auction.objects.count() == 0 


@pytest.mark.django_db
def test_buy_now_get_own_auction(client, user_create, auction):
    """Test the GET request of BuyNow view"""
    client.force_login(user_create)
    url = f'/buy-now/{auction.pk}'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_buy_now_get_expired_or_sold(client, user_create, auction):
    """Test the GET request of BuyNow view for expired or sold auction"""
    client.force_login(user_create)
    auction.status = 'expired'  # Change auction status for 'expired'
    auction.save()
    url = f'/buy-now/{auction.pk}' 
    response = client.get(url)
    assert response.status_code == 302 
    assert response.url == f'/auction/{auction.pk}'


@pytest.mark.django_db
def test_buy_now_get_available_without_price(client, user_create, auction):
    """Test the GET request of BuyNow view for available auction without price"""
    client.force_login(user_create)
    auction.buy_now_price = None  # Delete buy_now_price from the auction
    auction.save()
    url = f'/buy-now/{auction.pk}' 
    response = client.get(url)
    assert response.status_code == 404 


@pytest.mark.django_db
def test_buy_now_post(client, user_create, auction):
    """Test the POST request of BuyNow view"""
    client.force_login(user_create)
    url = f'/buy-now/{auction.pk}' 
    response = client.post(url)
    auction.refresh_from_db()   # Refresh auction in database to see changes
    assert response.status_code == 302
    assert response.url == '/auctions'
    assert auction.status == 'sold'
    assert auction.buyer == user_create

