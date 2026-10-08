---
title: "Agents with Amazon Ads MCP Server workshop overview"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/amazon-ads-mcp-server/01-overview"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-10-07"
status: "captured"
---

# Module 1: Workshop Overview and Prerequisites

Note

Learn what this workshop covers, review the end-state architecture, and verify your environment meets all prerequisites.

## Workshop Overview

This workshop is designed to help technical teams at advertisers, agencies, and technology partners accelerate the development of agentic AI solutions for Amazon Ads. By the end of this workshop, you will have hands-on experience building MCP servers, creating LangGraph agents, deploying them to Amazon Bedrock AgentCore, and integrating with the Amazon Ads MCP Server.

### Purpose and Objectives

- Understand the Model Context Protocol (MCP) and how it connects AI models to external tools and APIs.
- Build and deploy a custom MCP server that wraps an Amazon Bedrock Knowledge Base.
- Create a LangGraph agent that discovers and orchestrates MCP tools using Claude on Amazon Bedrock.
- Deploy MCP servers and agents to Amazon Bedrock AgentCore as managed runtimes.
- Connect to the official Amazon Ads MCP Server to manage advertising campaigns through natural language.
- Provide scalable, production-ready artifacts that teams can adapt for their own agentic AI workflows.

### Target Audience

This workshop is intended for solutions architects, software engineers, and technical leads who work with the Amazon Ads API and want to build AI-powered automation using MCP and AgentCore.

## Contributors

This workshop was created by Chintan Sanghavi and Christelle Ngambula, both Senior Solutions Architects at Amazon Ads. Chintan works with advertisers and partners to design scalable integrations with the Amazon Ads API, with a focus on agentic AI and MCP-based architectures. Christelle helps partners and advertisers build AI-powered advertising solutions, specializing in agent frameworks, MCP server development, and Amazon Bedrock AgentCore deployments. For questions or additional details about this workshop, connect with either contributor via LinkedIn.

## When to Use

- You are starting the workshop for the first time
- You want to verify your environment is ready before diving into the hands-on modules

## Step 1: Understand the Learning Tracks

This workshop is organized into two learning tracks so you can choose the depth that fits your needs.

**Track A — Build and Deploy Custom MCP Servers and Agents (Modules 1–6)**

Track A walks you through building an MCP server with FastMCP, deploying it to Amazon Bedrock AgentCore, creating a LangGraph agent that connects to the deployed MCP server, and deploying the agent to AgentCore using the A2A protocol. You will finish Track A with a fully deployed agent that can answer questions using a Bedrock Knowledge Base.

**Track B — Amazon Ads MCP Server Integration (Modules 7–9)**

Track B extends your agent by connecting it to the Amazon Ads MCP Server (open beta). You will discover Ads API tools, build a multi-server agent that combines your custom Knowledge Base MCP server with the Ads MCP Server, and test the end-to-end flow. Track B requires Amazon Ads API credentials (Client ID, Client Secret, Refresh Token). If you do not have Ads credentials, you can stop after Module 6.

**Module 10 — Cleanup** applies to both tracks and guides you through deleting all workshop resources.

## Step 2: Review the Architecture

The diagram below shows the end-state architecture you will build across both tracks.

```
┌─────────────────────────────────────────────────────────┐
│                Amazon Bedrock AgentCore                  │
│                                                          │
│  ┌──────────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  LangGraph Agent  │  │ Knowledge Base│  │Amazon Ads │  │
│  │  (A2A Protocol)   │  │  MCP Server   │  │MCP Server │  │
│  └────────┬─────────┘  └──────┬───────┘  └─────┬─────┘  │
│           │                   │                 │        │
└───────────┼───────────────────┼─────────────────┼────────┘
            │                   │                 │
            ▼                   ▼                 ▼
┌───────────────────────────────────────┐  ┌────────────┐
│            AWS Services               │  │   External    │
│                                       │  │             │
│  Amazon Bedrock (Claude)              │  │ Amazon Ads  │
│  Bedrock Knowledge Base               │  │    API      │
│  AWS Secrets Manager                  │  │             │
│  CloudWatch Logs                      │  └────────────┘
└───────────────────────────────────────┘
```

