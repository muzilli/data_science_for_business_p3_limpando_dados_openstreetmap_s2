#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import json
import pprint
import re
import xml.etree.cElementTree as ET
from datetime import datetime

OSM_FILE = "data/map.osm"
SAMPLE_FILE = "data/map_sample_2.osm"

# Regex
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
lower_dot = re.compile(r'^([a-z]|_)*.([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# Filters and Mapping to Fix
FIX_KEY = {'Phone' : 'phone_fixed'}

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

PRIMARY_MAP_FEATURE = [
  'aerialway', 'aeroway', 'amenity', 'barrier',
  'boundary', 'building', 'craft', 'emergency',
  'geological', 'highway', 'cycleway', 'busway',
  'sidewalk', 'historic', 'landuse', 'leisure',
  'man_made', 'military', 'natural', 'office',
  'place', 'power', 'line', 'public_transport',
  'railway', 'route', 'shop', 'sport',
  'tourism', 'waterway'
]

POSTAL_CODE_NY_RANGE = [10000, 14999]

EXPRECTED_STREET_TYPE = ["STREET", "AVENUE", "BOULEVARD", "DRIVE", "COURT", "PLACE", "SQUARE", "LANE", "ROAD",
            "TRAIL", "PARKWAY", "COMMONS"]

FIX_STREET_TYPE = { 
  "RD": "ROAD",
  "RD.": "ROAD",
  "STREEET" : "STREET",
  "STEET" : "STREET",
  "ST.," : "STREET",
  "ST." : "STREET",
  "ST," : "STREET",
  "ST" : "STREET",
  "STREER" : "STREET",
  "STE" : "SUITE",
  "STE." : "SUITE",
  "STE," : "SUITE",
  "PL" : "PLACE",
  "BLVD" : "BOULEVARD",
  "BLV." : "BOULEVARD",
  "BLV," : "BOULEVARD",
  "AVENUE," : "AVENUE",
  "AVENEU" : "AVENUE",
  "AVE." : "AVENUE",
  "AVE," : "AVENUE",
  "AVE" : "AVENUE",
}

FIX_CARDINAL_NAMES = {
  'W.' : 'WEST',
  'W'  : 'WEST',
  'S'  : 'SOUTH',
  'N'  : 'NORTH',
  'E.' : 'EAST',
  'E'  : 'EAST'
}

WEEK_DAYS = {
'mo' : 'monday',
'tu' : 'tuesday',
'we' : 'wednesday',
'th' : 'thursday',
'fr' : 'friday',
'sa' : 'saturday',
'su' : 'sunday'
}

FIX_PERIOD_WEEK_DAYS = {
  'mo-su' : ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'],
  'su-su' : ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'],
  'mo-mo' : ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'],
  'mo-sa' : ['mo', 'tu', 'we', 'th', 'fr', 'sa'],
  'mo-fr' : ['mo', 'tu', 'we', 'th', 'fr'],
  'mo-th' : ['mo', 'tu', 'we', 'th'],
  'mo-we' : ['mo', 'tu', 'we'],
  'mo-tu' : ['mo'],

  'tu-su' : ['tu', 'we', 'th', 'fr', 'sa', 'su'],
  'tu-sa' : ['tu', 'we', 'th', 'fr', 'sa'],
  'tu-fr' : ['tu', 'we', 'th', 'fr'],
  'tu-th' : ['tu', 'we', 'th'],
  'tu-we' : ['tu', 'we'],

  'we-su' : ['we', 'th', 'fr', 'sa', 'su'],
  'we-sa' : ['we', 'th', 'fr', 'sa'],
  'we-fr' : ['we', 'th', 'fr'],
  'we-th' : ['we', 'th'],

  'th-su' : ['th', 'fr', 'sa', 'su'],
  'th-sa' : ['th', 'fr', 'sa'],
  'th-fr' : ['th', 'fr'],

  'fr-su' : ['fr', 'sa', 'su'],
  'fr-sa' : ['fr', 'sa'],

}

MAIN_TAGS = ['node', 'relation', 'way']


def process_json(element, restrictions_keys):
  """ Function: process_json.

      The function will receive 02 parameters from the tag in the XML file. If the tag
      element represents a ``node`` or a ``way`` in the map selected region the node will
      be added with the following characteristics: basic data node, position, and a tag
      with the ``restrictions_keys`` passed as a parameter. It will represents the end of the
      node construction.

      Args:
          element (tag element): represents the postal_code that will be audited.
          restrictions_keys (tag element): The key that represents the of the node.

      Returns:
          node: The node in case of success, otherwise `None` value.

      `PEP 484`_ type annotations are supported. If attribute, parameter, and
      return types are annotated according to `PEP 484`_, they do not need to be
      included in the docstring:

      .. _PEP 484:
          https://www.python.org/dev/peps/pep-0484/

      """
  node = {}
  if element.tag == "node" or element.tag == "way":
    node = process_basic_data_node(element, node)
    node = process_position_node(element, node)
    node = process_sub_element_node_refs_node(element, node)
    node = process_sub_elements_tag_node(element, node, restrictions_keys)
    return node
  else:
    return None

def process_sub_elements_tag_node(element, node, restrictions_keys):
  """ Function: process_sub_elements_tag_node.

      The function will receive 03 parameters from the tag in the XML file.
      This function will be called by the function `process_json`.

      For all sub elements in the element ``tag`` that has a valid key, the sub element will be
      treated and normalized. The reason for that is to create sub elements in the same element context.

      Args:
          element (tag element): represents the postal_code that will be audited.
          node (str): The node tag
          restrictions_keys (tag element): The key that represents the of the node.

      Returns:
          node: The node value treated.

      `PEP 484`_ type annotations are supported. If attribute, parameter, and
      return types are annotated according to `PEP 484`_, they do not need to be
      included in the docstring:

      .. _PEP 484:
          https://www.python.org/dev/peps/pep-0484/

      """
  for sub_element in element.findall('tag'):
    key = sub_element.get('k')
    value = sub_element.get('v')

    # Corrigindo aspas simples
    if value:
      value = value.replace("'", "`")

    if is_valid_key_from_tag(key):
      
      if key in PRIMARY_MAP_FEATURE:
        process_sub_element_to_node(node, key, value, key, '', 'primary_map_feature')
      
      if key in restrictions_keys:
        process_sub_element_to_node(node, key, value, key, '', 'restrictions_rules')
        
      process_sub_element_to_node(node, key, value, 'addr', ':', 'address')

      process_sub_element_to_node(node, key, value, 'building')

      process_sub_element_to_node(node, key, value, 'cityracks', '.')

      process_sub_element_to_node(node, key, value, 'crossing')

      process_sub_element_to_node(node, key, value, 'gnis')

      process_sub_element_to_node(node, key, value, 'tiger')

      if key == 'name':
        node['name'] = normalize_and_clean_name(value)
      elif key.startswith('name') or key.startswith('old_name'):
        process_sub_element_to_node(node, key, value, 'name', '', 'names')
        process_sub_element_to_node(node, key, value, 'old_name', '', 'names')

  return node

def get_key_data_from_node(node, name_key, type={}):
  """ Function: get_key_data_from_node.

      The function will receive 03 parameters from the tag in the XML file.
      This function will be called by the function `process_sub_element_to_node`.
      This function will return the key of the node or the node type in case of the root.

      Args:
          element (tag element): represents the postal_code that will be audited.
          node (str): The node tag
          restrictions_keys (tag element): The key that represents the of the node.

      Returns:
          The key of the node or the node, if its the root element.

      `PEP 484`_ type annotations are supported. If attribute, parameter, and
      return types are annotated according to `PEP 484`_, they do not need to be
      included in the docstring:

      .. _PEP 484:
          https://www.python.org/dev/peps/pep-0484/

      """
  if name_key in node:
    return node[name_key]
  else:
    return type

def get_key_name_normalized(key, wipe_name=''):
  """ Function: get_key_name_normalized.

      The function will receive 02 parameters.
      This function will be called by the function `process_sub_element_to_node` and
      will correct the return key for a dictionary.

      Args:
          key (tag element): represents the key that will be audited.
          wipe_name (str): The arg if not provided will be empty and represents the wiped name of an element.

      Returns:
          A specific and normalized key for a dictionary.

      `PEP 484`_ type annotations are supported. If attribute, parameter, and
      return types are annotated according to `PEP 484`_, they do not need to be
      included in the docstring:

      .. _PEP 484:
          https://www.python.org/dev/peps/pep-0484/

      """
  if key is not None:
    return key.strip().replace(wipe_name, '').replace('-', '_').replace('.', '_').replace(':', '_')

def get_json_main_key(xml_starts_with_key, main_key_json):
  """ Function: get_json_main_key.

      The function will receive 02 parameters.
      This function will be called by the function `process_sub_element_to_node` and
      will correct the main json key for a dictionary if is a main json key.

      Args:
          xml_starts_with_key (key element): represents the key that will represent the json start key in the model.
          main_key_json (key element): represents the key that will be audited if its a main json key.

      Returns:
          A specific and normalized key for a dictionary. The Strip method will remove all characters found in the
          argument string that lead, or end the string.

      `PEP 484`_ type annotations are supported. If attribute, parameter, and
      return types are annotated according to `PEP 484`_, they do not need to be
      included in the docstring:

      .. _PEP 484:
          https://www.python.org/dev/peps/pep-0484/

      """
  if main_key_json is not None and len(main_key_json.strip()) > 0:
    return main_key_json
  else:
    return xml_starts_with_key

def is_valid_key_from_tag(k_key):
    """ Function: is_valid_key_from_tag.

         The function will receive 01 parameter.
         This function will be called by the function `process_sub_elements_tag_node` and
         will test if a specific key is valid from the tag.

         Args:
             k_key (key element): represents the key to be tested.

         Returns:
             True: according with the following test: `is not None and problemchars.search(k_key) is None and (lower.search(k_key) or lower_colon.search(k_key) or lower_dot.search(k_key))`
                  otherwise will return False

         `PEP 484`_ type annotations are supported. If attribute, parameter, and
         return types are annotated according to `PEP 484`_, they do not need to be
         included in the docstring:

         .. _PEP 484:
             https://www.python.org/dev/peps/pep-0484/

         """
    return k_key is not None and \
           problemchars.search(k_key) is None and \
           (lower.search(k_key) or lower_colon.search(k_key) or lower_dot.search(k_key))

def process_basic_data_node(element, node):
  """ Function: process_basic_data_node.

       The function will receive 02 parameters.
       This function will be called by the function `process_json` and
       will process a basic data node.

       Args:
        element (tag element): represents the element key to be created.
        node (str): This argument represents the name of the main node created.

       Returns:
           the main node (json format)

       `PEP 484`_ type annotations are supported. If attribute, parameter, and
       return types are annotated according to `PEP 484`_, they do not need to be
       included in the docstring:

       .. _PEP 484:
           https://www.python.org/dev/peps/pep-0484/

       """
  node['id'] = element.get('id')
  node['type'] = element.tag
  node['visible'] = element.get('visible')
  node = process_created_node(element, node)
  return node

def process_created_node(element, node):
  """ Function: process_created_node.

       The function will receive 02 parameters.
       This function will be called by the function `process_basic_data_node` and
       will process the created node.

       Args:
        element (tag element): represents the element key to be created.
        node (str): This argument represents the name of the node to be created.

       Returns:
           the main node (json format)

       `PEP 484`_ type annotations are supported. If attribute, parameter, and
       return types are annotated according to `PEP 484`_, they do not need to be
       included in the docstring:

       .. _PEP 484:
           https://www.python.org/dev/peps/pep-0484/

       """
  created = {}
  for c in CREATED:
    created[c] = element.get(c)
  node['created'] = created
  return node

def process_position_node(element, node):
    """ Function: process_position_node.

            The function will receive 02 parameters.
            This function will be called by the function `process_json` and
            will the node position based on latitude and longitude.

            Args:
             element (tag element): represents the element key to be created.
             node (str): This argument represents the name of the node to be created.

            Returns:
                the main node (json format)

            `PEP 484`_ type annotations are supported. If attribute, parameter, and
            return types are annotated according to `PEP 484`_, they do not need to be
            included in the docstring:

            .. _PEP 484:
                https://www.python.org/dev/peps/pep-0484/

         """
    lat = element.get('lat')
    lon = element.get('lon')
  
    if lat is not None and lon is not None:
        node['pos'] = [float(lat), float(lon)]
    return node

def process_sub_element_node_refs_node(element, node):
    """ Function: process_sub_element_node_refs_node.

            The function will receive 02 parameters.
            This function will be called by the function `process_json` and
            will process sub elements of the referenced node.

            Args:
             element (tag element): represents the element key to be created.
             node (str): This argument represents the name of the node to be created.

            Returns:
                the referenced node (json format)

            `PEP 484`_ type annotations are supported. If attribute, parameter, and
            return types are annotated according to `PEP 484`_, they do not need to be
            included in the docstring:

            .. _PEP 484:
                https://www.python.org/dev/peps/pep-0484/

       """
    node_refs = []
    for sub_element in element.findall('nd'):
        node_refs.append(sub_element.get('ref'))
  
    if len(node_refs) > 0:
        node['node_refs'] = node_refs
    return node

def process_sub_element_to_node(node, key, value, xml_starts_with_key, sep=':', main_key_json=None):
    """ Function: process_sub_element_to_node.

              The function will receive 06 parameters.
              This function will be called by the function `process_sub_elements_tag_node` and
              will process sub elements of the referenced node.

              Args:
               node (str): Represents the name of the node to be processed
               key (key element): Represents the key node to be processed
               value (str): a key value in the node
               xml_starts_with_key (str): xml start with the key provided
               sep (str): a constant of `:` otherwise a separator new value
               main_key_json (key): the key name in the json format

              Returns:
                  the node (json format)

              `PEP 484`_ type annotations are supported. If attribute, parameter, and
              return types are annotated according to `PEP 484`_, they do not need to be
              included in the docstring:

              .. _PEP 484:
                  https://www.python.org/dev/peps/pep-0484/

       """
    xml_key_starts_with_sep = xml_starts_with_key + sep

    if key.startswith(xml_key_starts_with_sep):
        main_json_key = get_json_main_key(xml_starts_with_key, main_key_json)
        if key == xml_key_starts_with_sep:
            normalized_key = get_key_name_normalized(key)
        else:
            normalized_key = get_key_name_normalized(key, xml_key_starts_with_sep)
        sub_node = get_key_data_from_node(node, main_json_key, {})
      
        if main_key_json == 'restrictions_rules':
            if value.strip() == '24/7':
                # forcando o valor ser de segunda a domingo
                value = 'mo-su'

            if value not in ['yes', 'no']:
                value = normalize_and_clean_conditional_values_from_nodes(value, key)
        elif main_key_json == 'address':
            if key == 'addr:street':
                value = normalize_and_clean_street_name(value)
            elif key in ['addr:zip', 'addr:postcode']:
                value = normalize_and_clean_zip_code(value)
        sub_node[normalized_key] = value

        node[main_key_json] = sub_node
    return node

'''
''  Funcoes para limpeza e normalizacao de tags do tipo conditional
'''
def normalize_and_clean_name(name):
    """ Function: normalize_and_clean_name.

              The function will receive 01 parameter.
              This function will be called by the function `process_sub_elements_tag_node` and
              will normalize and clean the node name provided.

              Args:
               name (key name): Represents the name of the node to be processed

              Returns:
                  the node name normalized(json format)

              `PEP 484`_ type annotations are supported. If attribute, parameter, and
              return types are annotated according to `PEP 484`_, they do not need to be
              included in the docstring:

              .. _PEP 484:
                  https://www.python.org/dev/peps/pep-0484/

       """
    return name.upper().replace('"', " ").replace("'", " ").replace('|', " ").replace('\\', " ").replace('/', " ").replace('-', " ").replace('  ', " ")
  
def normalize_and_clean_street_name(street_address_name):
    """ Function: normalize_and_clean_street_name.

              The function will receive 01 parameter.
              This function will be called by the function `process_sub_element_to_node` and
              will normalize and clean the street name provided.

              Args:
               name (key name): Represents the name of the node to be processed

              Returns:
                  the new street name normalized

              `PEP 484`_ type annotations are supported. If attribute, parameter, and
              return types are annotated according to `PEP 484`_, they do not need to be
              included in the docstring:

              .. _PEP 484:
                  https://www.python.org/dev/peps/pep-0484/

       """
    street_name_normalized = []
    for i, s in enumerate(street_address_name.upper().split()):
        s_new = s
        if s not in EXPRECTED_STREET_TYPE:
            if i > 0 and s in FIX_STREET_TYPE:
                s_new = FIX_STREET_TYPE[s]
    
            if s in FIX_CARDINAL_NAMES:
                s_new = FIX_CARDINAL_NAMES[s]
      
    street_name_normalized.append(s_new)
    s = " ".join(street_name_normalized)
    return s

def normalize_and_clean_zip_code(zipcode):
    """ Function: normalize_and_clean_zip_code.

              The function will receive 01 parameter.
              This function will be called by the function `process_sub_element_to_node` and
              will normalize and clean the zipcode provided.

              Args:
               zipcode (key name): Represents the zipcode of the node to be processed

              Returns:
                  the node name normalized(json format)

              `PEP 484`_ type annotations are supported. If attribute, parameter, and
              return types are annotated according to `PEP 484`_, they do not need to be
              included in the docstring:

              .. _PEP 484:
                  https://www.python.org/dev/peps/pep-0484/

       """
    zip = zipcode.split()
    for z in zip:
        if z.isdigit() or len(z) == 10 or len(z) == 11 or (len(z) == 5 and z.isdigit()):
            zipcode = z
        break

    return zipcode

def normalize_and_clean_conditional_values_from_nodes(conditional, node_key):
    """ Function: normalize_and_clean_conditional_values_from_nodes.

              The function will receive 02 parameters.
              This function will be called by the function `process_sub_element_to_node` and
              will normalize and clean conditionals values from the nodes.

              Args:
                  conditional (str): this conditional will test the value to be clean and normalized in the node
                  node_key (key name): Represents the node key to be processed

              Returns:
                  the conditional rule in the dictionary (json format)

              `PEP 484`_ type annotations are supported. If attribute, parameter, and
              return types are annotated according to `PEP 484`_, they do not need to be
              included in the docstring:

              .. _PEP 484:
                  https://www.python.org/dev/peps/pep-0484/

       """
    # adjusting XML encoding values
    conditional = conditional.replace('&lt;=', ' <= ').replace('&gt;=', ' >= ').replace('&lt;', ' < ').replace('&gt;',' > ').replace('&quot;', '"')
    # removing additional spaces between ',' and '-' and normalizing as lower
    conditional = conditional.replace(', ', ',').replace(' ,', ',').replace('- ', '-').replace(' -', '-').lower()
    # sppliting rules from conditional
    if node_key == 'opening_hours':
      conditional = conditional.split(';')
    else:
      conditional = conditional.split(');')

    conditional_rule_dict = {}
    for v in conditional:

      # Ajuste para opening_hours seguir o mesmo padrao da restricao com condicional yes
      if node_key == 'opening_hours':
        v = 'yes @ ' + v

      value_splited = strip_and_remove_parentesis(v).split('@')
      key, value = None, None

      if len(value_splited) == 0:
        pass
      elif len(value_splited) == 1:
        key = strip_and_remove_parentesis(value_splited[0])
      else:
        key = strip_and_remove_parentesis(value_splited[0])
        value = strip_and_remove_parentesis(value_splited[1])

      values_to_dict = {}
      if (key in conditional_rule_dict):
        values_to_dict = conditional_rule_dict[key]

      values_to_dict = normalize_condition_rule(value, values_to_dict)

      if values_to_dict is None and len(conditional) == 1:
        conditional_rule_dict = key
      elif values_to_dict is None:
        conditional_rule_dict[key] = key
      else:
        conditional_rule_dict[key] = values_to_dict

    return conditional_rule_dict

def normalize_condition_rule(condition, condition_map={}):
    """ Function: normalize_condition_rule.

                  The function will receive 02 parameters.
                  This function will be called by the function `normalize_and_clean_conditional_values_from_nodes` and
                  will normalize .

                  Args:
                      condition (str): this conditional will test the value to be clean and normalized in the node
                      condition_map (dict): Represents the condition map in the node

                  Returns:
                      the condition map normalized (json format)

                  `PEP 484`_ type annotations are supported. If attribute, parameter, and
                  return types are annotated according to `PEP 484`_, they do not need to be
                  included in the docstring:

                  .. _PEP 484:
                      https://www.python.org/dev/peps/pep-0484/

           """
    if condition is not None:
      if condition_map is None:
        condition_map = {}
      conditions = condition.split(';')

      for c in conditions:
        raw_condition = c
        c = c.strip().split(' ', 1)

        if (c is not None and len(c) > 0):
          key = strip_and_remove_parentesis(c[0])
          value = None
          if len(c) == 2:
            value = strip_and_remove_parentesis(c[1])
          condition_map = normalize_condition_map_from_rule(condition_map, key, value, raw_condition)

      return condition_map
    else:
      return None

def normalize_condition_map_from_rule(condition_map, key, value, raw_condition):
    """ Function: normalize_condition_map_from_rule.

                      The function will receive 04 parameters.
                      This function will be called by the function `normalize_condition_rule` and
                      will normalize a condition map from a specific rule.

                      Args:
                          condition_map (dict): Represents the condition map in the node
                          key (key element): the keys to be normalized
                          value (dict): the new values of the key
                          raw_condition: the raw condition to normalize

                      Returns:
                          the condition map normalized (json format)

                      `PEP 484`_ type annotations are supported. If attribute, parameter, and
                      return types are annotated according to `PEP 484`_, they do not need to be
                      included in the docstring:

                      .. _PEP 484:
                          https://www.python.org/dev/peps/pep-0484/

               """
    # Normalizando chaves com dias da semana e lista de chaves de condicoes
    keys = FIX_PERIOD_WEEK_DAYS.get(key)

    if keys is None or len(keys) == 0:
        keys = key.split(',')

    # normalizando horarios e valores
    values = []
    if (value is not None):
        values = value.split(',')

    condition_map = normalize_condition_map_by_keys_and_values(condition_map, keys, values, raw_condition)

    return condition_map

def normalize_condition_map_by_keys_and_values(condition_map, keys, values, raw_condition):
    """ Function: normalize_condition_map_by_keys_and_values.

                      The function will receive 04 parameters.
                      This function will be called by the function `normalize_condition_map_from_rule` and
                      will normalize a condition map by keys and values for the node.

                      Args:
                          condition_map (dict): Represents the condition map in the node
                          key (key element): the keys to be normalized
                          value (dict): the new values of the key
                          raw_condition: the raw condition to normalize

                      Returns:
                          the condition map normalized (json format)

                      `PEP 484`_ type annotations are supported. If attribute, parameter, and
                      return types are annotated according to `PEP 484`_, they do not need to be
                      included in the docstring:

                      .. _PEP 484:
                          https://www.python.org/dev/peps/pep-0484/

               """
    for key in keys:
        key_name = WEEK_DAYS.get(key)
        v = []

        if key_name is None:
            key_name = raw_condition
            values = None
        else:
            if values is None or len(values) == 0:
                v = ['00:00-24:00']
            else:
                v = values

        if key_name in condition_map:
            condition_map[key_name].append(v)
        else:
            condition_map[key_name] = v
    return condition_map

def strip_and_remove_parentesis(v):
  """ Function: strip_and_remove_parentesis.

          The function will receive 01 parameter.
          This function will be called by the function `normalize_and_clean_conditional_values_from_nodes` and
          will strip and remove parentesis in the string provided in the parameter.

          Args:
              y (str): Represents the condition map in the node

          Returns:
              the string normalized.

          `PEP 484`_ type annotations are supported. If attribute, parameter, and
          return types are annotated according to `PEP 484`_, they do not need to be
          included in the docstring:

          .. _PEP 484:
              https://www.python.org/dev/peps/pep-0484/

       """
  if v is not None and len(v) > 0:
    return v.strip().replace('(' , '').replace(')' , '')
  else:
    return None

# Funcoes referente a auditoria de dados
def audit_count_tags_attributes(tags, element):
  """ Function: audit_count_tags_attributes.

          The function will receive 02 parameters.
          This function will be called by the function `audit_tags_subtags` and will audit and count a
          specific element in the tag provided.

          Args:
            tags    (tag element): represents the tag to be audited.
            element (element key): represents the element of the key to be audited.

          Returns:
              a tag audited and counted (json format)

          `PEP 484`_ type annotations are supported. If attribute, parameter, and
          return types are annotated according to `PEP 484`_, they do not need to be
          included in the docstring:

          .. _PEP 484:
              https://www.python.org/dev/peps/pep-0484/

       """
  attributes = {}
  v = 1

  if element.tag in  tags:
    attributes = tags[element.tag]
    v = tags[element.tag]['quantidade'] + 1    

  attributes['quantidade'] = v
  tags[element.tag] = attributes

  for key in element.attrib.keys():
    v = 1

    if key in  attributes:
      v = attributes[key] + 1
    attributes[key] = v

  return tags

def audit_count_tag_attribute_k(tag_k_auditing, element):
  """ Function: audit_count_tag_attribute_k.

          The function will receive 02 parameters.
          This function will be called in the `main` and will audit and count a specific element in the tag provided
          if is element with attrib is `k`.

          Args:
            tag_k_auditing (tag element): represents the tag to be audited.
            element (element key): represents the element of the key to be audited.

          Returns:
              a tag audited and counted (json format)

          `PEP 484`_ type annotations are supported. If attribute, parameter, and
          return types are annotated according to `PEP 484`_, they do not need to be
          included in the docstring:

          .. _PEP 484:
              https://www.python.org/dev/peps/pep-0484/

       """
  if element.tag == 'tag':
    v = 1
    k = element.attrib['k']
    if k in tag_k_auditing:
      v = tag_k_auditing[k] + 1
    tag_k_auditing[k] = v
  return tag_k_auditing

# Regras para key entrar na chave de restrictions
def audit_count_tag_attribute_k_with_v_yes_no(tag_k_v_yes_no_auditing, element):
  """ Function: audit_count_tag_attribute_k_with_v_yes_no.

          The function will receive 02 parameters.
          This function will be called in the `main` and will audit and count a specific element in the tag provided
          if is element with attrib is `k` and `v` = `yes` or `no`.

          Args:
            tag_k_v_yes_no_auditing (tag element): represents the tag to be audited.
            element (element key): represents the element of the key to be audited.

          Returns:
              a tag audited and counted (json format)

          `PEP 484`_ type annotations are supported. If attribute, parameter, and
          return types are annotated according to `PEP 484`_, they do not need to be
          included in the docstring:

          .. _PEP 484:
              https://www.python.org/dev/peps/pep-0484/

       """
  if element.tag == 'tag':
    v = element.attrib['v']
    k = element.attrib['k']
    if v == 'yes' or v == 'no' or v.startswith('yes ') or v.startswith('no ') or 'conditional' in k or k == 'opening_hours':
      tag_k_v_yes_no_auditing.add(k)
  return tag_k_v_yes_no_auditing

def audit_tags_subtags(tags_auditing, element):
  """ Function: audit_tags_subtags.

          The function will receive 02 parameters.
          This function will be called in the `main` and will audit a specific element in the subtag provided.

          Args:
            tags_auditing (tag element): represents the tag to be audited.
            element (element key): represents the element of the key to be audited.

          Returns:
              a subtag audited (json format)

          `PEP 484`_ type annotations are supported. If attribute, parameter, and
          return types are annotated according to `PEP 484`_, they do not need to be
          included in the docstring:

          .. _PEP 484:
              https://www.python.org/dev/peps/pep-0484/

       """
  tags_auditing = audit_count_tags_attributes(tags_auditing, element)

  subElements = element.findall('*')
  subTags = {}
  if(subElements is not None and len(subElements) > 0):
    if 'subtags' in tags_auditing[element.tag]:
      subTags = tags_auditing[element.tag]['subtags']
    
    for e in subElements:
      subTags = audit_count_tags_attributes(subTags, e)
    
    tags_auditing[element.tag]['subtags'] = subTags
  
  return tags_auditing

def audit_postal_code(postal_code, element):
  """ Function: audit_postal_code.

      The function will receive 02 parameters from the tag in the XML file. If the tag
      is a `zip` or `postcode` and has a length of 05 and belongs to NY range, the node will
      be keep kept

      Args:
          postal_code (str): represents the postal_code that will be audited.
          element     (tag element): The element in XML. It must be with attribute = `k`

      Returns:
          postal_code: The returned attribute audited

      `PEP 484`_ type annotations are supported. If attribute, parameter, and
      return types are annotated according to `PEP 484`_, they do not need to be
      included in the docstring:

      .. _PEP 484:
          https://www.python.org/dev/peps/pep-0484/

      """
  if element.tag == 'tag' and element.attrib['k'] in ['addr:zip', 'addr:postcode']:
    if len(element.attrib['v']) != 5:
      postal_code.add(element.attrib['v'])
    else:
      try:
        v = int(element.attrib['v'])
        if not (POSTAL_CODE_NY_RANGE[0] <= v <= POSTAL_CODE_NY_RANGE[1]):
          postal_code.add(element.attrib['v'])
      except ValueError: 
        postal_code.add(element.attrib['v'])
    
  return postal_code

def audit_street_name(street_address, element):
  """ Function: audit_street_name.

          The function will receive 02 parameters.
          This function will be called in the `main` and will audit the street address in the element provided.

          Args:
            street_address (str): a string address.
            element (element key): represents the element of the key to be audited.

          Returns:
              the street address audited (string)

          `PEP 484`_ type annotations are supported. If attribute, parameter, and
          return types are annotated according to `PEP 484`_, they do not need to be
          included in the docstring:

          .. _PEP 484:
              https://www.python.org/dev/peps/pep-0484/

       """
  if element.tag == 'tag' and element.attrib['k'] == 'addr:street':
    v = element.attrib['v'].upper().split(' ')
    for valor in v:
      count = 1
      if valor in street_address:
        count = street_address[valor] + 1
      street_address[valor] = count
  return street_address

'''This function will be working to audit elements and process data to JSON for ingest in mongodb'''
def main(filename):

  json_list = []
 
  tags_auditing = {}
  tag_k_auditing = {}
  tag_k_v_yes_no_auditing = set()
  postal_code = set()
  street_address = {}

  pprint.pprint('Inicio Auditoria ' + str(datetime.now()))
  for event, element in ET.iterparse(filename):
    street_address = audit_street_name(street_address, element)
    postal_code = audit_postal_code(postal_code, element)
    audit_count_tag_attribute_k_with_v_yes_no(tag_k_v_yes_no_auditing, element)
    tag_k_auditing = audit_count_tag_attribute_k(tag_k_auditing, element)
    
    if element.tag in MAIN_TAGS:
      tags_auditing = audit_tags_subtags(tags_auditing, element)

  pprint.pprint('Fim auditoria e inicio Limpeza e estrutucação dos dados ' + str(datetime.now()))
  for event, element in ET.iterparse(filename):
    if element.tag in MAIN_TAGS:
      json_list.append(process_json(element, tag_k_v_yes_no_auditing))
        
  pprint.pprint('Fim de limpeza e estruturacao e inicio Criacao Json ' + str(datetime.now()))
  # You do not need to change this file
  file_out = "{0}.json".format(filename)
  with codecs.open(file_out, "w") as fo:
    fo.write(json.dumps(json_list))
  
  pprint.pprint('Fim Criacao Json ' + str(datetime.now()))

  auditing_items = str('==========================================================\n')
  auditing_items += str('==========   TAGS AUDITING                   =============\n')
  auditing_items += str('==========================================================\n\n\n')
  auditing_items += str(tags_auditing)
  auditing_items += str('\n\n\n==========================================================\n')
  auditing_items += str('==========   TAGS Com Chaves AUDITING            =========\n')
  auditing_items += str('==========================================================\n\n\n')
  auditing_items += str(tag_k_auditing)
  auditing_items += str('\n\n\n==========================================================\n')
  auditing_items += str('==========   TAGS Chave Restrictions AUDITING    =========\n')
  auditing_items += str('==========================================================\n\n\n')
  auditing_items += str(tag_k_v_yes_no_auditing)
  auditing_items += str('\n\n\n==========================================================\n')
  auditing_items += str('==========   TAGS Postal Code AUDITING           =========\n')
  auditing_items += str('==========================================================\n\n\n')
  auditing_items += str(postal_code)
  auditing_items += str('\n\n\n==========================================================\n')
  auditing_items += str('==========   TAGS Street Address AUDITING        =========\n')
  auditing_items += str('==========================================================\n\n\n')
  auditing_items += str(street_address)
  auditing_items += str('\n\n\n==========================================================\n')
  auditing_items += str('==========   Quantidade de linhas no Json        =========\n')
  auditing_items += str('==========================================================\n\n\n')
  auditing_items += str(len(json_list))

  file_out = "{0}-auditing.log".format(filename)
  with codecs.open(file_out, "w") as fo:
    fo.write(auditing_items)

  # pprint.pprint('====================================================') 
  # pprint.pprint(tags_auditing)
  # pprint.pprint('====================================================') 
  # print_items_sorted(tag_k_auditing)
  # pprint.pprint('====================================================') 
  # pprint.pprint(tag_k_v_yes_no_auditing)
  # pprint.pprint('====================================================') 
  # pprint.pprint(postal_code)
  # pprint.pprint('====================================================')
  # print_items_sorted(street_address, key_value=0, reverse=True)
  # pprint.pprint('====================================================')
 

# Caso seja value onde se encontra a key = 0 inserir 1
def print_items_sorted(items, key_value=0, reverse=False):
  print ("{")
  
  for key, value in sorted(items.items(), key=lambda value: value[key_value], reverse=reverse):
    print ("'%s' : %d ," % (key, value))
  print ("}")


pprint.pprint('Inicio do Processo ' + str(datetime.now()))
# main(SAMPLE_FILE)
main(OSM_FILE)
pprint.pprint('Fim Processo ' + str(datetime.now()))

'''
Teste de regras  de condicionais

week_days_map = {}
pprint.pprint('============================================')
condition = 'Mo-Fr 10:00-08:00; Sa,Su'
normalize_condition_rule(condition)
pprint.pprint('============================================')
condition_2 = 'Mo-Th 12:00-02:00; Fr 12:00-04:00; Sa, Su 11:30-04:00; Mo-Fr 19:00-07:00; Sa,Su;SH off'
normalize_condition_rule(condition_2)
pprint.pprint('============================================')
condition_3 = "Mo-Fr 8:00-16:00, 17:00-23:00; Sa 9:00-16:00, 17:00-23:00; Su 9:00-17:00" 
normalize_condition_rule(condition_3)
pprint.pprint('============================================')
'''

'''
Teste de normalizacao de regras  de condicionais

pprint.pprint('============================================')
conditional = "yes @ (axles=2 AND weight&lt;40 st); yes @ (axles=3 AND weight&lt;60 st); yes @ (axles=4 AND weight&lt;70 st); yes @ (axles&gt;=5 AND weight&lt;80 st); no_left_turn @ (Mo-Fr 06:00-10:00,15:00-19:00); no_left_turn @ (Mo-Sa 07:00- 20:00); permissive @ (Mo-Fr 07:00-22:00; SH off);yes @ (Mo-Th 09:00-17:00; Fr 09:00-18:00; Sa 10:00-14:00)"
normalize_and_clean_conditional_values_from_nodes(conditional)
pprint.pprint('============================================')
'''
