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

else:
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
        unmanaged_switch = lab.create_node("unmanaged_switch", "unmanaged_switch", 550, 500, populate_interfaces=True)
        ext_conn = lab.create_node("ext_conn", "external_connector", 300, 500, populate_interfaces=True)

        # create additional interfaces for spines
        print(f"\nCreating additional interfaces to spines..")
        spines = [spine1, spine2]
        iosv_intf_list = ['GigabitEthernet0/4', 'GigabitEthernet0/5']
        for node in spines:
            for intf in iosv_intf_list:
                print(f"\nAdding {intf} to {node}")
                intf = node.create_interface()

        # place all nodes in a list
        nodes = [spine1, spine2, leaf1, leaf2, leaf3, leaf4, leaf5]

        # connect clos fabric - spine1   <-- MORE WORK HERE, convert to function and YAML
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


        # create OOB conns for spine and leaf
        print(f"\nConnecting router to OOB unmanaged switch..")
        port_num = 0
        for node in nodes:
            lab.create_link(node.get_interface_by_label('GigabitEthernet0/0'),
                            unmanaged_switch.get_interface_by_label(f"port{port_num}"))
            port_num = port_num + 1

        # connect unmanaged_switch to ext-conn
        print(f"\nConnecting unmanaged switch to external connector..")
        lab.create_link(unmanaged_switch.get_interface_by_label('port7'),
                        ext_conn.get_interface_by_label('port'))

        # set ext-conn as bridge mode
        print(f"\nSetting external connector to bridge mode..")
        ext_conn.config = 'bridge0'

        # set sample bootstrap config for spine + leaf
        print(f"\nBootstrapping router configs..")
        for node in nodes:
            path = '../04_build_configs/files/complete/'
            with open(f"{path}/{node.label}.cfg") as fh:
                config_file = fh.read()
            node.config = config_file

        # start nodes incrementally
        print(f"\nStarting node: ext_conn")
        ext_conn.start()
        print(f"\nStarting node: unmanaged_switch")
        unmanaged_switch.start()
        for node in nodes:
            print(f"\nStarting node: {node}")
            node.start()
            # 15sec delay before starting each veos node
            time.sleep(15)

    except Exception as e:
        print(f"\nError creating lab, {e}")
