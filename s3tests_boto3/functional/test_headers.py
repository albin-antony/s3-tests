import boto3
from nose.tools import eq_ as eq
from nose.plugins.attrib import attr
from nose.plugins.attrib import attr
import nose
from botocore.exceptions import ClientError
from email.utils import formatdate

from .utils import assert_raises

from . import (
    get_client,
    get_v2_client,
    get_new_bucket,
    get_new_bucket_name,
    )

#TODO: move this into utils
def _get_status_and_error_code(response):
    status = response['ResponseMetadata']['HTTPStatusCode']
    error_code = response['Error']['Code']
    return status, error_code

def _add_header_create_object(headers, client=None):
    """ Create a new bucket, add an object w/header customizations
    """
    bucket_name = get_new_bucket()
    if client == None:
        client = get_client()
    key_name = 'foo'

    # pass in custom headers before PutObject call
    add_headers = (lambda **kwargs: kwargs['params']['headers'].update(headers))
    client.meta.events.register('before-call.s3.PutObject', add_headers)
    client.put_object(Bucket=bucket_name, Key=key_name)

    return bucket_name, key_name


def _add_header_create_bad_object(headers, client=None):
    """ Create a new bucket, add an object with a header. This should cause a failure 
    """
    bucket_name = get_new_bucket()
    if client == None:
        client = get_client()
    key_name = 'foo'

    # pass in custom headers before PutObject call
    add_headers = (lambda **kwargs: kwargs['params']['headers'].update(headers))
    client.meta.events.register('before-call.s3.PutObject', add_headers)
    e = assert_raises(ClientError, client.put_object, Bucket=bucket_name, Key=key_name, Body='bar')

    return e


def _remove_header_create_object(remove, client=None):
    """ Create a new bucket, add an object without a header
    """
    bucket_name = get_new_bucket()
    if client == None:
        client = get_client()
    key_name = 'foo'

    # remove custom headers before PutObject call
    def remove_header(**kwargs):
        if (remove in kwargs['params']['headers']):
            del kwargs['params']['headers'][remove]

    client.meta.events.register('before-call.s3.PutObject', remove_header)
    client.put_object(Bucket=bucket_name, Key=key_name)

    return bucket_name, key_name

def _remove_header_create_bad_object(remove, client=None):
    """ Create a new bucket, add an object without a header. This should cause a failure
    """
    bucket_name = get_new_bucket()
    if client == None:
        client = get_client()
    key_name = 'foo'

    # remove custom headers before PutObject call
    def remove_header(**kwargs):
        if (remove in kwargs['params']['headers']):
            del kwargs['params']['headers'][remove]

    client.meta.events.register('before-call.s3.PutObject', remove_header)
    e = assert_raises(ClientError, client.put_object, Bucket=bucket_name, Key=key_name, Body='bar')

    return e


def _add_header_create_bucket(headers, client=None):
    """ Create a new bucket, w/header customizations
    """
    bucket_name = get_new_bucket_name()
    if client == None:
        client = get_client()

    # pass in custom headers before PutObject call
    add_headers = (lambda **kwargs: kwargs['params']['headers'].update(headers))
    client.meta.events.register('before-call.s3.CreateBucket', add_headers)
    client.create_bucket(Bucket=bucket_name)

    return bucket_name


def _add_header_create_bad_bucket(headers=None, client=None):
    """ Create a new bucket, w/header customizations that should cause a failure 
    """
    bucket_name = get_new_bucket_name()
    if client == None:
        client = get_client()

    # pass in custom headers before PutObject call
    add_headers = (lambda **kwargs: kwargs['params']['headers'].update(headers))
    client.meta.events.register('before-call.s3.CreateBucket', add_headers)
    e = assert_raises(ClientError, client.create_bucket, Bucket=bucket_name)

    return e