**Data flow:**

- **Participant / Client** → invokes the LangGraph Agent via `invoke_agent_runtime` (A2A)
- **LangGraph Agent** → invokes MCP servers via `invoke_agent_runtime` (MCP)
- **LangGraph Agent** → calls Claude via `InvokeModel` on Amazon Bedrock
- **Knowledge Base MCP Server** → calls `retrieve` / `retrieve_and_generate` on Bedrock Knowledge Base
- **Amazon Ads MCP Server** → calls the Amazon Ads API
- **LangGraph Agent** → reads secrets from AWS Secrets Manager via `GetSecretValue`
- All runtimes stream logs to **CloudWatch Logs**

**Key components:**

- **Knowledge Base MCP Server** — A FastMCP server you build and deploy to AgentCore. It exposes `query_knowledge_base` and `retrieve_and_generate` tools backed by an Amazon Bedrock Knowledge Base.
- **Amazon Ads MCP Server** — The official Amazon Ads MCP Server (open beta) deployed on AgentCore. It translates natural language into Amazon Ads API calls.
- **LangGraph Agent** — A Python agent built with LangChain and LangGraph. It discovers tools from both MCP servers, converts them to LangChain StructuredTool objects, and orchestrates calls using Claude on Amazon Bedrock.
- **AgentCore** — The managed runtime that hosts both MCP servers and the agent. MCP servers use the MCP protocol; the agent uses the A2A protocol.

## Step 3: Verify Prerequisites

Note

This workshop is designed for Linux and macOS environments. All commands use bash syntax. If you are on Windows, we recommend using Windows Subsystem for Linux (WSL) to follow along.

Confirm you have the following before starting Module 2.

### Required for All Tracks

| Prerequisite | Details |
| --- | --- |
| **Python 3.13+** | Required runtime for MCP servers and agents. Verify with `python --version`. |
| **AWS Account** | An AWS account with Amazon Bedrock access enabled in your target region. |
| **AWS CLI configured** | Run `aws configure` to set your access key, secret key, and default region. |
| **AgentCore CLI** | Install with `pip install bedrock-agentcore` and `pip install --upgrade bedrock-agentcore-starter-toolkit`. Verify with `agentcore --help`. |
| **uv** | Python package runner required by the `agentcore` CLI. Install with `pip install uv`. Verify with `uv --version`. |
| **pip** | Python package manager for installing dependencies. Ships with Python 3.13+. |

### Required for Track B Only (Modules 7–9)

| Prerequisite | Details |
| --- | --- |
| **Amazon Ads API Client ID** | Obtain from the Amazon Ads developer console. |
| **Amazon Ads API Client Secret** | Obtain from the Amazon Ads developer console. |
| **Amazon Ads API Refresh Token** | Generated during the OAuth flow for your Ads API application. |

### Configure AWS Credentials

If you have not already configured the AWS CLI, run:

```
aws configure
```

Enter the following when prompted:

```
AWS Access Key ID:   <YOUR_ACCESS_KEY> 
 AWS Secret Access Key:   <YOUR_SECRET_KEY> 
 Default region name:   us-east-1 
 Default output format:   json
```

Note

For production environments, use IAM Identity Center (SSO) or temporary credentials instead of long-lived access keys. Long-lived keys should be rotated regularly and never shared or committed to source control.

Verify your credentials are working:

```
aws sts get-caller-identity
```

You should see your account ID, user ARN, and user ID. If this fails, double-check your access key and secret key.

### Create a Virtual Environment and Install Dependencies

Create a dedicated virtual environment for the workshop to keep dependencies isolated from your system Python:

```
mkdir  workshop-mcp
 cd  workshop-mcp
python -m venv .venv
```

Activate the virtual environment:

```
# macOS / Linux 
 source  .venv/bin/activate

 # Windows (PowerShell) 
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` in your terminal prompt. Install the core dependencies:

