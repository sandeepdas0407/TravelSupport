targetScope = 'resourceGroup'

@description('Environment name, used to suffix resource names (e.g. dev, prod)')
param environmentName string

@description('Azure region for regional resources')
param location string = resourceGroup().location

@description('Static Web App SKU')
@allowed(['Free', 'Standard'])
param staticWebAppSku string = 'Free'

@description('Allowed CORS origins for the backend API (comma-separated)')
param allowedOrigins string

@secure()
@description('Anthropic API key, used server-side for trip-plan synthesis')
param anthropicApiKey string

@secure()
@description('Google Places API key, used server-side for lodging suggestions')
param googlePlacesApiKey string

var resourcePrefix = 'travelsupport-${environmentName}'

module logAnalytics 'modules/logAnalytics.bicep' = {
  name: 'logAnalytics'
  params: {
    location: location
    name: '${resourcePrefix}-logs'
  }
}

module appInsights 'modules/appInsights.bicep' = {
  name: 'appInsights'
  params: {
    location: location
    name: '${resourcePrefix}-appinsights'
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
  }
}

module azureMaps 'modules/azureMaps.bicep' = {
  name: 'azureMaps'
  params: {
    name: '${resourcePrefix}-maps'
  }
}

module functionApp 'modules/functionApp.bicep' = {
  name: 'functionApp'
  params: {
    location: location
    name: '${resourcePrefix}-func'
    anthropicApiKey: anthropicApiKey
    azureMapsSubscriptionKey: azureMaps.outputs.primaryKey
    googlePlacesApiKey: googlePlacesApiKey
    allowedOrigins: allowedOrigins
    appInsightsConnectionString: appInsights.outputs.connectionString
  }
}

module staticWebApp 'modules/staticWebApp.bicep' = {
  name: 'staticWebApp'
  params: {
    location: location
    name: '${resourcePrefix}-swa'
    sku: staticWebAppSku
    backendResourceId: functionApp.outputs.functionAppId
    backendRegion: location
  }
}

output staticWebAppHostname string = staticWebApp.outputs.defaultHostname
output staticWebAppName string = staticWebApp.outputs.staticWebAppName
output functionAppName string = functionApp.outputs.functionAppName
output functionAppHostname string = functionApp.outputs.defaultHostname