def _remove_header_create_bucket(remove, client=None):
    """ Create a new bucket, without a header
    """
    bucket_name = get_new_bucket_name()
    if client == None:
        client = get_client()

    # remove custom headers before PutObject call
    def remove_header(**kwargs):
        if (remove in kwargs['params']['headers']):
            del kwargs['params']['headers'][remove]

    client.meta.events.register('before-call.s3.CreateBucket', remove_header)
    client.create_bucket(Bucket=bucket_name)

    return bucket_name

def _remove_header_create_bad_bucket(remove, client=None):
    """ Create a new bucket, without a header. This should cause a failure
    """
    bucket_name = get_new_bucket_name()
    if client == None:
        client = get_client()

    # remove custom headers before PutObject call
    def remove_header(**kwargs):
        if (remove in kwargs['params']['headers']):
            del kwargs['params']['headers'][remove]

    client.meta.events.register('before-call.s3.CreateBucket', remove_header)
    e = assert_raises(ClientError, client.create_bucket, Bucket=bucket_name)

    return e

def tag(*tags):
    def wrap(func):
        for tag in tags:
            setattr(func, tag, True)
        return func
    return wrap

#
# common tests
#

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/invalid MD5')
@attr(assertion='fails 400')
def test_object_create_bad_md5_invalid_short():
    e = _add_header_create_bad_object({'Content-MD5':'YWJyYWNhZGFicmE='})
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)
    eq(error_code, 'InvalidDigest')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/mismatched MD5')
@attr(assertion='fails 400')
def test_object_create_bad_md5_bad():
    e = _add_header_create_bad_object({'Content-MD5':'rL0Y20xC+Fzt72VPzMSk2A=='})
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)
    eq(error_code, 'BadDigest')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/empty MD5')
@attr(assertion='fails 400')
def test_object_create_bad_md5_empty():
    e = _add_header_create_bad_object({'Content-MD5':''})
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)
    eq(error_code, 'InvalidDigest')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/no MD5 header')
@attr(assertion='succeeds')
def test_object_create_bad_md5_none():
    bucket_name, key_name = _remove_header_create_object('Content-MD5')
    client = get_client()
    client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/Expect 200')
@attr(assertion='garbage, but S3 succeeds!')
def test_object_create_bad_expect_mismatch():
    bucket_name, key_name = _add_header_create_object({'Expect': 200})
    client = get_client()
    client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/empty expect')
@attr(assertion='succeeds ... should it?')
def test_object_create_bad_expect_empty():
    bucket_name, key_name = _add_header_create_object({'Expect': ''})
    client = get_client()
    client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/no expect')
@attr(assertion='succeeds')
def test_object_create_bad_expect_none():
    bucket_name, key_name = _remove_header_create_object('Expect')
    client = get_client()
    client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/empty content length')
@attr(assertion='fails 400')
@attr('fails_on_rgw')
def test_object_create_bad_contentlength_empty():
    e = _add_header_create_bad_object({'Content-Length':''})
    status, error_code = _get_status_and_error_code(e.response)
    #NOTES: the boto2 version succeeeds and returns a 400, the boto3 version succeeds and returns a 403. 
    # Look at what the outgoing requests look like and see what gives??
    # - RGW does not even get a the 400 from boto2
    # - RGW does not even get a the 403 from boto3 shows up though
    eq(status, 400)

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/negative content length')
@attr(assertion='fails 400')
@attr('fails_on_mod_proxy_fcgi')
# TODO: remove 'fails_on_rgw' once I figure out what's going on
def test_object_create_bad_contentlength_negative():
    #boto2 version works fine, boto3 version returns a 403, the content length doesn't get sent through to boto3 I think. Search for 'CONTENT_LENGTH' in rgw log
    # need to see what the difference is between the http requests
    e = _add_header_create_bad_object({'Content-Length':'-1'})
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/no content length')
@attr(assertion='fails 411')
def test_object_create_bad_contentlength_none():
    remove = 'Content-Length'
    e = _remove_header_create_bad_object('Content-Length')
    # TODO: boto2 version works just fine, boto3 version doesn't throw an error at all. I'm guessing the http requests between the two must be different.
    # run a new vstart and run the boto2 version
    # run a new vstart and run the boto3 version
    # compare the logs
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 411)
    eq(error_code, 'MissingContentLength')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/content length too long')
