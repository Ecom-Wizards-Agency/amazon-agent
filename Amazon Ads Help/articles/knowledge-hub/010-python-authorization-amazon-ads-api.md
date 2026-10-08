---
title: "Step-by-Step Guide: Implementing Amazon Ads API Authorization Flow using Python"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/blogs/usage-examples/2025-03-step-by-step-guide-authorization-amazon-ads-api-requests-using-python"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-10-07"
status: "captured"
security_note: "Credential-bearing examples summarized instead of saved as runnable code."
---

# Step-by-Step Guide: Implementing Amazon Ads API Authorization Flow using Python

Implementing the authorization flow is a crucial step for developers in integrating with the Amazon Ads API to build their own SaaS products for serving their Amazon advertising clients. However, for developers who are not familiar with API authorization and the OAuth2 protocol, implementing the authorization flow may present a significant learning curve, prolonging the time required to understand and properly implement this crucial step. This article aims to explain the essential concepts related to Amazon Ads API authorization flow alongside Python code examples that developers can reference to accelerate their development process.

Two options for Python implementation are described below, one using native Python and the `requests` library, the other using the `requests_oauthlib` library.

## What is authorization and why is it needed?

Authorization is a process by which the resource owner gives permission to a third party to access its resources. In the case of Amazon Ads, the advertisers own and control access to their data. For a third party to access and make changes to the data and services of the advertisers on their behalf via API, a safe and robust authorization process is required. Amazon Ads implements its API authorization based on OAuth2, an industry-standard protocol for authorization. Third parties can only access the data and services of an advertiser after they complete the authorization process with the advertiser.

## Amazon Ads API authorization flow

The diagram below illustrates the key roles as well as the activities throughout the authorization flow. More details can be found on the Amazon Ads advanced tools center.

### Key roles

- **API caller**: this is often referred to as the client. In the case of Amazon Ads API, this is a Login with Amazon (LwA) client application. This is the third party that is trying to obtain access to the data and services of an advertiser.
- **Advertiser**: this is often referred to as the resource owner. During the authorization flow, the advertiser gives permission to an API caller to access their data and services.
- **Login with Amazon authorization server**: this is often referred to as the authorization server. It issues the access token and refresh token to the API caller after the authorization is completed successfully.
- **API endpoints:** these are hosted by the resource server, it returns the data and services when being called by the API caller.

### Key activities

- **Retrieve LwA client ID and secret**: The authentication and authorization process begins with LwA client ID and the client secret. You will retrieve these details from your Amazon Developer Account.
- **Get approval from advertisers**: The API caller will send an authorization URL to the advertiser. When the advertiser clicks on the URL, they will be led to the Amazon sign-in page. They will sign in their Amazon account using their credential and approve the permission scopes requested by the API caller. The advertiser will then be redirected to the return URL with the authorization code, which will expire after 5 minutes. As a result, the authorization code should be shared with the API caller right away to obtain the access token and refresh token in the next step. See below an illustration that explains the different components of an authorization URL.

- **Get access token and refresh token**: The API caller presents the client ID, client secret as well as the authorization code to the authorization server, which will return the access token and refresh token. Access token serves as a permit and is required when the API caller makes an API call to access the data and services of the advertiser. An access token is valid for 60 minutes. After the access token expires, the API caller will use the refresh token to generate a new access token. The refresh token remains valid until the advertiser who granted authorization revokes the authorization.
- **Retrieve profile ID(s)**: Profiles represent an account of an advertiser in a specific marketplace. The API caller can use the client ID and the access token to make a call to the profile endpoints (`/v2/profiles`). This will return all the profiles under the advertiser in a particular region. To get profiles across regions, the API caller will need to make separate calls using the specific host. For example, to get profiles in the `EU` region, the API caller will need to call `https://advertising-api-eu.amazon.com/v2/profiles`.
- **Make an API call**: Once the list of profiles from the advertiser is available, the API caller can go ahead to use the client ID, access token and the specific profile ID to make various API calls and access the data and services of the advertiser.

## User interface steps

The first two steps in the OAuth process require using Amazon user interfaces to retrieve credentials for the client application and to grant authorization from the resource owner. You will need to note four values as a result of these steps to use in your code later:

- client ID
- client secret
- return URL
- authorization code

Note

