#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script for spatial data validation
# Authors: Betka & Jachym
#

__version__ = 0.2

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from osgeo import ogr
from cStringIO import StringIO

import json
import re
import os, sys

NOT_PROVIDED = u'nezadáno'
MISSING = u'chybí'
EXTRA = u'navíc'
NOT_MATCH = u'neodpovídá'

class AttributeNotFound(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


class Validator(object):
    """Class for validating features
    :param validator: function, which will do the job
    :param attributes: list of attributes to be checked
    :param allowed_values: object with allowed values
    :param where: WHERE statement for feature selection
    """
    def __init__(self, validator, attributes=None,
                 allowed_values=None, where=None, islike=None):

        self.__attributes = attributes
        self.__validate_function = validator
        self.__allowed_values = allowed_values
        self.__where = where
        self.__islike = islike

    def validate(self, layer):
        """Validate given features with given method
        you can specify attribute and allowed values of given attribute as well
        """

        features = self.get_features(layer)

        errors = self.__validate_function(features,
                                          attributes=self.__attributes,
                                          allowed_values=self.__allowed_values,
                                          islike=self.__islike)

        return errors

    def get_features(self, layer):
        """Get features from layer eventually with given WHERE statement
        """

        features = None
        if self.__where:        
            qgsexpr = QgsExpression(self.__where)
            if qgsexpr.hasParserError():          
                raise AttributeNotFound('error in where statement: "%s"' %(self.__where))
            where_columns = qgsexpr.referencedColumns()
            fields = layer.pendingFields()
            layer_columns = []
            for f in fields:
                layer_columns.append(f.name())

            for i in where_columns:
                if i not in layer_columns:
                    raise AttributeNotFound('error in where statement, where attribute "%s" not in layer' %(i))

            qgsreq = QgsFeatureRequest(qgsexpr)
            features = layer.getFeatures(qgsreq)
        else:
            features = layer.getFeatures()

        return features


def __check_attributes(features, allowed_values,
                       attributes=None, islike=None):
    """Empty proxy function for calling check_attributes with propper parameters
    """
    return check_attributes(features, allowed_values)

def __is_like(features, attributes=None, islike=None,
              allowed_values=None):
    """Empty proxy function for calling check_not_null with propper parameters
    """
    return is_like(features, attributes, islike)


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
    islike = None

    try:
        if rule['validator'] == "islike":
            validing_function = __is_like
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

    if rule.has_key('islike'):
        islike = rule['islike']


    validator = Validator(validing_function,
                          attributes=attributes,
                          allowed_values=allowed_values,
                          where=where,
                          islike=islike)

    return validator

def check_existency(attribute, feature):
    """Check if attribute which has to be validated exists in  layer,
    if doesnt it will raise exception"""
    attrs = feature.fields()
    list_of_attrs = []
    for a in attrs:
        list_of_attrs.append(a.name())
    if attribute in list_of_attrs:
        feature_value = feature[attribute] 
    else:
        raise AttributeNotFound('Not found attibute "%s" in validated layer' % (attribute))

    return feature_value

def get_attributes_validator(attribute, allowed_values):
    """Returns function, which will validate given feature based on
    allowed_values and attribute
    """
   
    def __is_proper_allowedvalue(feature):
        """This function is the one, which will be called for makeing sure,
        feature is all right
        Error is also when attribute is NULL, then is written "nezadáno"
        """

        feature_value = check_existency(attribute, feature)
         
        if feature_value not in allowed_values:
            if feature_value == NULL:
                feature_value = NOT_PROVIDED
            fid = feature['id']
            if fid == NULL:
                fid = None
            return feature_value
        else:
            return None

    def __is_null(feature):
        """Checking input feature if attribute has filled value.
           If attribute is NULL
        """
        value = check_existency(attribute, feature)
        value = feature[attribute]        
        if value == NULL:
            return MISSING
        else:
            return None

    def __is_not_null(feature):
        """Check whether feature is NOT NULL
        """

        value2 = feature[attribute]
        if value2 != NULL:
            return EXTRA
        else:
            return None



    valid_function = None

    if type(allowed_values) == type([]):
        valid_function = __is_proper_allowedvalue
    elif allowed_values == "NULL":
        valid_function = __is_not_null
    elif allowed_values == "NOTNULL":
        valid_function = __is_null

    return valid_function

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


def is_like(features, attributes, islike):
    """Check, whether choosen attribute fits to declared template
    """

    false_features = {}
    attribute = attributes[0]
    for feature in features:
        value = check_existency(attribute, feature)
        #value = feature[attribute]
        reached = 0
        if value == NULL:
            value = 'NULL'
        for pattern in islike:
            regex = re.compile(pattern)
            match = regex.search(value)
            if match != None:
                reached = 1
                break
        if reached == 0:
            false_features[feature.id()] = {attribute: NOT_MATCH}

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

def output_layer(layer, errors, err_file):
    """Create new shapefile layer from selected features (with error)
    and add new attribute "error_desc" where is written name of attribute
    and type of error
    """

    provider = layer.dataProvider()

    fields = provider.fields()
    fields.append(QgsField('error_desc', QVariant.String))
    writer = QgsVectorFileWriter(err_file, provider.encoding(),
                                 fields, QGis.WKBPolygon,
                                 provider.crs())
    layer2 = QgsVectorLayer(err_file, 'l1', 'ogr')
    features = layer.selectedFeatures()

    layer2.startEditing()

    errors_edit = []
    for feature in features:
        for k in errors.keys():
            if k == feature.id():
                error = errors[k]
                text = []
                size = len(error)
                loop_size = list(range(size))
                for i in loop_size:
                    key = error.keys()
                    value = error.values()
                    string = key[i] + " - " + value[i]
                    text.append(string)
                all_errors = ', '.join(text)
                errors_edit.append(all_errors)
                writer.addFeature(feature)
    layer2.commitChanges()

    return errors_edit

def edit_attribute(errors_edit, err_file):
    """ Write error in string as new attribute to output layer
    """

    layer = QgsVectorLayer(err_file, 'l1', 'ogr')
    layer.startEditing()
    delka = len(errors_edit)
    loop_size = list(range(delka))

    for feature in layer.getFeatures():
        for position in loop_size:
            if position == feature.id():
                feature["error_desc"] = errors_edit[position]
                layer.updateFeature(feature)
                break
    layer.commitChanges()

def validate(rulesfile, outputfile, layer, err_file):
    """Validate selected layer with given rules file, make output shapefile with errors
    """

    rules = json.load(open(rulesfile))

    errors = {}
    for rule in rules:
        validator = validator_factory(rule)
        new_errors = validator.validate(layer)

        merge_errors(errors, new_errors)

    if errors:
        layer.setSelectedFeatures(errors.keys())

        errors_edit = output_layer(layer, errors, err_file)
        edit_attribute(errors_edit, err_file)

def main():
    """Main function, collecting necessary data and running the app
    """

    #output_file="/tmp/out.txt"
    #output_file='D:/GEOSENSE/TMO/kontrola atributu/vystupy/komunikace_VHA.txt'
    #output = open(output_file, 'w')

    #rulesfile = 'C:/Users/betka/Desktop/rules_komunikace.json'
    #outputfile = '/tmp/errors.txt'
    #err_file = 'D:/GEOSENSE/TMO/kontrola atributu/vystupy/komunikace2.shp'
    #layer = iface.activeLayer()

    validate(rulesfile, outputfile, layer, err_file)

if __name__ == '__console__':
    try:
        main()
    except:
        print "neprobehlo"
    