@attr(assertion='fails 400')
@attr('fails_on_rgw')
def test_object_create_bad_contentlength_mismatch_above():
    # same as object as add_header_create_bad_object
    content = 'foo'
    length = len(content) + 1

    e = _add_header_create_bad_object({'Content-Length': length})
    status, error_code = _get_status_and_error_code(e.response)
    #NOTES: the boto2 version succeeeds and returns a 400, the boto3 version succeeds and returns a 403. 
    # Look at what the outgoing requests look like and see what gives??
    eq(status, 400)

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/content type text/plain')
@attr(assertion='succeeds')
def test_object_create_bad_contenttype_invalid():
    bucket_name, key_name = _add_header_create_object({'Content-Type': 'text/plain'})
    client = get_client()
    client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/empty content type')
@attr(assertion='succeeds')
def test_object_create_bad_contenttype_empty():
    bucket_name, key_name = _add_header_create_object({'Content-Type': ''})
    client = get_client()
    client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/no content type')
@attr(assertion='succeeds')
def test_object_create_bad_contenttype_none():
    # TODO: see if this actually removes content-type header
    boto3.set_stream_logger(name='botocore')
    #bucket_name, key_name = _remove_header_create_object('Content-Type')
    bucket_name = get_new_bucket()
    key_name = 'foo'
    client = get_client()
    #client.put_object(Bucket=bucket_name, Key=key_name, Body='bar', ContentType='text/blahh')
    client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')


@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/empty authorization')
@attr(assertion='fails 403')
def test_object_create_bad_authorization_empty():
    # TODO: run this on boto2 and see what happens, this doesn't assert on the RGW
    boto3.set_stream_logger(name='botocore')
    e = _add_header_create_bad_object({'Authorization': ''})
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    print error_code

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/date and x-amz-date')
@attr(assertion='succeeds')
def test_object_create_date_and_amz_date():
    # TODO: is 'Date' and this test even necessary? 
    date = formatdate(usegmt=True)
    #bucket_name, key_name = _add_header_create_object({'Date': date, 'X-Amz-Date': date})
    bucket_name, key_name = _add_header_create_object({'X-Amz-Date': date})
    client = get_client()
    client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/x-amz-date and no date')
@attr(assertion='succeeds')
def test_object_create_amz_date_and_no_date():
    # TODO: is 'Date' and this test even necessary? 
    # 1) this asserts when it shouldn't. Figure out what's wrong, look at detailed logs
    # 2) figure out what to put in so that the Date is empty. Is it None or a empty string
    date = formatdate(usegmt=True)
    bucket_name, key_name = _add_header_create_object({'Date': '', 'X-Amz-Date': date})
    client = get_client()
    client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

# the teardown is really messed up here. check it out
@tag('auth_common')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/no authorization')
@attr(assertion='fails 403')
def test_object_create_bad_authorization_none():
    # TODO: run this on boto2 and see what happens, this doesn't assert on the RGW
    e = _remove_header_create_bad_object('Authorization')
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    print error_code

@tag('auth_common')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/no content length')
@attr(assertion='succeeds')
def test_bucket_create_contentlength_none():
    # TODO: see if this actually removes content-length header
    remove = 'Content-Length'
    _remove_header_create_bucket(remove)

@tag('auth_common')
@attr(resource='bucket')
@attr(method='acls')
@attr(operation='set w/no content length')
@attr(assertion='succeeds')
def test_object_acl_create_contentlength_none():
    # TODO: see if this actually removes content-length header
    bucket_name = get_new_bucket()
    client = get_client()
    client.put_object(Bucket=bucket_name, Key='foo', Body='bar')

    remove = 'Content-Length'
    def remove_header(**kwargs):
        if (remove in kwargs['params']['headers']):
            del kwargs['params']['headers'][remove]

    client.meta.events.register('before-call.s3.PutObjectAcl', remove_header)
    client.put_object_acl(Bucket=bucket_name, Key='foo', ACL='public-read')

