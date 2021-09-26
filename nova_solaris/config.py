# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2019, Guillermo Adrian Molina. All rights reserved.
#
# Copyright (c) 2013, Oracle and/or its affiliates. All rights reserved.
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

from oslo_config import cfg

CONF = cfg.CONF

solariszones_group = cfg.OptGroup(
    'solariszones',
    title='Solaris Zones Options')


solariszones_opts = [
    cfg.StrOpt('boot_volume_type',
               default=None,
               help='Cinder volume type to use for boot volumes'),
    cfg.StrOpt('boot_volume_az',
               default=None,
               help='Cinder availability zone to use for boot volumes'),
    cfg.StrOpt('glancecache_dirname',
               default='/var/share/nova/images',
               help='Default path to Glance cache for Solaris Zones.'),
    cfg.StrOpt('nfs_username',
               default=None,
               help='Username used to mount NFS volumes.'),
    cfg.StrOpt('nfs_groupname',
               default=None,
               help='Groupname used to mount NFS volumes.'),
    cfg.StrOpt('live_migration_cipher',
               help='Cipher to use for encryption of memory traffic during '
                    'live migration. If not specified, a common encryption '
                    'algorithm will be negotiated. Options include: none or '
                    'the name of a supported OpenSSL cipher algorithm.'),
    cfg.StrOpt('solariszones_snapshots_directory',
               default='$instances_path/snapshots',
               help='Location to store snapshots before uploading them to the '
                    'Glance image service.'),
    cfg.StrOpt('zones_suspend_path',
               default='/var/share/zones/SYSsuspend',
               help='Default path for suspend images for Solaris Zones.'),
    cfg.BoolOpt('solariszones_boot_options',
                default=True,
                help='Allow kernel boot options to be set in instance '
                     'metadata.'),
]

def register_opts(conf):
    conf.register_group(solariszones_group)
    conf.register_opts(solariszones_opts, group=solariszones_group)

# To generate a sample config run:
# $ oslo-config-generator --namespace nova_solariszones > nova_solariszones_sample.conf
def list_opts():
    # The nova conf tooling expects each module to return a dict of options.
    # When solariszones is pulled into nova proper the return value would be in
    # this form:
    # return {solariszones_group.name: solariszones_opts}
    #
    # The oslo-config-generator tooling expects a tuple:
    return [(solariszones_group.name, solariszones_opts)]
