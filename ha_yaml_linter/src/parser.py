import ruamel.yaml
from ruamel.yaml import YAML
from ruamel.yaml.nodes import ScalarNode, SequenceNode, MappingNode

# Custom classes representing Home Assistant tags
class HATag:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value!r})"

    def __eq__(self, other):
        if type(self) is type(other):
            return self.value == other.value
        return False

class HASecret(HATag): pass
class HAInclude(HATag): pass
class HAIncludeDirList(HATag): pass
class HAIncludeDirNamed(HATag): pass
class HAIncludeDirMergeList(HATag): pass
class HAIncludeDirMergeNamed(HATag): pass
class HAEnvVar(HATag): pass

# A generic constructor factory that can handle any kind of YAML node
def make_ha_tag_constructor(tag_class):
    def constructor(loader, node):
        if isinstance(node, ScalarNode):
            return tag_class(loader.construct_scalar(node))
        elif isinstance(node, SequenceNode):
            return tag_class(loader.construct_sequence(node))
        elif isinstance(node, MappingNode):
            return tag_class(loader.construct_mapping(node))
        return tag_class(node.value)
    return constructor

def get_ha_yaml_parser() -> YAML:
    """
    Returns an initialized and configured ruamel.yaml parser that supports
    all Home Assistant-specific tags natively without choking.
    """
    yaml = YAML(typ='rt')  # 'rt' stands for Round-Trip, preserving comments and format
    
    # Map tag names to their respective custom classes
    ha_tags = {
        '!secret': HASecret,
        '!include': HAInclude,
        '!include_dir_list': HAIncludeDirList,
        '!include_dir_named': HAIncludeDirNamed,
        '!include_dir_merge_list': HAIncludeDirMergeList,
        '!include_dir_merge_named': HAIncludeDirMergeNamed,
        '!env_var': HAEnvVar,
    }

    # Register each tag with the round-trip loader constructor
    for tag, tag_class in ha_tags.items():
        yaml.constructor.add_constructor(tag, make_ha_tag_constructor(tag_class))

    return yaml

def parse_yaml(content: str):
    """
    Parses a YAML string using the HA-configured parser.
    Returns the parsed Python structure.
    """
    parser = get_ha_yaml_parser()
    return parser.load(content)
