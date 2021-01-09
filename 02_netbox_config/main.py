import netaddr
import pynetbox
import sys
import yaml
from braceexpand import braceexpand
from pprint import pprint


# set netbox-docker api address and token
nb = pynetbox.api(
    'http://192.168.137.100:8000',
    token='0123456789abcdef0123456789abcdef01234567')

# get tenancy, create new if necessary
print(f"\nChecking netbox tenants...")
all_tenants = nb.tenancy.tenants.all()


def create_tenant(name):
    slug = name.lower()
    if name not in [x.name for x in all_tenants]:
        print(f"\nAdding {name} tenant...")
        tenant = nb.tenancy.tenants.create(
            name=name,
            slug=slug
            )


# create upstart_crow tenant
create_tenant('upstart_crow')
upstart_crow = nb.tenancy.tenants.get(name='upstart_crow')

# get regions
print(f"\nChecking netbox regions...")
all_regions = nb.dcim.regions.all()


def create_region(region):
    slug = region.lower()
    if region not in [x.name for x in all_regions]:
        print(f"\nAdding {region} region...")
        region = nb.dcim.regions.create(
            name=region,
            slug=slug
            )


# create EMEA region and pull object
create_region('EMEA')
emea = nb.dcim.regions.get(name='EMEA')

# get sites
print(f"\nChecking netbox sites...")
all_sites = nb.dcim.sites.all()


def create_site(site, region):
    slug = site.lower()
    if site not in [x.name for x in all_sites]:
        print(f"\nAdding {site} site to region {region}...")
        site = nb.dcim.sites.create(
            name=site,
            region=region.id,
            slug=slug
            )


# create LD4 site and pull object
create_site('LD4', emea)
ld4 = nb.dcim.sites.get(name='LD4')

# get active device roles
print(f"\nChecking device roles...")
all_roles = nb.dcim.device_roles.all()


def create_device_role(role):
    slug = role.lower()
    if role not in [x.name for x in all_roles]:
        print(f"\nAdding {role} to device roles...")
        role = nb.dcim.device_roles.create(
            name=role,
            slug=slug
            )


# create roles
create_device_role('spine')
create_device_role('leaf')
create_device_role('server')
spine = nb.dcim.device_roles.get(name='spine')
leaf = nb.dcim.device_roles.get(name='leaf')
server = nb.dcim.device_roles.get(name='server')

# get active RIR's
print(f"\nChecking IPAM RIR's...")
all_rirs = nb.ipam.rirs.all()


def create_rir(rir, is_private):
    slug = rir.lower()
    if rir not in [x.name for x in all_rirs]:
        print(f"\nCreating {rir} RIR...")
        rir = nb.ipam.rirs.create(
            name=rir,
            is_private=is_private,
            slug=slug
            )


# create rfc1918 RIR
create_rir('rfc1918', True)
rfc1918 = nb.ipam.rirs.get(name='rfc1918')

# get active ipam roles
print(f"\nChecking IPAM roles...")
ipam_roles = nb.ipam.roles.all()


def create_ipam_role(role_name):
    print(f"\nCreating {role_name} IPAM role...")
    if role_name not in [x.name for x in ipam_roles]:
        role_name = nb.ipam.roles.create(
            name=role_name,
            slug=role_name,
            description=role_name)


# create ipam roles for subnet
create_ipam_role('loopback')
create_ipam_role('oob_mgmt')
create_ipam_role('server_mgmt')
create_ipam_role('interswitch_link')

# get active aggregates
print(f"\nChecking IPAM aggregate data...")
all_aggregates = nb.ipam.aggregates.all()


def create_ip_aggregate(prefix, rir, tenant):
    if str(prefix) not in [x.prefix for x in all_aggregates]:
        print(f"\nCreating IPAM {prefix} aggregate...")
        aggregate = nb.ipam.aggregates.create(
            prefix=str(prefix),
            rir=rfc1918.id,
            tenant=upstart_crow.id)


# define aggregate networks
loopback_agg = netaddr.IPNetwork('150.0.0.0/8')
interswitch_link_agg = netaddr.IPNetwork('155.0.0.0/8')
oob_mgmt_agg = netaddr.IPNetwork('192.168.0.0/16')

# get active vrfs
print(f"\nChecking IPAM VRF's...")
all_vrfs = nb.ipam.vrfs.all()


def create_vrf(name, rd, tenant):
    if name not in [x.name for x in all_vrfs]:
        print(f"\nCreating IPAM {name} VRF...")
        vrf = nb.ipam.vrfs.create(
            name=name,
            rd=rd,
            tenant=tenant.id
            )

        return vrf


