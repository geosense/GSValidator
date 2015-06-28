#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Skript na validaci vstupních dat
# Authors: Betka & Jachym
#

__version__ = 0.2

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import qgis.utils

import json
import os, sys
from prettytable import PrettyTable

class Validator(object):
    """Class for validating features

    :param validator: function, which will do the job
    :param attributes: list of attributes to be checked
    :param allowed_values: object with allowed values
    :param where: WHERE statement for feature selection
    """
    def __init__(self, validator, attributes = None,
            allowed_values = None, where=None):

        self.__attributes = attributes
        self.__validate_function = validator
        self.__allowed_values = allowed_values
        self.__where = where

    def validate(self, layer):
        """Validate given features with given method

        you can specify attribute and allowed values of given attribute as well
        """

        features = self.get_features(layer)

        errors = self.__validate_function(features,
                attributes = self.__attributes,
                allowed_values = self.__allowed_values)

        return errors

    def get_features(self, layer):
        """Get features from layer eventually with given WHERE statement
        """

        features = None
        if self.__where:
            qgsexpr = QgsExpression(self.__where)
            qgsreq = QgsFeatureRequest(qgsexpr)
            features = layer.getFeatures(qgsreq) 
        else:
            features = layer.getFeatures()
        return features

def __check_attributes(features, allowed_values, attributes = None):
    """Empty proxy function for calling check_attributes with propper parameters
    """
    return check_attributes(features, allowed_values)


def __check_is_null(features, attributes = None, allowed_values=None):
    """Empty proxy function for calling check_is_null with propper parameters
    """
    return check_is_null(features, attributes)

def __check_not_null(features, attributes = None, allowed_values=None):
    """Empty proxy function for calling check_not_null with propper parameters
    """
    return check_not_null(features, attributes)


def validator_factory(rule):
    """Creates instances of Validator, based on 'rules' json, which can contain
    following keys:

    validator - function, which will validate
    attributes - list of attributes, which will be validated
    attribute - single attribute with same meaning
    allowed_values - dictionary with attribute_name as key and list of allowed
                    values
    """

    validing_function = None
    attributes = None
    allowed_values = None
    where = None

    try:
        if rule['validator'] == "isnull":
            validing_function = __check_is_null
        elif rule['validator'] == "notnull":
            validing_function = __check_not_null
        elif rule['validator'] == "allowedvalues":
            validing_function = __check_attributes
    except:
        pass

    if not validing_function:
        raise Exception("No validation function found for validator '%s'" %\
                rule['validator'])

    if rule.has_key('attribute'):
        attributes = [rule['attribute']]
    elif rule.has_key('attributes'):
        attributes = rule['attributes']

    if rule.has_key('allowed_values'):
        allowed_values = rule['allowed_values']

    if rule.has_key('where'):
        where = rule['where']


    validator = Validator(validing_function,
            attributes = attributes,
            allowed_values = allowed_values,
            where = where)

    return validator

    

def get_attributes_validator(attribute, allowed_values):
    """Returns function, which will validate given feature based on
    allowed_values and attribute
    """

    def __is_proper_allowedvalue(feature):
        """This function is the one, which will be called for makeing sure,
        feature is all right
        """

        feature_value = feature[attribute]
        if feature_value not in allowed_values:
            if feature_value == NULL:
                feature_value = None
            id = feature['id']
            if id == NULL:
                id = None
            return feature_value
        else:
            return None

    return __is_proper_allowedvalue

def check_feature_attributes(feature, allowed_values):
    """Checke for all feature attributes
    """

    attributes = {}

    for attr in allowed_values.keys():
        checking_function = get_attributes_validator(attr, allowed_values[attr])
        checked = checking_function(feature)
        if checked:
            attributes[attr] = checked
            feature.setValid(False)
    
    return attributes or None

def check_attributes(features, allowed_values):
    """check for all filled attributes in required detail
    """

    false_attributes = {}
    for feature in features:
        wrong_attributes = check_feature_attributes(feature, allowed_values)
        if wrong_attributes:
            false_attributes[feature.id()] = wrong_attributes

    return false_attributes

def check_is_null(features, attributes):
    """Check, whether given attribute of features is null
    """
    return check_not_null(features, attributes, True)

def check_not_null(features, attributes, reverse = False):
    """Check, whether given attribute of given feature is NOT NULL
    """

    false_features = {}
    for feature in features:
        for attribute in attributes:
            value = feature[attribute]
            if value == NULL:
                value = None
            if not value and not reverse:
                false_features[feature.id()] = {attribute: value}
            elif reverse and value:
                false_features[feature.id()] = {attribute: value}

    return false_features

def merge_errors(old, new):
    """Merge new errors into already existing errors object
    """

    for e in new:
        if e in old:
            copy_old = old[e].copy()
            copy_old.update(new[e])
            old[e] = copy_old
        else:
            old[e] = new[e]

    return old

def write_errors(errors):
    """Create string with rendered errors
    """

    outstr = ""

    columns = ["Feature"]
    for e in errors:
        keys = errors[e].keys()
        for k in keys:
            if k not in columns:
                columns.append(k)

    table = PrettyTable(columns)

    for i in errors:
        row = [i]

        for k in columns[1:]:
            feature = errors[i]
            if feature.has_key(k):
                row.append(feature[k])
            else:
                row.append('')

        table.add_row(row)

    return table.get_string()

def validate(rulesfile, outputfile, layer):
    """Validate selected layer with given rules file
    """

    rules = json.load(open(rulesfile))

    errors = {}
    for rule in rules:
        validator = validator_factory(rule)
        new_errors = validator.validate(layer)

        merge_errors(errors, new_errors)

    if errors:
        layer.setSelectedFeatures(errors.keys())
        errors_txt = write_errors(errors)

        out = None
        if outputfile and os.path.isfile(outputfile):
            out = open(outputfile, 'w')
        else:
            out = sys.stdout
        out.write(errors_txt) 

def main():
    """Main function, collecting necessary data and running the app
    """

    #output_file="/tmp/out.txt"
    # output_file = 'D:/GEOSENSE/TMO/kontrola atributu/vystupy/komunikace_VHA.txt'
    #output = open(output_file, 'w')

    rulesfile = '/home/jachym/src/gs/qgis-scripts/passports/rules.json'
    outputfile = '/tmp/errors.txt'
    layer = iface.activeLayer()

    validate(rulesfile, outputfile, layer)

if __name__ == '__console__':
    main()