```
pip install mcp boto3 python-dotenv langchain langchain-core langchain-aws langgraph pydantic fastapi uvicorn bedrock-agentcore bedrock-agentcore-starter-toolkit uv
```

Note

**Important:** Make sure the virtual environment is activated (`(.venv)` visible in your prompt) every time you open a new terminal for this workshop. All subsequent modules assume you are working inside `workshop-mcp/` with the virtual environment active.

Tip

Using a virtual environment keeps workshop dependencies isolated from your system Python. When you are done with the workshop, you can simply delete the `workshop-mcp/` folder to clean up everything.

### Verify Bedrock Access

Confirm Claude is available in your region:

```
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query  "modelSummaries[?contains(modelId, 'claude')].[modelId]"  \
  --output table
```

If no models appear, enable Claude in the Amazon Bedrock console under **Model access**.

### Optional: Install Node.js 18+ (for MCP Inspector)

Node.js is not required for the workshop, but the MCP Inspector is a useful debugging tool that lets you connect to a running MCP server, browse its tools, and invoke them interactively. Install Node.js 18+ if you want to use it:

```
node --version    # Should be 18+ 
npm --version
```

### Verify Your Setup

Run this quick verification script to confirm everything is ready. Create a file called `verify_setup.py`:

```
"""Verify workshop environment setup.""" 
 import  sys
 import  subprocess

checks = []

 # Python version 
v = sys.version_info
checks.append(( "Python 3.13+" , v.major ==  3   and  v.minor >=  13 ))

 # Required packages 
 for  pkg  in  [ "mcp" ,  "boto3" ,  "dotenv" ,  "langchain" ,  "langgraph" ,  "pydantic" ,  "fastapi" ,  "uvicorn" ]:
     try :
         __import__ (pkg)
        checks.append(( f"Package:  {pkg} " ,  True ))
     except  ImportError:
        checks.append(( f"Package:  {pkg} " ,  False ))

 # AWS CLI 
 try :
    result = subprocess.run([ "aws" ,  "--version" ], capture_output= True , text= True )
    checks.append(( "AWS CLI" , result.returncode ==  0 ))
 except  FileNotFoundError:
    checks.append(( "AWS CLI" ,  False ))

 # Print results 
 print ( "\n=== Workshop Environment Check ===\n" )
all_pass =  True 
 for  name, passed  in  checks:
    status =  "PASS"   if  passed  else   "FAIL" 
    icon =  "[OK]"   if  passed  else   "[!!]" 
     print ( f"   {icon}   {name} :  {status} " )
     if   not  passed:
        all_pass =  False 

 print ()
 if  all_pass:
     print ( "All checks passed. You are ready for the workshop!" )
 else :
     print ( "Some checks failed. Please install the missing items before proceeding." )
```

Run it:

```
python verify_setup.py
```

All checks should show `[OK]`. Fix any failures before moving to Module 2.

## Step 4: Create an Amazon Bedrock Knowledge Base

The MCP server you build in Module 3 queries an Amazon Bedrock Knowledge Base. Create one now so it is ready when you need it.

### Create an S3 Bucket for Source Documents

Create an S3 bucket to store the documents your Knowledge Base will index:

1. Open the S3 console.
2. Click **Create bucket**.
3. Enter a unique bucket name (for example, `workshop-kb-docs-<YOUR_ACCOUNT_ID>`).
4. Select your target region (for example, `us-east-1`).
5. Leave all other settings as default and click **Create bucket**.
6. Upload one or more documents (PDF, TXT, HTML, or Markdown) to the bucket. These can be product documentation, advertising best practices, campaign guides, or any reference material you want the agent to query.

Tip

For this workshop, you can upload the Amazon Ads API documentation or any product catalog files. Even a few pages of text will work for testing.

### Create the Knowledge Base

1. Open the Amazon Bedrock console.
2. In the left sidebar, click **Knowledge bases** under **Orchestration**.
3. Click **Create knowledge base**.
4. Enter a name (for example, `workshop-knowledge-base`) and an optional description.
5. Click **Next**.

### Configure the Data Source

