from flask import Flask, render_template, request, session, flash, redirect, url_for
import pyodbc, string, random, hashlib
from flask_mail import Mail, Message
from datetime import datetime
from scipy.optimize import linear_sum_assignment as la
import numpy as np
import scipy
import json

app = Flask(__name__)
app.secret_key = 'ABCDEFG'

# Database connection 
#conx_string = "driver={SQL SERVER}; server=aa14ghc88ioxf82.ci9f7zusg4md.ap-southeast-1.rds.amazonaws.com; database=CZ2006;UID=admin;PWD=9khnaai4"
#conx_string = "driver={SQL SERVER}; server=DESKTOP-6LENMH4\SQLEXPRESS;database=CZ2006;"

conx_string = "driver={SQL SERVER}; server=DESKTOP-6L4758E\SQLEXPRESS;database=CZ2006;"

# Nav bar page change
@app.route("/")

# Before Login pages

@app.route("/Login", methods=['GET', 'POST'])
def Login():
    if request.method == 'POST':
        email = request.form["userEmail"]
        password = request.form["userPassword"]
        hashedpw= str2hash(password)
        #check if email && password == user table data
        found_user = False
        try:
            found_user = checkLogin(email,hashedpw)
        except:
            pass
        if found_user:
            #store username into a session to be called in html
            session["userName"] = getFullName(email)
            session["email"] = email
            projectsList = getProjectsByUser(email)
            roleType = "All"
            return render_template('ViewProject.html', projectsList = projectsList, roleType = roleType)

        else:
            flash("Incorrect username or password", "info")
            return render_template("Login.html")
    else:
        session.clear()
        print("session cleared")
        return render_template('Login.html')


@app.route("/SignUp", methods=['GET', 'POST'])
def SignUp():
    if request.method == 'POST':
        userEmail = request.form["userEmail"]
        if checkEmailExists(userEmail):
            flash('Email already registered!')
            return render_template('SignUp.html')
        else:
            userFirstName = request.form["userFirstName"]
            userLastName = request.form["userLastName"]
            userPassword = request.form["userPassword"]
            # session["userName"] = getFullName(userEmail)
            # session["email"] = userEmail

            #Store into database
            hashedpw = str2hash(userPassword)
            updateUser(userEmail,hashedpw,userFirstName,userLastName) 
            flash('Account Created!')
            session["userName"] = getFullName(userEmail)
            session["email"] = userEmail
            return render_template('ViewProject.html')
    
    else:
        return render_template('SignUp.html')


@app.route("/GenerateReport", methods=['GET', 'POST'])
def GenerateReport():
    if request.method == "POST":
        projectID= request.form["projectId"]
        print(projectID)
        grpSummary= getSummaryDict(projectID)
        # print(grpSummary)
        leader= getLeaderByProjectID(projectID)
        datasets = getDataSet(projectID)
        labels = getLabels(projectID)
        totalTasks = 0
        for d in datasets:
            totalTasks+=d
        print(datasets, json.dumps(labels))

    return render_template('GenerateReport.html', grpSummary= grpSummary, leader=leader, datasets=datasets, labels=json.dumps(labels), totalTasks=totalTasks)

@app.route("/ViewProject", methods=['GET', 'POST'])
def ViewProject():
    # Get projects by user email  
    projectsList = getProjectsByUser(session['email'])
    roleType = "All"
    if request.method == "POST" :             
        purpose = request.form['purpose']

        if purpose == 'filter':
            roleType = request.form['roleType']
            if(roleType == 'Leader'):
                projectsList =  list(v for v in projectsList if v[2] == True)          
            elif(roleType == 'Member'):
                projectsList =  list(v for v in projectsList if v[2] == False)
        else:
            # dismiss team
            projectId = request.form['projectId']
            deleteUserProject(projectId)
            projectsList = getProjectsByUser(session['email'])

    return render_template('ViewProject.html', projectsList = projectsList, roleType = roleType)

