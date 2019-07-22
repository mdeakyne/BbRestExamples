#%% [markdown]
# # Setting up the environment variables.
# ## Now with data libraries!
# You don't want to ever publish your key or secret - which is why these are stored in a .env file that is not shared in your git repo / or visible when presenting.  Python has two functions to get these values in a secure way: 
# 
# load_dotenv - adds the contents of .env file to your environment.
# getenv - reads the environment variables into local python variables.
# 
# maya - library for dealing with time
# dask - parallelized data frame library
# pandas - the default data frame library
# pyarrow - needed to store info as parquet files
# hvplot - a pretty good plotting library
# 
# 
# _NOTE: You can skip this step, and hardcode in the values - but you should avoid committing these anywhere, or displaying them for others._

#%%
from dotenv import load_dotenv
from os import getenv

if load_dotenv():
    key, secret, url = getenv('key'), getenv('secret'), getenv('dataurl')
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
    
from bbrest import BbRest
bb = BbRest(key, secret, url)


#%%
import maya
import dask.dataframe as dd
import pandas as pd
import json
import hvplot.dask
from urllib.parse import parse_qs
import asyncio

#%% [markdown]
# # Reading in the Google Analytics information
# We are going to put the google analytics information into a dataframe.
# This information is aggregated pageviews by week of the year, specific to the Spring Semester

#%%
df = dd.read_csv('gabrowser.csv')
df = df.repartition(npartitions=4)
df.columns=['browser','page','week','pageviews']
#if running into connectivity issues, just do:
#df = df.read_csv('data/computed_data*.csv')


#%%
df.head()

#%% [markdown]
# # Data Transformation 
# The urls can be parsed to extract course and content information 

#%%
def parse(url):
    area = url.split('?')[0].split('/')[-1]
    query = url.split('?')[1]
    if 'new_loc' in query:
        area = url.split('?')[1].split('/')[-1]
        query = url.split('?')[2]
    query_dict = parse_qs(query)
    course_id = query_dict.get('course_id',[''])[0]
    content_id = query_dict.get('content_id',[''])[0]
    return {'area':area, 'query':query, 'course_id':course_id, 'content_id':content_id}

df['info'] = df['page'].apply(parse, meta=('page','object'))
df['area'] = df['info'].apply(lambda x:x['area'], meta=('area','str'))
df['course_id'] = df['info'].apply(lambda x:x['course_id'], meta=('course_id','str'))
df['content_id'] = df['info'].apply(lambda x:x['content_id'], meta=('content_id','str'))


#%%
df.head()


#%%
course_ids = df[df['course_id'] != '']['course_id'].unique().compute()
len(course_ids)


#%%
st = maya.now()
for course in course_ids:
    bb.GetCourse(course)
et = maya.now()
print(et-st)


#%%
#Run through all courses and grab course info, then create a dictionary mapping.
st = maya.now()
tasks = []
resps = []
for i in range(0, len(course_ids), 200):
    tasks = []
    for course in course_ids[i:i+200]:
        tasks.append(bb.GetCourse(course, asynch=True))
    resps += await asyncio.gather(*tasks)
course_map = dict(zip(course_ids, resps))
et=maya.now()
print(et-st)


#%%
content_ids = df[df['content_id'] != ''][['course_id','content_id']]
content_ids['combo']=content_ids['course_id'] + '|' + content_ids['content_id']
ucontent_ids = content_ids['combo'].unique().compute()


#%%
#Run though all content and grab content info, then create a dictionary mapping
st = maya.now()
tasks = []
resps = []
pairs = []
for i in range(0, len(ucontent_ids), 150):
    tasks = []
    for combo in ucontent_ids[i:i+150]:
        course_id, content_id = combo.split('|')
        pairs.append((course_id, content_id))
        tasks.append(bb.GetContent(course_id, content_id, asynch=True))
    resps += await asyncio.gather(*tasks)
content_map = dict(zip(pairs, resps))
et = maya.now()
print(et-st)


