#%% [markdown]
# # Developer
# ## Setup : this should seem really familiar

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


#%%
from bbrest import BbRest
bb = BbRest(key, secret, url)

#%% [markdown]
# # Use Case : Creating groups for merged classes
# Steps involved:
# * Getting all course memberships
# * Getting child course information
# * Generating groups for each section (parent and child)
# * Enrolling students into groups for each section
# 
# Important note: more logic is needed if you want to check the status of the groups, or if you want to update the groups regularly.  To hear more about that logic, and see an actual tool built around this usecase - I am presenting on this tomorrow.
#%% [markdown]
# ## Get all course memberships
# Note : This is much more difficult with larger classes due to paging.  This is simplified here. BbRest should eventually deal with this, but there's no great way to do this currently.

#%%
members = bb.GetCourseMemberships('NAC-DevCon1', params={'limit':'100'}).json()['results']


#%%
members[:10]

#%% [markdown]
# ## Get all unique courseIds to create groups

#%%
courseIds = set([member.get('childCourseId', member.get('courseId', '')) for member in members])
print(courseIds)

#%% [markdown]
# ## Generate groups for each section (parent and child)

#%%
for courseId in courseIds:
    course_info = bb.GetCourse(courseId).json()
    group = {
        'name':course_info['courseId'],
        'externalId':course_info['courseId'],
        'availability':{'available':'Yes'}
    }
    r = bb.CreateGroup('NAC-DevCon1', payload=group)
    print(r.status_code)

#%% [markdown]
# ## Enroll students in their sections

#%%
students = [member for member in members if member['courseRoleId'] == 'Student']
for student in students:
    userId = student['userId']
    courseId = student.get('childCourseId', student.get('courseId', ''))
    groupId = bb.GetCourse(courseId).json()['courseId']
    r = bb.PutGroupMembership(courseId="NAC-DevCon1", userId=userId, groupId=f'{groupId}')
    print(r.status_code)


#%%
for course in ['NAC-DevCon1', 'NAC-DevCon2', 'NAC-DevCon3']:
    r = bb.PutGroupMembership(courseId='NAC-DevCon1', userId='m500d520', groupId=course)


#%%
bb.GetGroups('NAC-DevCon1').json()


#%%
bb.GetGroupMemberships('NAC-DevCon1','NAC-DevCon2').json()


#%%



