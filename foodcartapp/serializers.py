from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from .models import Order, OrderItem, Product


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1, error_messages={'min_value': 'Количество должно быть больше 0'})

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, write_only=True)
    firstname = serializers.CharField(required=True, allow_blank=False,
                                      error_messages={'required': 'Это поле обязательно',
                                                      'blank': 'Имя не может быть пустым'})
    lastname = serializers.CharField(required=True, allow_blank=False,
                                     error_messages={'required': 'Это поле обязательно',
                                                     'blank': 'Фамилия не может быть пустой'})
    phonenumber = PhoneNumberField(region="RU", error_messages={
        'required': 'Обязательное поле',
        'invalid': 'Введен некорректный номер телефона',
    })

    address = serializers.CharField(required=True, allow_blank=False,
                                    error_messages={'required': 'Это поле обязательно',
                                                    'blank': 'Адрес не может быть пустым'})

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for product_data in products_data:
            OrderItem.objects.create(order=order, **product_data)
        return order
