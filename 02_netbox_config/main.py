import netaddr, pynetbox, re
from braceexpand import braceexpand
from pprint import pprint

# set netbox-docker api address and token
nb = pynetbox.api(
    'http://192.168.137.100:8000',
    token='0123456789abcdef0123456789abcdef01234567'
)

# get tenancy, create new if necessary
upstart_crow = nb.tenancy.tenants.get(name='upstart_crow')
if not upstart_crow:
    upstart_crow = nb.tenancy.tenants.create(
        name = 'upstart_crow',
        slug = 'upstart_crow')


# get regions
all_regions = nb.dcim.regions.all()
def create_region(region):
    slug = region.lower()
    if region not in [x.name for x in all_regions]:
        region = nb.dcim.regions.create(
            name = region,
            slug = slug
            )

# get emea region
create_region('EMEA')
emea = nb.dcim.regions.get(name='EMEA')

# check if site LD4 exists
ld4 = nb.dcim.sites.get(name='LD4')
if not ld4:
    ld4 = nb.dcim.sites.create(
        name = 'LD4',
        region = emea.id,
        slug = 'ld4')

# get active device roles
roles = nb.dcim.device_roles.all()

# create roles
if 'spine' not in [x.name for x in roles]:
    spine = nb.dcim.device_roles.create(
        name = 'spine',
        slug = 'spine')
if 'leaf' not in [x.name for x in roles]:
    leaf = nb.dcim.device_roles.create(
        name = 'leaf',
        slug = 'leaf')

# get active RIR's
all_rirs = nb.ipam.rirs.all()

# create rfc1918 RIR
if 'rfc1918' not in [x.name for x in all_rirs]:
    rfc1918 = nb.ipam.rirs.create(
        name = 'rfc1918',
        is_private = True,
        slug = 'rfc1918')

# get active ipam roles
ipam_roles = nb.ipam.roles.all()

# define function for ipam role creation
def create_ipam_role(role_name):
    if role_name not in [x.name for x in ipam_roles]:
        role_name = nb.ipam.roles.create(
            name = role_name,
            slug = role_name,
            description = role_name)

# create ipam roles for subnet
create_ipam_role('loopback')
create_ipam_role('oob_mgmt')
create_ipam_role('interswitch_link')

# get active aggregates
all_aggregates = nb.ipam.aggregates.all()

def create_ip_aggregate(prefix):
    if str(prefix) not in [x.prefix for x in all_aggregates]:
        role = nb.ipam.aggregates.create(
            prefix = str(prefix),
            site = ld4.id,
            rir = rfc1918.id,
            tenant = upstart_crow.id)

# get active prefixes
all_prefixes = nb.ipam.prefixes.all()

# define function for prefix creation
def create_ip_prefix(prefix, role, pool):
    # get role.id
    role = nb.ipam.roles.get(name=role)
    if str(prefix) not in [x.prefix for x in all_prefixes]:
        role = nb.ipam.prefixes.create(
            prefix = str(prefix),
            role = role.id,
            site = ld4.id,
            tenant = upstart_crow.id,
            is_pool = pool)

# define aggregate networks
loopback_agg = netaddr.IPNetwork('150.0.0.0/8')
interswitch_link_agg = netaddr.IPNetwork('155.0.0.0/8')
oob_mgmt_agg = netaddr.IPNetwork('192.168.0.0/16')

# create ip aggregates
create_ip_aggregate(loopback_agg)
create_ip_aggregate(interswitch_link_agg)
create_ip_aggregate(oob_mgmt_agg)

# define prefixes
loopback_1_agg = netaddr.IPNetwork('150.1.1.0/24')
loopback_2_agg = netaddr.IPNetwork('150.2.2.0/24')
loopback_3_agg = netaddr.IPNetwork('150.3.3.0/24')
loopback_4_agg = netaddr.IPNetwork('150.4.4.0/24')
loopback_5_agg = netaddr.IPNetwork('150.5.5.0/24')
loopback_6_agg = netaddr.IPNetwork('150.6.6.0/24')
interswitch_link_11 = netaddr.IPNetwork('155.1.11.0/24')
interswitch_link_12 = netaddr.IPNetwork('155.1.12.0/24')
interswitch_link_13 = netaddr.IPNetwork('155.1.13.0/24')
interswitch_link_14 = netaddr.IPNetwork('155.1.14.0/24')
interswitch_link_21 = netaddr.IPNetwork('155.1.21.0/24')
interswitch_link_22 = netaddr.IPNetwork('155.1.22.0/24')
interswitch_link_23 = netaddr.IPNetwork('155.1.23.0/24')
interswitch_link_24 = netaddr.IPNetwork('155.1.24.0/24')
oob_mgmt_1 = netaddr.IPNetwork('192.168.137.0/24')

# create ip prefixes
create_ip_prefix(loopback_1_agg, 'loopback', True)
create_ip_prefix(loopback_2_agg, 'loopback', True)
create_ip_prefix(loopback_3_agg, 'loopback', True)
create_ip_prefix(loopback_4_agg, 'loopback', True)
create_ip_prefix(loopback_5_agg, 'loopback', True)
create_ip_prefix(loopback_6_agg, 'loopback', True)
create_ip_prefix(interswitch_link_11, 'interswitch_link', True)
create_ip_prefix(interswitch_link_12, 'interswitch_link', True)
create_ip_prefix(interswitch_link_13, 'interswitch_link', True)
create_ip_prefix(interswitch_link_14, 'interswitch_link', True)
create_ip_prefix(interswitch_link_21, 'interswitch_link', True)
create_ip_prefix(interswitch_link_22, 'interswitch_link', True)
create_ip_prefix(interswitch_link_23, 'interswitch_link', True)
create_ip_prefix(interswitch_link_24, 'interswitch_link', True)
create_ip_prefix(oob_mgmt_1, 'oob_mgmt', True)
