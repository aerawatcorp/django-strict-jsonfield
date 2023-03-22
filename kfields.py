import inspect
import json
import os
from datetime import date

from django.conf import settings
from django.core import exceptions
from django.db import models
from django.utils import timezone
from jsonschema import exceptions as jsonschema_exceptions
from jsonschema import validate
from shortuuid import ShortUUID

KIDX_MODEL_MAP = getattr(settings, "KIDX_MODEL_MAP", {})


class KIdxField(models.CharField):
    description = "A short UUID field."
    alphabet = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"

    def __init__(self, *args, **kwargs):
        self.length = kwargs.pop("length", 8)

        if "max_length" not in kwargs:
            kwargs["max_length"] = 15

        kwargs.update({"unique": True, "editable": False, "blank": True})

        super().__init__(*args, **kwargs)

    def _generate_uuid(self, _prefix):
        """Generate a short random string."""
        _year = str(date.today().year)[2:]
        _uuid = ShortUUID(alphabet=self.alphabet).random(length=self.length)
        return f"{_prefix}{_year}{_uuid}".upper()

    def pre_save(self, instance, add):
        """
        This is used to ensure that we auto-set values if required.
        See CharField.pre_save
        """

        value = super().pre_save(instance, add)
        if not value:
            _table_name = instance._meta.db_table
            prefix = getattr(KIDX_MODEL_MAP, _table_name, "ID")
            value = self._generate_uuid(prefix)
        setattr(instance, self.attname, value)
        return value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["length"] = self.length
        kwargs.pop("default", None)
        return name, path, args, kwargs


class CreatedDateField(models.DateField):
    def __init__(self, *args, **kwargs):
        kwargs.update({"editable": False, "db_index": True})
        super().__init__(*args, **kwargs)

    def pre_save(self, instance, add):
        value = super().pre_save(instance, add)
        if not value:
            created_on = getattr(instance, "created_on", None) or timezone.now()
            value = timezone.localdate(created_on)
        return value


class InforcedKeyJSONField(models.JSONField):
    def __init__(
        self,
        verbose_name=None,
        name=None,
        encoder=None,
        decoder=None,
        full=None,
        partial=None,
        schema=None,
        read_time_validate=False,
        allowed_keys: set = set(),
        **kwargs,
    ):
        super().__init__(verbose_name, name, **kwargs)
        if full and not schema:
            raise exceptions.ValidationError(
                f": For full inforce, Schema Params is required",
                code="No Schema Provided",
                params={"value": "Schema Missing"},
            )
        elif partial and not allowed_keys:
            raise exceptions.ValidationError(
                f": For partial inforce, allowed_keys Params is required",
                code="No allow key Provided",
                params={"value": "No Keys Provided"},
            )
        self.full = full
        self.partial = partial
        self.schema = schema
        self.allowed_keys = allowed_keys
        self.read_time_validate = read_time_validate

    @property
    def _schema_data(self):
        model_file = inspect.getfile(self.model)
        dirname = os.path.dirname(model_file)
        # schema file related to model.py path
        p = os.path.join(dirname, self.schema)
        with open(p, "r") as file:
            return json.loads(file.read())

    def _validate_schema(self, value):

        # Disable validation when migrations are faked
        if self.model.__module__ == "__fake__":
            return True
        try:
            status = validate(value, self._schema_data)
        except jsonschema_exceptions.ValidationError as e:
            raise exceptions.ValidationError(e.message, code="invalid")
        return status

    def _partial_validate(self, value):

        if value and not (set(self.allowed_keys) == set(value.keys())):
            raise exceptions.ValidationError(
                f": Must have {self.allowed_keys} keys ",
                code="Invalid Values",
                params={"value": value},
            )

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if self.full:
            self._validate_schema(value)
        elif self.partial:
            if not isinstance(self.value, dict):
                raise exceptions.ValidationError(
                    f": Must be a clear json/dict ",
                    code="Invalid Values",
                    params={"value": value},
                )
            self._partial_validate(value)

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        if value:
            if self.full:
                self._validate_schema(value)
            elif self.partial:
                self._partial_validate(value)
        return value

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        if self.read_time_validate:
            if self.full:
                self._validate_schema(value)
            elif self.partial:
                self._partial_validate(value)
        return value


# full  -- schima restriction   (choice for validation during readtime)
# partial -- key only
# none -- none
# def from_db_value(self, value, expression, connection):
#     value = super().from_db_value(value, expression, connection)
#     return pd.DataFrame(value)