# create vrf
create_vrf('mgmt', '1:1', upstart_crow)
mgmt_vrf = nb.ipam.vrfs.get(name='mgmt')

# create ip aggregates
aggregates = [loopback_agg, interswitch_link_agg, oob_mgmt_agg]
for agg in aggregates:
    create_ip_aggregate(agg, rfc1918, upstart_crow)

# get active prefixes
print(f"\nChecking active IPAM prefixes...")
all_prefixes = nb.ipam.prefixes.all()


def create_ip_prefix(prefix, role, site, tenant, pool):
    role = nb.ipam.roles.get(name=role)
    if str(prefix) not in [x.prefix for x in all_prefixes]:
        print(f"\nCreating IPAM {prefix} prefix...")
        prefix = nb.ipam.prefixes.create(
            prefix=str(prefix),
            role=role.id,
            site=ld4.id,
            tenant=upstart_crow.id,
            is_pool=pool
            )

        return prefix


# create loopback prefixes
x = 1
while x < 7:
    loopback = netaddr.IPNetwork(f"150.1.{x}.0/24")
    create_ip_prefix(loopback, 'loopback', ld4, upstart_crow, True)
    x += 1

# create interswitch links
x = 0
while x < 20:
    interswitch_link = netaddr.IPNetwork(f"155.1.11.{x}/31")
    create_ip_prefix(interswitch_link, 'interswitch_link', ld4,
                     upstart_crow, False)
    x += 2

# create oob prefix
oob_mgmt = netaddr.IPNetwork('192.168.137.0/24')
create_ip_prefix(oob_mgmt, 'oob_mgmt', ld4, upstart_crow, False)
oob_mgmt = nb.ipam.prefixes.get(prefix='192.168.137.0/24')

# create server LAN prefixes
server_lan1 = netaddr.IPNetwork('192.168.100.0/24')
server_lan2 = netaddr.IPNetwork('192.168.200.0/24')
create_ip_prefix(server_lan1, 'server_mgmt', ld4, upstart_crow, False)
create_ip_prefix(server_lan2, 'server_mgmt', ld4, upstart_crow, False)

# assign vrf to oob_mgmt
oob_mgmt.vrf = mgmt_vrf.id
oob_mgmt.save()

# get manufacturers/vendors
print(f"\nChecking DCIM manufacturers...")
all_manufacturers = nb.dcim.manufacturers.all()


def create_manufacturer(name):
    slug = name.lower()
    if name not in [x.name for x in all_manufacturers]:
        print(f"\nAdding {name} to DCIM manufacturers...")
        manufacturer = nb.dcim.manufacturers.create(
            name=name,
            slug=slug
            )


# add 'cisco' and 'linux' as new manufacturers
create_manufacturer('cisco')
create_manufacturer('linux')
cisco = nb.dcim.manufacturers.get(name='cisco')
linux = nb.dcim.manufacturers.get(name='linux')

# get platforms
print(f"\nChecking DCIM platforms...")
all_platforms = nb.dcim.platforms.all()


def create_network_platform(name, vendor, napalm_driver):
    slug = name.lower()
    if name not in [x.name for x in all_platforms]:
        print(f"\nCreating {name} DCIM platform...")
        platform = nb.dcim.platforms.create(
            name=name,
            manufacturer=vendor.id,
            napalm_driver=napalm_driver,
            slug=slug
            )

def create_server_platform(name, vendor):
    slug = name.lower()
    if name not in [x.name for x in all_platforms]:
        print(f"\nCreating {name} DCIM platform...")
        platform = nb.dcim.platforms.create(
            name=name,
            manufacturer=vendor.id,
            slug=slug
            )


# add 'ios' and ubuntu as new platforms
create_network_platform('ios', cisco, 'ios')
create_server_platform('ubuntu1804', linux)
ios = nb.dcim.platforms.get(name='ios')
ubuntu1804 = nb.dcim.platforms.get(name='ubuntu1804')

# get device_types
all_device_types = nb.dcim.device_types.all()


def create_device_type(name, vendor):
    slug = name.lower()
    if name not in [x.model for x in all_device_types]:
        print(f"\nCreating {name} DCIM device_type...")
        device_type = nb.dcim.device_types.create(
            model=name,
            manufacturer=vendor.id,
            slug=slug
            )


