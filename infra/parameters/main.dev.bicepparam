using '../main.bicep'

param environmentName = 'dev'
param location = 'eastus2'
// App Service compute quota (Y1/B1 VMs) is 0 for this subscription in eastus2 — trying eastus
// for the Function App specifically. See plans/architecture.md's 2026-09-17 addendum.
param functionAppLocation = 'eastus'
param staticWebAppSku = 'Free'
param allowedOrigins = 'http://localhost:5173'

// Supplied at deploy time via --parameters anthropicApiKey=... (or KEYVAULT_/CI secret injection);
// never commit real values here.
param anthropicApiKey = ''
param googlePlacesApiKey = ''
