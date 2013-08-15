from mongoengine import fields

from milkman.milkfactory import MilkCarton, MilkmanRegistry, MilkTruck

from datetime import datetime, date, time
import random, string, sys

class BaseGenerator(MilkCarton):
    """
        Returns a value if value is set, or calls and uses the return value of func
    """
    defaults = {'value':None, "func":None, "choices":[]}

    def run(self, field=None):
        if self.choices:
            return random.choice(self.choices)
        if self.func:
            val = self.func(self, field)
            return val
        return self.value

class IntGenerator(MilkCarton):
    """
        Returns a randomly generated int between min and max, or an int of length.
        If astype is set, the generator treats it as a function and wraps it around the 
        return value.
    """
    defaults = {"min": 0, "max": 50000, "length": 0, "astype": int}

    def run(self, field=None):
        if field and field.choices and len(field.choices):
            i = random.choice(field.choices)
            if isinstance(i, (tuple, list)):
                return i[0]
            return i
        if self.length:
            return self.astype(int(''.join([str(random.randint(0, 9)) for i in range(0, self.length)])))
        return self.astype(random.randint(self.min, self.max))

class SmartIntGenerator(IntGenerator):
    """
        Trys to load defaults from mongoengine field
    """
    defaults = {"min": 0, "max": 50000, "length": 0, "astype": int}

    def run(self, field=None):
        if field:
            # Don't ask
            if field.min_value: self.min = field.min_value
            if field.max_value: self.max = field.max_value
            if field.default: return field.default

        return IntGenerator.run(self, field)

class FloatGenerator(MilkCarton):
    """
        Returns a randomly generated float between min and max
    """
    defaults = {"min": sys.float_info.min, "max": sys.float_info.max}

    def run(self, field=None):
        return random.uniform(self.min, self.max)

class DecimalGenerator(MilkCarton):
    """
        Returns a randomly generated decimal, using the generator gen
    """
    defaults = {"gen": IntGenerator()}

    def run(self, field=None):
        return '{0}.{1}'.format(self.gen.run(i), abs(self.gen.run(i)))

class BooleanGenerator(MilkCarton):
    """
        Returns true or false randomly
    """
    def run(self, field=None):
        return random.choice([True, False])

class DateGenerator(MilkCarton):
    """
        Returns a random date (no time!)
    """
    defaults = {
        "start_date": date.today().replace(day=1, month=1).toordinal(),
        "end_date": date.today().toordinal()}

    def run(self, field=None):
        return date.fromordinal(random.randint(self.start_date, self.end_date))

class TimeGenerator(MilkCarton):
    """
        Returns a random time
    """
    defaults = {"ms": False}
    def run(self, field=None):
        if self.ms:
            ms = random.randint(0, 1000000)
        else:
            ms = 0
        return time(random.randint(0, 23), random.randint(0, 59), random.randint(0, 59), ms)

class DateTimeGenerator(MilkCarton):
    """
        Returns a random date+time using date_gen and time_gen.
        If complex, it will use MS times
    """
    defaults = {
        "date_gen": DateGenerator(),
        "time_gen": TimeGenerator(),
        "complex": False
    }

    def run(self, field=None):
        if self.complex:
            self.time_gen.ms = True
        return datetime.combine(self.date_gen.run(), self.time_gen.run())

class StringGenerator(MilkCarton):
    """
        Returns a randomly generated string between length min+1, max
        If chars is provided, will use only chars from chars. If upper,
        will return upper case and lower case.
    """
    defaults = {"max": 10, "min": 0, "chars": None, "upper": False}

    def looper(self, string_set):
        return ''.join([random.choice(string_set) for i in range(self.min, self.max)])

    def run(self, field=None):
        if field and field.choices and len(field.choices):
            i = random.choice(field.choices)
            if isinstance(i, (tuple, list)):
                return i[0]
            else:
                return i
        if field and field.max_length: self.max = field.max_length
        if self.chars: 
            res = self.looper(self.chars)
        else:
            res = self.looper(string.ascii_letters + string.digits)
        if not self.upper:
            return res.lower()