#%%
#Gets the number of students in each course.
async def get_memberships(courseId):
    tasks = []
    resps = []
    for i in range(0,1600,200):
        tasks.append(bb.GetCourseMemberships(courseId, 
                                             params={'offset':i}, 
                                             asynch=True))
    resps = await asyncio.gather(*tasks)
    results = [resp['results'] for resp in resps]
    memberships = [item for sublist in results for item in sublist]
    students = [membership for membership 
            in memberships
            if membership['courseRoleId'] == 'Student' 
            and membership['availability']['available'] == 'Yes']
    return len(students)


#%%
#Creates a course enrollment mapping for each course
st=maya.now()
tasks = []
resps = []

for i in range(0, len(course_ids), 15):
    tasks = []
    for course in course_ids[i:i+15]:
        if not course:
            continue
        tasks.append(get_memberships(course))
    resps += await asyncio.gather(*tasks)
course_enrl_map = dict(zip(course_ids, resps))
et=maya.now()
print(et-st)


#%%
#Applies the mappings across the dataframes
df['course_info'] = df['course_id'].apply(lambda x:course_map.get(x,{}), meta=('course_id','object'))
df['content_info'] = df.apply(axis=1,func=lambda row:content_map.get((row.course_id, row.content_id), {}), meta='object')
df['course_enrl'] = df['course_id'].apply(lambda x:course_enrl_map.get(x,0), meta=('course_id','int'))

df['courseId'] = df['course_info'].apply(lambda x: x.get('courseId',''), meta=('course_info','str'))
df['courseDesc'] = df['course_info'].apply(lambda x:x.get('description',''), meta=('course_info','str'))
df['courseName'] = df['course_info'].apply(lambda x:x.get('name',''), meta=('course_info','str'))


#%%
def get_dept(row):
    if '4192' not in row.courseId:
        return 'NAC'
    
    dept = row.courseName.split('-')[1].split()[0]
    return dept


#%%
df['dept'] = df.apply(get_dept, axis=1, meta='str')


#%%
df.head()

#%% [markdown]
# # Applying visualizations
# They are simple but take a good amount of time to compute.

#%%
df.groupby(['week','browser']).sum().hvplot(x='week', y='pageviews', by='browser')


#%%
df[df['browser']=='Edge'].groupby(['week','dept']).sum().hvplot.heatmap(x='week',y='dept',C='pageviews', height=800)


#%%
df['norm_pageviews'] = df['pageviews'] / df['course_enrl']


#%%
df[df['browser']=='Edge'].groupby(['week','dept']).sum().hvplot.heatmap(x='week',y='dept',C='norm_pageviews', height=800)


#%%
df.to_csv('data/computed_data*.csv', )


#%%
df2 = dd.read_csv('data/computed_data*.csv')


#%%
len(df2)


#%%
df[(df['browser']=='Edge') & df['dept'].isin(['ENGL','PSYC'])].groupby(['week','courseId']).sum().hvplot.heatmap(x='week',y='courseId',C='pageviews', height=800)

#%% [markdown]
# # Actionable Data
# With this overview, we can go on to use BbRest to pull additional information that would be helpful to make a business change, and measure this change.

#%%
async def get_instructors(courseId):
    tasks = []
    resps = []
    for i in range(0,1600,200):
        tasks.append(bb.GetCourseMemberships(courseId, 
                                             params={'offset':i}, 
                                             asynch=True))
    resps = await asyncio.gather(*tasks)
    results = [resp['results'] for resp in resps]
    memberships = [item for sublist in results for item in sublist]
    instructors = [membership for membership 
            in memberships
            if membership['courseRoleId'] == 'Instructor' 
            and membership['availability']['available'] == 'Yes']
    return instructors


#%%
instructors = await get_instructors('4192-79133')


#%%
for instructor in instructors:
    user_info = bb.GetUser(instructor['userId']).json()
    course_info = bb.GetCourse(instructor['courseId']).json()
    
    last = user_info['name']['family']
    first = user_info['name']['given']
    email = user_info['contact']['email']
    course = course_info['name']
    section = course_info['courseId']
    print(f'{first} {last} teachs {course}, section {section} and can be reaced at {email}\n')
    


#%%