1. Select **Amazon S3** as the data source.
2. Browse to the S3 bucket you created above.
3. Leave the chunking strategy as default (or choose **Fixed-size chunking** with 300 tokens for smaller documents).
4. Click **Next**.

### Select the Vector Store

1. Select **Amazon OpenSearch Serverless** as the vector database.
2. Choose **Quick create a new vector store** — this creates an OpenSearch Serverless collection automatically.
3. Click **Next**.

### Select the Embeddings Model

1. Select an embeddings model (for example, **Amazon Titan Embeddings V2**).
2. Review the configuration summary and click **Create knowledge base**.

The creation process takes a few minutes. Once the status shows **Ready**:

1. Click on your Knowledge Base to view its details.
2. Note the **Knowledge Base ID** — you will need this in Module 3 (for example, `XFG61CFOTV`).
3. Click **Sync** to index the documents from your S3 bucket.

Note

The Knowledge Base ID is the value you will set as `KNOWLEDGE_BASE_ID` in your `.env` file in Module 3. Make sure the sync completes successfully before proceeding — check that the document count is greater than zero.

## Step 5: Review the Module Listing

The table below lists all 10 modules in order. Track A covers Modules 1–6. Track B covers Modules 7–9. Module 10 applies to both tracks.

| Module | Title | Description | Time |
| --- | --- | --- | --- |
| 01 | Workshop Overview and Prerequisites | Learning tracks, architecture, prerequisites, and module listing (this module) | 20 min |
| 02 | MCP and AgentCore Concepts | MCP protocol primitives, AgentCore runtime, deployment types, and communication flow | 15 min |
| 03 | Build an MCP Server | Create a FastMCP server with `query_knowledge_base` and `retrieve_and_generate` tools | 30 min |
| 04 | Deploy MCP Server to AgentCore | Deploy the MCP server using `agentcore configure` and `agentcore deploy` | 20 min |
| 05 | Build a LangGraph Agent | Create a LangGraph agent that discovers and invokes MCP tools via AgentCore | 45 min |
| 06 | Deploy Agent to AgentCore | Deploy the agent as an A2A server with Secrets Manager and IAM configuration | 20 min |
| 07 | Connect to Amazon Ads MCP Server | Obtain Ads API credentials, configure the Ads MCP Server, and discover tools | 30 min |
| 08 | Build an Ads Campaign Agent | Combine the custom MCP server and Ads MCP Server into a multi-server agent | 45 min |
| 09 | Testing and Monitoring | End-to-end testing, CloudWatch logs, and troubleshooting | 20 min |
| 10 | Cleanup and Next Steps | Delete all workshop resources and links to further reading | 10 min |

**Total estimated time: ~4 hours** (Track A: ~2.5 hours, Track B adds ~1.5 hours)

## Step 6: Understand What You Will Build

By the end of this workshop you will have built and deployed the following:

1. **A Knowledge Base MCP Server** — A Python application built with FastMCP that wraps an Amazon Bedrock Knowledge Base. It exposes two MCP tools (`query_knowledge_base` and `retrieve_and_generate`) and runs on AgentCore using the MCP protocol with `stateless_http` transport.
2. **A LangGraph Agent** — A Python agent that uses Claude on Amazon Bedrock as its foundation model. The agent connects to your deployed MCP server (and optionally the Amazon Ads MCP Server), discovers available tools at runtime via `tools/list`, converts them to LangChain StructuredTool objects, and uses `create_react_agent` to orchestrate multi-step tool calls.
3. **An Ads Campaign Agent (Track B)** — An extended version of the LangGraph agent that aggregates tools from both your custom Knowledge Base MCP server and the Amazon Ads MCP Server. You can send natural language prompts like "Create a Sponsored Products campaign for my top-selling items" and the agent will orchestrate the correct sequence of Ads API calls.

All components are deployed to Amazon Bedrock AgentCore using the `agentcore` CLI. MCP servers use the MCP protocol. Agents use the A2A protocol. Secrets (ARNs, credentials) are stored in AWS Secrets Manager. Logs stream to CloudWatch.

Next: MCP and AgentCore Concepts →
