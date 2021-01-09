# data_platform

The goal of this project is to simulate a production network using code.

## Objectives

*  Deploy immutable network infrastucture on Cisco Modeling Labs 2.1
   using the python virl2_client library. 

*  Deploy, configure and store the network DCIM + IPAM data in Netbox

*  Generate and deploy network configuration files using Ansible Roles + Netbox

*  Connect immutable servers to either side of the topology and ensure
   reachability across the network.

### Infrastructure

*  1x Intel NUC Kit, part# NUC8I7BEH, 32GB RAM, 128GB M.2 NVMe 1.3 SSD, running
   ESXI 6.7.0 Update 3 and Cisco Modeling Labs 2.1 (Personal License).

*  1x Intel NUC Kit, part# DN2820FYKH, 8GB RAM, 240GB SSD, running Centos 7
   with Ansible, netbox-docker and ELK.

## Diagram

This topology diagram will be updated as the build evolves.

![data_platform_diagram](lib/images/data_platform.png)

## Prerequistes

This build assumes:

1. Cisco CML 2.x VM host address is 192.168.137.252

2. Node data_controller (as per the diagram) is running Centos 7 and has 
   python3 installed. 

   Note: I spent several hours trying to run netbox-docker on Centos 8 but
   postgres was inaccesible to the netbox container on TCP 5432.

3. Your python/ansible source machine's public SSH key has been copied to
   your data controller.

4. Ensure your data_controller hostname is 'localhost', otherwise netbox
   docker may fail to start.

## Setting up your environment

1. On your python/ansible controller, clone this repository

2. Create a new virtualenv ```python3 -m venv venv```

3. Start the virtualenv ```source venv/bin/activate```

4. Install the necessary python packages ```pip install -r requirements.txt```

## Method

### 1. Data Controller

1. Setup your controller node by installing Centos 7. This node host netbox.

2. Once the OS is installed, copy your desktop SSH private key onto the
   controller:
   ```ssh-copy-id {{ username }}@{{ controller_ip }}```

3. Within this repo, move to the 01_deploy_controller directory:
   ```cd 01_deploy_controller```

4. Execute the ansible playbook to update the controller with the required
   software:
   ```ansible-playbook playbook.yml -i hosts.yml -u <username> -K```

   Enter the sudo password when prompted.

5. Once complete, the data controller is ready to go. Netbox should be running
   after a few minutes. 

   To check the status of netbox, login to the controller and type:
   ```docker ps```

   To check logs for the netbox containers, type:
   ```docker logs <container_id>```

### 2. Netbox

1. Move to 02_network_build directory
   ```cd 02_network_build```

2. Push the inventory and IPAM data into Netbox, execute:
   ```python3 main.py```

Netbox should now be accessible on http://192.168.137.100:8000

### 3. Generate network node config files

1. Move to the 03_build_configs directory
   ```cd 03_build_configs```

2. Get Ansible to generate the network config files based on data in Netbox,
   execute:
   ```ansible-playbook playbook.yml -i hosts.yml```

Config files will be stored in files/complete/ directory.

### 4. Create the topology and bootstrap network nodes

1. Move to 04_network_build
   ```cd 04_network_build```

2. Create the virtual network topology into CML, execute:
   ```python3 main.py```

The network topology should now be accessible via CML.
