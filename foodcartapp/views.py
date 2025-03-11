import json

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Product,Order,OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })

@api_view(['POST'])
def register_order(request):
    try:
        data = request.data
        if 'products' not in data:
            raise ValidationError(
                {
                    'products': 'Поле products обязательно к заполнению'
                }
            )
        print(data)
        products = data['products']
        if not isinstance(products, list) or not products:
            raise ValidationError(
                {
                    'products': 'Поле products не может быть пустым или не списком'
                }
            )
        order = Order.objects.create(
            firstname=data['firstname'],
            lastname=data['lastname'],
            phonenumber=data['phonenumber'],
            address=data['address'],
        )
        for product in data['products']:
            product_id = product['product']
            quantity = product['quantity']
            if not product_id:
                raise ValidationError(
                    {
                        'error': 'Продукт не найден'
                    }
                )
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                product=product,
                order=order,
                quantity=quantity
            )
    except ValidationError as e:
        return Response({
            'error': str(e.detail),
        },status=400)
    except ValueError as e:

        return Response({
            'error': 'Некорректный формат данных',
        }, status=400)
    return Response({
        'success': 'ok',
    })
