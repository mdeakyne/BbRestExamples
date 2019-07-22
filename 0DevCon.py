#%% [markdown]
# # Setting up the environment variables.
# You don't want to ever publish your key or secret - which is why these are stored in a .env file that is not shared in your git repo / or visible when presenting.  Python has two functions to get these values in a secure way: 
# 
# load_dotenv - adds the contents of .env file to your environment.
# getenv - reads the environment variables into local python variables.
# 
# _NOTE: You can skip this step, and hardcode in the values - but you should avoid committing these anywhere, or displaying them for others._

#%%
from dotenv import load_dotenv
from os import getenv

if load_dotenv():
    key, secret, url = getenv('key'), getenv('secret'), getenv('url')
    try:
        assert key, "Key not loaded"
        assert secret, "Secret not loaded"
        assert url, "Url not loaded"
        print("All environment variables loaded successfully")
    except AssertionError as e:
        print(e)
        print("Ensure your .env file has url, key and secret")
else:
    print('Make sure you have a .env file')
    

#%% [markdown]
# # Setup 
# Setup requires knowing your key, secret and base url.  
# These are made up values below.
# Example values:
# 
# ```python
# url = 'https://domain.school.edu'
# key = 'e08909a-8373-3843-4b38-0ed9a0cbfa' 
# secret = 'Isd89Snass8ds7yJScjdd80saNUX' 
# ```

#%%
from bbrest import BbRest


#%%
bb = BbRest(key, secret, url)

#%% [markdown]
# # Solved Problems
# 
# Let's start by going over some inconveniences with the rest api.  
# 
# * Token Management: If you are just getting started with Bb APIs, token management is a huge obstacle.  Especially for less-technical fields. 
# 
# * API availability: SaaS is constantly rolling out APIs, and these eventually arrive at MH or SH clients with version upgrades (not Cumulative Updates).  Knowing what methods are avaialble to you is easier now, but still an inconvenience. 
# 
# * API discovery: Navigating developers.blackboard.com can be tricky - and this tries to help you do this from the command line, rather than coding with a bunch of tabs open.
# 
# * Call tracking: Sometimes you use a lot of API calls when trying things out.  Being able to keep track of how many you've used is possible but difficult.  This makes it easier
#%% [markdown]
# ## Token Management
# BbRest gets a token for all calls when created.  You can manually check expiration, and manually refresh the token if you want.  Tokens in Blackboard can't be manually expired, however, and refreshing the token before it's expired ... just gets back the same token.  

#%%
bb.expiration()


#%%
bb.refresh_token()


#%%
bb.expiration()

#%% [markdown]
# ## API availability
# BbRest only creates functions for the specific version of Blackboard it's instantiated on.  It uses APIs to check the version, and then generated methods for that version.  This is really helpful when switching between a test system and production, and testing between the two.

#%%
bb.version


#%%
bb.GetGradeColumns('TST-101').url

#%% [markdown]
# ## API Discovery
# Tab completion, and dynamic docstrings make navigating the library a little easier.  All based on [developer.blackboard.com](developer.blackboard.com)

#%%
#Examples of searching through available documentation

#bb.Get...
#bb.GetUser()...

#%% [markdown]
# ## Call Tracking
# There have been times during testing that KU used 10000 calls in a matter of minutes. We've also been interested in limiting the number of calls in certain applications, though modifications.  Tracking the number of calls is possible with headers - but BbRest makes it easier. 

#%%
bb.calls_remaining()

#%% [markdown]
# # Use Cases
# I've built out three notebook files to demonstrate three potential use cases for this library, each for a specific audience.

#%%



