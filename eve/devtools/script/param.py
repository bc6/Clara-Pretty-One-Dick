#Embedded file name: eve/devtools/script\param.py


def _typecast(cls, value):
    try:
        return cls(value)
    except StandardError:
        if type(cls) == type:
            raise Error('invalid %s argument: %s' % (cls.__name__, value))
        raise


class Error(StandardError):
    __guid__ = 'param.Error'


class ParamObject:

    def __init__(self, line):
        self.line = line
        self.argc = -1
        self.error = 'Param object not initialized'
        self.__call__ = self.ParseTypes

    def __len__(self):
        return len(self.argi)

    def __getitem__(self, idx):
        if type(idx) != int:
            raise TypeError('Unsupported key for __getitem__')
        self._compile()
        if idx >= self.argc:
            raise IndexError(self.error)
        else:
            return self.args[idx]

    def __getslice__(self, left, right):
        self._compile()
        if left > self.argc:
            raise IndexError(self.error)
        if right < 2147483647:
            raise ValueError('ParamObjects only support [x:] slicing')
        try:
            return self.line[self.argi[left]:]
        except IndexError:
            raise IndexError(self.error)

    def _compile(self):
        if self.argc > -1:
            return
        self.args = []
        self.argi = []
        quoted = False
        line = self.line
        length = len(line)
        self.error = 'param index out of range'
        idx = 0
        while idx < length:
            while line[idx] == ' ':
                idx += 1

            self.argi.append(idx)
            if line[idx] == '"':
                idx += 1
                left = idx
                idx = line.find('"', idx)
                if idx == -1:
                    self.error = 'unterminated quote'
                    break
                arg = self.line[left:idx]
                self.args.append(arg)
                idx += 1
                if idx >= length:
                    break
                if line[idx] != ' ':
                    self.error = 'crap behind quote at position %d' % (idx - 1)
                    break
            else:
                left = idx
                idx = line.find(' ', idx)
                if idx == -1:
                    idx = 2147483647
                arg = self.line[left:idx]
                q = arg.find('"')
                if q > -1:
                    self.error = 'crap before quote at position %d' % (left + q)
                    break
                self.args.append(arg)

        self.argc = len(self.args)

    def Parse(self, template, offset = 0):
        ret = []
        a = ret.append
        n = offset
        qty = 1
        wasdigit = False
        optional = False
        try:
            tlist = list(template)
            while tlist:
                c = tlist.pop(0)
                while qty:
                    if c == 's':
                        a(self[n])
                    elif c == 'i':
                        try:
                            a(int(self[n]))
                        except ValueError as e:
                            raise Error(e)

                    elif c == 'f':
                        a(float(self[n]))
                    elif c == 'x':
                        self[n]
                    else:
                        if c == '.':
                            return ret
                        if c == '?':
                            optional = 1
                            n -= 1
                        else:
                            if c == 'r':
                                a(self[n:])
                                return ret
                            if c.isdigit():
                                if wasdigit:
                                    qty = 10 * qty + int(c)
                                else:
                                    qty = int(c)
                                    wasdigit = True
                                break
                    wasdigit = False
                    qty -= 1
                    n += 1
                else:
                    qty = 1

        except IndexError:
            if optional:
                tlist.append('s')
            else:
                raise Error('not enough arguments for template string')

        if optional:
            while tlist:
                c = tlist.pop()
                if c != '?':
                    a(None)

        elif n != self.argc:
            raise Error('not all arguments converted during template parsing')
        return ret

    def ParseTypes(self, *args, **kwargs):
        eol = kwargs.get('eol', False)
        optional = False
        positional = 0
        n = 0
        ret = []
        todo = list(args)
        while todo:
            typeClass = todo.pop(0)
            if typeClass:
                if isinstance(typeClass, list):
                    todo = typeClass
                    optional = True
                    positional = n
                    continue
                try:
                    if eol and not todo:
                        value = self[n:]
                        n = self.argc
                    else:
                        value = self[n]
                        n += 1
                except IndexError as e:
                    if optional:
                        ret.append(None)
                    else:
                        raise Error(e)
                else:
                    ret.append(_typecast(typeClass, value))

            else:
                ret.append(None)

        if positional != self.argc and n != self.argc:
            raise Error('not all parameters converted during type parsing')
        return ret


exports = {'param.Error': Error,
 'param.ParamObject': ParamObject}
