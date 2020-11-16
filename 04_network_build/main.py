import getpass
import time
import telnetlib
import re
import sys
import urllib3
from braceexpand import braceexpand
from virl2_client import ClientLibrary
from pprint import pprint

# Get login credentials
username = input("Enter CML username: ")
password = getpass.getpass(prompt = "Enter CML password: ")

# login to cml
try:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    client = ClientLibrary("https://192.168.137.252", username, password, ssl_verify=False)
    client.is_system_ready()
except:
    print(f"\nUnable to contact CML2.x server, please check server connectivity.")

# get list of labs
all_labs = client.all_labs()

# check if data_platform exists
if 'data_platform' in [lab.title for lab in all_labs]:
    print(f"\ndata_platform exists, deleting lab..")
    lab = client.find_labs_by_title(title='data_platform')[0]
    try:
        lab.stop()
        lab.wipe()
        lab.remove()
    except Exception as e:
        print(f"Unable to stop data_platform lab, error: {e}")
    print(f"\ndata_platform has been successfully deleted..")

print(f"\ndata_platform doesn't exist, creating lab..")

# create new data_platform lab
try:
    lab = client.create_lab(title='data_platform')

    # create nodes
    print(f"\nCreating nodes..")
    spine1 = lab.create_node("spine1", "iosv", 300, 100, populate_interfaces=True)
    spine2 = lab.create_node("spine2", "iosv", 500, 100, populate_interfaces=True)
    leaf1 = lab.create_node("leaf1", "iosv", 0, 300, populate_interfaces=True)
    leaf2 = lab.create_node("leaf2", "iosv", 200, 300, populate_interfaces=True)
    leaf3 = lab.create_node("leaf3", "iosv", 400, 300, populate_interfaces=True)
    leaf4 = lab.create_node("leaf4", "iosv", 600, 300, populate_interfaces=True)
    leaf5 = lab.create_node("leaf5", "iosv", 800, 300, populate_interfaces=True)
    switch1 = lab.create_node("switch1",
        "unmanaged_switch", 550, 500, populate_interfaces=True)
    switch2 = lab.create_node("switch2",
        "unmanaged_switch", 400, 500, populate_interfaces=True)
    ext_conn = lab.create_node("ext_conn", "external_connector", 250, 500, populate_interfaces=True)
    server1 = lab.create_node("server1", "server", 0, 100, populate_interfaces=True)
    server2 = lab.create_node("server2", "server", 800, 100, populate_interfaces=True)

    # create additional interfaces for spines
    print(f"\nCreating additional interfaces to spines..")
    spines = [spine1, spine2]
    iosv_intf_list = ['GigabitEthernet0/4', 'GigabitEthernet0/5']
    for node in spines:
        for intf in iosv_intf_list:
            print(f"\nAdding {intf} to {node}")
            intf = node.create_interface()

    # create additional interfaces for servers
    print(f"\nCreating additional interfaces for servers..")
    servers = [server1, server2]
    for server in servers:
        print(f"\nAdding eth1 to {node}")
        intf = server.create_interface()

    # place all nodes in a list
    nodes = [spine1, spine2, leaf1, leaf2, leaf3, leaf4, leaf5]

    # connect clos fabric - spine1
    print(f"\nConnecting topology..")
    lab.create_link(spine1.get_interface_by_label('GigabitEthernet0/1'),
                    leaf1.get_interface_by_label('GigabitEthernet0/1'))
    lab.create_link(spine1.get_interface_by_label('GigabitEthernet0/2'),
                    leaf2.get_interface_by_label('GigabitEthernet0/1'))
    lab.create_link(spine1.get_interface_by_label('GigabitEthernet0/3'),
                    leaf3.get_interface_by_label('GigabitEthernet0/1'))
    lab.create_link(spine1.get_interface_by_label('GigabitEthernet0/4'),
                    leaf4.get_interface_by_label('GigabitEthernet0/1'))
    lab.create_link(spine1.get_interface_by_label('GigabitEthernet0/5'),
                    leaf5.get_interface_by_label('GigabitEthernet0/1'))

    # connect clos fabric - spine2
    lab.create_link(spine2.get_interface_by_label('GigabitEthernet0/1'),
                    leaf1.get_interface_by_label('GigabitEthernet0/2'))
    lab.create_link(spine2.get_interface_by_label('GigabitEthernet0/2'),
                    leaf2.get_interface_by_label('GigabitEthernet0/2'))
    lab.create_link(spine2.get_interface_by_label('GigabitEthernet0/3'),
                    leaf3.get_interface_by_label('GigabitEthernet0/2'))
    lab.create_link(spine2.get_interface_by_label('GigabitEthernet0/4'),
                    leaf4.get_interface_by_label('GigabitEthernet0/2'))
    lab.create_link(spine2.get_interface_by_label('GigabitEthernet0/5'),
                    leaf5.get_interface_by_label('GigabitEthernet0/2'))

    # connect clos fabric -  servers
    lab.create_link(server1.get_interface_by_label('eth0'),
                    leaf1.get_interface_by_label('GigabitEthernet0/3'))
    lab.create_link(server2.get_interface_by_label('eth0'),
                    leaf5.get_interface_by_label('GigabitEthernet0/3'))

    # connect OOB conns for servers
    lab.create_link(server1.get_interface_by_label('eth1'),
                     switch2.get_interface_by_label('port2'))
    lab.create_link(server2.get_interface_by_label('eth1'),
                     switch2.get_interface_by_label('port3'))


    # create OOB conns for spine and leaf
    print(f"\nConnecting router to OOB unmanaged switch..")
    port_num = 0
    for node in nodes:
        lab.create_link(node.get_interface_by_label('GigabitEthernet0/0'),
                        switch1.get_interface_by_label(f"port{port_num}"))
        port_num = port_num + 1

    # connect switch1 to switch2
    print(f"\nConnecting unmanaged switches..")
    lab.create_link(switch1.get_interface_by_label('port7'),
        switch2.get_interface_by_label('port7'))

    # connect unmanaged_switch to ext-conn
    print(f"\nConnecting unmanaged switch to external connector..")
    lab.create_link(switch2.get_interface_by_label('port1'),
                    ext_conn.get_interface_by_label('port'))

    # set ext-conn as bridge mode
    print(f"\nSetting external connector to bridge mode..")
    ext_conn.config = 'bridge0'

    # set bootstrap config for spine + leaf
    print(f"\nBootstrapping router configs..")
    for node in nodes:
        path = '../03_build_configs/files/complete/'
        with open(f"{path}/{node.label}.cfg") as fh:
            config_file = fh.read()
        node.config = config_file

    # set server1 bootstrap config
    print(f"\nBootstrapping server configs..")
    servers = [server1, server2]
    x = 208
    y = 100
    for server in servers:
        server_config = (
            f"hostname {server.label}\n"
            f"ifconfig eth0 192.168.{y}.{x} netmask 255.255.255.0 up\n"
            f"ifconfig eth1 192.168.137.{x} netmask 255.255.255.0 up\n"
            f"route add -net 0.0.0.0/0 dev eth1\n"
            f"route add -net 150.1.0.0/16 dev eth0\n")
        x += 1
        y += 100
        server.config = server_config

    # start nodes incrementally
    print(f"\nStarting node: ext_conn")
    ext_conn.start()
    print(f"\nStarting node: switch1")
    switch1.start()
    print(f"\nStarting node: switch2")
    switch2.start()
    for node in nodes:
        print(f"\nStarting node: {node}")
        node.start()
        # 20sec delay before starting each veos node
        time.sleep(20)
    print(f"\nStarting node: server1")
    server1.start()
    time.sleep(20)
    print(f"\nStarting node: server2")
    server2.start()
    time.sleep(20)

except Exception as e:
    print(f"\nError creating lab, {e}")

# wait 3 mins for topology to start
time.sleep(180)

# generate ssh rsa keys using telnet
for node in nodes:
    # get mgmt IP address via api
    match = re.search(r'(192.168.137.\d+)', node.config, re.DOTALL)
    if match:
        mgmt_ip = match.group(1)
    user = 'cisco'
    password = 'cisco'
    try:
        print(f"\nGenerating SSH public keys on {node.label}...")
        tn = telnetlib.Telnet(mgmt_ip)
        tn.set_debuglevel(1)
        tn.read_until(b"Username: ")
        tn.write(user.encode('ascii') + b"\n")
        if password:
            tn.read_until(b"Password: ")
            tn.write(password.encode('ascii') + b"\n")
        tn.write(b"conf t\n")
        tn.write(b"crypto key generate rsa\n")
        tn.read_until(b"How many bits in the modulus [512]:")
        tn.write(b"2048\n")
        time.sleep(5)
        tn.write(b"\n")
        tn.write(b"end\n")
        tn.write(b"exit\n")
        print(tn.read_all())
        time.sleep(15)

    except Exception as e:
        print(f"\nUnable to create SSH key for {node.label}...")

print(f"\nJob complete.")
