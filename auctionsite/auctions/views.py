from django.shortcuts import render, redirect
from django.views.generic import View, ListView, CreateView
from django.contrib.auth import get_user_model
from django.contrib import messages

from .models import Auction, Item, Opinion, Bid
from .utils import average_rating
from .forms import BidForm


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
    """The view destined to bid on auctions"""
    form = BidForm()
    context = {}

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        auction = Auction.objects.get(id=pk)
        self.context['auction'] = auction
        self.context['form'] = self.form
        return render(request, 'auctions/bid_form.html', self.context)

    def post(self, request, *args, **kwargs):
        form = BidForm(request.POST)
        pk = kwargs['pk']
        auction = Auction.objects.get(id=pk)
        if form.is_valid():
            new_price = form.cleaned_data['amount']
            bidder = form.cleaned_data['bidder']
            if auction.min_price >= new_price:  # Check if new price is bigger than minimum price of the auction
                messages.error(request, 'New price cannot be less than minimum price')
                return render(request, 'auctions/bid_form.html', self.context)
            else:
                auction.min_price = new_price
                auction.buyer = bidder
                auction.save()
                Bid.objects.create(amount=new_price, auction=auction, bidder=bidder)
            messages.success(request, 'Bid successfully')  # Display success and redirect to the auction details page
            return redirect(f'/auction/{auction.id}')
