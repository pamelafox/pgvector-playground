metadata description = 'Creates an Azure App Service in an existing Azure App Service plan.'
param name string
param location string = resourceGroup().location
param tags object = {}

@secure()
param administratorLogin string
@secure()
param administratorLoginPassword string

@description('The Object ID of the Azure AD admin.')
param aadAdminObjectid string

@description('Azure AD admin name.')
param aadAdminName string

@description('Azure AD admin Type')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param aadAdminType string = 'User'

param databaseNames array = []
param allowAzureIPsFirewall bool = false
param allowAllIPsFirewall bool = false
param allowedSingleIPs array = []

resource srv 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
    name: name
    location: location
    sku: {
      name: 'Standard_D2ds_v4'
      tier: 'GeneralPurpose'
    }
    properties: {
      administratorLogin: administratorLogin
      administratorLoginPassword: administratorLoginPassword
      authConfig: {
        activeDirectoryAuth: 'Enabled'
        passwordAuth: 'Disabled'
        tenantId: subscription().tenantId
      }
      version: '15'
      storage: { storageSizeGB: 128 }
  }  

    resource addAddUser 'administrators' = {
        name: aadAdminObjectid
        properties: {
            tenantId: subscription().tenantId
            principalType: aadAdminType
            principalName: aadAdminName
        }
    }

  resource configurations 'configurations@2022-12-01' = {
    name: 'azure.extensions'
    properties: {
      value: 'vector'
      source: 'user-override'
    } 
  }


  resource database 'databases' = [for name in databaseNames: {
    name: name
  }]


  resource firewall_all 'firewallRules' = if (allowAllIPsFirewall) {
    name: 'allow-all-IPs'
    properties: {
      startIpAddress: '0.0.0.0'
      endIpAddress: '255.255.255.255'
    }
  }

  resource firewall_azure 'firewallRules' = if (allowAzureIPsFirewall) {
    name: 'allow-all-azure-internal-IPs'
    properties: {
      startIpAddress: '0.0.0.0'
      endIpAddress: '0.0.0.0'
    }
  }

  resource firewall_single 'firewallRules' = [for ip in allowedSingleIPs: {
    name: 'allow-single-${replace(ip, '.', '')}'
    properties: {
      startIpAddress: ip
      endIpAddress: ip
    }
  }]
}