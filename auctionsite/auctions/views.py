from django.shortcuts import render
from django.views.generic import View, ListView, CreateView
from django.contrib.auth import get_user_model

from .models import Auction, Item, Opinion
from .utils import average_rating


User = get_user_model()


class StartPage(View):
    """This view shows the start page of the auction house"""
    template_name = 'auctions/base_template.html'
    title = 'Auction house'
    auctions = Auction.objects.count()
    users = User.objects.count()

    def get(self, request):
        context = {
            'title': self.title,
            'auctions': self.auctions,
            'users': self.users
        }
        return render(request, self.template_name, context)


class ItemsList(ListView):
    """Shows a list of all available items"""
    model = Item


class ItemDetails(View):
    """This view shows the details of particural item"""
    template_name = 'auctions/item_detail.html'

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']   # Get the primary key of the item from the URL
        item = Item.objects.get(pk=pk)
        return render(request, self.template_name, {'item': item})


class AuctionsList(ListView):
    """Shows a list of all auctions"""
    model = Auction


class AuctionDetails(View):
    """This view shows the details (includes opinions) of particural auction"""
    template_name = 'auctions/auction_detail.html'

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']   # Get the primary key of the auction from the URL
        auction = Auction.objects.get(pk=pk)
        opinions = auction.opinion_set.all()
        ratings = []
        for opinion in opinions:
            ratings.append(opinion.rating)  # Get every rating from opinion
        average_rate = average_rating(ratings)  # Count average rating
        context = {
            'auction': auction,
            'opinions': opinions,
            'average_rating': average_rate,
        }
        return render(request, self.template_name, context)


class AddAuction(CreateView):
    """This view creates new auction (prefer to create item before creating auction)"""
    model = Auction
    fields = ['name', 'item', 'min_price', 'buy_now_price', 'end_date', 'seller']
    template_name = 'auctions/auction_form.html'
    success_url = '/auctions'


class AddItem(CreateView):
    """This view creates new item that should be used in creating auction"""
    model = Item
    fields = ['name', 'description', 'image', 'category']
    template_name = 'auctions/item_form.html'
    success_url = '/items'


class AddOpinion(CreateView):
    model = Opinion
    fields = ['auction', 'reviewer', 'rating', 'comment']
    template_name = 'auctions/opinion_form.html'
    success_url = 'auctions'


class BidAuction(View):
    pass