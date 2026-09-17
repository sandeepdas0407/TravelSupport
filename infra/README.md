# Infra bootstrap

The Bicep in this folder provisions Azure Maps, Application Insights (+ Log Analytics), and the
Static Web App. It's applied by `.github/workflows/infra-apply.yml` (manual `workflow_dispatch`,
gated by a GitHub Environment) and previewed by `.github/workflows/infra-plan.yml` (automatic
`what-if` on PRs touching `infra/**`).

Both workflows authenticate to Azure via OIDC (`azure/login@v2`), so there's no long-lived Azure
credential stored as a GitHub secret. Setting up that trust relationship is a one-time manual step
— it can't be done by Bicep itself, since the identity doing the deploying has to exist before
anything can be deployed.

## One-time setup

1. **Create a resource group** (if it doesn't exist):
   ```
   az group create --name rg-travelsupport --location eastus2
   ```

2. **Create an Azure AD app registration + service principal** for GitHub Actions:
   ```
   az ad app create --display-name "travelsupport-github-actions"
   # note the appId (client ID) from the output
   az ad sp create --id <appId>
   ```

3. **Grant it Contributor on the resource group** (least-privilege: scope to the RG, not the subscription):
   ```
   az role assignment create \
     --assignee <appId> \
     --role Contributor \
     --scope /subscriptions/<subscription-id>/resourceGroups/rg-travelsupport
   ```

4. **Add a federated credential** trusting GitHub Actions OIDC tokens from this repo. Repeat for
   each workflow/environment that needs to authenticate (PR-triggered `infra-plan.yml` uses
   `pull_request`, manually-dispatched `infra-apply.yml` uses `environment`):
   ```
   az ad app federated-credential create --id <appId> --parameters '{
     "name": "travelsupport-pr",
     "issuer": "https://token.actions.githubusercontent.com",
     "subject": "repo:<org>/<repo>:pull_request",
     "audiences": ["api://AzureADTokenExchange"]
   }'

   az ad app federated-credential create --id <appId> --parameters '{
     "name": "travelsupport-infra-apply-dev",
     "issuer": "https://token.actions.githubusercontent.com",
     "subject": "repo:<org>/<repo>:environment:dev",
     "audiences": ["api://AzureADTokenExchange"]
   }'
   ```
   (Add a matching `environment:prod` credential once a `prod` GitHub Environment exists.)

5. **Add repo secrets** (Settings → Secrets and variables → Actions):
   - `AZURE_CLIENT_ID` — the `appId` from step 2
   - `AZURE_TENANT_ID` — `az account show --query tenantId -o tsv`
   - `AZURE_SUBSCRIPTION_ID` — `az account show --query id -o tsv`
   - `AZURE_RESOURCE_GROUP` — `rg-travelsupport`
   - `ANTHROPIC_API_KEY`, `GOOGLE_PLACES_API_KEY` — passed as secure Bicep parameter overrides during apply (see `infra-apply.yml`)

6. **Configure GitHub Environments** (Settings → Environments) named `dev` and `prod`, each with
   required reviewers, so `infra-apply.yml` (`environment: ${{ inputs.environment }}`) pauses for
   human approval before applying — this is the manual gate that deliberately keeps infra apply
   out of the agentic loop.

7. **First apply**: run `infra-apply.yml` manually (Actions tab → Infra apply → Run workflow,
   choose `dev`). After it succeeds, fetch the Static Web App's deployment token and add it as the
   `AZURE_STATIC_WEB_APPS_API_TOKEN` secret so `deploy-and-verify.yml` can deploy to it:
   ```
   az staticwebapp secrets list --name travelsupport-dev-swa --query "properties.apiKey" -o tsv
   ```
