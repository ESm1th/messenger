
import json
import os
from functools import reduce

from pymongo import MongoClient
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.config import Config


Config.set('graphics', 'resizable', False)
Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '300')


path = os.path.join(
    os.path.dirname(__file__), 'credentials.json'
)
with open(path) as file:
    credentials = json.load(file)


class ShoppingList:

    def __init__(self):
        self.client = MongoClient(**credentials)

    def update(self, items):
        with self.client as client:
            client.product_list.list.update_one(
                {'name': 'shopping_list'},
                {'$set': {'items': items}}
            )

    def get_items(self):
        with self.client as client:
            return client.product_list.list.find_one(
                {'name': 'shopping_list'}
            )['items']


class ItemLabel(Label):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.size_hint_x = 0.5
        self.size_hint_y = None
        self.height = 30


class ListBoxLayout(BoxLayout):

    shopping_list = ShoppingList()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for item in self.shopping_list.get_items():
            for title, quantity in item.items():
                self.create_item_box(title, quantity)

    def create_item_box(self, item, quantity):
        if item and quantity:
            box = BoxLayout(size_hint_y=None, height=30, spacing=2)
            box.add_widget(ItemLabel(text=item))
            box.add_widget(ItemLabel(text=quantity))
            self.item_list.add_widget(box)

    def add_item_to_list(self):
        item = self.item.text
        quantity = self.quantity.text
        self.create_item_box(item, quantity)

    def save_shopping_list(self):
        items = reduce(
            lambda lst, child: lst + [
                {child.children[1].text: child.children[0].text}
            ],
            self.item_list.children,
            []
        )
        self.shopping_list.update(items)


class ShoplistApp(App):

    def build(self):
        return ListBoxLayout()


if __name__ == '__main__':
    ShoplistApp().run()
