using '../main.bicep'

param environmentName = 'dev'
param location = 'eastus2'
param staticWebAppSku = 'Free'
param allowedOrigins = 'http://localhost:5173'

// Supplied at deploy time via --parameters anthropicApiKey=... (or KEYVAULT_/CI secret injection);
// never commit real values here.
param anthropicApiKey = ''
param googlePlacesApiKey = ''
