# Copyright 2021, Guillermo Adrian Molina.
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

from cinderclient import exceptions as cinder_exception
from keystoneclient import exceptions as keystone_exception

from nova import exception

from nova.volume.cinder import API as CinderAPI
from nova.volume.cinder import cinderclient
from nova.volume.cinder import translate_volume_exception
from nova.volume.cinder import _untranslate_volume_summary_view

class SolarisVolumeAPI(CinderAPI):
    """ Extending the volume api to support additional cinder sub-commands
    """

    @translate_volume_exception
    def create(self, context, size, name, description, snapshot=None,
               image_id=None, volume_type=None, metadata=None,
               availability_zone=None, source_volume=None):
        """Clone the source volume by calling the cinderclient version of
        create with a source_volid argument

        :param context: the context for the clone
        :param size: size of the new volume, must be the same as the source
            volume
        :param name: display_name of the new volume
        :param description: display_description of the new volume
        :param snapshot: Snapshot object
        :param image_id: image_id to create the volume from
        :param volume_type: type of volume
        :param metadata: Additional metadata for the volume
        :param availability_zone: zone:host where the volume is to be created
        :param source_volume: Volume object

        Returns a volume object
        """
        client = cinderclient(context)

        if snapshot is not None:
            snapshot_id = snapshot['id']
        else:
            snapshot_id = None

        if source_volume is not None:
            source_volid = source_volume['id']
        else:
            source_volid = None

        kwargs = dict(snapshot_id=snapshot_id,
                      volume_type=volume_type,
                      user_id=context.user_id,
                      project_id=context.project_id,
                      availability_zone=availability_zone,
                      metadata=metadata,
                      imageRef=image_id,
                      source_volid=source_volid)

        kwargs['name'] = name
        kwargs['description'] = description

        try:
            item = cinderclient(context).volumes.create(size, **kwargs)
            return _untranslate_volume_summary_view(context, item)
        except cinder_exception.OverLimit:
            raise exception.OverQuota(overs='volumes')
        except (cinder_exception.BadRequest,
                keystone_exception.BadRequest) as reason:
            raise exception.InvalidInput(reason=reason)

    @translate_volume_exception
    def update(self, context, volume_id, fields):
        """Update the fields of a volume for example used to rename a volume
        via a call to cinderclient

        :param context: the context for the update
        :param volume_id: the id of the volume to update
        :param fields: a dictionary of of the name/value pairs to update
        """
        cinderclient(context).volumes.update(volume_id, **fields)

    @translate_volume_exception
    def extend(self, context, volume, newsize):
        """Extend the size of a cinder volume by calling the cinderclient

        :param context: the context for the extend
        :param volume: the volume object to extend
        :param newsize: the new size of the volume in GB
        """
        cinderclient(context).volumes.extend(volume, newsize)