@app.route("/ViewRequest", methods=['GET' , 'POST'])
def ViewRequest():
    if request.method == "POST":
        ProjectID = request.form['projectId']
        email = session["email"]

        if request.form['purpose'] == "accept":
            acceptInv(ProjectID,email)
            requestlist = getRequestList(email)
            return render_template('ViewRequest.html', requestlist=requestlist)

        if request.form['purpose'] == "dismiss":
            declineInv(ProjectID,email)
            requestlist = getRequestList(email)
            return render_template('ViewRequest.html', requestlist=requestlist)

    email = session["email"]
    requestlist = getRequestList(email)
    return render_template('ViewRequest.html', requestlist=requestlist)


@app.route("/CreateProject", methods=['GET', 'POST'])
def CreateProject():
    currentUser = session['email']
    usersList = allUser(currentUser)

    return render_template('CreateProject.html', usersList = usersList)

@app.route("/TaskDelegation", methods=['GET', 'POST'])
def TaskDelegation():
    currentUser = session['email']
    usersList = allUser(currentUser)

    if request.method == "POST":
        purpose = request.form["purpose"]
        if(purpose == "check"):
            # create project, insert project members
            allEmails = request.form["emails"]
            teamName = request.form["teamName"]
            description = request.form["description"]
            projectName = request.form["projectName"]

            errors = []       
            if(projectName.strip() == ''):
                errors.append(" Project Name")
            
            if(description.strip() == ''):
                errors.append(" Description")

            if teamName.strip() == '':
                errors.append(" Team Name")
                        
            if(allEmails.strip() == ''):
                errors.append(" invite members.")

            noOfMembers = 0
            # has error
            if(len(errors) != 0):
                i = 0
                allErrors = "Please enter"
                for x in errors:          
                    if('invite' in x):
                        allErrors = allErrors[0:len(allErrors)-1]
                        allErrors += " and Invite Members."
                    else:
                        if(i == len(errors) - 1):
                            allErrors += x
                        else:
                            allErrors += x  + ","       
                    i += 1

                flash(allErrors)
                return render_template('CreateProject.html', usersList = usersList)
            else:
                # has no error
                # count number of members invited

                # insert project
                insertProject(projectName, description, teamName)
                projectId = getProjectID(projectName, description, teamName)[0][0]

                # insert user project
                insertUserProject(currentUser, True, projectId)
                allEmails = allEmails.split(',')
                for email in allEmails:
                    insertUserProject(email, False, projectId)

                noOfMembers = len(allEmails) + 1
                # new project id inserted
                #session['ProjectID'] = projectId
                session['projectName'] = projectName
                session['teamName'] = teamName

            session['noOfMembers'] = noOfMembers
        elif (purpose=='delegate'):
            noOfMembers = session['noOfMembers']
            projectId = request.form['projectId']
            return render_template('TaskDelegation.html', usersList = usersList, noOfMembers=noOfMembers, projectId = projectId, purpose = purpose)
        else:
            # delegate task
            noOfMembers = session['noOfMembers'] 
            currentUser = session['email']
            # get tasks
            taskList = []
            projectId = request.form['projectId']
            for i in range(1, noOfMembers+1):
                task = request.form.get('taDescription' + str(i))
                taskList.append(task)
                # insert task into db
                insertTask(projectId, task)

            # POST method
            # Display tasks
            currentUserRole = getUserRoleByProjectID(projectId,currentUser)[0][2]

            return render_template('ManageProject.html', projectId = projectId, currentUser=currentUser, currentUserRole=currentUserRole, taskList = taskList, isAllocated=False, hasResult = False , hasIndicated = False, hasAllIndicated=False, purpose = 'backToManage')
            
           
    return render_template('TaskDelegation.html', usersList = usersList, noOfMembers=noOfMembers, projectId = projectId, purpose = purpose)

