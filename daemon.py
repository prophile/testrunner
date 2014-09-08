import tempfile
import urllib.parse
import os.path
import subprocess
from itertools import chain
from shlex import quote

import redis

DOCKER_BINARY='docker'
DOCKER_IMAGE='alynn/svr-travis'
CLONE_ONLY=False

conn = redis.StrictRedis()

class TestJob(object):
    def __init__(self, command, cwd):
        self.elements = ["$ cd {}".format(cwd).encode('utf-8'),
                         "$ {}".format(' '.join('"' + arg + '"' if '$' in arg or ' ' in arg else arg
                                                  for arg in command)).encode('utf-8')]

    def __iter__(self):
        return iter(self.elements)

    @property
    def status(self):
        return True # true for success, false for failure, bees

class RealJob(object):
    def __init__(self, command, cwd):
        self.first_line = ('$ ' + ' '.join(quote(arg) for arg in command) + '\n').encode('utf-8')
        self.proc = subprocess.Popen(command, cwd=cwd,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def __iter__(self):
        return chain([self.first_line], self.proc.stdout)

    @property
    def status(self):
        self.proc.wait()
        return self.proc.returncode == 0

job_class = RealJob

class JobFailureException(Exception):
    pass

def run_job(jobID, *args, **kwargs):
    job = job_class(*args, **kwargs)
    for line in job:
        print(line.decode('utf-8'), end='')
        conn.append('jobs:{}:log'.format(jobID), line)
    end_status = job.status
    if end_status is None:
        raise JobFailureException('Job never finished')
    if not end_status:
        raise JobFailureException('Job exited uncleanly')

while True:
    (_, job) = conn.blpop('queue:builds')
    (uri, ref, jobID) = job.decode('utf-8').split(' ')
    print(job)
    with conn.pipeline() as pipe:
        pipe.set('jobs:{}:log'.format(jobID), '')
        pipe.set('jobs:{}:status'.format(jobID), 'running')
        pipe.execute()
    name = urllib.parse.urlparse(uri).path.rstrip('/').split('/')[-1]
    success = False
    try:
        with tempfile.TemporaryDirectory() as f:
            run_job(jobID, ('git', 'clone', '-n', uri, name), f)
            target_dir = os.path.join(f, name)
            run_job(jobID, ('git', 'fetch', 'origin', ref), target_dir)
            run_job(jobID, ('git', 'checkout', 'FETCH_HEAD'), target_dir)
            run_job(jobID, ('git', 'submodule', 'update', '--init', '--recursive'), target_dir)
            if not CLONE_ONLY:
                run_job(jobID, (DOCKER_BINARY, 'run', '--rm', '-v', '{}:/data'.format(target_dir), DOCKER_IMAGE, 'install', 'script'), target_dir)
        success = True
    except JobFailureException:
        pass
    finally:
        with conn.pipeline() as pipe:
            status_message = 'complete' if success else 'failure'
            pipe.set('jobs:{}:status'.format(jobID),
                     status_message)
            pipe.publish('jobs', '{} {}'.format(jobID, status_message))
            pipe.execute()


