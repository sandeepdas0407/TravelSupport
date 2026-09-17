@description('Azure region for the Function App and its storage account')
param location string

@description('Base name for the Function App (also used, sanitized, for its storage account and plan)')
param name string

@secure()
param anthropicApiKey string

@secure()
param azureMapsSubscriptionKey string

@secure()
param googlePlacesApiKey string

param claudeModel string = 'claude-sonnet-4-5'
param allowedOrigins string
param appInsightsConnectionString string

var storageAccountName = take(replace('${name}stg', '-', ''), 24)

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  #disable-next-line BCP334
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Y1 (Consumption): eastus2/eastus both have 0 quota for Y1/B1 VMs on this subscription, and F1
// (Free) is quota-available but Azure explicitly rejects Function Apps on Free/Shared plans
// (FreeOrSharedFunctionsAppServicePlanNotSupported). Trying Y1 in westus2, a region already
// proven to have *some* App Service quota on this subscription (an existing F1 plan runs there).
resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${name}-plan'
  location: location
  kind: 'functionapp'
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true
  }
}

@description('Storage account connection string used by the Functions runtime itself (AzureWebJobsStorage) — an operational credential, not application data')
#disable-next-line outputs-should-not-contain-secrets
var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: name
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'AzureWebJobsStorage', value: storageConnectionString }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
        { name: 'ANTHROPIC_API_KEY', value: anthropicApiKey }
        { name: 'CLAUDE_MODEL', value: claudeModel }
        { name: 'AZURE_MAPS_SUBSCRIPTION_KEY', value: azureMapsSubscriptionKey }
        { name: 'GOOGLE_PLACES_API_KEY', value: googlePlacesApiKey }
        { name: 'ALLOWED_ORIGINS', value: allowedOrigins }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
      ]
    }
  }
}

output functionAppName string = functionApp.name
output functionAppId string = functionApp.id
output defaultHostname string = functionApp.properties.defaultHostName
