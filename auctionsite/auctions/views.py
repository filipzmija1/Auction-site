from datetime import datetime
from typing import Any, Dict, Optional, Type
from PIL import Image
from io import BytesIO

from django import forms
from django.db import models
from django.forms.models import BaseModelForm, modelform_factory
from django.shortcuts import render, redirect
from django.views.generic import View, ListView, CreateView, DeleteView, DetailView, UpdateView
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.safestring import mark_safe
from django.urls import reverse_lazy, reverse

from django_email_verification import send_email
from twilio.rest import Client

from .models import Auction, Item, Opinion, Bid, Category, Account
from .utils import average_rating
from .forms import SearchForm, LoginForm, AddUserForm, ResetPasswordForm, \
    EditUserForm



User = get_user_model()


class StartPage(View):
    """This view shows the start page of the auction house"""
    template_name = 'auctions/base_template.html'
    title = 'Auction house'
    
    def get(self, request):
        users = User.objects.count()
        auctions = Auction.objects.count()
        context = {
            'title': self.title,
            'auctions': auctions,
            'users': users,
        }
        return render(request, self.template_name, context)


class ItemsList(ListView):
    """Shows a list of all available items"""
    model = Item
    paginate_by = 10


class ItemDetails(DetailView):
    """This view shows the details of particural item"""
    model = Item
    context_object_name = 'item'


class AuctionsList(ListView):
    """Shows a list of all auctions 
    # TODO: after server depoloyment use scheduler to automate changing auction status"""
    model = Auction
    context_object_name = 'auctions'
    paginate_by = 10
    ordering = '-end_date'

    def get_context_data(self, **kwargs):
        """Method is used to change auction status after expired or sold"""
        context = super().get_context_data(**kwargs)    # Get default context data
        for auction in context['auctions']:
            if auction.status == 'available':
                if auction.end_date < timezone.now():   # Check if end date is past
                    auction.status = 'expired'
                    auction.save()   
                if auction.end_date < timezone.now() and auction.bid_set.count() > 0:
                    auction.status = 'sold'
                    auction.save()      
        return context

    def get_template_names(self, **kwargs):
        """Method is used to dynamically determine the template to use based on the 'status' parameter in the URL"""
        status = self.request.GET.get('status')     # Get status parameter from the request
        if status == 'expired':
            return 'auctions/expired_auction_list.html'
        elif status == 'available':
            return 'auctions/available_auction_list.html'
        elif status == 'sold':
            return 'auctions/sold_auction_list.html'
        else:
            return 'auctions/auction_list.html'


class AuctionDetails(DetailView):
    """This view shows the details (includes opinions) of particural auction"""
    context_object_name = 'auction'
    model = Auction


class CategoriesList(ListView):
    """Shows names and descriptions of categories"""
    model = Category


class CategoryDetails(DetailView):
    """Shows category details include category items"""
    context_object_name = 'category'
    model = Category

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        category_slug = self.kwargs['slug']
        category = Category.objects.get(name=category_slug)
        return category
    

class AddAuction(LoginRequiredMixin, CreateView):
    """This view creates new auction (prefer to create item before creating auction)"""
    model = Auction
    fields = ['name', 'item', 'min_price', 'buy_now_price', 'end_date']

    def get_success_url(self):
        """Returns URL where user will be redirected after successfull object create"""
        return '/auctions'

    def form_valid(self, form):
        """Check if form is valid and saves data"""
        form.instance.seller = self.request.user
        min_price = form.cleaned_data['min_price']
        buy_now_price = form.cleaned_data['buy_now_price']
        end_date = form.cleaned_data['end_date']
        
        if buy_now_price and min_price > buy_now_price:
            form.add_error('buy_now_price', 'Price without bidding cannot be less than minimum price')
            return self.form_invalid(form)
        if end_date < timezone.now():   # Check if date is not past
            form.add_error('end_date', 'End date cannot be past')
            return self.form_invalid(form)
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_form(self, form_class=None):
        """Creates widget"""
        form = super().get_form(form_class)
        form.fields['item'].queryset = Item.objects.filter(creator=self.request.user)
        form.fields['end_date'].help_text = mark_safe('Enter the date in the format: month/day/year hour:minutes:seconds')
        return form


