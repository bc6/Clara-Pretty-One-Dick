#Embedded file name: carbon/common/lib\ccp_exceptions.py
from eveexceptions import UserError, SQLError, ConnectionError, UnmarshalError, RoleNotAssignedError
exports = {'exceptions.UserError': UserError,
 'exceptions.SQLError': SQLError,
 'exceptions.ConnectionError': ConnectionError,
 'exceptions.UnmarshalError': UnmarshalError,
 'exceptions.RoleNotAssignedError': RoleNotAssignedError}