# add 'iosv' and ubuntu as device_types
create_device_type('iosv', cisco)
create_device_type('ubuntu1804_cloud_init', linux)
iosv = nb.dcim.device_types.get(model="iosv")
ubuntu1804_cloud_init = nb.dcim.device_types.get(model="ubuntu1804_cloud_init")

# create ios, ubuntu interface template
ios_interfaces = ['GigabitEthernet0/{0..3}']
ubuntu_interfaces = ['ens2', 'ens3']

# create an empty set
asserted_ios_interface_list = set()
asserted_ubuntu_interface_list = set()

# build set of ios interfaces
for port in ios_interfaces:
    asserted_ios_interface_list.update(braceexpand(port))

for port in ubuntu_interfaces:
    asserted_ubuntu_interface_list.add(port)

# convert set to dict and set port speed
interface_data = {}

# iterate over ios interfaces
for port in asserted_ios_interface_list:
    data = {}
    intf_type = '1000base-t'
    mgmt_status = False
    # set gig0/0 as oob_mgmt port
    if port == 'GigabitEthernet0/0':
        mgmt_status = True
    data.setdefault(port, dict(device_type=iosv.id, name=port,
                               mgmt_only=mgmt_status, type=intf_type))
    interface_data.update(data)

# iterate over ubuntu interfaces
for port in asserted_ubuntu_interface_list:
    data = {}
    intf_type = '1000base-t'
    mgmt_status = False
    # set gig0/0 as oob_mgmt port
    if port == 'ens3':
        mgmt_status = True
    data.setdefault(port, dict(device_type=ubuntu1804_cloud_init.id, name=port,
                               mgmt_only=mgmt_status, type=intf_type))
    interface_data.update(data)

# add interface template for ios and ubuntu to netbox:
print(f"\nChecking DCIM interface templates...")
for intf, intf_data in interface_data.items():
    try:
        # check if interfaces already exist
        ifGet = nb.dcim.interface_templates.get(
            devicetype_id=intf_data['device_type'],
            name=intf)
        if ifGet:
            continue
        else:
            # create interfaces if they don't exist
            print(f"\nCreating DCIM interface templates...")
            ifSuccess = nb.dcim.interface_templates.create(
                device_type=intf_data['device_type'],
                name=intf,
                type=intf_data['type'],
                mgmt_only=intf_data['mgmt_only'],
                )
    except pynetbox.RequestError as e:
        print(e.error)

# create node list:
nodes = ['spine1', 'spine2', 'leaf1', 'leaf2', 'leaf3', 'server1', 'server2']

# create an empty dict to store all device data
master = {}

# parse topology interface data from external file
print(f"\nReading topology interface data...")
with open('./interfaces.yml', 'r') as f:
    clos = yaml.safe_load(f)

# build out master dict for each node
print(f"\nBuilding python dict of node and interface data...")
x = 201
for node, node_data in clos.items():
    tenant = upstart_crow.id
    site = ld4.id
    status = 'active'
    if node.startswith('server'):
        device_type = ubuntu1804_cloud_init.id
        device_role = server.id
        platform = ubuntu1804.id
    else:
        device_type = iosv.id
        device_role = leaf.id
        platform = ios.id
    # set spine device_role
    if node.startswith('spine'):
        device_role = spine.id
    # set primary_ip4
    primary_ip4 = {'address': f'192.168.137.{x}/32'}
    x += 1
    interfaces = {}
    for intf, intf_data in node_data.items():
        # create empty dict per interface
        data = {}
        # set default parameters
        name = intf
        device = None
        description = intf_data['description']
        type = '1000base-t'
        ip = intf_data['ip']
        mode = None
        enabled = True
        lag = None
        tagged_vlans = None
        untagged_vlan = None
        data.setdefault(intf, dict(description=description,
                                   lag=lag, mode=mode,
                                   tagged_vlans=tagged_vlans,
                                   untagged_vlan=untagged_vlan,
                                   type='virtual', ip=ip,
                                   enabled=enabled))
        interfaces.update(data)
    master.setdefault(node, dict(name=node, device_type=device_type,
                                 device_role=device_role, tenant=tenant,
                                 platform=platform, site=site, status=status,
                                 primary_ip4=primary_ip4,
                                 interfaces=interfaces))

# get all active netbox nodes
print(f"\nChecking DCIM nodes...")
all_nodes = nb.dcim.devices.all()

