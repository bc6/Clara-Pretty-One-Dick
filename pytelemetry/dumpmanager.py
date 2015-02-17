#Embedded file name: pytelemetry\dumpmanager.py
import os
import sys
import shutil
import time
import threading
import zipfile
import re
import blue
from _winreg import *
zip_thread = None

class AsyncZipAndSaveTelemetryFiles(threading.Thread):

    def __init__(self, output_folder):
        threading.Thread.__init__(self)
        self.output_folder = output_folder

    def run(self):
        global zip_thread
        telemetry_files = get_telemetry_files()
        if telemetry_files:
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
            zip_file = time.strftime('%a-%d-%b-%Y-%H-%M-%S', time.gmtime())
            z = zipfile.ZipFile('%s.zip' % zip_file, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)
            for filepath in telemetry_files:
                filename = os.path.split(filepath)[1]
                z.write(filepath, filename)

            z.close()
            shutil.move(zip_file + '.zip', self.output_folder)
            discard_newest_capture_files()
        zip_thread = None


TELEMETRY_DUMP_PATH = os.path.join(blue.paths.ResolvePath(u'root:/server/cache'))

def is_telemetry_file(f):
    if re.match('tmdata\\.\\d\\d\\d', f):
        return True
    return False


def save(output_folder):
    global zip_thread
    zip_thread = AsyncZipAndSaveTelemetryFiles(output_folder)
    zip_thread.start()


def check_save_complete():
    return zip_thread is None


def discard_newest_capture_files():
    map(os.remove, get_telemetry_files())


def get_telemetry_files():
    l = []
    if not os.path.exists(TELEMETRY_DUMP_PATH):
        return l
    for filename in os.listdir(TELEMETRY_DUMP_PATH):
        if is_telemetry_file(filename) and os.path.isfile(os.path.join(TELEMETRY_DUMP_PATH, filename)):
            l.append(os.path.join(TELEMETRY_DUMP_PATH, filename))

    return l


def get_existing_files(dump_folder):
    if not os.path.exists(dump_folder):
        return []
    return [ os.path.join(dump_folder, i) for i in os.listdir(dump_folder) ]