class BuyNow(LoginRequiredMixin, UpdateView):
    """This view is used to buy auction item without bidding (only if auction allows that)"""
    model = Auction
    context_object_name = 'auction'
    template_name = 'auctions/buy_auction_now.html'
    fields = ['buyer', 'status']

    def get_success_url(self):
        auction = self.get_object()
        return reverse('auction-detail', kwargs={'pk': auction.pk})

    def form_valid(self, form):
        """Check if form is valid, display messages and saves data"""
        user = self.request.user
        auction = self.get_object()  # Access the auction object
        error_messages = {
            auction.bid_set.count() > 0: 'You cannot buy right now because someone started to bid on auction already(you can bid too)',
            auction.status == 'available' and auction.buy_now_price is None: 'You can not do this because auction has no buy-now price',
            auction.status == 'sold' or auction.status == 'expired': 'Buying expired or sold auctions is prohibited',
            auction.seller == user or auction.buyer == user: 'Buying as buyer or seller is prohibited',
        }
        for condition, error_message in error_messages.items():
            if condition:
                messages.error(self.request, error_message)
                return redirect(reverse_lazy('auction-detail', kwargs={'pk': auction.pk}))
        form.instance.buyer = user
        form.instance.status = 'sold'
        auction = form.save()
        messages.success(self.request, f'Congratulation! You bought {auction.item.name} from {auction.name}')
        return super().form_valid(form)
        
    def get_object(self, queryset=None):
        """Returns objects from the URL"""
        if queryset is None:
            queryset = self.get_queryset()
        auction_id = self.kwargs['pk']
        auction = Auction.objects.get(pk=auction_id)
        return auction


class AddItem(LoginRequiredMixin, CreateView):
    """This view creates new item that should be used in creating auction"""
    model = Item
    fields = ['name', 'description', 'image', 'category']
    template_name = 'auctions/item_form.html'
    success_url = '/items'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class AddOpinion(LoginRequiredMixin, CreateView):
    """View destined to add new opinions about auctions"""
    model = Opinion
    context_object_name = 'opinion'
    fields = ['comment', 'rating']

    def get_success_url(self):
        auction = self.get_object()
        return reverse('auction-detail', kwargs={'pk': auction.pk})

    def get_object(self, queryset=None):
        """Retrieve the auction for which there is an opinion"""
        if queryset is None:
            queryset = self.get_queryset()
        auction_id = self.kwargs['pk']
        auction = Auction.objects.get(pk=auction_id)
        return auction

    def form_valid(self, form):
        form.instance.reviewer = self.request.user
        form.instance.auction = self.get_object()
        return super().form_valid(form)



class EditOpinion(LoginRequiredMixin, UpdateView):
    """This view edits opinion"""
    model = Opinion
    fields = ['comment', 'rating']
    
    def get_success_url(self):
        auction = self.object.auction
        return reverse('auction-detail', kwargs={'pk': auction.pk})


    def get_object(self, queryset=None):
        opinion_id = self.kwargs['pk']
        user = self.request.user
        opinion = Opinion.objects.get(pk=opinion_id)
        if opinion.reviewer.id != user.id:
            raise PermissionDenied
        return opinion
    
    def form_valid(self, form):
        form.instance.date_edited = datetime.now()
        form.save()
        return super().form_valid(form)


