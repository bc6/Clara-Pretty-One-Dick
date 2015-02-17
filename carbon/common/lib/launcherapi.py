#Embedded file name: carbon/common/lib\launcherapi.py
"""
This module provides some simple mmap wrappers to pass status information between the EVE 
client and the EVE launcher, such as client boot progress (client->launcher) and staged 
install status (launcher->client)

This file exists within the client scope, and goes hand in hand with a similarly named
file within the Launcher scope. When changing one of these files please ensure that the
other is updated too.
"""
import logmodule
import json
import mmap
import os
NULL = chr(0)

class MemoryOverflow(Exception):
    """raised when we try to write too much data to a given shared memory block"""
    pass


class UpdateFailedWrongDataType(Exception):
    """raised when we try to .Update() a dict key, in memory, but the .Read() data 
    isn't a dict"""
    pass


class BaseSharedMemory(object):
    """Base mmap wrapper class. Handles simple read/write functions"""

    def __init__(self, size, name):
        self.size = size
        self.name = name
        self.memory = mmap.mmap(-1, size, name)
        self.EMPTY = self.size * NULL

    def Read(self):
        self.memory.seek(0)
        return self.memory.readline()

    def Write(self, what):
        self.memory.seek(0)
        self.memory.write(str(what))

    def Wipe(self):
        self.memory.seek(0)
        for i in xrange(self.size):
            self.memory.write(NULL)

    def IsEmpty(self):
        data = self.Read()
        return data == self.EMPTY


class JsonMemory(BaseSharedMemory):
    """JSON shared memory handler. Reads and writes JSON data rather than just plain strings"""
    size = 1024

    def Read(self):
        """Reads the data from memory, and .strip()'s the trailing linebreak"""
        response = super(JsonMemory, self).Read()
        try:
            data = json.loads(response.strip())
        except ValueError:
            data = response.strip()

        return data

    def Write(self, what):
        """Writes data to shared memory. Converts to JSON data, so should probably only accept dicts
        since any other datatype doesn't really make sense"""
        data = json.dumps(what) + '\n'
        if len(data) > self.size:
            raise MemoryOverflow('Data is of length {} whilst the memory will only hold {}'.format(len(data), self.size))
        super(JsonMemory, self).Write(data)

    def Update(self, key, value):
        """Updates a dictionary that we've previously written to memory. Only updates the key 
        specified"""
        state = self.Read()
        if self.IsEmpty():
            state = {}
        if not isinstance(state, dict):
            raise UpdateFailedWrongDataType('Data in memory is of type {!r}'.format(type(state)))
        state[key] = value
        self.Write(state)


class ClientBootManager(JsonMemory):

    def __init__(self):
        self.name = 'exefile{}'.format(os.getpid())
        super(ClientBootManager, self).__init__(self.size, self.name)
        logmodule.GetChannel('sharedMemory')
        self.log = logmodule.GetChannel('sharedMemory').Log

    def SetPercentage(self, percentage):
        self.log('Client boot progress: %s' % percentage)
        self.Update('clientBoot', percentage)
