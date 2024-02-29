from datetime import date

from marshmallow import Schema, validates, ValidationError, validates_schema
from marshmallow.fields import Str, Int, Float, Date, List, Nested
from marshmallow.validate import Length, OneOf, Range

from sales.config import Config
