from django import forms
from backend.star_burger import settings
from django.db.models import Count
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
import requests
from geopy import distance
from backend.foodcartapp.models import Product, Restaurant, Order
from backend.Placegeo.models import Place

class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "templates/login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "templates/login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="templates/products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="templates/restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })

def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat

def get_or_create_place(apikey, address):
    place, created = Place.objects.get_or_create(address=address)
    if place.latitude is not None and place.longitude is not None:
        return place.longitude, place.latitude
    else:
        coordinates = fetch_coordinates(apikey, address)
        if coordinates:
            place.latitude, place.longitude = coordinates
            place.save()
            return coordinates
    return None, None


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    apikey = settings.YANDEX_API_KEY
    order_items = (
        Order.objects.total_sum()
        .prefetch_related('orders__product')
        .select_related('restaurant')
        .exclude(status='delivered')
        .order_by('status')
    )
    for order in order_items:
        order.lon, order.lat = get_or_create_place(apikey, order.address)
        products = order.orders.values_list('product', flat=True)
        restaurants = Restaurant.objects.filter(
            menu_items__product__in=products,
            menu_items__availability=True
        ).annotate(rest=Count('menu_items__product'))
        order.restaurants = []
        for restaurant in restaurants:
            restaurant.lon, restaurant.lat = get_or_create_place(apikey, restaurant.address)
            if order.lon and order.lat:
                restaurant.distance = distance.distance((order.lat, order.lon), (restaurant.lat, restaurant.lon)).km
            else:
                restaurant.distance = 'Ошибка определения координат'
            order.restaurants.append(restaurant)

    return render(request, template_name='templates/order_items.html', context={
        'order_items': order_items
    })


