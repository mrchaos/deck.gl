"""
Support serializing objects into JSON
"""
import json
import re

# Attributes to ignore during JSON serialization
IGNORE_KEYS = [
    "mapbox_key",
    "google_maps_key",
    "deck_widget",
    "binary_data_sets",
    "_binary_data",
    "_kwargs",
]


def to_camel_case(snake_case):
    """Makes a snake case string into a camel case one

    Parameters
    -----------
    snake_case : str
        Snake-cased string (e.g., "snake_cased") to be converted to camel-case (e.g., "camelCase")

    Returns
    -------
    str
        Camel-cased (e.g., "camelCased") version of input string
    """
    output_str = ""
    should_upper_case = False
    for c in snake_case:
        if c == "_":
            should_upper_case = True
            continue
        output_str = output_str + c.upper() if should_upper_case else output_str + c
        should_upper_case = False
    return output_str


def lower_first_letter(s):
    return s[:1].lower() + s[1:] if s else ""


def camel_and_lower(w):
    return lower_first_letter(to_camel_case(w))


def lower_camel_case_keys(attrs):
    """Makes all the keys in a dictionary camel-cased and lower-case

    Parameters
    ----------
    attrs : dict
        Dictionary for which all the keys should be converted to camel-case
    """
    for snake_key in list(attrs.keys()):
        if "_" not in snake_key:
            continue
        camel_key = camel_and_lower(snake_key)
        attrs[camel_key] = attrs.pop(snake_key)


def default_serialize(o, remap_function=lower_camel_case_keys):
    """Default method for rendering JSON from a dictionary"""
    attrs = vars(o)
    attrs = {k: v for k, v in attrs.items() if v is not None}
    for ignore_attr in IGNORE_KEYS:
        if attrs.get(ignore_attr):
            del attrs[ignore_attr]
    if remap_function:
        remap_function(attrs)
    return attrs


def serialize(serializable):
    """Takes a serializable object and JSONifies it"""
    return json.dumps(serializable, sort_keys=True, default=default_serialize)


def multiple_replace(patterns, text):
    """Regex replace for multiple patterns"""
    regex = re.compile("(%s)" % "|".join(map(re.escape, patterns.keys())))
    return regex.sub(lambda mo: patterns[mo.string[mo.start():mo.end()]], text)


def all_numpy_to_list(obj):
    """Converts all arrays nested in an Iterable (dict included) to list"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = all_numpy_to_list(v)

    if is_array(obj):
        obj = list(obj)

        for i, item in enumerate(obj):
            if is_array(item) or isinstance(item, dict):
                obj[i] = all_numpy_to_list(item)

    return obj


def julia_pycall_compatible_serialize(serializable,
                                      remap_function=lower_camel_case_keys):
    """Serializer compatible with Julia's PyCall package"""
    attrs = vars(serializable)
    # numpy array needs to be converted to list
    attrs = {k: all_numpy_to_list(v) for k, v in attrs.items() if v is not None}
    for ignore_attr in IGNORE_KEYS:
        if attrs.get(ignore_attr):
            del attrs[ignore_attr]
    if remap_function:
        remap_function(attrs)

    # json.dumps is not compatible with PyCall, use str() and regex instead
    patterns = {
        "'": '"',
        "False": "false",
        "True": "true"
    }
    return multiple_replace(patterns, str(attrs))


class JSONMixin(object):
    def __repr__(self):
        """
        Override of string representation method to return a JSON-ified version of the
        Deck object.
        """
        return julia_pycall_compatible_serialize(self)

    def to_json(self):
        """
        Return a JSON-ified version of the Deck object.
        """
        return julia_pycall_compatible_serialize(self)