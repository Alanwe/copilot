This project will make works as Foundry for creating reusable components for azure cloud services using python
The project foundtry should use github copilots to create components based on issues.

Each components should follow the same template guidelines which implement best practices for producing components includiding documentations, examples and tests
Each component will then be placed in a gallery including the scripts to deploy to the azure services.
The components should deploy best azure best practice. Eg Authentication, Key Management(vaults)

Azure services that should be deployable. 
 - Azure ML Components and pipelines (YAML/AzureML SDKV2 only)
 - Azure ML Batch Inference
 - Azure ML Endpoints
 - Azure Functions
 - Azure Managed Endpoints Serverless

A manifest should exist in the / directory of all components and and a cross reference to which azure services are required for deployment.

Gitgub actions should check the manifest and deploy need new or edited components, (after testing) to a specified azure subscription (using tags) and update the manifest.
If Gitgub action cannot update the manifest directory a script will be needed to be developed that can discover the deployed services  (using tags).

