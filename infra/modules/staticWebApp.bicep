@description('Azure region for the Static Web App')
param location string

@description('Name of the Static Web App')
param name string

@description('SKU tier: Free or Standard')
@allowed(['Free', 'Standard'])
param sku string = 'Free'

@secure()
param anthropicApiKey string

@secure()
param azureMapsSubscriptionKey string

@secure()
param googlePlacesApiKey string

param claudeModel string = 'claude-sonnet-4-5'
param allowedOrigins string
param appInsightsConnectionString string

resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: name
  location: location
  sku: {
    name: sku
    tier: sku
  }
  properties: {
    provider: 'GitHub'
  }
}

resource appSettings 'Microsoft.Web/staticSites/config@2023-12-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    ANTHROPIC_API_KEY: anthropicApiKey
    CLAUDE_MODEL: claudeModel
    AZURE_MAPS_SUBSCRIPTION_KEY: azureMapsSubscriptionKey
    GOOGLE_PLACES_API_KEY: googlePlacesApiKey
    ALLOWED_ORIGINS: allowedOrigins
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsightsConnectionString
  }
}

output defaultHostname string = staticWebApp.properties.defaultHostname
output staticWebAppName string = staticWebApp.name
