
# Used by as logging filter for Graylog (see setting.py)
import logging


class FieldFilter(logging.Filter):

    def __init__(self, fields):
        self.fields = fields

    def filter(self, record):
        for k, v in self.fields.items():
            setattr(record, k, v)
        return True