@app.route("/ManageProject", methods=['GET', 'POST'])
def ManageProject():
    currentUser = session['email']
    memberEmail = ''
    hasResult = False
    taskList = ''
    selectedRanks = ''
    projectLogList= []
    grpProjectLog =[]

    if request.method == "GET":    
        projectId = request.args.get("projectId")
        
        purpose = request.args.get("purpose")
        # if project id is not null, from view project's page
        if(projectId != None):   
            teamName = request.args.get("teamName")   
            projectName = request.args.get("projectName")
            session['teamName'] = teamName
            
            # current onclick project         
            session['projectName'] = projectName

        else:
            # from the task delegation page
            teamName = session['teamName']            
            projectId = request.form['projectId']
            projectName = session['projectName']
        
        # Get project member, is leader == true
        currentUserRole = getUserRoleByProjectID(projectId,currentUser)[0][2]
        # Display tasks
        taskList = getTasksByProjectID(projectId)
        noOfmembers = getNoOfMember(projectId)
        session['noOfMembers'] = noOfmembers
        
        # result has not been released
        try:
            isAllocated = list(v for v in taskList)[0][3]
            if(isAllocated == None):
                isAllocated = False
            else:
                # is allocated 
                taskList = getAllocationList(projectId)
                isAllocated = True
                session['taskID']=getUserTaskID(projectId,currentUser)
        except:
            usersList = allUser(currentUser)
            return render_template('TaskDelegation.html', usersList = usersList, noOfMembers=noOfmembers, projectId = projectId, purpose = "delegate")


        hasIndicated = checkHasIndicatedPreference(projectId, currentUser)
        if(hasIndicated):
            selectedRanks = getRankList(projectId, currentUser)

        hasAllIndicated = checkHasAllUserIndicate(projectId)
        if(hasAllIndicated):
            userAllocation(projectId)
        
    else:
        purpose = request.form['purpose']
        print(purpose)
        teamName = session['teamName'] 
        print(teamName)
        projectId = request.form['projectId']
        print(projectId)
        projectName = session['projectName']
        print(projectName)

        userRoleTemp = getUserRoleByProjectID(projectId,currentUser)
       
        if(len(userRoleTemp) == 0):
            pass
        else:
            currentUserRole = getUserRoleByProjectID(projectId,currentUser)[0][2]

        # Display tasks
        taskList = getTasksByProjectID(projectId)

        isAllocated = list(v for v in taskList)[0][3]
        if(isAllocated == None):
    
            isAllocated = False      
        else:
            isAllocated = True
            taskList = getAllocationList(projectId)

        # get options
        selectedRanks = request.form.getlist('ddlRank')

        if(len(selectedRanks) == 0):
            selectedRanks = getRankList(projectId, currentUser)
       
        if(purpose == 'indicatePreference'):
            i = 0
            # Indicate user preference
            for task in taskList:
                insertUserPreference(currentUser, task[0], selectedRanks[i])
                i += 1
        hasIndicated = checkHasIndicatedPreference(projectId, currentUser)
        print(1)
        hasAllIndicated = checkHasAllUserIndicate(projectId)
        if(hasAllIndicated):
            userAllocation(projectId)
            isAllocated = True
            hasResult = True
            taskList = getTaskAllocated(projectId)
        if (purpose=='newLog'):
            taskid = session['taskID']
            print(taskid)
            log = request.form['log']
            insertTaskLog(taskid,log)
            flash('Log updated!')
      

    projectLogList = getMemberProjectLog(projectId,currentUser)
    print(projectLogList)
    grpProjectLog = getGrpProjectLog(projectId)
    return render_template('ManageProject.html',projectName=projectName, teamName = teamName, projectId = projectId, 
    currentUser=currentUser, currentUserRole=currentUserRole, memberEmail=memberEmail, taskList = taskList, 
    isAllocated=isAllocated, hasResult = hasResult, selectedRanks=selectedRanks, hasIndicated = hasIndicated, 
    hasAllIndicated=hasAllIndicated, purpose = purpose, projectLogList=projectLogList, grpProjectLog=grpProjectLog)
# @app.route("/ManageProject", methods=['GET', 'POST'])
# def ManageProject():
#     currentUser = session['email']
#     memberEmail = ''
#     hasResult = False
#     taskList = ''
#     selectedRanks = ''

#     if request.method == "GET":    
#         projectId = request.args.get("projectId")
#         purpose = request.args.get("purpose")
#         # if project id is not null, from view project's page
#         if(projectId != None):   
#             teamName = request.args.get("teamName")   
#             projectName = request.args.get("projectName")
#             session['teamName'] = teamName
            
