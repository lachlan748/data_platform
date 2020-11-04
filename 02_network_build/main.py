import getpass
import time
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
    print(f"Unable to contact CML2.x server, please check server connectivity.")

# get list of labs
all_labs = client.all_labs()

# check if data_platform exists
if 'data_platform' not in [lab.title for lab in all_labs]:
    print(f"\ndata_platform doesn't exist, creating lab")

    # create new data_platform lab
    try:
        lab = client.create_lab(title='data_platform')

        # create nodes
        print(f"Creating nodes")
        spine1 = lab.create_node("spine1", "iosv", 100, 100, populate_interfaces=True)
        spine2 = lab.create_node("spine2", "iosv", 300, 100, populate_interfaces=True)
        leaf1 = lab.create_node("leaf1", "iosv", 0, 300, populate_interfaces=True)
        leaf2 = lab.create_node("leaf2", "iosv", 200, 300, populate_interfaces=True)
        leaf3 = lab.create_node("leaf3", "iosv", 400, 300, populate_interfaces=True)
        unmanaged_switch = lab.create_node("unmanaged_switch", "unmanaged_switch", 300, 500, populate_interfaces=True)
        ext_conn = lab.create_node("ext_conn", "external_connector", 600, 500, populate_interfaces=True)

        # place all nodes in a list
        nodes = [spine1, spine2, leaf1, leaf2, leaf3]

        # define veos interfaces list
        #veos_intf_summary = ['Ethernet{1..4}', 'Management1']
        #veos_intf_list = set()
        #for intf in veos_intf_summary:
        #    veos_intf_list.update(braceexpand(intf))

        # create interfaces for veos nodes
        #for node in nodes:
        #    for intf in veos_intf_list:
        #        print(f"Adding {intf} to {node}")
        #        intf = node.create_interface()

        # connect clos fabric - spine1
        lab.create_link(spine1.get_interface_by_label('GigabitEthernet0/1'),
                        leaf1.get_interface_by_label('GigabitEthernet0/1'))
        lab.create_link(spine1.get_interface_by_label('GigabitEthernet0/2'),
                        leaf2.get_interface_by_label('GigabitEthernet0/1'))
        lab.create_link(spine1.get_interface_by_label('GigabitEthernet0/3'),
                        leaf3.get_interface_by_label('GigabitEthernet0/1'))

        # connect clos fabric - spine2
        lab.create_link(spine2.get_interface_by_label('GigabitEthernet0/1'),
                        leaf1.get_interface_by_label('GigabitEthernet0/2'))
        lab.create_link(spine2.get_interface_by_label('GigabitEthernet0/2'),
                        leaf2.get_interface_by_label('GigabitEthernet0/2'))
        lab.create_link(spine2.get_interface_by_label('GigabitEthernet0/3'),
                        leaf3.get_interface_by_label('GigabitEthernet0/2'))

        # create OOB conns for spine and leaf
        port_num = 0
        for node in nodes:
            lab.create_link(node.get_interface_by_label('GigabitEthernet0/0'),
                            unmanaged_switch.get_interface_by_label(f"port{port_num}"))
            port_num = port_num + 1

        # connect unmanaged_switch to ext-conn
        lab.create_link(unmanaged_switch.get_interface_by_label('port7'),
                        ext_conn.get_interface_by_label('port'))

        # set ext-conn as bridge mode
        ext_conn.config = 'bridge0'

        # set sample bootstrap config for spine + leaf
        for node in nodes:
            node.config = 'ntp server 1.2.3.4'

        # start nodes incrementally
        print(f"\nStarting node: ext_conn")
        ext_conn.start()
        print(f"\nStarting node: unmanaged_switch")
        unmanaged_switch.start()
        for node in nodes:
            print(f"\nStarting node: {node}")
            node.start()
            # 30 sec delay before starting each veos node
            time.sleep(15)

    except Exception as e:
        print(f"Error creating lab, {e}")

else:
    print(f"\ndata_platform lab already exists.")
