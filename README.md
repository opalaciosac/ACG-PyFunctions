<!--
---
name: Azure Functions Python HTTP Trigger using Azure Developer CLI
description: This repository contains an Azure Functions HTTP trigger quickstart written in Python and deployed to Azure Functions Flex Consumption using the Azure Developer CLI (azd). The sample uses managed identity and a virtual network to make sure deployment is secure by default. You can opt out of a VNet being used in the sample by setting VNET_ENABLED to false in the parameters.
page_type: sample
languages:
- azdeveloper
- python
- bicep
products:
- azure
- azure-functions
- entra-id
urlFragment: functions-quickstart-python-azd
---
-->

# Azure Functions Python HTTP Trigger using Azure Developer CLI

This template repository contains an HTTP trigger reference sample for Azure Functions written in Python and deployed to Azure using the Azure Developer CLI (`azd`). The sample uses managed identity and a virtual network to make sure deployment is secure by default.

This source code supports the article [Quickstart: Create and deploy functions to Azure Functions using the Azure Developer CLI](https://learn.microsoft.com/azure/azure-functions/create-first-function-azure-developer-cli?pivots=programming-language-python).

## Prerequisites

+ [Python 3.11](https://www.python.org/)
+ [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (for local storage emulation)
+ [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local?pivots=programming-language-python#install-the-azure-functions-core-tools)
+ [Azure Developer CLI (AZD)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
+ To use Visual Studio Code to run and debug locally:
  + [Visual Studio Code](https://code.visualstudio.com/)
  + [Azure Functions extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)

## Initialize the local project

You can initialize a project from this `azd` template in one of these ways:

+ Use this `azd init` command from an empty local (root) folder:

    ```shell
    azd init --template functions-quickstart-python-http-azd
    ```

    Supply an environment name, such as `flexquickstart` when prompted. In `azd`, the environment is used to maintain a unique deployment context for your app.

+ Clone the GitHub template repository locally using the `git clone` command:

    ```shell
    git clone https://github.com/Azure-Samples/functions-quickstart-python-http-azd.git
    cd functions-quickstart-python-http-azd
    ```

    You can also clone the repository from your own fork in GitHub.

## Local settings

The `local.settings.json` file is included in this template with default values for local development. This file is excluded from deployment by `.funcignore`.


## Create a virtual environment

The way that you create your virtual environment depends on your operating system.
Open the terminal, navigate to the project folder, and run these commands:

### Linux/macOS/bash

```bash
python -m venv .venv
source .venv/bin/activate
```

#### Windows (Cmd)

```shell
py -m venv .venv
.venv\scripts\activate
```

## Run your app from the terminal

1. Start Azurite for local storage emulation. In a separate terminal, run:

    ```shell
    azurite
    ```

1. In your project terminal, start the Functions host:

    ```shell
    pip3 install -r requirements.txt
    func start
    ```

1. From your HTTP test tool in a new terminal, call the `fill-template` endpoint through the path-based router:

    ```shell
        curl -i http://localhost:7071/api/fill-template \
            -H "Content-Type: application/json" \
            -d "{\"data\":{\"Client1FullName\":\"Awesome Developer\",\"Client1Executor\":\"Taylor Example\"},\"scrub\":true,\"outputName\":\"filled.vsdx\"}"
    ```

1. When you're done, press Ctrl+C in the terminal window to stop the `func.exe` host process.

1. Run `deactivate` to shut down the virtual environment.

## Run your app using Visual Studio Code

1. Open the root folder in a new terminal.
1. Run the `code .` code command to open the project in Visual Studio Code.
1. Press **Run/Debug (F5)** to run in the debugger. Select **Debug anyway** if prompted about local emulator not running.
1. Send a POST request to the `fill-template` endpoint (`/api/fill-template`) using your HTTP test tool. If you have the [RestClient](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension installed, you can execute the request directly from the [`test.http`](test.http) project file.

## Source Code

The HTTP entrypoint is in [`function_app.py`](./function_app.py). It uses a single catch-all Azure Functions route (`{*path}`) and dispatches requests with a route table keyed by `(method, path)`.

Current route registration:

- `POST /fill-template` → executes the Visio template filler logic from [`pyscripts/fill_template.py`](./pyscripts/fill_template.py)

To add more routes (for example `/generate-diagram`), register another handler in the `ROUTES` dictionary with minimal changes.

## Deploy to Azure

Run this command to provision the function app, with any required Azure resources, and deploy your code:

```shell
azd up
```

By default, this sample deploys with a virtual network (VNet) for enhanced security, ensuring that the function app and related resources are isolated within a private network. 
The `VNET_ENABLED` parameter controls whether a VNet is used during deployment:
- When `VNET_ENABLED` is `true` (default), the function app is deployed with a VNet for secure communication and resource isolation.
- When `VNET_ENABLED` is `false`, the function app is deployed without a VNet, allowing public access to resources.

This parameter replaces the previous `SKIP_VNET` parameter. If you were using `SKIP_VNET` in earlier versions, set `VNET_ENABLED` to `false` to achieve the same behavior.

To disable the VNet for this sample, set `VNET_ENABLED` to `false` before running `azd up`:
```bash
azd env set VNET_ENABLED false
azd up
```

You're prompted to supply these required deployment parameters:

| Parameter | Description |
| ---- | ---- |
| _Environment name_ | An environment that's used to maintain a unique deployment context for your app. You aren't prompted when you created the local project using `azd init`.|
| _Azure subscription_ | Subscription in which your resources are created.|
| _Azure location_ | Azure region in which to create the resource group that contains the new Azure resources. Only regions that currently support the Flex Consumption plan are shown.|

To learn how to obtain your new function endpoints in Azure along with the required function keys, see [Invoke the function on Azure](https://learn.microsoft.com/azure/azure-functions/create-first-function-azure-developer-cli?pivots=programming-language-java#invoke-the-function-on-azure) in the companion article [Quickstart: Create and deploy functions to Azure Functions using the Azure Developer CLI](https://learn.microsoft.com/azure/azure-functions/create-first-function-azure-developer-cli?pivots=programming-language-java#invoke-the-function-on-azure).

## Redeploy your code

You can run the `azd up` command as many times as you need to both provision your Azure resources and deploy code updates to your function app.

>[!NOTE]
>Deployed code files are always overwritten by the latest deployment package.

## Clean up resources

When you're done working with your function app and related resources, you can use this command to delete the function app and its related resources from Azure and avoid incurring any further costs:

```shell
azd down
```
