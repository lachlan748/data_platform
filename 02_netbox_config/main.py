import netaddr, pynetbox, re, sys, yaml
from braceexpand import braceexpand
from pprint import pprint

# set netbox-docker api address and token
nb = pynetbox.api(
    'http://192.168.137.100:8000',
    token='0123456789abcdef0123456789abcdef01234567'
)

# get tenancy, create new if necessary
print(f"\nChecking netbox tenants...")
upstart_crow = nb.tenancy.tenants.get(name='upstart_crow')
if not upstart_crow:
    upstart_crow = nb.tenancy.tenants.create(
        name = 'upstart_crow',
        slug = 'upstart_crow')


# get regions
print(f"\nChecking netbox region...")
all_regions = nb.dcim.regions.all()
def create_region(region):
    slug = region.lower()
    if region not in [x.name for x in all_regions]:
        region = nb.dcim.regions.create(
            name = region,
            slug = slug
            )

# get emea region
print(f"\nAdding EMEA region...")
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
print(f"\nChecking device roles...")
roles = nb.dcim.device_roles.all()

# create roles
spine = nb.dcim.device_roles.get(name='spine')
leaf = nb.dcim.device_roles.get(name='leaf')
if 'spine' not in [x.name for x in roles]:
    print(f"\nCreating 'spine' device role...")
    spine = nb.dcim.device_roles.create(
        name = 'spine',
        slug = 'spine')
if 'leaf' not in [x.name for x in roles]:
    print(f"\nCreating 'leaf' device role...")
    leaf = nb.dcim.device_roles.create(
        name = 'leaf',
        slug = 'leaf')

# get active RIR's
print(f"\nChecking IPAM RIR's...")
all_rirs = nb.ipam.rirs.all()

# create rfc1918 RIR
if 'rfc1918' not in [x.name for x in all_rirs]:
    print(f"\nCreating RFC1918 RIR...")
    rfc1918 = nb.ipam.rirs.create(
        name = 'rfc1918',
        is_private = True,
        slug = 'rfc1918')

# get active ipam roles
print(f"\nChecking IPAM roles...")
ipam_roles = nb.ipam.roles.all()

# define function for ipam role creation
def create_ipam_role(role_name):
    print(f"\nCreating '{role_name}' IPAM role...")
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
print(f"\nChecking IPAM aggregate data...")
all_aggregates = nb.ipam.aggregates.all()

def create_ip_aggregate(prefix):
    if str(prefix) not in [x.prefix for x in all_aggregates]:
        print(f"\nCreating IPAM {prefix} aggregate...")
        role = nb.ipam.aggregates.create(
            prefix = str(prefix),
            site = ld4.id,
            rir = rfc1918.id,
            tenant = upstart_crow.id)

# get active prefixes
print(f"\nChecking active IPAM prefixes...")
all_prefixes = nb.ipam.prefixes.all()

# define function for prefix creation
def create_ip_prefix(prefix, role, pool):
    print(f"\nCreating IPAM {prefix} prefix...")
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

# create loopback prefixes
x = 1
while x < 7:
    loopback = netaddr.IPNetwork(f"150.{x}.{x}.0/24")
    create_ip_prefix(loopback, 'loopback', True)
    x += 1

# create interswitch links
x = 0
while x < 20:
    interswitch_link = netaddr.IPNetwork(f"155.1.11.{x}/31")
    create_ip_prefix(interswitch_link, 'interswitch_link', False)
    x += 2

# create oob prefix
oob_mgmt = netaddr.IPNetwork('192.168.137.0/24')
create_ip_prefix(oob_mgmt, 'oob_mgmt', False)

# add 'cisco' as a new manufacturer
print(f"\nChecking DCIM vendor list...")
cisco = nb.dcim.manufacturers.get(name='cisco')
if not cisco:
    cisco = nb.dcim.manufacturers.create(
        name = 'cisco',
        slug = 'cisco')

# add 'ios' as a new platform
print(f"\nChecking DCIM platform list...")
ios = nb.dcim.platforms.get(name='ios')
if not ios:
    ios = nb.dcim.platforms.create(
        name = 'ios',
        slug = 'ios')

# add the iosv device type
print(f"\nChecking DCIM device types...")
iosv = nb.dcim.device_types.get(model='iosv')
if not iosv:
    print(f"\nCreating IOSv device type...")
    iosv = nb.dcim.device_types.create(
        model = 'iosv',
        manufacturer = ios.id,
        slug = 'iosv')

# create ios interface template
ios_interfaces = ['GigabitEthernet0/{0..5}']

# create an empty set
asserted_ios_interface_list = set()

# build set of ios interfaces
for port in ios_interfaces:
    asserted_ios_interface_list.update(braceexpand(port))

# convert set to dict and set port speed
interface_data = {}
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

# add interface template for ios to netbox:
print(f"\nChecking DCIM interface templates...")
for intf, intf_data in interface_data.items():
    try:
        # check if interfaces already exist
        ifGet = nb.dcim.interface_templates.get(devicetype_id=intf_data['device_type'], 
                                                name=intf)
        if ifGet:
            continue
        else:
            # create interfaces if they don't exist
            print(f"\nCreating DCIM interface templates...")
            ifSuccess = nb.dcim.interface_templates.create(
                device_type = intf_data['device_type'],
                name = intf,
                type = intf_data['type'],
                mgmt_only = intf_data['mgmt_only'],
                )
    except pynetbox.RequestError as e:
        print(e.error)    

# create node list:
#nodes = ['spine1', 'spine2', 'leaf1', 'leaf2', 'leaf3', 'leaf4', 'leaf5']

# create an empty dict to store all device data
master = {}

# parse topology interface data from external file
print(f"\nReading topology interface data...")
with open('./interfaces.yml', 'r') as f:
    clos = yaml.safe_load(f)

# build out master dict for each node
print(f"\nBuilding python dict of node and interface data...")
for node, node_data in clos.items():
    device_type = iosv.id
    device_role = leaf.id
    # set spine device_role
    if node.startswith('spine'):
        device_role = spine.id
    tenant = upstart_crow.id
    platform = ios.id
    site = ld4.id
    status = 'active'
    # set primary_ip4
    x = node[-1]
    primary_ip4 = {'address': f'150.1.{x}.{x}/32'}
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
            name = node,
            site = node_data['site'],
            device_type = node_data['device_type'],
            platform = node_data['platform'],
            tenant = node_data['tenant'],
            device_role = node_data['device_role'])

        for intf, intf_data in node_data['interfaces'].items():
            # create Loopback0 interface and bind to node
            if intf.lower().startswith('loop'):
                print(f"Creating Loopback0 and binding to {node}...")
                nbintf = nb.dcim.interfaces.create(
                    name = intf,
                    device = node_new.id,
                    type = 'virtual',
                    description = intf_data['description'],
                    )

                # add IP data to Loopback0 interface
                x = node[-1]
                intf_ip = nb.ipam.ip_addresses.create(
                    address = intf_data['ip'],
                    status = 'active',
                    interface =  nbintf.id,
                    tenant = upstart_crow.id,
                    role = 'loopback'
                    )

                # now set Loopback0
                print(f"Setting Loopback0 as primary_ip4 interface...")
                node_new.primary_ip4 = {'address': intf_data['ip']}
                node_new.save()
