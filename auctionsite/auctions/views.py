from django.shortcuts import render, redirect
from django.views.generic import View, ListView, CreateView, UpdateView
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.db.models import Q

from .models import Auction, Item, Opinion, Bid, Category
from .utils import average_rating
from .forms import BidForm, OpinionForm, SearchForm, LoginForm, AddUserForm, ResetPasswordForm, AddAuctionForm


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


class CategoriesList(ListView):
    """Shows names and descriptions of categories"""
    model = Category


class CategoryDetails(View):
    """Shows category details include category items"""
    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']   # Get category name from URL
        category = Category.objects.get(name=slug)
        items = category.item_set.all()
        context = {
            'category': category,
            'items': items
        }
        return render(request, 'auctions/category_detail.html', context)


class AddAuction(LoginRequiredMixin, CreateView):
    """This view creates new auction (prefer to create item before creating auction)"""
    form = AddAuctionForm()
    template_name = 'auctions/auction_form.html'
    login_url = '/login'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form})

    def post(self, request, *args, **kwargs):
        form = AddAuctionForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            item = form.cleaned_data['item']
            min_price = form.cleaned_data['min_price']
            buy_now_price = form.cleaned_data['buy_now_price']
            end_date = form.cleaned_data['end_date']
            user = request.user
            Auction.objects.create(name=name,
                                   item=item,
                                   min_price=min_price,
                                   buy_now_price=buy_now_price,
                                   end_date=end_date,
                                   seller=user)
            return redirect('/auctions')
        else:
            return render(request, self.template_name, {'form': self.form})


class AddItem(CreateView):
    """This view creates new item that should be used in creating auction"""
    model = Item
    fields = ['name', 'description', 'image', 'category']
    template_name = 'auctions/item_form.html'
    success_url = '/items'


class AddOpinion(LoginRequiredMixin, View):
    """View destined to add new opinions about auctions"""
    template_name = 'auctions/opinion_form.html'
    login_url = '/login'
    LOGIN_REDIRECT_URL = '/add-opinion'

    def get(self, request, *args, **kwargs):    # Handle GET request to display the opinion form
        form = OpinionForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = OpinionForm(request.POST)
        pk = kwargs['pk']
        auction = Auction.objects.get(pk=pk)
        if form.is_valid():     # If form is valid create a new Opinion object and redirect to auction detail page
            reviewer = request.user
            comment = form.cleaned_data['comment']
            rating = form.cleaned_data['rating']
            Opinion.objects.create(auction=auction, reviewer=reviewer, rating=rating, comment=comment)
            messages.success(request, 'Added opinion successfully')
            return HttpResponseRedirect(f'/auction/{auction.id}')
        else:   # If form is not valid render the opinion form again with the validation errors
            return render(request, self.template_name, {'form': form})


class EditOpinion(SuccessMessageMixin, UpdateView):
    """This view edits opinion"""
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
    """This view is destined to search auction, category or item by name"""
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
            category_result = Category.objects.filter(Q(name__icontains=search) | Q(name__startswith=search))
            if not item_results and not auction_result and not category_result:
                messages.error(request, 'Didnt match any result')   # If no results found display error message
                return render(request, self.template_name, context)
            else:   # If results found display them
                context['item_result'] = item_results
                context['auction_result'] = auction_result
                context['category_result'] = category_result
                return render(request, self.template_name, context)


class Login(View):
    template_name = 'auctions/login_form.html'
    login_url = '/login'

    def get(self, request, *args, **kwargs):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            next_url = request.GET.get('next')  # Get next page from URL
            if user:    # If user is authenticated log in and redirect to home page
                login(request, user)
                if next_url:  
                    return redirect(next_url)
                else:
                    return redirect(f'/user/{user.username}')
            else:
                form.add_error(None, 'Invalid username or password')
                return render(request, self.template_name, {'form': form})


class Logout(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('/home')


class AddUser(View):
    """View that creates new user and login after valid form"""
    form = AddUserForm()
    template_name = 'auctions/add_user_form.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form})

    def post(self, request, *args, **kwargs):
        form = AddUserForm(request.POST)
        users = User.objects.all()  # Retrieve all users data
        usernames = []
        emails = []
        for user in users:  # Getting usernames and emails
            usernames.append(user.username)
            emails.append(user.email)
        if form.is_valid():
            username = form.cleaned_data['username']
            confirm_password = form.cleaned_data['confirm_password']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            if username in usernames:   # Check if username already exists
                form.add_error(None, 'User already exists')
            elif password != confirm_password:
                form.add_error(None, 'Passwords do not match')
            elif email in emails:   # Check if email already exists
                form.add_error(None, 'Email is already in used')
            else:
                User.objects.create_user(username=username,
                                         first_name=first_name,
                                         last_name=last_name,
                                         password=password,
                                         email=email)
                user = authenticate(username=username, password=password)
                login(request, user)       # If user is authenticated log in and redirect to home
                messages.success(request, 'You account has been created')
                return redirect('/home')
        return render(request, self.template_name, {'form': form})


class UserProfile(View):
    """This view shows user data"""
    def get(self, request, *args, **kwargs):
        username = kwargs['username']   # Get user profile from the URL
        user = User.objects.get(username=username)  # Get user data
        bids = Bid.objects.filter(bidder=user).order_by('-time')  # Get every user bids
        context = {
            'user': user,
            'bids': bids,
        }
        return render(request, 'auctions/user_profile.html', context)


class EditUserProfile(SuccessMessageMixin, UpdateView):
    """This view edits user profile"""
    model = User
    fields = ['first_name', 'last_name', 'email']
    template_name = 'auctions/edit_user_profile.html'
    success_url = '/home'
    success_message = 'Account changed'


class ResetPassword(View):
    """Reset logged user password"""
    template_name = 'auctions/reset_password_form.html'
    form = ResetPasswordForm()

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form})

    def post(self, request, *args, **kwargs):
        username = kwargs['username']   # Get user username from the URL
        user = User.objects.get(username=username)
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully')
                return redirect('/home')
        messages.error(request, 'Passwords do not match')
        return render(request, self.template_name, {'form': self.form})