class DeleteOpinion(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """This view deletes opinion"""
    model = Opinion
    success_message = 'Opinion deleted successfully'

    def get_object(self, queryset=None):
        opinion_id = self.kwargs['pk']  # Get opinion id from the URL
        user = self.request.user    # Get logged user
        opinion = Opinion.objects.get(pk=opinion_id)
        if opinion.reviewer.id != user.id:
            raise PermissionDenied
        return opinion

    def get_success_url(self):
        """This method get the success URL from opinion id"""
        opinion_id = self.kwargs.get('pk')  # Get opinion id from the URL
        opinion = Opinion.objects.get(id=opinion_id)
        auction = opinion.auction
        return f'/auction/{auction.id}'


class BidAuction(LoginRequiredMixin, CreateView):
    """The view destined to bid on auctions (if bid is 20 minutes before end of auction,
    it increases end of auction time for 20 minutes). 
    # TODO after server deployment use account_sid and auth_token to send SMS whenever auction is outbid """
    model = Bid
    fields = ['amount']

    def get_object(self, queryset=None):
        auction_id = self.kwargs['pk']
        auction = Auction.objects.get(id=auction_id)
        return auction
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['auction'] = self.get_object()
        return context
    
    def form_valid(self, form):
        """Check if form is valid, sends errors and if everything is OK sends mail to outbided person."""
        user = self.request.user
        auction = self.get_object()
        new_price = form.cleaned_data['amount']
        # account_sid = ''  # account sid used to send SMS
        # auth_token = ''     # account auth_token used to send SMS
        # client = Client(account_sid, auth_token)
        error_messages = {
            auction.buyer == user: 'You cannot bid because last person who bids is you!',
            auction.seller == user: 'You cannot bid on your own auction!',
            auction.status == 'expired' or auction.status == 'sold': 'Bid on expired or sold auctions is not allowed!',
            auction.min_price >= new_price: 'New price cannot be equal or less than minimum price!',
        }
        for condition, error_message in error_messages.items():
            if condition:
                messages.error(self.request, error_message)
                return redirect(reverse_lazy('auction-detail', kwargs={'pk': auction.pk}))
        if timezone.now() + timezone.timedelta(minutes=20) > auction.end_date:
            auction.end_date += timezone.timedelta(minutes=20)
        # if auction.buyer and auction.buyer.phone_number:
        #     client.messages.create(
        # body=f'Your auction: "{auction.name}" has been outbid. New price is {new_price}!',
        # from_='+12543544729',
        # to='+48{}'.format(auction.buyer.phone_number)
        # )
        if auction.buyer and auction.buyer.email:
            send_mail(f'{auction.name}',    # Sends email to outbid person
                    f'You have been outbid. New price is {new_price}',
                    f'{settings.EMAIL_HOST_USER}',
                    [f'{auction.buyer.email}'])  
        auction.min_price = new_price
        auction.buyer = user
        auction.save()
        form.instance.amount = new_price
        form.instance.auction = auction
        form.instance.bidder = user
        form.save()
        messages.success(self.request, 'Bid successfully')  # Display success and redirect to the auction details page
        return super().form_valid(form)
    
    def get_success_url(self):
        auction = self.get_object()
        return reverse('auction-detail', kwargs={'pk': auction.pk})


class BidHistory(ListView):
    """Shows every bid for auction"""
    model = Bid
    template_name = 'auctions/bid_history_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        auction_id = self.kwargs['pk']      # Get auction ID from the URL
        auction = Auction.objects.get(pk=auction_id)
        bids = auction.bid_set.order_by('-time')
        context['auction'] = auction
        context['bids'] = bids
        return context

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
        else:
            return render(request, self.template_name, {'form': form})


class Login(View):
    template_name = 'auctions/login_form.html'

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
        else:
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
            if username in usernames:   # Check if username already exists
                form.add_error(None, 'User already exists')
            elif password != confirm_password:
                form.add_error(None, 'Passwords do not match')
            elif email in emails:   # Check if email already exists
                form.add_error(None, 'Email is already in used')
            else:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email)
                user.is_active = False
                Account.objects.create(user=user)
                send_email(user)    # Send email to verify account
                messages.success(request, 'Check email to enable your account')
                return redirect('/home')
        return render(request, self.template_name, {'form': form})


class UserProfile(View):
    """This view shows user data (if user is created by all-auth library it creates extra account fields)"""
    def get(self, request, *args, **kwargs):
        username = kwargs['username']   # Get user profile from the URL
        user = User.objects.get(username=username)  # Get user data
        bids = Bid.objects.filter(bidder=user).order_by('-time')  # Get every user bids
        paginator = Paginator(bids, 3)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'user': user,
            'bids': page_obj,
        }
        try:
            user_account = Account.objects.get(user=user)
            context['user_account'] = user_account
            return render(request, 'auctions/user_profile.html', context)
        except:
            user_account = Account.objects.create(user=user)
            context['user_account'] = user_account
            return render(request, 'auctions/user_profile.html', context)

class EditUserProfile(LoginRequiredMixin, SuccessMessageMixin, View):
    """This view edits user profile"""
    template_name = 'auctions/edit_user_profile.html'

    def get(self, request, *args, **kwargs):
        user_id = kwargs['pk']  # Get id from the URL
        user = request.user
        user_account = Account.objects.get(user=user)
        form = EditUserForm(initial={
            'first_name':user.first_name,
            'last_name':user.last_name,
            'phone_number':user_account.phone_number})
        if user_id != user.id:
            raise PermissionDenied
        else:
            return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = EditUserForm(request.POST)
        user = request.user
        user_account = Account.objects.get(user=user)
        if form.is_valid():     # Check if form is valid
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user_account.phone_number = form.cleaned_data['phone_number']
            user_account.save()
            user.save()
            messages.success(request, 'Account data changed successfully')
            return redirect(f'/user/{user.username}')
        else:   # If form is not valid return form with errors
            return render(request, self.template_name, {'form': form})


class ResetPassword(LoginRequiredMixin, View):
    """Reset logged user password"""
    template_name = 'auctions/reset_password_form.html'
    form = ResetPasswordForm()

    def get(self, request, *args, **kwargs):
        username = kwargs['username']  # Get user username from the URL
        user = request.user
        if user.username != username:
            raise PermissionDenied
        else:
            return render(request, self.template_name, {'form': self.form})

    def post(self, request, *args, **kwargs):
        form = ResetPasswordForm(request.POST)
        user = request.user
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


class DeleteUser(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """This view allows user to delete his own profile"""
    model = User
    success_message = 'Your account has been deleted successfully'
    template_name = 'auctions/user_confirm_delete.html'
    
    def get_success_url(self):
        user = self.request.user    # Get logged user
        user_id = self.kwargs.get('pk') # Get user id from the URL
        if user.id != user_id:
            raise PermissionDenied
        else:
            return '/home'