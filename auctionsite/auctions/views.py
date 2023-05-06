from django.shortcuts import render, redirect
from django.views.generic import View, ListView, CreateView, UpdateView
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.db.models import Q

from .models import Auction, Item, Opinion, Bid
from .utils import average_rating
from .forms import BidForm, OpinionForm, SearchForm


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


class AddOpinion(View):
    """View destined to add new opinions about auctions"""
    template_name = 'auctions/opinion_form.html'

    def get(self, request, *args, **kwargs):    # Handle GET request to display the opinion form
        form = OpinionForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = OpinionForm(request.POST)
        pk = kwargs['pk']
        auction = Auction.objects.get(pk=pk)
        if form.is_valid():     # If form is valid create a new Opinion object and redirect to auction detail page
            reviewer = form.cleaned_data['reviewer']
            comment = form.cleaned_data['comment']
            rating = form.cleaned_data['rating']
            Opinion.objects.create(auction=auction, reviewer=reviewer, rating=rating, comment=comment)
            messages.success(request, 'Added opinion successfully')
            return HttpResponseRedirect(f'/auction/{auction.id}')
        else:   # If form is not valid render the opinion form again with the validation errors
            return render(request, self.template_name, {'form': form})


class EditOpinion(SuccessMessageMixin, UpdateView):
    model = Opinion
    fields = ['rating', 'comment']
    success_message = 'Opinion was updated successfully'
    template_name = 'auctions/opinion_edit.html'
    success_url = '/auctions'


class BidAuction(View):
    """The view destined to bid on auctions"""
    form = BidForm()
    context = {}
    template_name = 'auctions/bid_form.html'

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        auction = Auction.objects.get(id=pk)
        self.context['auction'] = auction
        self.context['form'] = self.form
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        form = BidForm(request.POST)
        pk = kwargs['pk']
        auction = Auction.objects.get(id=pk)
        if form.is_valid():
            new_price = form.cleaned_data['amount']
            bidder = form.cleaned_data['bidder']
            if auction.min_price >= new_price:  # Check if new price is bigger than minimum price of the auction
                messages.error(request, 'New price cannot be less than minimum price')
                return render(request, self.template_name, self.context)
            else:
                auction.min_price = new_price
                auction.buyer = bidder
                auction.save()
                Bid.objects.create(amount=new_price, auction=auction, bidder=bidder)
            messages.success(request, 'Bid successfully')  # Display success and redirect to the auction details page
            return redirect(f'/auction/{auction.id}')


class SearchAuction(View):
    """This view is destined to search auction or item by name"""
    template_name = 'auctions/search_form.html'

    def get(self, request, *args, **kwargs):
        form = SearchForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = SearchForm(request.POST)
        context = {
            'form': form,
        }
        if form.is_valid():
            search = form.cleaned_data['search']    # Get search query from form
            item_results = Item.objects.filter(Q(name__icontains=search) | Q(name__startswith=search))
            auction_result = Auction.objects.filter(Q(name__icontains=search) | Q(name__startswith=search))
            if not item_results and not auction_result:     # If no results found display error message
                messages.error(request, 'Didnt match any result')
                return render(request, self.template_name, context)
            else:   # If results found display them
                context['item_result'] = item_results
                context['auction_result'] = auction_result
                return render(request, self.template_name, context)
