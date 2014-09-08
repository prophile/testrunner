import redis
from functools import wraps
from bottle import route, run, response, request, app, url
import json
import uuid

get_url = url
conn = redis.StrictRedis()

def get(path):
    def wrapper(fn):
        route(path=path, method='GET', callback=fn, name=fn.__name__)
        return fn
    return wrapper

def post(path):
    def wrapper(fn):
        route(path=path, method='POST', callback=fn, name=fn.__name__)
        return fn
    return wrapper

def json_out(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        result = f(*args, **kwargs)
        response.content_type = 'application/json'
        return json.dumps(result)
    return wrapper

@get('/')
@json_out
def root():
    return {'submit': get_url('submit_get'),
            'jobs': {'status': get_url('job_status', id='{id}'),
                     'log': get_url('job_log', id='{id}')}}

@get('/submit')
@json_out
def submit_get():
    return {'params': ['uri', 'ref']}

@post('/submit')
@json_out
def submit_post():
    uri = request.forms.get('uri')
    ref = request.forms.get('ref', 'refs/heads/master')
    if uri is None:
        response.status = 400
        return {'error': 'No URI given'}
    jobID = str(uuid.uuid4())
    conn.set('job:{}:status', 'queued')
    conn.rpush('queue:builds', '{} {} {}'.format(uri, ref, jobID))
    response.status = 202
    return {'id': jobID,
            'status': get_url('job_status', id=jobID),
            'log': get_url('job_log', id=jobID)}

@get('/jobs')
@json_out
def jobs_get():
    # this is expensive
    keys = conn.keys('jobs:*:status')
    return [key[5:-7] for key in keys]

@get('/jobs/:id')
@json_out
def job_get(id):
    return {'id': id,
            'status': get_url('job_status', id=id),
            'log': get_url('job_log', id=id)}

@get('/jobs/:id/status')
@json_out
def job_status(id):
    status = conn.get('jobs:{}:status'.format(id))
    if status is None:
        response.status = 404
        return {'error': 'Job not found'}
    return {'id': id,
            'status': status.decode('utf-8')}

@get('/jobs/:id/log')
@json_out
def job_log(id):
    data = conn.get('jobs:{}:log'.format(id))
    if data is None:
        response.status = 404
        return {'error': 'Log unavailable'}
    return {'id': id,
            'log': data.decode('utf-8')}

if __name__ == '__main__':
    run(port=3000)

