---
name: PostgreSQL + pgvector
description: Deploy a PostgreSQL Flexible Server to Azure with the pgvector extension enabled.
languages:
- bicep
- azdeveloper
- python
products:
- azure-database-postgresql
- azure
page_type: sample
urlFragment: azure-postgres-pgvector-python
---

# PostgreSQL + pgvector on Azure

This repository makes it easy to deploy a PostgreSQL Flexible Server to Azure with the [pgvector](https://pgvector.dev) extension installed. The pgvector extension provides a vector similarity search engine for PostgreSQL, allowing you to perform similarity searches on your data using vector embeddings.

The repository contains infrastructure-as-code (Bicep) to deploy an Azure PostgreSQL Flexible Server with  pgvector extension enabled, password authentication disabled, and Entra (Active Directory) authentication enabled. The repository also contains example Python scripts to demonstrate how to use pgvector.

Table of contents:

* [Opening this project](#opening-this-project)
  * [GitHub Codespaces](#github-codespaces)
  * [VS Code Dev Containers](#vs-code-dev-containers)
  * [Local environment](#local-environment)
* [Deploying to Azure](#deploying-to-azure)
* [Example scripts](#example-scripts)

## Opening this project

You have a few options for setting up this project.
The easiest way to get started is GitHub Codespaces, since it will setup all the tools for you,
but you can also [set it up locally](#local-environment) if desired.

### GitHub Codespaces

You can run this repo virtually by using GitHub Codespaces, which will open a web-based VS Code in your browser:

[![Open in GitHub Codespaces](https://img.shields.io/static/v1?style=for-the-badge&label=GitHub+Codespaces&message=Open&color=brightgreen&logo=github)](https://codespaces.new/Azure-Samples/azure-postgres-pgvector-python)

Once the codespace opens (this may take several minutes), open a terminal window.

### VS Code Dev Containers

A related option is VS Code Dev Containers, which will open the project in your local VS Code using the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

1. Start Docker Desktop (install it if not already installed)
1. Open the project:
    [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/azure-samples/azure-postgres-pgvector-python)
1. In the VS Code window that opens, once the project files show up (this may take several minutes), open a terminal window.

### Local environment

1. Install the required tools:

    * [Azure Developer CLI](https://aka.ms/azure-dev/install)
    * [Python 3.9, 3.10, or 3.11](https://www.python.org/downloads/) (Only necessary if you want to run the Python scripts)

2. Create a new folder and switch to it in the terminal.
3. Run this command to download the project code:

    ```shell
    azd init -t azure-postgres-pgvector-python
    ```

    Note that this command will initialize a git repository, so you do not need to clone this repository.

4. Create a Python virtual environment and install the required packages:

    ```shell
    python -m pip install -r requirements.txt
    ```

5. Open a terminal window inside the project folder.

## Deploying to Azure

Follow these steps to deploy a PostgreSQL Flexible Server to Azure with the pgvector extension enabled:

1. Login to your Azure account:

    ```shell
    azd auth login
    ```

1. Create a new azd environment:

    ```shell
    azd env new
    ```

    Enter a name that will be used for the resource group.
    This will create a new folder in the `.azure` folder, and set it as the active environment for any calls to `azd` going forward.

1. Run this command to provision all the resources:

    ```shell
    azd provision
    ```

    This will create a new resource group, and create the PostgreSQL Flexible server inside that group.

1. Once the deployment is complete, run this command to copy the `azd` environment variables into your local `.env`:

    ```shell
    azd env get-values > .env
    ```

1. Now you may run the Python scripts in order to interact with the PostgreSQL server.

    ```shell
    python examples/sqlalchemy_async.py
    ```

    Note that each of the script starts off with a `CREATE EXTENSION pgvector;` command, which will install the pgvector extension into the database. Once you run that once, you do not need to run it again.

## Example scripts

The `examples` folder contains example Python scripts that demonstrate how to use pgvector,based on the [pgvector sample code](https://github.com/pgvector/pgvector-python).

| Script | Dependencies | Description |
|--------|--------------|-------------|
| [`sqlalchemy_async.py`](./examples/sqlalchemy_async.py) | `asyncpg`, `sqlalchemy`, `pgvector` | Uses pgvector with SQLAlchemy and asyncpg for a simple 3-dimension vector. |
| [`sqlalchemy_items.py`](./examples/sqlalchemy_items.py) | `psycopg2`, `sqlalchemy`, `pgvector` | Uses pgvector with SQLAlchemy and psycopg2 for a simple 3-dimension vector. |
| [`sqlalchemy_movies.py`](./examples/sqlalchemy_movies.py) | `psycopg2`, `sqlalchemy`, `pgvector` | Uses pgvector with SQLAlchemy and psycopg2 for 1536-dimension vectors calculated previously with OpenAI's text-embedding-ada-002 model. |
| [`sqlmodel_items.py`](./examples/sqlmodel_items.py) | `sqlmodel`, `pgvector` | Uses pgvector with SQLModel for a simple 3-dimension vector. |
| [`asyncpg_items.py`](./examples/asyncpg_items.py) | `asyncpg`, `pgvector` | Uses pgvector with asyncpg for a simple 3-dimension vector. |
| [`psycopg_items.py`](./examples/psycopg_items.py) | `psycopg2`, `pgvector` | Uses pgvector with psycopg2 for a simple 3-dimension vector. |

Let us know if there are any other examples you would like to see!
