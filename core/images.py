# utils.py
from django.templatetags.static import static

def get_fastfood_photos():
    return [
        static('images/fastfood/Vitumbuwa.jpeg'),
        static('images/fastfood/fries.png'),
        static('images/fastfood/scones.jpeg'),
    ]

def get_drinks_photos():
    return [
        static('images/drink/Fanta.jpg'),
        static('images/drink/mirinda.webp'),
        static('images/drink/coca.png'),
        static('images/drink/vatra.png'),
        static('images/drink/Mojo.png'),
        static('images/drink/supershake.png'),
    ]

def get_restaurant_photos():
    return [
        static('images/food.jpg'),
        static('images/fish1.jpg'),
        static('images/beef.jpg'),
        static('images/fish001.jpg'),
        static('images/fish2.jpg'),
        static('images/nsima.png'),
        static('images/whole-smoked-chicken-6.jpg'),
        static('images/5.webp'),
    ]


# /home/surecode/Documents/GitHub/django/coreEat/core/images.py