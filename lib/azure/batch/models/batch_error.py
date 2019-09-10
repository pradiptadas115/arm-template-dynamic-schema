# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model
from msrest.exceptions import HttpOperationError


class BatchError(Model):
    """An error response received from the Azure Batch service.

    :param code: An identifier for the error. Codes are invariant and are
     intended to be consumed programmatically.
    :type code: str
    :param message: A message describing the error, intended to be suitable
     for display in a user interface.
    :type message: :class:`ErrorMessage <azure.batch.models.ErrorMessage>`
    :param values: A collection of key-value pairs containing additional
     details about the error.
    :type values: list of :class:`BatchErrorDetail
     <azure.batch.models.BatchErrorDetail>`
    """ 

    _attribute_map = {
        'code': {'key': 'code', 'type': 'str'},
        'message': {'key': 'message', 'type': 'ErrorMessage'},
        'values': {'key': 'values', 'type': '[BatchErrorDetail]'},
    }

    def __init__(self, code=None, message=None, values=None):
        self.code = code
        self.message = message
        self.values = values


class BatchErrorException(HttpOperationError):
    """Server responsed with exception of type: 'BatchError'.

    :param deserialize: A deserializer
    :param response: Server response to be deserialized.
    """

    def __init__(self, deserialize, response, *args):

        super(BatchErrorException, self).__init__(deserialize, response, 'BatchError', *args)
