# -*- coding: utf-8 -*-
from .. import model
from ..context import Ctx, DevDataType, DevField
from ..profile import Base,base_types

def get_message_field_raw_value(message, field_name):
    field = message.fields.pick(True, name=field_name)
    return field.raw_value if field else None

def _register_developer_data_id(developer_data_index, application_id=None, fields=None):
    Ctx.developer_data_types[developer_data_index] = DevDataType(
        developer_data_index = developer_data_index,
        application_id = application_id
    )

def register_developer_data_id(message):
    developer_data_index = get_message_field_raw_value(message, 'developer_data_index')
    application_id = get_message_field_raw_value(message, 'application_id')
    _register_developer_data_id(developer_data_index, application_id)

def register_developer_field(message):
    developer_data_index = get_message_field_raw_value(message, 'developer_data_index')
    field_def_num = get_message_field_raw_value(message, 'field_definition_number')
    base_type_id = get_message_field_raw_value(message, 'fit_base_type_id')
    field_name = get_message_field_raw_value(message, 'field_name') or 'unnamed_dev_field_%s' % field_def_num
    units = get_message_field_raw_value(message, 'units')
    native_field_num = get_message_field_raw_value(message, 'native_field_num')

    assert developer_data_index in Ctx.developer_data_types
    Ctx.developer_data_types[developer_data_index].fields[field_def_num] = DevField(
        dev_data_index=developer_data_index,
        def_num=field_def_num,
        base_type=base_types.pick(base_type_id),
        name=field_name,
        units=units,
        native_field_num=native_field_num
    )

class Message(Base):
    def __init__(self, header):
        self.header = header

    @classmethod
    def unpack(cls, header, reader):
        if isinstance(header, model.NormalHeader) and header.definition:
            message = model.MessageDefinition.unpack(header, reader)
            Ctx.message_definitions[header.local_message_type] = message
        else:
            message = model.MessageData.unpack(header, reader)
            if message.definition.name == 'developer_data_id':
                register_developer_data_id(message)
            elif message.definition.name == 'field_description':
                register_developer_field(message)
        return message
