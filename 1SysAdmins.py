#%% [markdown]
# # System Administrators
# ## Setup : this should seem familiar

#%%
from dotenv import load_dotenv
from os import getenv
from faker import Faker
fake = Faker()
import random

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
# # Three Use Cases:
# 
# * 1. Creating fake users, three fake courses, and fake memberships. 
# * 2. Getting a users last accessed courses 
# * 3. Disabling and enabling a course and user. 
#%% [markdown]
# ## Creating Fake Users, Courses and Memberships
#%% [markdown]
# ### Creating Fake Courses
# We are going to create 3 fake courses.  Since we are only creating a handful, we will enter the information manually.

#%%
r = bb.CreateCourse(payload={'name':'DevCon-Demo1','courseId':'NAC-DevCon1'})
print(r.json())


#%%
r1 = bb.CreateCourse(payload={'name':'DevCon-Demo2','courseId':'NAC-DevCon2'})
r2 = bb.CreateCourse(payload={'name':'DevCon-Demo3','courseId':'NAC-DevCon3'})

print(r1.status_code)
print(r2.status_code)

#%% [markdown]
# ### Creating Fake Users
# For this, we are going to create 50 users with the help from the libary 'faker'.  Faker generates random names / addresses / passwords ... basically all user info needed for this use case.

#%%
students = []
for _ in range(50):
    name = fake.name()
    while len(name.split()) > 2:
        name = fake.name()
    names = name.split()  
    first = names[0]
    last = names[-1]
    userName = f'{first[0]}{last}{fake.random_number(digits=3)}'.lower()
    studentId = fake.random_number(digits=9,fix_len=True)
    email = f'{userName}@ku.edu'
    password = fake.password()
    
    student = {'name':{'family': last, 'given': first},
               'userName': userName,
               'password': password,
               'studentId': studentId,
               'externalId': studentId,
               'contact': {'email':email}
              }
    
    
    r = bb.CreateUser(payload=student)
    
    if r.status_code == 201:
        print(f'Created account for {name}')
        students.append(student)
    else:
        print(r.text)
        print(f'Account not created for {name}')

#%% [markdown]
# ### Creating Fake Memberships
# We are going to add my account as an instructor in these three courses, and the students each into one of the three courses.

#%%
courses = ['NAC-DevCon1', 'NAC-DevCon2', 'NAC-DevCon3']
for course in courses:
    r = bb.CreateMembership(userId='m500d520', courseId=course, payload={'courseRoleId':'Instructor'})
    print(r.status_code)


#%%
import random
random.choice(courses)


#%%
random.choice(courses)


#%%
for student in students:
    userName = student['userName']
    course = random.choice(courses)
    r = bb.CreateMembership(userId=userName, courseId=course, payload={})
    if r.status_code == 201:
        print(f'Added {userName} to {course}')
    else:
        print(r.text)

#%% [markdown]
# ## 2. Getting a User's Last accessed courses
# This is the start of some useful reporting, and can help focuse the search space for grade or access data.

#%%
r = bb.GetUserMemberships('m500d520', 
                      params={'lastAccessed':'2019-07-01',
                              'lastAccessedCompare':'greaterOrEqual'})
r.json()


#%%
courses = r.json()['results']
for course in courses:
    courseId = course['courseId']
    r = bb.GetCourse(courseId)
    course_info = r.json()
    print(course_info['name'])

#%% [markdown]
# ## 3. Disabling and enabling a user and a course
# Sometimes SIS integrations cause issues. We use SAIP, and courses have been disabled when a section changes and enrollments have been disabled when a student changes sections.  Here are quick ways to correct this with the API.

#%%
#Causing course and user to be disabled on purpose
r1 = bb.UpdateCourse('NAC-DevCon2', payload={'availability':{'available':'Disabled'}})
r2 = bb.UpdateMembership(userId='m500d520', courseId='NAC-DevCon1', payload={'availability':{'available':'Disabled'}})

print(r1.json())
print(r2.json())


#%%
r1 = bb.UpdateCourse('NAC-DevCon2', payload={'availability':{'available':'Yes'}})
r2 = bb.UpdateMembership(userId='m500d520', courseId='NAC-DevCon1', payload={'availability':{'available':'Yes'}})

print(r1.json())
print(r2.json())

#%% [markdown]
# # Clean-up
# Run this after the other demonstrations.  You need the users, courses and memberships for the next two Notebooks. 

#%%
for user in [student['externalId'] for student in students]:
    r = bb.DeleteUser(f'externalId:{user}')
    print(r.status_code)


#%%
for course in ['NAC-DevCon1', 'NAC-DevCon2', 'NAC-DevCon3']:
    r = bb.DeleteMembership(courseId=course, userId='m500d520')
    r = bb.DeleteCourse(course)
    print(r.status_code)


#%%