# push node data to netbox
for node, node_data in master.items():

    # create node if it doesn't exist
    if node not in [x.name for x in all_nodes]:
        print(f"\nCreating {node} in DCIM...")
        node_new = nb.dcim.devices.create(
            name=node,
            site=node_data['site'],
            device_type=node_data['device_type'],
            platform=node_data['platform'],
            tenant=node_data['tenant'],
            device_role=node_data['device_role'])

        for intf, intf_data in node_data['interfaces'].items():
            # create Loopback0 interface and bind to node
            if intf.lower().startswith('loop'):
                print(f"\nCreating Loopback0 and binding to {node}...")
                nbintf = nb.dcim.interfaces.create(
                    name=intf,
                    device=node_new.id,
                    type='virtual',
                    description=intf_data['description'],
                    )

                # add IP data to Loopback0 interface
                x = node[-1]
                intf_ip = nb.ipam.ip_addresses.create(
                    address=intf_data['ip'],
                    status='active',
                    # note, the interface ref will not work in Netbox 2.9.x
                    # interface=nbintf.id,
                    tenant=upstart_crow.id,
                    role='loopback',
                    # specify 3x assigned object values instead of interface
                    assigned_object=node_new.id,
                    assigned_object_id=nbintf.id,
                    assigned_object_type='dcim.interface'
                    )

            # update iosv device template interfaces
            elif intf.lower().startswith(('gigabit', 'ens')):
                print(f"\nUpdating {intf} details...")
                nbintf = nb.dcim.interfaces.get(name=intf, device=node)
                nbintf.description = intf_data['description']
                nbintf.enabled = intf_data['enabled']
                nbintf.save()

                # now add IP data per interface
                print(f"\nBinding {intf_data['ip']} to {intf}...")
                intf_ip = nb.ipam.ip_addresses.create(
                    address=intf_data['ip'],
                    status='active',
                    # note, the interface ref will not work in Netbox 2.9.x
                    # interface=nbintf.id,
                    tenant=upstart_crow.id,
                    assigned_object=node_new.id,
                    assigned_object_id=nbintf.id,
                    assigned_object_type='dcim.interface'
                    )

                # update vrf for GigabitEthernet0/0
                if intf.lower() == 'gigabitethernet0/0':
                    print(f"\nUpdating {intf} with VRF data...")
                    intf_ip.vrf = mgmt_vrf.id
                    intf_ip.save()

                    # now set GigabitEthernet0/0 as the primary mgmt interface
                    print(f"\nSetting Gig0/0 as primary_ip4 interface...")
                    node_new.primary_ip4 = {'address': intf_data['ip']}
                    node_new.save()

                # update server primary_ip
                if intf.lower() == 'ens3':
                    print(f"\nSetting {intf} as primary_ip4 interface...")
                    node_new.primary_ip4 = {'address': intf_data['ip']}
                    node_new.save()


# define patch function
def patch_cables(node_a, node_b, link_a, link_b):
    link_a = nb.dcim.interfaces.get(device=node_a, name=link_a)
    link_b = nb.dcim.interfaces.get(device=node_b, name=link_b)
    # check if link_a/b is connected already
    if link_a.connection_status == None and link_b.connection_status == None:
        new_cable = nb.dcim.cables.create(
            termination_a_type="dcim.interface",
            termination_a_id=link_a.id,
            termination_b_type="dcim.interface",
            termination_b_id=link_b.id
            )


# connect topology
def get_node(node_name):
    """ grab node object from nb, based on name """

    node_object = nb.dcim.devices.get(name=node_name)
    return node_object


spine1 = get_node('spine1')
spine2 = get_node('spine2')
leaf1 = get_node('leaf1')
leaf2 = get_node('leaf2')
leaf3 = get_node('leaf3')
server1 = get_node('server1')
server2 = get_node('server2')

# patch cables
leafs = [leaf1, leaf2, leaf3]
x = 1
while x < 4:
    for leaf in leafs:
        print(f"\nConnecting {leaf} to spines...")
        patch_cables(spine1, leaf, f"GigabitEthernet0/{x}",
                     f"GigabitEthernet0/1")
        patch_cables(spine2, leaf, f"GigabitEthernet0/{x}",
                     f"GigabitEthernet0/2")
        x += 1

# enable gig0/3 for server connectivity
for node in leafs:
    if node in [leaf1, leaf3]:
        print(f"\nEnabled GigabitEthernet0/3 on {node}...")
        gig3 = nb.dcim.interfaces.get(name='GigabitEthernet0/3', device=node)
        gig3.enabled = True
        gig3.save()

print(f"\nJob complete.")
