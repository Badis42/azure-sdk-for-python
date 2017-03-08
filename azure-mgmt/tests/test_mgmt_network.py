﻿# coding: utf-8

#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
import unittest

import azure.mgmt.network
from testutils.common_recordingtestcase import record
from tests.mgmt_testcase import HttpStatusCode, AzureMgmtTestCase

class MgmtNetworkTest(AzureMgmtTestCase):

    def setUp(self):
        super(MgmtNetworkTest, self).setUp()
        self.network_client = self.create_mgmt_client(
            azure.mgmt.network.Client
        )
        if not self.is_playback():
            self.create_resource_group()

    @record
    def test_network_interface_card(self):
        virtual_networks = self.network_client.virtual_networks()
        subnets = self.network_client.subnets()
        network_interfaces = self.network_client.network_interfaces()

        vnet_name = self.get_resource_name('pyvnet')
        subnet_name = self.get_resource_name('pysubnet')
        nic_name = self.get_resource_name('pynic')

        # Create VNet
        async_vnet_creation = virtual_networks.create_or_update(
            self.group_name,
            vnet_name,
            {
                'location': self.region,
                'address_space': {
                    'address_prefixes': ['10.0.0.0/16']
                }
            }
        )
        async_vnet_creation.wait()

        # Create Subnet
        async_subnet_creation = subnets.create_or_update(
            self.group_name,
            vnet_name,
            subnet_name,
            {'address_prefix': '10.0.0.0/24'}
        )
        subnet_info = async_subnet_creation.result()

        # Create NIC
        async_nic_creation = network_interfaces.create_or_update(
            self.group_name,
            nic_name,
            {
                'location': self.region,
                'ip_configurations': [{
                    'name': 'MyIpConfig',
                    'subnet': {
                        'id': subnet_info.id
                    }
                }]
            }
        )
        nic_info = async_nic_creation.result()

        nic_info = network_interfaces.get(
            self.group_name,
            nic_info.name
        )
         
        nics = list(network_interfaces.list(
            self.group_name
        ))
        self.assertEqual(len(nics), 1)

        nics = list(network_interfaces.list_all())
        self.assertGreater(len(nics), 0)

        async_delete = network_interfaces.delete(
            self.group_name,
            nic_info.name
        )
        async_delete.wait()

    @record
    def test_load_balancers(self):
        virtual_networks = self.network_client.virtual_networks()
        subnets = self.network_client.subnets()
        network_interfaces = self.network_client.network_interfaces()
        public_ip_addresses = self.network_client.public_ip_addresses()
        load_balancers = self.network_client.load_balancers()

        public_ip_name = self.get_resource_name('pyipname')
        frontend_ip_name = self.get_resource_name('pyfipname')
        addr_pool_name = self.get_resource_name('pyapname')
        probe_name = self.get_resource_name('pyprobename')
        lb_name = self.get_resource_name('pylbname')

        front_end_id = ('/subscriptions/{}'
            '/resourceGroups/{}'
            '/providers/Microsoft.Network'
            '/loadBalancers/{}'
            '/frontendIPConfigurations/{}').format(
                self.settings.SUBSCRIPTION_ID,
                self.group_name,
                lb_name,
                frontend_ip_name
            )
        back_end_id = ('/subscriptions/{}'
            '/resourceGroups/{}'
            '/providers/Microsoft.Network'
            '/loadBalancers/{}'
            '/backendAddressPools/{}').format(
                self.settings.SUBSCRIPTION_ID,
                self.group_name,
                lb_name,
                addr_pool_name
            )

        probe_id = ('/subscriptions/{}'
            '/resourceGroups/{}'
            '/providers/Microsoft.Network'
            '/loadBalancers/{}'
            '/probes/{}').format(
                self.settings.SUBSCRIPTION_ID,
                self.group_name,
                lb_name,
                probe_name
            )

        # Create PublicIP
        public_ip_parameters = {
            'location': self.region,
            'public_ip_allocation_method': 'static',
            'idle_timeout_in_minutes': 4
        }
        async_publicip_creation = public_ip_addresses.create_or_update(
            self.group_name,
            public_ip_name,
            public_ip_parameters
        )
        public_ip_info = async_publicip_creation.result()

        # Building a FrontEndIpPool
        frontend_ip_configurations = [{
            'name': frontend_ip_name,
            'private_ip_allocation_method': 'Dynamic',
            'public_ip_address': {
                'id': public_ip_info.id
            }
        }]

        # Building a BackEnd adress pool
        backend_address_pools = [{
            'name': addr_pool_name
        }]

        # Building a HealthProbe
        probes = [{
            'name': probe_name,
            'protocol': 'Http',
            'port': 80,
            'interval_in_seconds': 15,
            'number_of_probes': 4,
            'request_path': 'healthprobe.aspx'
        }]

        # Building a LoadBalancer rule
        load_balancing_rules = [{
            'name': 'azure-sample-lb-rule',
            'protocol': 'tcp',
            'frontend_port': 80,
            'backend_port': 80,
            'idle_timeout_in_minutes': 4,
            'enable_floating_ip': False,
            'load_distribution': 'Default',
            'frontend_ip_configuration': {
                'id': front_end_id
            },
            'backend_address_pool': {
                'id': back_end_id
            },
            'probe': {
                'id': probe_id
            }
        }]

        # Building InboundNATRule1
        inbound_nat_rules = [{
            'name': 'azure-sample-netrule1',
            'protocol': 'tcp',
            'frontend_port': 21,
            'backend_port': 22,
            'enable_floating_ip': False,
            'idle_timeout_in_minutes': 4,
            'frontend_ip_configuration': {
                'id': front_end_id
            }
        }]

        # Building InboundNATRule2
        inbound_nat_rules.append({
            'name': 'azure-sample-netrule2',
            'protocol': 'tcp',
            'frontend_port': 23,
            'backend_port': 22,
            'enable_floating_ip': False,
            'idle_timeout_in_minutes': 4,
            'frontend_ip_configuration': {
                'id': front_end_id
            }
        })

        # Creating Load Balancer
        lb_async_creation = load_balancers.create_or_update(
            self.group_name,
            lb_name,
            {
                'location': self.region,
                'frontend_ip_configurations': frontend_ip_configurations,
                'backend_address_pools': backend_address_pools,
                'probes': probes,
                'load_balancing_rules': load_balancing_rules,
                'inbound_nat_rules' :inbound_nat_rules
            }
        )
        lb_info = lb_async_creation.result()

        # Get it
        lb_info = load_balancers.get(
            self.group_name,
            lb_name
        )

        # List all
        lbs = load_balancers.list_all()
        lbs = list(lbs)
        self.assertGreater(len(lbs), 0)

        # List RG
        lbs = load_balancers.list(self.group_name)
        lbs = list(lbs)
        self.assertGreater(len(lbs), 0)

        # Delete
        async_lb_delete = load_balancers.delete(
            self.group_name,
            lb_name
        )
        async_lb_delete.wait()

    @record
    def test_public_ip_addresses(self):
        virtual_networks = self.network_client.virtual_networks()
        subnets = self.network_client.subnets()
        network_interfaces = self.network_client.network_interfaces()
        public_ip_addresses = self.network_client.public_ip_addresses()
        models = azure.mgmt.network.models('2016-09-01')

        public_ip_name = self.get_resource_name('pyipname')

        params_create = models.PublicIPAddress(
            location=self.region,
            public_ip_allocation_method=models.IPAllocationMethod.dynamic,
            tags={
                'key': 'value',
            },
        )
        result_create = public_ip_addresses.create_or_update(
            self.group_name,
            public_ip_name,
            params_create,
        )
        result_create.wait() # AzureOperationPoller
        #self.assertEqual(result_create.status_code, HttpStatusCode.OK)

        result_get = public_ip_addresses.get(
            self.group_name,
            public_ip_name,
        )
        #self.assertEqual(result_get.status_code, HttpStatusCode.OK)
        self.assertEqual(result_get.location, self.region)
        self.assertEqual(result_get.tags['key'], 'value')

        result_list = public_ip_addresses.list(self.group_name)
        #self.assertEqual(result_list.status_code, HttpStatusCode.OK)
        result_list = list(result_list)
        self.assertEqual(len(result_list), 1)

        result_list_all = public_ip_addresses.list_all()
        #self.assertEqual(result_list_all.status_code, HttpStatusCode.OK)
        result_list_all = list(result_list_all)
        self.assertGreater(len(result_list_all), 0)

        result_delete = public_ip_addresses.delete(
            self.group_name,
            public_ip_name,
        )
        result_delete.wait() # AzureOperationPoller
        #self.assertEqual(result_delete.status_code, HttpStatusCode.OK)

        result_list = public_ip_addresses.list(self.group_name)
        #self.assertEqual(result_list.status_code, HttpStatusCode.OK)
        result_list = list(result_list)
        self.assertEqual(len(result_list), 0)

    @record
    def test_virtual_networks(self):
        virtual_networks = self.network_client.virtual_networks()
        subnets = self.network_client.subnets()
        network_interfaces = self.network_client.network_interfaces()
        public_ip_addresses = self.network_client.public_ip_addresses()
        models = azure.mgmt.network.models('2016-09-01')

        network_name = self.get_resource_name('pyvnet')
        subnet1_name = self.get_resource_name('pyvnetsubnetone')
        subnet2_name = self.get_resource_name('pyvnetsubnettwo')

        params_create = models.VirtualNetwork(
            location=self.region,
            address_space=models.AddressSpace(
                address_prefixes=[
                    '10.0.0.0/16',
                ],
            ),
            dhcp_options=models.DhcpOptions(
                dns_servers=[
                    '10.1.1.1',
                    '10.1.2.4',
                ],
            ),
            subnets=[
                models.Subnet(
                    name=subnet1_name,
                    address_prefix='10.0.1.0/24',
                ),
                models.Subnet(
                    name=subnet2_name,
                    address_prefix='10.0.2.0/24',
                ),
            ],
        )

        result_create = virtual_networks.create_or_update(
            self.group_name,
            network_name,
            params_create,
        )
        vnet = result_create.result()

        vnet = virtual_networks.get(
            self.group_name,
            vnet.name,
        )

        ip_availability = virtual_networks.check_ip_address_availability(
            self.group_name,
            vnet.name,
            '10.0.1.35' # Should be available since new VNet sor Subnet 1
        )
        self.assertTrue(ip_availability.available)

        result_list = list(virtual_networks.list(
            self.group_name,
        ))
        self.assertEqual(len(result_list), 1)

        result_list_all = list(virtual_networks.list_all())

        async_delete = virtual_networks.delete(
            self.group_name,
            network_name,
        )
        async_delete.wait()

    @record
    def test_dns_availability(self):
        result_check = check_dns_name_availability(
            self.region,
            'pydomain',
        )
        #self.assertEqual(result_check.status_code, HttpStatusCode.OK)
        self.assertTrue(result_check)

    @record
    def test_subnets(self):
        virtual_networks = self.network_client.virtual_networks()
        subnets = self.network_client.subnets()
        network_interfaces = self.network_client.network_interfaces()
        public_ip_addresses = self.network_client.public_ip_addresses()
        models = azure.mgmt.network.models('2016-09-01')

        network_name = self.get_resource_name('pysubnet')
        subnet1_name = self.get_resource_name('pysubnetone')
        subnet2_name = self.get_resource_name('pysubnettwo')

        params_create = models.VirtualNetwork(
            location=self.region,
            address_space=models.AddressSpace(
                address_prefixes=[
                    '10.0.0.0/16',
                ],
            ),
            dhcp_options=models.DhcpOptions(
                dns_servers=[
                    '10.1.1.1',
                    '10.1.2.4',
                ],
            ),
            subnets=[
                models.Subnet(
                    name=subnet1_name,
                    address_prefix='10.0.1.0/24',
                ),
            ],
        )
        result_create = virtual_networks.create_or_update(
            self.group_name,
            network_name,
            params_create,
        )
        result_create.wait() # AzureOperationPoller

        params_create = models.Subnet(
            name=subnet2_name,
            address_prefix='10.0.2.0/24',
        )
        result_create = subnets.create_or_update(
            self.group_name,
            network_name,
            subnet2_name,
            params_create,
        )
        result_create.wait() # AzureOperationPoller

        result_get = virtual_networks.get(
            self.group_name,
            network_name,
        )
        self.assertEqual(len(result_get.subnets), 2)

        result_get = subnets.get(
            self.group_name,
            network_name,
            subnet2_name,
        )

        result_list = list(subnets.list(
            self.group_name,
            network_name,
        ))

        result_delete = subnets.delete(
            self.group_name,
            network_name,
            subnet2_name,
        )
        result_delete.wait()

    @record
    def test_network_security_groups(self):
        network_security_groups = self.network_client.network_security_groups()
        security_rules = self.network_client.security_rules()
        models = azure.mgmt.network.models('2016-09-01')

        security_group_name = self.get_resource_name('pysecgroup')
        security_rule_name = self.get_resource_name('pysecgrouprule')

        params_create = models.NetworkSecurityGroup(
            location=self.region,
            security_rules=[
                models.SecurityRule(
                    name=security_rule_name,
                    access=models.SecurityRuleAccess.allow,
                    description='Test security rule',
                    destination_address_prefix='*',
                    destination_port_range='123-3500',
                    direction=models.SecurityRuleDirection.inbound,
                    priority=500,
                    protocol=models.SecurityRuleProtocol.tcp,
                    source_address_prefix='*',
                    source_port_range='655',
                ),
            ],
        )
        result_create = network_security_groups.create_or_update(
            self.group_name,
            security_group_name,
            params_create,
        )
        result_create.wait() # AzureOperationPoller

        result_get = network_security_groups.get(
            self.group_name,
            security_group_name,
        )

        result_list = list(network_security_groups.list(
            self.group_name,
        ))
        self.assertEqual(len(result_list), 1)

        result_list_all = list(network_security_groups.list_all())

        # Security Rules
        new_security_rule_name = self.get_resource_name('pynewrule')
        async_security_rule = security_rules.create_or_update(
            self.group_name,
            security_group_name,
            new_security_rule_name,
            {
                    'access':models.SecurityRuleAccess.allow,
                    'description':'New Test security rule',
                    'destination_address_prefix':'*',
                    'destination_port_range':'123-3500',
                    'direction':models.SecurityRuleDirection.outbound,
                    'priority':400,
                    'protocol':models.SecurityRuleProtocol.tcp,
                    'source_address_prefix':'*',
                    'source_port_range':'655',
            }
        )
        security_rule = async_security_rule.result()

        security_rule = security_rules.get(
            self.group_name,
            security_group_name,
            security_rule.name
        )
        self.assertEqual(security_rule.name, new_security_rule_name)

        new_security_rules = list(security_rules.list(
            self.group_name,
            security_group_name
        ))
        self.assertEqual(len(new_security_rules), 2)

        result_delete = security_rules.delete(
            self.group_name,
            security_group_name,
            new_security_rule_name
        )
        result_delete.wait()

        # Delete NSG
        result_delete = network_security_groups.delete(
            self.group_name,
            security_group_name,
        )
        result_delete.wait()

    @record
    def test_routes(self):
        route_tables = self.network_client.route_tables()
        routes = self.network_client.routes()

        route_table_name = self.get_resource_name('pyroutetable')
        route_name = self.get_resource_name('pyroute')

        async_route_table = route_tables.create_or_update(
            self.group_name,
            route_table_name,
            {'location': self.region}
        )
        route_table = async_route_table.result()

        route_table = route_tables.get(
            self.group_name,
            route_table.name
        )
        self.assertEqual(route_table.name, route_table_name)

        rg_route_tables = list(route_tables.list(
            self.group_name
        ))
        self.assertEqual(len(rg_route_tables), 1)

        all_route_tables = list(route_tables.list_all())
        self.assertGreater(len(all_route_tables), 0)

        async_route = routes.create_or_update(
            self.group_name,
            route_table.name,
            route_name,
            {
                'address_prefix': '10.1.0.0/16',
                'next_hop_type': 'None'
            }
        )
        route = async_route.result()

        route = routes.get(
            self.group_name,
            route_table.name,
            route.name
        )
        self.assertEqual(route.name, route_name)

        all_routes = list(routes.list(
            self.group_name,
            route_table.name
        ))
        self.assertEqual(len(all_routes), 1)

        async_route_delete = routes.delete(
            self.group_name,
            route_table.name,
            route.name
        )
        async_route_delete.wait()

        async_route_table_delete = route_tables.delete(
            self.group_name,
            route_table_name
        )
        async_route_table_delete.wait()

    @record
    def test_usages(self):
        usages = list(self.network_client.usages().list(self.region))
        self.assertGreater(len(usages), 1)
        self.assertTrue(all(hasattr(u, 'name') for u in usages))

    @record
    def test_express_route_service_providers(self):
        ersp = list(self.network_client.express_route_service_providers().list())
        self.assertGreater(len(ersp), 0)
        self.assertTrue(all(hasattr(u, 'bandwidths_offered') for u in ersp))

    @record
    def test_express_route_circuit(self):
        express_route_circuit_peerings = self.network_client.express_route_circuit_peerings()
        express_route_circuit_authorizations = self.network_client.express_route_circuit_authorizations()
        express_route_circuits = self.network_client.express_route_circuits()

        express_route_name = self.get_resource_name('pyexpressroute')
        async_express_route = express_route_circuits.create_or_update(
            self.group_name,
            express_route_name,
            {
                "location": self.region,
                "sku": {
                    "name": "Standard_MeteredData",
                    "tier": "Standard",
                    "family": "MeteredData"
                },
                "service_provider_properties": {
                    "service_provider_name": "Comcast",
                    "peering_location": "Chicago",
                    "bandwidth_in_mbps": 100
                }
            }
        )
        express_route = async_express_route.result()

        express_route = express_route_circuits.get(
            self.group_name,
            express_route_name
        )

        routes = list(express_route_circuits.list(
            self.group_name
        ))
        self.assertEqual(len(routes), 1)

        routes = list(express_route_circuits.list_all())
        self.assertGreater(len(routes), 0)

        stats = express_route_circuits.get_stats(
            self.group_name,
            express_route_name
        )
        self.assertIsNotNone(stats)

        async_peering = express_route_circuit_peerings.create_or_update(
            self.group_name,
            express_route_name,
            'AzurePublicPeering',
            {
                "peering_type": "AzurePublicPeering",
                "peer_asn": 100, 
                "primary_peer_address_prefix": "192.168.1.0/30",
                "secondary_peer_address_prefix": "192.168.2.0/30",
                "vlan_id": 200,
            }
        )
        peering = async_peering.result()

        peering = express_route_circuit_peerings.get(
            self.group_name,
            express_route_name,
            'AzurePublicPeering'
        )

        peerings = list(express_route_circuit_peerings.list(
            self.group_name,
            express_route_name
        ))
        self.assertEqual(len(peerings), 1)

        stats = express_route_circuits.get_peering_stats(
            self.group_name,
            express_route_name,
            'AzurePublicPeering'
        )
        self.assertIsNotNone(stats)

        auth_name = self.get_resource_name('pyauth')
        async_auth = express_route_circuit_authorizations.create_or_update(
            self.group_name,
            express_route_name,
            auth_name,
            {}
        )
        auth = async_auth.result()

        auth = express_route_circuit_authorizations.get(
            self.group_name,
            express_route_name,
            auth_name
        )

        auths = list(express_route_circuit_authorizations.list(
            self.group_name,
            express_route_name
        ))
        self.assertEqual(len(auths), 1)

        async_auth = express_route_circuit_authorizations.delete(
            self.group_name,
            express_route_name,
            auth_name
        )
        async_auth.wait()

        async_peering = express_route_circuit_peerings.delete(
            self.group_name,
            express_route_name,
            'AzurePublicPeering'
        )
        async_peering.wait()

        async_express_route = express_route_circuits.delete(
            self.group_name,
            express_route_name
        )
        async_express_route.wait()

    @record
    def test_virtual_network_gateway_operations(self):
        virtual_networks = self.network_client.virtual_networks()
        subnets = self.network_client.subnets()
        virtual_network_gateways = self.network_client.virtual_network_gateways()
        public_ip_addresses = self.network_client.public_ip_addresses()
        models = azure.mgmt.network.models('2016-09-01')

        # https://docs.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-howto-site-to-site-resource-manager-portal

        vnet_name = self.get_resource_name('pyvirtnet')
        fe_name = self.get_resource_name('pysubnetfe')
        be_name = self.get_resource_name('pysubnetbe')
        gateway_name = self.get_resource_name('pysubnetga')

        # Create VNet
        async_vnet_creation = virtual_networks.create_or_update(
            self.group_name,
            vnet_name,
            {
                'location': self.region,
                'address_space': {
                    'address_prefixes': [
                        '10.11.0.0/16',
                        '10.12.0.0/16'
                    ]
                }
            }
        )
        async_vnet_creation.wait()

        # Create Front End Subnet
        async_subnet_creation = subnets.create_or_update(
            self.group_name,
            vnet_name,
            fe_name,
            {'address_prefix': '10.11.0.0/24'}
        )
        fe_subnet_info = async_subnet_creation.result()

        # Create Back End Subnet
        async_subnet_creation = subnets.create_or_update(
            self.group_name,
            vnet_name,
            be_name,
            {'address_prefix': '10.12.0.0/24'}
        )
        be_subnet_info = async_subnet_creation.result()

        # Create Gateway Subnet
        async_subnet_creation = subnets.create_or_update(
            self.group_name,
            vnet_name,
            'GatewaySubnet',
            {'address_prefix': '10.12.255.0/27'}
        )
        gateway_subnet_info = async_subnet_creation.result()

        # Public IP Address
        public_ip_name = self.get_resource_name('pyipname')
        params_create = models.PublicIPAddress(
            location=self.region,
            public_ip_allocation_method=models.IPAllocationMethod.dynamic,
            tags={
                'key': 'value',
            },
        )
        result_create = public_ip_addresses.create_or_update(
            self.group_name,
            public_ip_name,
            params_create,
        )
        public_ip_address = result_create.result()

        # Gateway itself
        vng_name = self.get_resource_name('pyvng')
        gw_params = {
            'location': self.region,
            'gateway_type': 'VPN',
            'vpn_type': 'RouteBased',
            'enable_bgp': False,
            'sku': {
                'tier': 'Standard',
                'capacity': 2,
                'name': 'Standard'},
            'ip_configurations':[{
                'name': 'default',
                'private_ip_allocation_method': 'Dynamic',
                'subnet': {
                    'id': gateway_subnet_info.id
                },
                'public_ip_address': {
                    'id': public_ip_address.id
                }
            }],
        }
        async_create = virtual_network_gateways.create_or_update(
            self.group_name,
            vng_name,
            gw_params
        )
        vng = async_create.result()
        self.assertEquals(vng.name, vng_name)


#------------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
