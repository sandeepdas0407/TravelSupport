targetScope = 'resourceGroup'

@description('Environment name, used to suffix resource names (e.g. dev, prod)')
param environmentName string

@description('Azure region for regional resources')
param location string = resourceGroup().location

@description('Azure region for the Function App + its plan. Separate from `location` because App Service compute quota is region-specific and can differ per subscription.')
param functionAppLocation string = location

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

@secure()
@description('Google Maps API key (Geocoding API + Routes API), used server-side for routing/geocoding')
param googleMapsApiKey string

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

module functionApp 'modules/functionApp.bicep' = {
  name: 'functionApp'
  params: {
    location: functionAppLocation
    name: '${resourcePrefix}-func'
    anthropicApiKey: anthropicApiKey
    googleMapsApiKey: googleMapsApiKey
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
    backendRegion: functionAppLocation
  }
}

output staticWebAppHostname string = staticWebApp.outputs.defaultHostname
output staticWebAppName string = staticWebApp.outputs.staticWebAppName
output functionAppName string = functionApp.outputs.functionAppName
output functionAppHostname string = functionApp.outputs.defaultHostname