#             # current onclick project         
#             session['projectName'] = projectName

#         else:
#             # from the task delegation page
#             teamName = session['teamName']            
#             projectId = request.form['projectId']
#             projectName = session['projectName']
#         # Get project member, is leader == true
#         currentUserRole = getUserRoleByProjectID(projectId,currentUser)[0][2]

#         # Display tasks
#         taskList = getTasksByProjectID(projectId)
        
#         # result has not been released
#         isAllocated = list(v for v in taskList)[0][3]
#         if(isAllocated == None):
#             isAllocated = False
#         else:
#             # is allocated 
#             taskList = getAllocationList(projectId)
#             isAllocated = True

#         hasIndicated = checkHasIndicatedPreference(projectId, currentUser)
#         if(hasIndicated):
#             selectedRanks = getRankList(projectId, currentUser)
        
#         hasAllIndicated = checkHasAllUserIndicate(projectId)

#     else:
#         purpose = request.form['purpose']
#         teamName = session['teamName'] 
#         if (purpose=='newLog'):
#             taskid = request.form['TaskID']
#             log = request.form['log']
#             insertTaskLog(taskid,log)
#             flash('Log updated!')
#         projectId = request.form['projectId']
#         projectName = session['projectName']

#         userRoleTemp = getUserRoleByProjectID(projectId,currentUser)
       
#         if(len(userRoleTemp) == 0):
#             pass
#         else:
#             currentUserRole = getUserRoleByProjectID(projectId,currentUser)[0][2]

#         # Display tasks
#         taskList = getTasksByProjectID(projectId)
#         hasAllIndicated = checkHasAllUserIndicate(projectId)
        
#         isAllocated = list(v for v in taskList)[0][3]
#         if(isAllocated == None):
#             isAllocated = False      
#         else:
#             isAllocated = True
#             taskList = getAllocationList(projectId)
        
#         if(purpose == 'indicate'):
#             # get options
#             selectedRanks = request.form.getlist('ddlRank')

#             if(len(selectedRanks) == 0):
#                 selectedRanks = getRankList(projectId, currentUser)
        
#             if(purpose != 'backToManage'):
#                 i = 0
#                 # Indicate user preference
#                 for task in taskList:
#                     insertUserPreference(currentUser, task[0], selectedRanks[i])
#                     i += 1
        
#         hasIndicated = checkHasIndicatedPreference(projectId, currentUser)
#     projectLogList = getMemberProjectLog(projectId,currentUser)
#     if(len(projectLogList) == 0):
#         isAllocated = False

#     grpProjectLog = getGrpProjectLog(projectId)
#     return render_template('ManageProject.html',projectName=projectName, teamName = teamName, projectId = projectId, currentUser=currentUser, currentUserRole=currentUserRole, memberEmail=memberEmail, taskList = taskList, isAllocated=isAllocated, hasResult = hasResult, selectedRanks=selectedRanks, hasIndicated = hasIndicated, hasAllIndicated=hasAllIndicated, purpose = purpose,  projectLogList=projectLogList, grpProjectLog=grpProjectLog)
    
@app.route("/ViewMembers", methods=['GET', 'POST'])
def ViewMembers(): 
    currentUser = session['email']
    memberEmail = ''

    if request.method == "POST":     
        # POST Method, remove team member
        teamName = session['teamName']     
        projectId = request.form['projectId']

        # View members
        projectName = session['projectName']
        purpose = request.form['purpose']
        print("1")

        if (purpose == "email"):
            print("1")
            recipient = request.form['email']
            print("1")
            RemindTeam(teamName,recipient)
            print("1")
            flash("Email sent!")
       
        elif(purpose == 'deleteMember') :
            memberEmail = request.form['memberEmail']    
            removeMember(projectId,memberEmail)     
        else:
            # view members
            pass 
    
    projectsList = getMembersByProjectID(projectId)
    currentUserRole = getcurrentUserRole(projectsList,currentUser)

    return render_template('ViewMembers.html',projectName=projectName, teamName = teamName, projectId = projectId, projectsList = projectsList, currentUser=currentUser, currentUserRole=currentUserRole, memberEmail=memberEmail)

