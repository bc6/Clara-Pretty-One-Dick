#Embedded file name: coverage\templite.py
"""A simple Python template renderer, for a nano-subset of Django syntax."""
import re, sys

class Templite(object):
    """A simple template renderer, for a nano-subset of Django syntax.
    
    Supported constructs are extended variable access::
    
        {{var.modifer.modifier|filter|filter}}
    
    loops::
    
        {% for var in list %}...{% endfor %}
    
    and ifs::
    
        {% if var %}...{% endif %}
    
    Comments are within curly-hash markers::
    
        {# This will be ignored #}
    
    Construct a Templite with the template text, then use `render` against a
    dictionary context to create a finished string.
    
    """

    def __init__(self, text, *contexts):
        """Construct a Templite with the given `text`.
        
        `contexts` are dictionaries of values to use for future renderings.
        These are good for filters and global values.
        
        """
        self.text = text
        self.context = {}
        for context in contexts:
            self.context.update(context)

        toks = re.split('(?s)({{.*?}}|{%.*?%}|{#.*?#})', text)
        ops = []
        ops_stack = []
        for tok in toks:
            if tok.startswith('{{'):
                ops.append(('exp', tok[2:-2].strip()))
            elif tok.startswith('{#'):
                continue
            elif tok.startswith('{%'):
                words = tok[2:-2].strip().split()
                if words[0] == 'if':
                    if_ops = []
                    ops.append(('if', (words[1], if_ops)))
                    ops_stack.append(ops)
                    ops = if_ops
                elif words[0] == 'for':
                    for_ops = []
                    ops.append(('for', (words[1], words[3], for_ops)))
                    ops_stack.append(ops)
                    ops = for_ops
                elif words[0].startswith('end'):
                    ops = ops_stack.pop()
                else:
                    raise SyntaxError("Don't understand tag %r" % words)
            else:
                ops.append(('lit', tok))

        self.ops = ops

    def render(self, context = None):
        """Render this template by applying it to `context`.
        
        `context` is a dictionary of values to use in this rendering.
        
        """
        ctx = dict(self.context)
        if context:
            ctx.update(context)
        engine = _TempliteEngine(ctx)
        engine.execute(self.ops)
        return ''.join(engine.result)


class _TempliteEngine(object):
    """Executes Templite objects to produce strings."""

    def __init__(self, context):
        self.context = context
        self.result = []

    def execute(self, ops):
        """Execute `ops` in the engine.
        
        Called recursively for the bodies of if's and loops.
        
        """
        for op, args in ops:
            if op == 'lit':
                self.result.append(args)
            elif op == 'exp':
                try:
                    self.result.append(str(self.evaluate(args)))
                except:
                    exc_class, exc, _ = sys.exc_info()
                    new_exc = exc_class("Couldn't evaluate {{ %s }}: %s" % (args, exc))
                    raise new_exc

            elif op == 'if':
                expr, body = args
                if self.evaluate(expr):
                    self.execute(body)
            elif op == 'for':
                var, lis, body = args
                vals = self.evaluate(lis)
                for val in vals:
                    self.context[var] = val
                    self.execute(body)

            else:
                raise AssertionError("TempliteEngine doesn't grok op %r" % op)

    def evaluate(self, expr):
        """Evaluate an expression.
        
        `expr` can have pipes and dots to indicate data access and filtering.
        
        """
        if '|' in expr:
            pipes = expr.split('|')
            value = self.evaluate(pipes[0])
            for func in pipes[1:]:
                value = self.evaluate(func)(value)

        elif '.' in expr:
            dots = expr.split('.')
            value = self.evaluate(dots[0])
            for dot in dots[1:]:
                try:
                    value = getattr(value, dot)
                except AttributeError:
                    value = value[dot]

                if hasattr(value, '__call__'):
                    value = value()

        else:
            value = self.context[expr]
        return value
