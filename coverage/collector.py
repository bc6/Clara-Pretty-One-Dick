#Embedded file name: coverage\collector.py
"""Raw data collector for Coverage."""
import os, sys, threading
try:
    from coverage.tracer import CTracer
except ImportError:
    if os.getenv('COVERAGE_TEST_TRACER') == 'c':
        sys.stderr.write("*** COVERAGE_TEST_TRACER is 'c' but can't import CTracer!\n")
        sys.exit(1)
    CTracer = None

class PyTracer(object):
    """Python implementation of the raw data tracer."""

    def __init__(self):
        self.data = None
        self.should_trace = None
        self.should_trace_cache = None
        self.warn = None
        self.cur_file_data = None
        self.last_line = 0
        self.data_stack = []
        self.last_exc_back = None
        self.last_exc_firstlineno = 0
        self.arcs = False
        self.thread = None
        self.stopped = False

    def _trace(self, frame, event, arg_unused):
        """The trace function passed to sys.settrace."""
        if self.stopped:
            return
        if self.last_exc_back:
            if frame == self.last_exc_back:
                if self.arcs and self.cur_file_data:
                    pair = (self.last_line, -self.last_exc_firstlineno)
                    self.cur_file_data[pair] = None
                self.cur_file_data, self.last_line = self.data_stack.pop()
            self.last_exc_back = None
        if event == 'call':
            self.data_stack.append((self.cur_file_data, self.last_line))
            filename = frame.f_code.co_filename
            if filename not in self.should_trace_cache:
                tracename = self.should_trace(filename, frame)
                self.should_trace_cache[filename] = tracename
            else:
                tracename = self.should_trace_cache[filename]
            if tracename:
                if tracename not in self.data:
                    self.data[tracename] = {}
                self.cur_file_data = self.data[tracename]
            else:
                self.cur_file_data = None
            self.last_line = -1
        elif event == 'line':
            if self.cur_file_data is not None:
                if self.arcs:
                    self.cur_file_data[self.last_line, frame.f_lineno] = None
                else:
                    self.cur_file_data[frame.f_lineno] = None
            self.last_line = frame.f_lineno
        elif event == 'return':
            if self.arcs and self.cur_file_data:
                first = frame.f_code.co_firstlineno
                self.cur_file_data[self.last_line, -first] = None
            self.cur_file_data, self.last_line = self.data_stack.pop()
        elif event == 'exception':
            self.last_exc_back = frame.f_back
            self.last_exc_firstlineno = frame.f_code.co_firstlineno
        return self._trace

    def start(self):
        """Start this Tracer.
        
        Return a Python function suitable for use with sys.settrace().
        
        """
        self.thread = threading.currentThread()
        sys.settrace(self._trace)
        return self._trace

    def stop(self):
        """Stop this Tracer."""
        self.stopped = True
        if self.thread != threading.currentThread():
            return
        if hasattr(sys, 'gettrace') and self.warn:
            if sys.gettrace() != self._trace:
                msg = 'Trace function changed, measurement is likely wrong: %r'
                self.warn(msg % (sys.gettrace(),))
        sys.settrace(None)

    def get_stats(self):
        """Return a dictionary of statistics, or None."""
        return None


class Collector(object):
    """Collects trace data.
    
    Creates a Tracer object for each thread, since they track stack
    information.  Each Tracer points to the same shared data, contributing
    traced data points.
    
    When the Collector is started, it creates a Tracer for the current thread,
    and installs a function to create Tracers for each new thread started.
    When the Collector is stopped, all active Tracers are stopped.
    
    Threads started while the Collector is stopped will never have Tracers
    associated with them.
    
    """
    _collectors = []

    def __init__(self, should_trace, timid, branch, warn):
        """Create a collector.
        
        `should_trace` is a function, taking a filename, and returning a
        canonicalized filename, or None depending on whether the file should
        be traced or not.
        
        If `timid` is true, then a slower simpler trace function will be
        used.  This is important for some environments where manipulation of
        tracing functions make the faster more sophisticated trace function not
        operate properly.
        
        If `branch` is true, then branches will be measured.  This involves
        collecting data on which statements followed each other (arcs).  Use
        `get_arc_data` to get the arc data.
        
        `warn` is a warning function, taking a single string message argument,
        to be used if a warning needs to be issued.
        
        """
        self.should_trace = should_trace
        self.warn = warn
        self.branch = branch
        self.reset()
        if timid:
            self._trace_class = PyTracer
        else:
            self._trace_class = CTracer or PyTracer

    def __repr__(self):
        return '<Collector at 0x%x>' % id(self)

    def tracer_name(self):
        """Return the class name of the tracer we're using."""
        return self._trace_class.__name__

    def reset(self):
        """Clear collected data, and prepare to collect more."""
        self.data = {}
        self.should_trace_cache = {}
        self.tracers = []

    def _start_tracer(self):
        """Start a new Tracer object, and store it in self.tracers."""
        tracer = self._trace_class()
        tracer.data = self.data
        tracer.arcs = self.branch
        tracer.should_trace = self.should_trace
        tracer.should_trace_cache = self.should_trace_cache
        tracer.warn = self.warn
        fn = tracer.start()
        self.tracers.append(tracer)
        return fn

    def _installation_trace(self, frame_unused, event_unused, arg_unused):
        """Called on new threads, installs the real tracer."""
        sys.settrace(None)
        fn = self._start_tracer()
        if fn:
            fn = fn(frame_unused, event_unused, arg_unused)
        return fn

    def start(self):
        """Start collecting trace information."""
        if self._collectors:
            self._collectors[-1].pause()
        self._collectors.append(self)
        traces0 = []
        if hasattr(sys, 'gettrace'):
            fn0 = sys.gettrace()
            if fn0:
                tracer0 = getattr(fn0, '__self__', None)
                if tracer0:
                    traces0 = getattr(tracer0, 'traces', [])
        fn = self._start_tracer()
        for args in traces0:
            (frame, event, arg), lineno = args
            try:
                fn(frame, event, arg, lineno=lineno)
            except TypeError:
                raise Exception('fullcoverage must be run with the C trace function.')

        threading.settrace(self._installation_trace)

    def stop(self):
        """Stop collecting trace information."""
        self.pause()
        self.tracers = []
        self._collectors.pop()
        if self._collectors:
            self._collectors[-1].resume()

    def pause(self):
        """Pause tracing, but be prepared to `resume`."""
        for tracer in self.tracers:
            tracer.stop()
            stats = tracer.get_stats()
            if stats:
                print '\nCoverage.py tracer stats:'
                for k in sorted(stats.keys()):
                    print '%16s: %s' % (k, stats[k])

        threading.settrace(None)

    def resume(self):
        """Resume tracing after a `pause`."""
        for tracer in self.tracers:
            tracer.start()

        threading.settrace(self._installation_trace)

    def get_line_data(self):
        """Return the line data collected.
        
        Data is { filename: { lineno: None, ...}, ...}
        
        """
        if self.branch:
            line_data = {}
            for f, arcs in self.data.items():
                line_data[f] = ldf = {}
                for l1, _ in list(arcs.keys()):
                    if l1:
                        ldf[l1] = None

            return line_data
        else:
            return self.data

    def get_arc_data(self):
        """Return the arc data collected.
        
        Data is { filename: { (l1, l2): None, ...}, ...}
        
        Note that no data is collected or returned if the Collector wasn't
        created with `branch` true.
        
        """
        if self.branch:
            return self.data
        else:
            return {}