This article assumes that you have already completed the onboarding process for Amazon Ads, as documented in the onboarding guide. If you have not yet finished the onboarding steps, please follow the steps on the onboarding guide to complete the process before continuing with the rest of the steps provided below.

### Retrieve LwA client ID and secret from your Amazon Developer account

After you create your Login with Amazon security profile on your Amazon Developer account, you can retrieve your client ID and secret by:

1. Log into your Amazon Developer account
2. Click "Developer Console" on the top right corner
3. Click "Login with Amazon" on the top menu bar
4. Click "Show Client ID and Client Secret" for your security profile

More details can be found in Create a Login with Amazon application. Below is a screenshot showing where to find the client ID and secret.

### Retrieve refresh token

Note

If you choose to use the `requests_oauthlib` library below, this step will be partly automated by your code.

#### 1. Create an authorization URL

```
https://www.amazon.com/ap/oa?client_id=YOUR_LWA_CLIENT_ID&scope=advertising::campaign_management&response_type=code&redirect_uri=YOUR_RETURN_URL
```

**YOUR_LWA_CLIENT_ID**: This is the client ID you retrieved from the Amazon Developer Portal

**YOUR_RETURN_URL**: This is the return URL you used in the Amazon Developer Portal

#### 2. Grant access to Amazon Ads data

1. Paste the authorization URL determined above into the address bar of your browser. Navigate to the URL.
2. Sign in using an Amazon user account with access to the Amazon Ads accounts you want to manage through the API. This account may not be the same as the Amazon Developer account you used to create the LwA client.
3. You will be redirected to a consent form listing the specific data and services included in the authorization grant. To grant access, select Allow.
4. You will be redirected to the redirect_uri that you specified previously, with query parameters appended to the URL. Copy the address from the address bar of your browser, and note the value of the `code` parameter (the xxxx in the example below):

```
https://www.amazon.com/?code=xxxxxxxxxxxxxxxxxxx&scope=advertising::campaign_management
```

The `code` parameter (`xxxxxxxxxxxxxxxxxxx` in the example above) in the redirect URL is an authorization code, which you can now use in the next step of the onboarding process to get access and refresh tokens

## Implementing authorization in Python

Now let us examine how all the steps outlined above can be implemented in Python using two different approaches.

### Option 1: Retrieving tokens using the `requests` library

In this example we will show how to retrieve an access token using Python code.

Note

The `requests` library is not a native Python library, though many Python users have installed it globally. If this is not the case for your workspace, you may need to install `requests` either globally or in your virtual environment for this project. Learn more about installing `requests`.

#### Retrieve access and refresh tokens

You can use the four values retrieved from the user interface steps to retrieve access and refresh tokens as shown here:

```
import  requests

 """
 Get the refresh and access tokens from an authorization code
""" 

 # LwA authorization server 
auth_url =  "https://api.amazon.com/auth/o2/token" 

 # replace authorization_code, redirect_url, client_id, and client_secret below 
request_body= { 
    'grant_type' :  'authorization_code' , 
    'code' : authorization_code,
    'redirect_uri' : redirect_url,
    'client_id' : client_id,
    'client_secret' : client_secret
}

 # send the request 
token_response = requests.post(auth_url, data=request_body)

 # store the access and refresh tokens 
access_token = token_response.json()[ 'access_token' ]
refresh_token = token_response.json()[ 'refresh_token' ]

 # output 
 print ( f"Access token:  {access_token} " )
 print ( f"Refresh token:  {refresh_token} " )
```

#### Use a refresh token

When the access token expires (or even if it has not) you can use the refresh token from the above step to get a new access token.

```
import  requests

 """
Get access token
""" 

 # LwA authorization server 
auth_url =  "https://api.amazon.com/auth/o2/token" 

 # replace client_id, client_secret, and refresh_token below 
request_body = {
    'grant_type' :  'refresh_token' ,
    'client_id' : client_id,
    'client_secret' : client_secret,
    'refresh_token' : refresh_token
}

 # send the request 
refresh_response = requests.post(auth_url, data=request_body)

 # store the new access token 
access_token=refresh_response.json()[ 'access_token' ]

 # output 
 print ( f"Access token:  {access_token} " )
```

#### Retrieve a profile

For most other requests to the Amazon Ads API, a profile ID is required. Using your access token, you can retrieve a profile ID from the profiles endpoint.