def getcurrentUserRole(projectsList, currentUser):
    if(len(projectsList) != 0):   
        projectList = projectsList.copy()
        # get team 
        i = 0
        for t in projectList:
            if(t[2] == True):
                # is leader
                projectsList.pop(i)
                projectsList.insert(0,t)
            elif(t[1] == currentUser):
                # is current user
                projectsList.pop(i)
                projectsList.insert(0,t)
            i += 1

        currentUserRole = list(v[2] for v in projectsList if v[1] == currentUser)[0]

    return currentUserRole


def checkEmailExists(email):
    emailList=[]
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute('SELECT Email FROM CZ2006.dbo.[User]')
        data = cursor.fetchall()
        for row in data:
            emailList.append(row[0])
        # print(emailList)
        if (email in emailList):
            return True
        else: 
            return False

def getFullName(email):
    name=''
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute('SELECT FirstName, LastName FROM CZ2006.dbo.[User] Where Email=?', email)
        data = cursor.fetchall()
        for row in data[0]:
            name += row
        return name

def str2hash(string):
    result = hashlib.md5(string.encode())
    return result.hexdigest()

def checkLogin(email,password):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute('SELECT Password FROM CZ2006.dbo.[User] Where Email=?', email)
        data = cursor.fetchall()
        if (password == data[0][0]):
            return True
        else: 
            return False

def acceptInv(projectID,email):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("Update UserProject set [Status]='A' where ProjectID=? And UserEmail=?" , projectID, email)

def declineInv(projectID,email):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("Delete from UserProject where ProjectID=? And UserEmail=?" , projectID, email)


def insertProject(name, description, teamName):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("INSERT INTO Project (Name, Description, TeamName) VALUES(?,?,?)", (name, description, teamName))

def insertTask(projectId, description):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("INSERT INTO Task (ProjectID, Description) VALUES(?,?)", (projectId, description))

def getProjectID(name, description, teamName):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from  Project where Name = ? and Description = ? and TeamName = ?" , name, description, teamName)
        data = cursor.fetchall()
    
    return data

def insertUserProject(email, isLeader, projectID):
    
    if(isLeader):
        status = ''
    else:
        status = 'P'
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("INSERT INTO UserProject (UserEmail, isLeader, Status, ProjectID) VALUES(?,?,?,?)", (email, isLeader, status, projectID))

def getProjectsByUser(email):
    teamList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from  UserProject ut inner join Project t on ut.ProjectID = t.ProjectID where UserEmail = ? and (Status = 'A' or isLeader = 'true')" , email) 
        data = cursor.fetchall()

        for row in data:
            teamList.append(row)

    return teamList

def getProjectsByProjectID(projectId):
    teamList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from  UserProject ut inner join Project t on ut.ProjectID = t.ProjectID inner join dbo.[User] u on u.Email = ut.UserEmail where ut.ProjectID = ? and (Status = ? or Status = '')" , projectId, 'A') 
        data = cursor.fetchall()

        for row in data:
            teamList.append(row)

    return teamList

def getMembersByProjectID(projectId):
    teamList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from  UserProject ut inner join Project t on ut.ProjectID = t.ProjectID inner join dbo.[User] u on u.Email = ut.UserEmail where ut.ProjectID = ?" , projectId) 
        data = cursor.fetchall()

        for row in data:
            teamList.append(row)

    return teamList  

def getUserRoleByProjectID(projectId, email):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from  UserProject where ProjectID = ? and UserEmail = ?" , projectId, email)
        data = cursor.fetchall()
        
        return data

def getUserPreference(projectId, email):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select Rank from UserPreference up inner join Task t on up.TaskID = t.TaskID where UserEmail = ? and ProjectID = ?" , email, projectId)
        data = cursor.fetchall()
        
        return data

def removeMember(projectId, memberEmail):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("DELETE FROM UserProject WHERE ProjectID = ? AND UserEmail = ?" , projectId, memberEmail) 

def allUser(currentUser):
    usersList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from [dbo].[User] where Email != ?" , currentUser) 
        data = cursor.fetchall()

        for row in data:
            usersList.append(row)    
    
    return usersList

