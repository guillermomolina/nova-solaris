# Copyright 2021, Guillermo Adrian Molina.
# Copyright 2011 Justin Santa Barbara
# All Rights Reserved.
#
# Copyright (c) 2013, 2017, Oracle and/or its affiliates. All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import shutil

from oslo_concurrency import lockutils, processutils
from oslo_log import log as logging
from oslo_utils import fileutils

import rad.bindings.com.oracle.solaris.rad.zonemgr_1 as zonemgr
import rad.client

from nova_solaris.solariszones.config import CONF

LOG = logging.getLogger(__name__)

def lookup_resource(zone, resource):
    """Lookup specified resource from specified Solaris Zone."""
    try:
        val = zone.getResources(zonemgr.Resource(resource))
    except rad.client.ObjectError:
        return None
    except Exception:
        raise
    return val[0] if val else None


def lookup_resource_property(zone, resource, prop, filter=None):
    """Lookup specified property from specified Solaris Zone resource."""
    try:
        val = zone.getResourceProperties(zonemgr.Resource(resource, filter),
                                         [prop])
    except rad.client.ObjectError:
        return None
    except Exception:
        raise
    return val[0].value if val else None


def lookup_resource_property_value(zone, resource, prop, value):
    """Lookup specified property with value from specified Solaris Zone
    resource. Returns resource object if matching value is found, else None
    """
    try:
        resources = zone.getResources(zonemgr.Resource(resource))
        for resource in resources:
            for propertee in resource.properties:
                if propertee.name == prop and propertee.value == value:
                    return resource
        else:
            return None
    except rad.client.ObjectError:
        return None
    except Exception:
        raise


def zonemgr_strerror(ex):
    """Format the payload from a zonemgr(3RAD) rad.client.ObjectError
    exception into a sensible error string that can be logged. Newlines
    are converted to a colon-space string to create a single line.

    If the exception was something other than rad.client.ObjectError,
    just return it as a string.
    """
    if not isinstance(ex, rad.client.ObjectError):
        return str(ex)
    payload = ex.get_payload()
    if payload.code == zonemgr.ErrorCode.NONE:
        return str(ex)
    error = [str(payload.code)]
    if payload.str is not None and payload.str != '':
        error.append(payload.str)
    if payload.stderr is not None and payload.stderr != '':
        stderr = payload.stderr.rstrip()
        error.append(stderr.replace('\n', ': '))
    result = ': '.join(error)
    return result


def copy_file(src, dest):
    """Copy a file to an existing directory
    """

    # We shell out to cp because that will intelligently copy
    # zfs files. 
    processutils.execute('/usr/bin/cp', '-z', src, dest)

def get_instance_path(instance, relative=False):
    """Determine the correct path for instance storage.

    This method determines the directory name for instance storage.

    :param instance: the instance we want a path for
    :param relative: if True, just the relative path is returned

    :returns: a path to store information about that instance
    """
    if relative:
        return instance.uuid
    return os.path.join(CONF.instances_path, instance.uuid)

def create_instance_dir(instance):
    # ensure directories exist and are writable
    instance_dir = get_instance_path(instance)
    if os.path.exists(instance_dir):
        LOG.debug("Instance directory exists: not creating",
                    instance=instance)
    else:
        LOG.debug("Creating instance directory", instance=instance)
        fileutils.ensure_tree(instance_dir)
    return instance_dir

def delete_instance_dir(instance):
    target_del = get_instance_path(instance)
    if os.path.exists(target_del):
        LOG.info('Deleting instance files %s',
                    target_del, instance=instance)
        try:
            shutil.rmtree(target_del)
        except OSError as e:
            LOG.error('Failed to cleanup directory %(target)s: %(e)s',
                        {'target': target_del, 'e': e}, instance=instance)
