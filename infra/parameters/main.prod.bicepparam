using '../main.bicep'

param environmentName = 'prod'
param location = 'eastus2'
param staticWebAppSku = 'Standard'
param allowedOrigins = 'https://travelsupport.azurestaticapps.net'

// Supplied at deploy time via --parameters anthropicApiKey=... (or KEYVAULT_/CI secret injection);
// never commit real values here.
param anthropicApiKey = ''
param googlePlacesApiKey = ''
