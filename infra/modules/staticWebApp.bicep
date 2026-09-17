@description('Azure region for the Static Web App')
param location string

@description('Name of the Static Web App')
param name string

@description('SKU tier: Free or Standard')
@allowed(['Free', 'Standard'])
param sku string = 'Free'

@description('Resource ID of the Azure Function App to link as this Static Web App\'s /api/* backend')
param backendResourceId string

@description('Region of the linked Function App (required by the linkedBackends API)')
param backendRegion string

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

// Requests to /api/* on the Static Web App's own domain are proxied to this Function App —
// same-origin from the frontend's perspective, so no CORS configuration is needed. This
// bypasses Azure Static Web Apps' "managed Functions" build/deploy path, which has an open
// platform-side bug as of this writing (see plans/architecture.md for the incident notes and
// tracking issue links).
resource linkedBackend 'Microsoft.Web/staticSites/linkedBackends@2023-12-01' = {
  parent: staticWebApp
  name: 'backend'
  properties: {
    backendResourceId: backendResourceId
    region: backendRegion
  }
}

output defaultHostname string = staticWebApp.properties.defaultHostname
output staticWebAppName string = staticWebApp.name