@tag('auth_common')
@attr(resource='bucket')
@attr(method='acls')
@attr(operation='set w/invalid permission')
@attr(assertion='fails 400')
def test_bucket_put_bad_canned_acl():
    bucket_name = get_new_bucket()
    client = get_client()

    headers = {'x-amz-acl': 'public-ready'}
    add_headers = (lambda **kwargs: kwargs['params']['headers'].update(headers))
    client.meta.events.register('before-call.s3.PutBucketAcl', add_headers)

    e = assert_raises(ClientError, client.put_bucket_acl, Bucket=bucket_name, ACL='public-read')
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)

# strangely, amazon doesn't report an error with a non-expect 100 also, our
# error comes back as html, and not xml as I normally expect
@tag('auth_common')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/expect 200')
@attr(assertion='garbage, but S3 succeeds!')
@attr('fails_on_rgw')
def test_bucket_create_bad_expect_mismatch():
    #NOTES: this passed just fine on RGW, look at headers to see if it worked fined, and run boto2 version
    bucket_name = get_new_bucket_name()
    client = get_client()

    headers = {'Expect': 200}
    add_headers = (lambda **kwargs: kwargs['params']['headers'].update(headers))
    client.meta.events.register('before-call.s3.CreateBucket', add_headers)
    client.create_bucket(Bucket=bucket_name)

@tag('auth_common')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/expect empty')
@attr(assertion='garbage, but S3 succeeds!')
def test_bucket_create_bad_expect_empty():
    headers = {'Expect': ''}
    _add_header_create_bucket(headers)

@tag('auth_common')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/empty content length')
@attr(assertion='fails 400')
@attr('fails_on_rgw')
def test_bucket_create_bad_contentlength_empty():
    #NOTES: this is supposed to fail on the RGW but it doesn't
    # the error_code is 400 not 'bad request' or something
    headers = {'Content-Length': ''}
    e = _add_header_create_bad_bucket(headers)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)

@tag('auth_common')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/negative content length')
@attr(assertion='fails 400')
@attr('fails_on_mod_proxy_fcgi')
def test_bucket_create_bad_contentlength_negative():
    headers = {'Content-Length': '-1'}
    e = _add_header_create_bad_bucket(headers)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)

@tag('auth_common')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/no content length')
@attr(assertion='succeeds')
def test_bucket_create_bad_contentlength_none():
    remove = 'Content-Length'
    _remove_header_create_bucket(remove)

@tag('auth_common')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/empty authorization')
@attr(assertion='fails 403')
def test_bucket_create_bad_authorization_empty():
    # TODO: client error is not being raised, need to look at the boto2 version to see what's going on
    headers = {'Authorization': ''}
    e = _add_header_create_bad_bucket(headers)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

@tag('auth_common')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/no authorization')
@attr(assertion='fails 403')
def test_bucket_create_bad_authorization_none():
    # TODO: an assertion error is never raised, perhaps, there is never an 'Authorization' header passed
    e = _remove_header_create_bad_bucket('Authorization')
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/invalid MD5')
@attr(assertion='fails 400')
def test_object_create_bad_md5_invalid_garbage_aws2():
    v2_client = get_v2_client()
    headers = {'Content-MD5': 'AWS HAHAHA'}
    e = _add_header_create_bad_object(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)
    eq(error_code, 'InvalidDigest')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/content length too short')
@attr(assertion='fails 400')
def test_object_create_bad_contentlength_mismatch_below_aws2():
    v2_client = get_v2_client()
    content = 'bar'
    length = len(content) - 1
    headers = {'Content-Length': str(length)}
    #TODO: this doesn't assert, figure out what's going wrong
    e = _add_header_create_bad_object(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)
    eq(error_code, 'BadDigest')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/incorrect authorization')
