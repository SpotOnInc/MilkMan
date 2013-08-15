from mongoengine import fields

class MilkCarton(object):
    """
        A milk carton provides milk to one field or field-type. It takes
        the field instance in, and generates a value to be set for that field.
    """
    defaults = {}
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.parent = None

        for i in self.defaults.keys():
            if i in self.kwargs.keys():
                self.__dict__[i] = self.kwargs[i]
            else:
                self.__dict__[i] = self.defaults[i]

    def __call__(self):
        return self.run()

    def run(self, field=None):
        return None

# This is somewhat derpy. MongoEngine has /really/ weird
# class inheritance due to the metaclasses/models system.
# The only way this registry actually works is using the class name.
class MilkmanRegistry(object):
    """
        The registry defines what milk cartons need to go to what
        fields and classes.
    """
    def __init__(self, default=None):
        self.classes = {} # FieldType => Generator
        self.fields = {} # FieldName => Generator

        self.default = default

    def addByClass(self, cls, gen):
        # Forgive me father for I have sinned
        self.classes[cls.__name__] = gen

    def addByField(self, field, gen):
        self.fields[field] = gen

    def getByCls(self, cls):
        if cls in self.classes:
            return self.classes[cls]

    def get(self, field):
        if field.name in self.fields.keys():
            return self.fields[field.name]
        # Best code EVAR
        if field.__class__.__name__ in self.classes.keys():
            return self.getByCls(field.__class__.__name__)

        return self.default

class MilkTruck(object):
    """
        The milk truck delivers cartons to specific fields based
        on the milk registry provided.
    """
    def __init__(self, registry, rows=100):
        self.registry = registry
        self.rows = rows

        self.field_to_gen = {}

    def packTruck(self, model_cls, quiet=False):
        for key, field in model_cls._fields.iteritems():
            gen = self.registry.get(field)
            if not gen and not quiet:
                raise Exception("Field '%s' is not in the registry!" % field)

            gen.parent = self

            self.field_to_gen[field.name] = (field, gen)

    def deliver(self, model_cls):
        self.packTruck(model_cls)

        for row in range(0, self.rows):
            instance = model_cls()
            for k, v in self.field_to_gen.items():
                setattr(instance, k, v[1].run(field=v[0]))
            yield instance