def checkHasIndicatedPreference(projectId, email):
    hasIndicated = False
    userPreferenceList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from UserPreference up inner join Task t on up.TaskID = t.TaskID where t.ProjectID = ? and up.UserEmail = ? and t.UserAllocated is null" , projectId,email) 
        data = cursor.fetchall()

        for row in data:
            userPreferenceList.append(row)
    
    if(len(userPreferenceList) != 0):
        hasIndicated = True
    
    return hasIndicated

def getRankList(projectId, email):
    userPreferenceList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select up.Rank from UserPreference up inner join Task t on up.TaskID = t.TaskID where t.ProjectID = ? and up.UserEmail = ? and t.UserAllocated is null" , projectId,email) 
        data = cursor.fetchall()   

        for row in data:
            userPreferenceList.append(row[0])
    
    return userPreferenceList

def getTasksByProjectID(projectId):
    taskList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Task where ProjectID = ?" , projectId) 
        data = cursor.fetchall()

        for row in data:
            taskList.append(row)    
    
    return taskList

def insertUser(teamId, email, isManager, status):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("INSERT INTO UserTeam(TeamID, UserEmail, isManager, Status) VALUES(?,?,?,?)", (teamId, email, isManager, status))


def insertUserPreference(email, taskId, rank):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("INSERT INTO UserPreference(UserEmail, TaskID, Rank) VALUES(?,?,?)", (email, taskId, rank))

def getLabels(projectId):
    userNameLabels = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select (TRIM(u.FirstName)+' ' +u.LastName) as FullName from [dbo].[User] u inner join (select distinct(UserAllocated) from Project p inner join Task t on p.ProjectID = t.ProjectID inner join ProjectLog pl on t.TaskID = pl.TaskID where p.ProjectID = ?) as p on u.Email = p.UserAllocated" , projectId) 
        data = cursor.fetchall()

        for row in data:
            userNameLabels.append(row[0].strip())
    
    return userNameLabels

def getDataSet(projectId):
    userDataSet = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select count(*) as UserCount  from Project p inner join Task t on p.ProjectID = t.ProjectID inner join ProjectLog pl on t.TaskID = pl.TaskID where p.ProjectID = ? group by UserAllocated" , projectId) 
        data = cursor.fetchall()

        for row in data:
            userDataSet.append(row[0])      
    
    return userDataSet

def allTeams():
    teamsList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Project") 
        data = cursor.fetchall()

        for row in data:
            teamsList.append(row)    
    
    return teamsList

def deleteUserProject(projectId):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("DELETE FROM UserProject WHERE ProjectID = ?" , projectId) 
        
def getMemberInProject(projectId):
    userPreferenceList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from UserProject up where up.ProjectID = ? and Status = ?", projectId, 'A') 
        data = cursor.fetchall()

        for row in data:
            userPreferenceList.append(row)
    
    return userPreferenceList

def getNoOfMember(projectId):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select count(*) from UserProject where ProjectID = ?", projectId) 
        data = cursor.fetchall()
        print(data[0])
    
    return data[0][0]

def getTaskAllocated(projectId):
    userTaskList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Task t inner join [dbo].[User] u on t.UserAllocated = u.Email where t.ProjectID = ?", projectId) 
        data = cursor.fetchall()

        for row in data:
            userTaskList.append(row)
    
    return userTaskList

def getALLMemberInProject(projectId):
    userPreferenceList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from UserProject up where up.ProjectID = ?", projectId) 
        data = cursor.fetchall()

        for row in data:
            userPreferenceList.append(row)
    
    return userPreferenceList

def getUsersInPreference(projectId):
    userPreferenceList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select distinct(up.UserEmail) from UserPreference up inner join Task t on up.TaskID = t.TaskID where ProjectID = ?", projectId) 
        data = cursor.fetchall()

        for row in data:       
            userPreferenceList.append(row[0])
    return userPreferenceList

def checkHasAllUserIndicate(projectId):
    membersList = getALLMemberInProject(projectId)
    # print(membersList)
    indicatedUserList = getUsersInPreference(projectId)
    # print(indicatedUserList)
    
    for member in membersList:
        if(member[1] not in indicatedUserList):
            return False

    return True