class UrlGenerator(MilkCarton):
    """
        Returns a randomly generated string of format proto+gen()+tld.
        If urls is provided, will just select random items from urls.
    """
    defaults = {"urls": None, "proto": "http://", "tld": ".com", "gen": StringGenerator()}

    def run(self, field=None):
        if self.urls:
            return random.choice(self.urls)

        return "{0}{1}{2}".format(self.proto, self.gen.run(i), self.tld)

class EmailGenerator(MilkCarton):
    """
        Returns a randomly generated email of format gen()@domain.
        If emails is provided, will just select random items from emails
    """
    defaults = {"domain": "test.com", "emails": None, "gen": StringGenerator()}

    def run(self, field=None):
        if self.emails:
            return random.choice(self.emails)

        return "{0}@{1}".format(self.gen.run(), self.domain)

class ListGenerator(MilkCarton):
    """
        Returns a randomly generated list using generators from types.
        Length is either lenght, or less than max_len.
    """
    defaults = {
        "types": [StringGenerator()],
        "length": 0,
        "max_len": 100,
    }

    def get_field_value(self):
        return random.choice(self.types).run()

    def run(self, field=None):
        if not self.length:
            self.length = random.randint(1, self.max_len)
        return [self.get_field_value() for _ in range(0, self.length)]

class DictGenerator(MilkCarton):
    """
        Returns a randomly generated dictionary. This is a somewhat
        complex generator, and will recursivly return more dictionaries
        to the depth of max_depth. It uses only generators from types, and will
        remain below max_size for the total size.
    """
    defaults = {
        "depth": 0, # Don't change
        "max_depth": 2,
        "types": [StringGenerator(), IntGenerator(), FloatGenerator()],
        "max_size": 10
    }

    def get_field_value(self, depth_check=False):
        f = self.types
        if depth_check and self.depth < self.max_depth:
            f.append(DictGenerator(depth=self.depth+1))
        return random.choice(f).run()

    def run(self, field=None):
        for tree in range(0, random.randint(1, self.max_size)):
            key[self.get_field_value()] = self.get_field_value(True)

class MapGenerator(ListGenerator):
    """
        (based of list)
        Returns a randomly generated map using the generator field.
    """
    defaults = {
        "field": StringGenerator(),
        "length": 0,
        "max_len": 100,
    }

    def get_field_value(self):
        return self.field

class EmbeddedGenerator(MilkCarton):
    """
        Attemps to auto-fill EmbeddedDocument fields.
    """
    
    def run(self, field=None):
        truck = getDairyTruck()
        truck.registry = self.parent.registry
        truck.rows = 1
        for i in truck.deliver(field.document_type):
            return i

class ObjectIDGenerator(MilkCarton):
    """
        Attempts to smartly fill ObjectID fields
    """
    defaults = {
        "model": None
    }

    def run(self, field=None):
        if not self.model:
            return

        obj = self.model.objects()
        amount = len(obj)

        if not amount:
            return

        obj = self.mode.objects.skip(random.randint(0, amount)).limit(1)
        return obj.id

def getDairyTruck():
    reg = MilkmanRegistry(default=BaseGenerator(value=None))
    reg.addByClass(fields.BooleanField, BooleanGenerator())
    reg.addByClass(fields.ComplexDateTimeField, DateTimeGenerator(complex=True))
    reg.addByClass(fields.DateTimeField, DateTimeGenerator())
    reg.addByClass(fields.DecimalField, DecimalGenerator())
    reg.addByClass(fields.DictField, DictGenerator())
    reg.addByClass(fields.EmailField, EmailGenerator())
    reg.addByClass(fields.FloatField, FloatGenerator())
    reg.addByClass(fields.IntField, SmartIntGenerator())
    #reg.addByClass(fields.ListField, ListGenerator()) #This doesn't work well right now
    reg.addByClass(fields.MapField, MapGenerator())
    reg.addByClass(fields.StringField, StringGenerator())
    reg.addByClass(fields.URLField, UrlGenerator())
    reg.addByClass(fields.EmbeddedDocumentField, EmbeddedGenerator())
    return MilkTruck(reg)