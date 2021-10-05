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

from oslo_log import log as logging

from nova.i18n import _

import rad.bindings.com.oracle.solaris.rad.zonemgr_1 as zonemgr
import rad.client

from nova_solaris.solariszones import utils

LOG = logging.getLogger(__name__)

class ZoneConfig(object):
    """ZoneConfig - context manager for access zone configurations.
    Automatically opens the configuration for a zone and commits any changes
    before exiting
    """

    def __init__(self, zone):
        """zone is a zonemgr object representing either a kernel zone or
        non-global zone.
        """
        self.zone = zone
        self.editing = False

    def __enter__(self):
        """enables the editing of the zone."""
        try:
            self.zone.editConfig()
            self.editing = True
            return self
        except Exception as ex:
            reason = utils.utils.zonemgr_strerror(ex)
            LOG.exception(_("Unable to initialize editing of instance '%s' "
                            "via zonemgr(3RAD): %s")
                          % (self.zone.name, reason))
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """looks for any kind of exception before exiting.  If one is found,
        cancel any configuration changes and reraise the exception.  If not,
        commit the new configuration.
        """
        if exc_type is not None and self.editing:
            # We received some kind of exception.  Cancel the config and raise.
            self.zone.cancelConfig()
            raise
        else:
            # commit the config
            try:
                self.zone.commitConfig()
            except Exception as ex:
                reason = utils.zonemgr_strerror(ex)
                LOG.exception(_("Unable to commit the new configuration for "
                                "instance '%s' via zonemgr(3RAD): %s")
                              % (self.zone.name, reason))

                # Last ditch effort to cleanup.
                self.zone.cancelConfig()
                raise

    def setprop(self, resource, prop, value):
        """sets a property for an existing resource OR creates a new resource
        with the given property(s).
        """
        current = utils.lookup_resource_property(self.zone, resource, prop)
        if current is not None and current == value:
            # the value is already set
            return

        try:
            if current is None:
                self.zone.addResource(zonemgr.Resource(
                    resource, [zonemgr.Property(prop, value)]))
            else:
                self.zone.setResourceProperties(
                    zonemgr.Resource(resource),
                    [zonemgr.Property(prop, value)])
        except Exception as ex:
            reason = utils.zonemgr_strerror(ex)
            LOG.exception(_("Unable to set '%s' property on '%s' resource for "
                            "instance '%s' via zonemgr(3RAD): %s")
                          % (prop, resource, self.zone.name, reason))
            raise

    def addresource(self, resource, props=None, ignore_exists=False):
        """creates a new resource with an optional property list, or set the
        property if the resource exists and ignore_exists is true.

        :param ignore_exists: If the resource exists, set the property for the
            resource.
        """
        if props is None:
            props = []

        try:
            self.zone.addResource(zonemgr.Resource(resource, props))
        except Exception as ex:
            if isinstance(ex, rad.client.ObjectError):
                code = ex.get_payload().code
                if (ignore_exists and
                        code == zonemgr.ErrorCode.RESOURCE_ALREADY_EXISTS):
                    self.zone.setResourceProperties(
                        zonemgr.Resource(resource, None), props)
                    return
            reason = utils.zonemgr_strerror(ex)
            LOG.exception(_("Unable to create new resource '%s' for instance "
                            "'%s' via zonemgr(3RAD): %s")
                          % (resource, self.zone.name, reason))
            raise

    def removeresources(self, resource, props=None):
        """removes resources whose properties include the optional property
        list specified in props.
        """
        if props is None:
            props = []

        try:
            self.zone.removeResources(zonemgr.Resource(resource, props))
        except Exception as ex:
            reason = utils.zonemgr_strerror(ex)
            LOG.exception(_("Unable to remove resource '%s' for instance '%s' "
                            "via zonemgr(3RAD): %s")
                          % (resource, self.zone.name, reason))
            raise

    def clear_resource_props(self, resource, props):
        """Clear property values of a given resource
        """
        try:
            self.zone.clearResourceProperties(zonemgr.Resource(resource, None),
                                              props)
        except rad.client.ObjectError as ex:
            reason = utils.zonemgr_strerror(ex)
            LOG.exception(_("Unable to clear '%s' property on '%s' resource "
                            "for instance '%s' via zonemgr(3RAD): %s")
                          % (props, resource, self.zone.name, reason))
            raise
