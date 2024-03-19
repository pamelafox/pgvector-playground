targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

param resourceGroupName string = ''

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
param databaseName string = 'db'

var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

var tags = { 'azd-env-name': environmentName }
var prefix = '${environmentName}-${resourceToken}'

resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : 'rg-${environmentName}'
  location: location
}

module pg 'pg.bicep' = {
  name: 'pg'
  scope: resourceGroup
  params: {
    name: '${prefix}-postgresql'
    location: location
    tags: tags
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorLoginPassword
    aadAdminObjectid: aadAdminObjectid
    aadAdminName: aadAdminName
    aadAdminType: aadAdminType
    databaseNames: [ databaseName ]
    allowAllIPsFirewall: true
  }
}

output POSTGRES_USERNAME string = aadAdminName
output POSTGRES_DATABASE string = databaseName
output POSTGRES_HOST string = pg.outputs.POSTGRES_DOMAIN_NAME
output POSTGRES_SSL string = 'require'
