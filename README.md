# Milkman, delivering fresh, low-fat, and delicious data
Milkman is a Python library built for generating bounded random data for database ORM's. It was built to be extremely extensible and easy to use, while remaining database agnostic. Currently the only implementation included is for MongoEngine.

Milkman is based of [this project](https://github.com/ccollins/milkman) by the same name. The original library was built around the Django ORM and was very minimalistic, this rewrite was intended to extend on the core ideas while allowing a large range of ORM's and fields with a smart interface for extendability.

## Contributing
Fork into a feature branch, submit a pull request, and profit!

## Using

```python
from milkman.dairy import *
from mongoengine import *
from my_models import User

def fill_customers(rows):
    truck = getDairyTruck()
truck.registry.addByField("custom_value", IntGEnerator(length=4, astype=str))
truck.rows = 500
[i.save() for i in truck.deliver(User)]
```