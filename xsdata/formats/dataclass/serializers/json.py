import json
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from io import StringIO
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import TextIO
from typing import Tuple

from xsdata.formats.bindings import AbstractSerializer
from xsdata.formats.converter import converter
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.models.elements import XmlVar
from xsdata.utils import collections


def filter_none(x: Tuple) -> Dict:
    return {k: v for k, v in x if v is not None}


class DictFactory:
    """Dictionary factory types."""

    FILTER_NONE = filter_none


@dataclass
class JsonSerializer(AbstractSerializer):
    """
    Json serializer for dataclasses.

    :param context: Model context provider
    :param dict_factory: Override default dict factory to add further logic
    :param dump_factory: Override default json.dump call with another implementation
    :param indent: Output indentation level
    """

    context: XmlContext = field(default_factory=XmlContext)
    dict_factory: Callable = field(default=dict)
    dump_factory: Callable = field(default=json.dump)
    indent: Optional[int] = field(default=None)

    def render(self, obj: object) -> str:
        """Convert the given object tree to json string."""
        output = StringIO()
        self.write(output, obj)
        return output.getvalue()

    def write(self, out: TextIO, obj: Any):
        """
        Write the given object tree to the output text stream.

        :param out: The output stream
        :param obj: The input dataclass instance
        """
        self.dump_factory(self.convert(obj), out, indent=self.indent)

    def convert(self, obj: Any, var: Optional[XmlVar] = None) -> Any:
        if var is None or self.context.class_type.is_model(obj):

            if collections.is_array(obj):
                return [self.convert(o) for o in obj]

            return self.dict_factory(
                [
                    (var.local_name, self.convert(getattr(obj, var.name), var))
                    for var in self.context.build(obj.__class__).get_all_vars()
                ]
            )

        if collections.is_array(obj):
            return type(obj)(self.convert(v, var) for v in obj)

        if isinstance(obj, (dict, int, float, str, bool)):
            return obj

        if isinstance(obj, Enum):
            return self.convert(obj.value, var)

        return converter.serialize(obj, format=var.format)