@attr(assertion='fails 403')
def test_object_create_bad_authorization_incorrect_aws2():
    v2_client = get_v2_client()
    headers = {'Authorization': 'AWS AKIAIGR7ZNNBHC5BKSUB:FWeDfwojDSdS2Ztmpfeubhd9isU='}
    #TODO: this doesn't assert, figure out what's going wrong
    # because HTTP_AUTHORIZATION in RGW log can't be changed by boto3, ask Casey about this
    e = _add_header_create_bad_object(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    #figure out what error code this produces
    print error_code
    #eq(error_code, 'InvalidDigest')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/invalid authorization')
@attr(assertion='fails 400')
def test_object_create_bad_authorization_invalid_aws2():
    v2_client = get_v2_client()
    headers = {'Authorization': 'AWS HAHAHA'}
    #TODO: this doesn't assert, figure out what's going wrong
    # because HTTP_AUTHORIZATION in RGW log can't be changed by boto3, ask Casey about this
    e = _add_header_create_bad_object(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 400)
    eq(error_code, 'InvalidArgument')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/empty user agent')
@attr(assertion='succeeds')
def test_object_create_bad_ua_empty_aws2():
    v2_client = get_v2_client()
    headers = {'User-Agent': ''}
    bucket_name, key_name = _add_header_create_object(headers, v2_client)
    v2_client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/no user agent')
@attr(assertion='succeeds')
def test_object_create_bad_ua_none_aws2():
    v2_client = get_v2_client()
    remove = 'User-Agent'
    bucket_name, key_name = _remove_header_create_object(remove, v2_client)
    v2_client.put_object(Bucket=bucket_name, Key=key_name, Body='bar')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/invalid date')
@attr(assertion='fails 403')
def test_object_create_bad_date_invalid_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': 'Bad Date'}
    e = _add_header_create_bad_object(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/empty date')
@attr(assertion='fails 403')
def test_object_create_bad_date_empty_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': ''}
    e = _add_header_create_bad_object(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/no date')
@attr(assertion='fails 403')
def test_object_create_bad_date_none_aws2():
    v2_client = get_v2_client()
    remove = 'x-amz-date'
    # TODO: boto3 never removes the date header because it can't be removed with "before-call or before-sign"
    e = _remove_header_create_bad_object(remove, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/date in past')
@attr(assertion='fails 403')
def test_object_create_bad_date_before_today_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': 'Tue, 07 Jul 2010 21:53:04 GMT'}
    e = _add_header_create_bad_object(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'RequestTimeTooSkewed')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/date before epoch')
@attr(assertion='fails 403')
def test_object_create_bad_date_before_epoch_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': 'Tue, 07 Jul 1950 21:53:04 GMT'}
    e = _add_header_create_bad_object(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

@tag('auth_aws2')
@attr(resource='object')
@attr(method='put')
@attr(operation='create w/date after 9999')
@attr(assertion='fails 403')
def test_object_create_bad_date_after_end_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': 'Tue, 07 Jul 9999 21:53:04 GMT'}
    e = _add_header_create_bad_object(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'RequestTimeTooSkewed')

@tag('auth_aws2')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/invalid authorization')
@attr(assertion='fails 400')
def test_bucket_create_bad_authorization_invalid_aws2():
    v2_client = get_v2_client()
    #headers = {'Authorization': 'AWS HAHAHA'}
    # TODO: this doesn't raise a ClientError on the RGW
    # because HTTP_AUTHORIZATION in RGW log can't be changed by boto3, ask Casey about this
    #e = _add_header_create_bad_bucket(headers, v2_client)
    #status, error_code = _get_status_and_error_code(e.response)
    #eq(status, 400)
    #eq(error_code, 'InvalidArgument')

    bucket_name = get_new_bucket_name()

    #headers = _get_acl_header()

    def add_headers_before_sign(**kwargs):
        #updated_headers = (kwargs['request'].__dict__['headers'].__dict__['_headers'] + headers)
        #kwargs['request'].__dict__['headers'].__dict__['_headers'] = updated_headers
        #print kwargs['request'].__dict__
        #print kwargs['request'].__dict__['headers'].__dict__
        #print kwargs['request'].__dict__['headers'].__dict__['_headers']
        kwargs['params']['context']['auth_type'] = 'AWS HAHAHA'
        print kwargs['params']['context']['auth_type']
        #print kwargs['params']['headers']

    #v2_client.meta.events.register('before-sign.s3.CreateBucket', add_headers_before_sign)
    v2_client.meta.events.register('before-call.s3.CreateBucket', add_headers_before_sign)
    boto3.set_stream_logger(name='botocore')
    v2_client.create_bucket(Bucket=bucket_name)

@tag('auth_aws2')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/empty user agent')
@attr(assertion='succeeds')
def test_bucket_create_bad_ua_empty_aws2():
    v2_client = get_v2_client()
    headers = {'User-Agent': ''}
    _add_header_create_bucket(headers, v2_client)

@tag('auth_aws2')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/no user agent')
@attr(assertion='succeeds')
def test_bucket_create_bad_ua_none_aws2():
    v2_client = get_v2_client()
    remove = 'User-Agent'
    _remove_header_create_bucket(remove, v2_client)

@tag('auth_aws2')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/invalid date')
@attr(assertion='fails 403')
def test_bucket_create_bad_date_invalid_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': 'Bad Date'}
    e = _add_header_create_bad_bucket(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

@tag('auth_aws2')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/empty date')
@attr(assertion='fails 403')
def test_bucket_create_bad_date_empty_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': ''}
    e = _add_header_create_bad_bucket(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

@tag('auth_aws2')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/no date')
@attr(assertion='fails 403')
def test_bucket_create_bad_date_none_aws2():
    # TODO: boto2 is passing (raising a 403), boto3 never removes the date header because it can't be removed with "before-call or before-sign"

    v2_client = get_v2_client()
    remove = 'x-amz-date'
    e = _remove_header_create_bad_bucket(remove, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

@tag('auth_aws2')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/date in past')
@attr(assertion='fails 403')
def test_bucket_create_bad_date_before_today_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': 'Tue, 07 Jul 2010 21:53:04 GMT'}
    e = _add_header_create_bad_bucket(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'RequestTimeTooSkewed')

@tag('auth_aws2')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/date in future')
@attr(assertion='fails 403')
def test_bucket_create_bad_date_after_today_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': 'Tue, 07 Jul 2030 21:53:04 GMT'}
    e = _add_header_create_bad_bucket(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'RequestTimeTooSkewed')

@tag('auth_aws2')
@attr(resource='bucket')
@attr(method='put')
@attr(operation='create w/date before epoch')
@attr(assertion='fails 403')
def test_bucket_create_bad_date_before_epoch_aws2():
    v2_client = get_v2_client()
    headers = {'x-amz-date': 'Tue, 07 Jul 1950 21:53:04 GMT'}
    e = _add_header_create_bad_bucket(headers, v2_client)
    status, error_code = _get_status_and_error_code(e.response)
    eq(status, 403)
    eq(error_code, 'AccessDenied')

def test_screw_around():
    bucket_name = get_new_bucket()
    client = get_client()
    key_name = 'foo'
    add_headers = (lambda **kwargs: kwargs['params']['headers'].update(headers))
    client.meta.events.register('before-sign.s3.PutObject', add_headers)
    client.put_object(Bucket=bucket_name, Key=key_name)

    v2_client = get_v2_client()
    bucket_name = get_new_bucket_name()

    #headers = _get_acl_header()

    def add_headers_before_sign(**kwargs):
        #updated_headers = (kwargs['request'].__dict__['headers'].__dict__['_headers'] + headers)
        #kwargs['request'].__dict__['headers'].__dict__['_headers'] = updated_headers
        #print kwargs['request'].__dict__
        #print kwargs['request'].__dict__['headers'].__dict__
        #print kwargs['request'].__dict__['headers'].__dict__['_headers']
        print kwargs
        #print kwargs['params']['headers']

    v2_client.meta.events.register('before-sign.s3.CreateBucket', add_headers_before_sign)
    #v2_client.meta.events.register('before-call.s3.CreateBucket', add_headers_before_sign)
    boto3.set_stream_logger(name='botocore')
    v2_client.create_bucket(Bucket=bucket_name)

