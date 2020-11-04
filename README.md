# data_platform

The goal of this project is to simulate a production network using code.

## Objectives

*  Deploy immutable virtual network infrastucture on Cisco Modeling Labs 2.1
   via API calls.

*  Store the network IPAM data in Netbox

*  Generate and deploy configuration files using Ansible Roles + Netbox

*  Connect immutable virtual servers to the network and simulate production
   network traffic including unicast and multicast data flows.

*  Monitor traffic flow and telemetry data, visualize using Kibana/Grafana

## Method

### Infrastructure

*  1x Intel NUC Kit, part# NUC8I7BEH, 32GB RAM, 128GB M.2 NVMe 1.3 SSD, running
   ESXI 6.7.0 Update 3 and Cisco Modeling Labs 2.1 (Personal License).

*  1x Intel NUC Kit, part# DN2820FYKH, 8GB RAM, 240GB SSD, running Ansible,
   Netbox and ELK.

## Diagram

This topology diagram will be updated as the build evolves.

![data_platform_diagram](lib/images/data_platform.png)

## Prerequistes

## Setting up your environment

WORK IN PROGRESS