def getAllocationList(projectId):
    userAllocationList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Task t inner join [dbo].[User] u on t.UserAllocated = u.Email where ProjectID = ?", projectId) 
        data = cursor.fetchall()

        for row in data:       
            userAllocationList.append(row)
    return userAllocationList

def getUserTaskID(projectId,email):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Task  where ProjectID=? and UserAllocated=? ", projectId, email) 
        data = cursor.fetchall()
        return data[0][0]

def RemindTeam(teamName, email):
#    query = 'SELECT t1.UserEmail, t1.ScheduleName, t1.TeamName,  t1.Deadline, t1.ScheduleID FROM (SELECT ut.UserEmail, s.ScheduleID, ut.TeamID, t.TeamName,  s.ScheduleName, s.Deadline FROM dbo.UserTeam AS ut INNER JOIN [dbo].[Team] as t on ut.TeamID = t.TeamID INNER JOIN [dbo].[Schedule] AS s on t.TeamID = s.TeamID WHERE (GETDATE() BETWEEN DATEADD(day, -7, s.Deadline) AND s.Deadline) AND s.CheckSentMail = 0) t1 LEFT JOIN (SELECT s.TeamID, s.ScheduleID, uso.ShiftID, uso.Email FROM UserShiftOption AS uso INNER JOIN ShiftOption AS so ON uso.ShiftID = so.ShiftID INNER JOIN Schedule AS s ON so.ScheduleID = s.ScheduleID WHERE (GETDATE() BETWEEN DATEADD(day, -7, s.Deadline) AND s.Deadline) AND s.CheckSentMail = 0) t2 ON (t1.TeamID = t2.TeamID AND t1.UserEmail = t2.Email AND t1.ScheduleID = t2.ScheduleID) WHERE t2.TeamID IS NULL'
    emailList = [email]
    # print(emailList)
    # with pyodbc.connect(conx_string) as conx:
    #     cursor = conx.cursor()
    #     cursor.execute("select UserEmail from UserProject where ProjectID = ? and Status ='A' " , projectID) 
    #     data = cursor.fetchall()
    #     for row in data:
    #         emailList.append(row[0])
    #     print(emailList)
    # with pyodbc.connect(conx_string) as conx:
    #     cursor = conx.cursor()
    #     cursor.execute("select TeamName from Project where ProjectID = ?", projectID) 
    #     data = cursor.fetchall()
    #     teamName= data[0][0]
    try:
        with app.app_context():
            app.config['DEBUG'] = True 
            app.config['TESTING'] = False
            app.config['MAIL_SERVER']='smtp.gmail.com'
            app.config['MAIL_PORT'] = 465
            app.config['MAIL_USERNAME'] = 'formailsendingapp@gmail.com'
            app.config['MAIL_PASSWORD'] = 'NTU2006!'
            app.config['MAIL_DEFAULT_SENDER'] = 'formailsendingapp@gmail.com'
            app.config['MAIL_USE_TLS'] = False
            app.config['MAIL_USE_SSL'] = True
            # for email in emailList:
            mail = Mail(app) 
            msg = Message('(Reminder) Schedule deadline!', recipients= emailList)
            msg.body = 'Dear user, \n\nThis is a reminder for you to update your progress on your part of the project in team ' + str(teamName) + '. \n\nThank you'
            mail.send(msg)
        return True
    except:
        pass
    return False

def updateUser(email, password, FirstName, LastName):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        insert_query = ''' INSERT INTO CZ2006.dbo.[User](Email, Password, FirstName, LastName)
                            VALUES(?,?,?,?)'''
        values = (email, password, FirstName, LastName)
        cursor.execute(insert_query,values)


def getMemberProjectLog(ProjectId,memberemail):
    projectlog= []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Task t inner join ProjectLog pl on t.TaskID=pl.TaskID where ProjectID=? and UserAllocated=? order by ProjectLogID desc", ProjectId, memberemail)
        data = cursor.fetchall()
        # print(data)
        for row in data:
            log = [row[0]]
            log.append(row[2])
            log.append(row[6])
            log.append(row[7])
            projectlog.append(log)
        # print(projectlog)
        return projectlog