```
import  requests

 """
Using the access token, get profiles.
API specification:https://advertising.amazon.com/API/docs/en-us/reference/2/profiles
""" 

profiles_url =  "https://advertising-api.amazon.com/v2/profiles" 

 # make sure to set access_token and client_id values above, or replace below 
profiles_headers = {
    'Authorization' :  f'Bearer  {access_token} ' ,
    'Amazon-Advertising-API-ClientId' : client_id
}

 # send the request 
response = requests.get(profiles_url, headers=profiles_headers)

 # print  
 print (response)

 # store the ID of the first profile returned as a string 
profile_id =  str (response.json()[ 0 ][ 'profileId' ])
```

#### Use a profile ID to make other requests

You can use a profile ID as the `Amazon-Advertising-API-Scope` header for other campaign management requests. Adding the following below your profiles request will list the Sponsored Products campaigns for the advertiser using the `/sp/campaign/list` endpoint with an empty request body.

```
# list campaigns URL 
campaigns_url =  "https://advertising-api.amazon.com//sp/campaigns/list" 

 # set required headers for POST sp/campaigns/list 
 # client_id, access_token, and profile_id must be set somewhere above 
headers = {
     "Amazon-Advertising-API-ClientId" : client_id,
     "Authorization" :  f'Bearer  {access_token} ' ,
     "Amazon-Advertising-API-Scope" : profile_id,
     "Accept" :  "application/vnd.spCampaign.v3+json" ,
     "Content-Type" :  "application/vnd.spCampaign.v3+json" 
}

response = requests.post(campaigns_url, headers=headers, json={})
 print (response.json())
```

Note

To make other requests to the API, view the specifications for your chosen operation to determine required headers and to find request body schemas. API specifications are listed under API reference > Resources in the advanced tools center.

### Option 2: Implementation of authorization flow with Requests-OAuthlib

Requests-OAuthlib is an open-source Python library built on top of Requests and OAuthlib. It provides an easy-to-use Python interface for building OAuth2 clients and abstracting away tasks such as putting together the authorization URL or regenerating an access token using the refresh token.

Note

See the Requests-OAuthlib documentation for information about installing the library.

#### Step 1: Go Through Authorization and Retrieve Access Token and Refresh Token:

In this walkthrough, you will manage the LwA client application credentials in a local JSON file named `lwa_app_credential.json`, which looks like the example below. For a production setup, you can use a cloud service such as AWS Secrets Manager to manage your credentials.

```
{ 
     "client_id" :   "amzn1.REDACTED" , 
     "client_secret" :   "5682xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" , 
     "redirect_uri" :   "https://amazon.com" 
 }
```

In your Python program, import the required libraries, set values for authorization and API URLs, and read the LwA client application credentials from the JSON file:

```
from  requests_oauthlib  import  OAuth2Session
 import  json

 # LwA authorization server 
auth_url =  "https://api.amazon.com/auth/o2/token" 

 # Amazon Ads API (North America) 
api_url =  "https://advertising-api.amazon.com" 

 # read LWA app credential from JSON 
c =  open ( 'lwa_app_credential.json' )
lwa_app_credential = json.load(c)
client_id = lwa_app_credential[ 'client_id' ]
client_secret = lwa_app_credential[ 'client_secret' ]
redirect_uri = lwa_app_credential[ 'redirect_uri' ]
```

Use these values plus the following permission scopes to initialize an `OAuth2Session`:

```
# set scope and initialize OAuth2Session 
scope = [ 'advertising::test:create_account' , 'advertising::campaign_management' ]
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri,scope=scope)
```

Now the OAuth session can be used to generate an authorization URL.

```
# create the authorization grant URL and display in terminal 
authorization_url, state = oauth.authorization_url( 'https://www.amazon.com/ap/oa' )
 print ( '\n\nPlease go to the following URL and authorize access:\n\n' , authorization_url,  '\n\n' )
```

Log in using the user account for the advertising account you want to administer, then input the full callback URL:

```
# input the authorization response 
authorization_response =  input ( 'Input the full callback URL here and press enter:' )
```

The OAuth session established above includes a built-in method for fetching access tokens based on the authorization response. Pass the response to the following method to retrieve access and refresh tokens.

```
# retrieve access and refresh tokens using the authorization response 
tokens = oauth.fetch_token(auth_url, authorization_response=authorization_response, client_secret=client_secret)
 print (json.dumps(tokens))
```

