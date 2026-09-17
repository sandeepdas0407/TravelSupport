@description('Azure region for the Azure Maps account (most Azure Maps pricing is global, but a region is still required)')
param location string = 'global'

@description('Name of the Azure Maps account')
param name string

resource mapsAccount 'Microsoft.Maps/accounts@2023-06-01' = {
  name: name
  location: location
  sku: {
    name: 'G2'
  }
  properties: {
    disableLocalAuth: false
  }
}

// MVP tradeoff: this key flows into the Static Web App's app settings via main.bicep, not into
// Key Vault. Acceptable for now (see plans/architecture.md's deferred-hardening note); revisit
// with Key Vault references + managed identity before this handles real production traffic.
@description('Primary subscription key for the Azure Maps account (used by the backend for geocoding/routing)')
#disable-next-line outputs-should-not-contain-secrets
output primaryKey string = mapsAccount.listKeys().primaryKey