def getGrpProjectLog(ProjectId):
    projectlog= []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Task t inner join ProjectLog pl on t.TaskID=pl.TaskID where ProjectID=? order by ProjectLogID desc", ProjectId)
        data = cursor.fetchall()
        # print(data)
        for row in data:
            log = [row[0]]
            log.append(row[2])
            log.append(row[3])
            log.append(row[6])
            log.append(row[7])
            projectlog.append(log)
        # print(projectlog)
        return projectlog

def insertTaskLog(taskId, log):
    currentdate = datetime.today().strftime('%Y-%m-%d')
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("INSERT INTO ProjectLog(TaskID,[Log],CreationDate) VALUES(?,?,?)", (taskId, log, currentdate))


def getRequestList(email):
    reqList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select Name,TeamName,UserEmail, p.ProjectID from Project p inner join UserProject up on p.ProjectId = up.ProjectID where p.ProjectID in ( SELECT p1.ProjectID FROM UserProject u1 inner join Project p1 on u1.ProjectID=p1.ProjectID Where UserEmail=? AND isLeader = 0 AND Status='P') and up.isLeader = 'true'", email)
        data = cursor.fetchall()
        for row in data:
            reqList.append(row)
        # print(reqList)
    return reqList
def getDistinctMemberList(projectId):
    membersList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select distinct(UserEmail) from UserPreference up inner join Task t on up.TaskID = t.TaskID where ProjectID=? order by UserEmail desc" , projectId) 
        data = cursor.fetchall()
        for row in data:
            membersList.append(row[0])

    return membersList

def getTaskList(projectId):
    taskIndexList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select distinct(TaskID) from Task where ProjectID = ?" , projectId) 
        data = cursor.fetchall()
        for row in data:
            taskIndexList.append(row[0])

    return taskIndexList

def getLeaderByProjectID(projectId):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from  UserProject ut inner join Project t on ut.ProjectID = t.ProjectID inner join dbo.[User] u on u.Email = ut.UserEmail where ut.ProjectID = ?" , projectId) 
        data = cursor.fetchall()

        for row in data:
            if (row[2] ==True):
                return row[1]

def updateUserAllocated(userEmail, projectId, taskId):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("UPDATE Task SET UserAllocated = ? where ProjectID = ? and TaskID = ?",userEmail , projectId, taskId) 

def getPrefByProjectID(projectId):
    preferencelist = []
    prefdict ={}
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select UserEmail,[Rank] from UserPreference up inner join Task t on up.TaskID = t.TaskID where ProjectID=?" , projectId) 
        data = cursor.fetchall()
        for row in data:
            if row[0] in prefdict:
                prefdict[row[0]].append(row[1])
            else:
                prefdict[row[0]]= [row[1]]
    for keys in prefdict:
        preferencelist.append(prefdict[keys])
    return preferencelist 

def getSummaryDict(projectID):
    summaryDict = {}
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Task t inner join ProjectLog pl on t.TaskID=pl.TaskID where ProjectID=? order by pl.TaskID, ProjectLogID", projectID)
        data = cursor.fetchall()
        # print(data)
        for row in data:
            if row[3] in summaryDict:
                summaryDict[row[3]][row[2]].append({row[6]:row[7]})
            else:
                summaryDict[row[3]]= {row[2]:[{row[6]:row[7]}]}

        # print(summaryDict)
        return summaryDict

def userAllocation(projectId):
    cost = np.array([[0, 0, 5], [0, 1, 3], [3, 2, 2]])
    preferencelist =np.array(getPrefByProjectID(projectId))

    row_id, col_id = la(preferencelist)

    membersList = getDistinctMemberList(projectId)
    taskIndexList = getTaskList(projectId)

    for index in row_id:
        memberEmail = membersList[index]
        taskIndex = col_id[index]
        taskId = taskIndexList[taskIndex]

        updateUserAllocated(memberEmail, projectId, taskId)

if __name__ == '__main__':
    app.run(debug=True)
