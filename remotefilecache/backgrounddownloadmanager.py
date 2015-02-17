#Embedded file name: remotefilecache\backgrounddownloadmanager.py
import logging
import remotefilecache
import uthread2
import blue
log = logging.getLogger('remotefilecache')

class DownloadSet(object):

    def __init__(self, key, fileset):
        self.key = key
        self.fileset = fileset


RESMAN_QUEUE_THRESHOLD = 3

class BackgroundDownloadManager(object):

    def __init__(self):
        self.is_running = False
        self.stop_requested = False
        self.sets = []
        self.sets_by_key = {}

    def schedule(self, key, fileset):
        if key in self.sets_by_key:
            return
        log.debug('Scheduling %s for download (%d files)' % (key, len(fileset)))
        ds = DownloadSet(key, list(fileset))
        self.sets.append(ds)
        self.sets_by_key[key] = ds
        if not self.is_running:
            log.debug('Starting download tasklet')
            self.start()

    def cancel(self, key):
        if key in self.sets_by_key:
            ds = self.sets_by_key[key]
            self.sets.remove(ds)
            del self.sets_by_key[key]

    def pull_to_front(self, key):
        if key in self.sets_by_key:
            ds = self.sets_by_key[key]
            self.sets.remove(ds)
            self.sets.insert(0, ds)

    def push_to_back(self, key):
        if key in self.sets_by_key:
            ds = self.sets_by_key[key]
            self.sets.remove(ds)
            self.sets.append(ds)

    def _run(self):
        self.is_running = True
        while self.is_running:
            while blue.resMan.pendingLoads > RESMAN_QUEUE_THRESHOLD:
                if self.stop_requested:
                    break
                blue.synchro.Yield()

            if not self.is_running:
                break
            if self.stop_requested:
                break
            if len(self.sets) == 0:
                break
            current_set = self.sets[0]
            if len(current_set.fileset) > 0:
                filename = current_set.fileset[0]
                del current_set.fileset[0]
                if not blue.paths.FileExistsLocally(filename):
                    log.debug('Downloading %s' % filename)
                    uthread2.StartTasklet(remotefilecache.prefetch_single_file, filename)
                    blue.synchro.Yield()
            if len(current_set.fileset) == 0:
                log.debug('Finished downloading %s' % current_set.key)
                if current_set.key in self.sets_by_key:
                    self.sets.remove(current_set)
                    del self.sets_by_key[current_set.key]

        self.is_running = False
        self.stop_requested = False

    def stop(self):
        self.stop_requested = True
        while self.is_running:
            blue.synchro.Yield()

    def start(self):
        if self.is_running:
            self.stop_requested = False
            return
        uthread2.StartTasklet(self._run)