Retrieve the access token and refresh token. In this example, we again write it into a local JSON file named `tokens.json`. For now, manually create this file, which should look like the example below. Again, you can use a cloud service to manage your credential more securely in production.

```
{ 
     "access_token" :   "Atza|IwEBIEfoD1ctR-JvXBfarwYifi7..." , 
     "refresh_token" :   "Atzr|IwEBIDpp_-uQFh-TpemsDnS2ba..." , 
     "token_type" :   "bearer" , 
     "expires_in" :   3600 , 
     "expires_at" :   1715890643.8363361 
 }
```

Tip

Aside from the library imports and credential setup, you will not need to run the above code again during this tutorial. Before moving on, either comment it out or set it aside in a function. The latter option might resemble the following:

```
# retrieve tokens using an authorization grant 
 def   auth_grant ():
     # set scope and establish session 
    scope = [ 'advertising::test:create_account' , 'advertising::campaign_management' ]
    oauth = OAuth2Session(credentials[ 'client_id' ], redirect_uri=redirect_uri, scope=scope)

     # print the authorization URL 
    authorization_url, state = oauth.authorization_url( 'https://www.amazon.com/ap/oa' )
     print ( 'Please go to %s and authorize access.'  % authorization_url)

     # input the full response URL 
    authorization_response =  input ( 'Input the full callback URL here and press enter:' )

     # fetch tokens 
    tokens = oauth.fetch_token(auth_url, authorization_response=authorization_response, client_secret=credentials[ 'client_secret' ])
     print (tokens)
```

#### Step 2: Setting up an authorized client

Requests-OAuthlib is also capable of automatically refreshing access tokens. We can use the tokens stored in `tokens.json` to configure a client to auto-refresh tokens when expired.

```
# create a refresh_credentials dictionary 
refresh_credentials= {
      'client_id' : client_id,
      'client_secret' : client_secret,
}

 # create a helper method to save tokens in tokens.json 
 def   token_saver ( tokens ):
    json_object = json.dumps(tokens, indent= 4 )
     with   open ( "tokens.json" ,  "w" )  as  output:
        output.write(json_object)

 # create a helper method to read tokens from tokens.json 
 def   token_reader ():
    t =  open ( 'tokens.json' )
     return  json.load(t)

 # initialize a client 
client = OAuth2Session(
    client_id, 
    token=token_reader(), 
    auto_refresh_url=auth_url,
    auto_refresh_kwargs=refresh_credentials, 
    token_updater=token_saver
)
```

Use this client to retrieve your list of profiles from the Amazon Ads API:

```
# set required headers for GET v2/profiles 
headers = {
     "Amazon-Advertising-API-ClientId" : client_id,
     "Authorization" :  f'Bearer  {token_reader()[ "access_token" ]} ' 
}

response = client.get( f" {api_url} /v2/profiles" , headers=headers)
 print (json.dumps(json.loads(response.content.decode( 'utf-8' )),indent= 2 ))
```

#### Step 3: Call other API endpoints

You can use a profile ID from the response above along with your OAuth client to make other calls to the Amazon Ads API.

```
# set a profile ID 
profile_id =  '186xxxxxxxxxxxxxx'
```

Define the headers and make the API call. In this example, we are listing the Sponsored Products campaigns for the advertiser using the `/sp/campaign/list` endpoint with an empty request body.

```
# set required headers for POST sp/campaigns/list 
headers = {
     "Amazon-Advertising-API-ClientId" : client_id,
     "Authorization" :  f'Bearer  {token_reader()[ "access_token" ]} ' ,
     "Amazon-Advertising-API-Scope" :  f' {profile_id} ' ,
     "Accept" :  "application/vnd.spCampaign.v3+json" ,
     "Content-Type" :  "application/vnd.spCampaign.v3+json" 
}

response = client.post( f" {api_url} /sp/campaigns/list" , headers=headers, json={})
 print (json.dumps(json.loads(response.content.decode( 'utf-8' )),indent= 2 ))
```

Note

To make other requests to the API, view the specifications for your chosen operation to determine required headers and to find request body schemas. API specifications are listed under API reference > Resources in the advanced tools center.

## Conclusion

In this article, we introduce two ways to implement the OAuth2 authorization flow for Amazon Ads API in Python, one without using any external libraries and one using the Requests-OAuthlib library. We hope these examples help you understand how the OAuth2 authorization flow works in the Amazon Ads API and can make your development process easier.
