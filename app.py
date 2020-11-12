from flask import Flask, render_template, request, session, flash, redirect, url_for
import pyodbc, string, random

app = Flask(__name__)
app.secret_key = 'ABCDEFG'

# Database connection (change to your own connection string)
# conx_string = "driver={SQL SERVER}; server=aa14ghc88ioxf82.ci9f7zusg4md.ap-southeast-1.rds.amazonaws.com; database=CZ2006;UID=admin;PWD=9khnaai4"
conx_string = "driver={SQL SERVER}; server=DESKTOP-6L4758E\SQLEXPRESS;database=CZ2006;"

# Nav bar page change
@app.route("/")

# Before Login pages

@app.route("/Login", methods=['GET', 'POST'])
def Login():
    return render_template('Login.html')

@app.route("/SignUp", methods=['GET', 'POST'])
def SignUp():
    return render_template('SignUp.html')

@app.route("/ViewProject", methods=['GET', 'POST'])
def ViewProject():
    # Get projects by user email  
    projectsList = getProjectsByUser('liyi@hotmail.com')
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
            projectID = session['projectID']
            deleteUserProject(projectID)
            projectsList = getProjectsByUser('liyi@hotmail.com')

    return render_template('ViewProject.html', projectsList = projectsList, roleType = roleType)

@app.route("/ViewRequest", methods=['GET' , 'POST'])
def ViewRequest():
    return render_template('ViewRequest.html')

@app.route("/CreateProject", methods=['GET', 'POST'])
def CreateProject():
    currentUser = 'liyi@hotmail.com'
    usersList = allUser(currentUser)
        
        # insertTeam(teamId, teamName)
        # split by comma
        # emails = allEmails.split(",")
        # for email in emails :
        #     insertUser(teamId,email, False, 'P')
        
        # insertUser(teamId,currentUser, True, 'P')
        

    return render_template('CreateProject.html', usersList = usersList)

@app.route("/TaskDelegation", methods=['GET', 'POST'])
def TaskDelegation():
    currentUser = 'liyi@hotmail.com'
    usersList = allUser(currentUser)

    if request.method == "POST":
        purpose = request.form["purpose"]
        if(purpose != 'delegateTask'):
            # create project page
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
                noOfMembers = len(allEmails)
                session['ProjectID'] = projectId
            session['noOfMembers'] = noOfMembers
        else:
            # delegate task
            noOfMembers = session['noOfMembers'] 

            # get tasks
            tasksList = []
            for i in range(1, noOfMembers+1):
                task = request.form.get('taDescription' + str(i))
                tasksList.append(task)
                # insert task into db
                insertTask(session['ProjectID'], task)

            return redirect(url_for('ManageProject'))
           
    return render_template('TaskDelegation.html', usersList = usersList, noOfMembers=noOfMembers)

@app.route("/ManageProject", methods=['GET', 'POST'])
def ManageProject():
    currentUser = 'liyi@hotmail.com'
    memberEmail = ''
    hasResult = False
    taskList = ''
    selectedRanks = ''

    if request.method == "GET":    
        projectID = request.args.get("projectID")
        if(projectID != None):   
            teamName = request.args.get("teamName")   
            projectName = request.args.get("projectName")
            session['teamName'] = teamName
            session['projectID'] = projectID
            session['projectName'] = projectName
        else:
            teamName = session['teamName'] 
            projectID = session['ProjectID'] 
            projectName = session['projectName']
            
        if(projectID == None):
            projectID = session['ProjectID']
        
        # back button
        print("here" , projectID)
        # Get project member
        currentUserRole = getUserRoleByProjectID(projectID,currentUser)[0][2]
        print("or here?")
        # Display tasks
        taskList = getTasksByProjectID(projectID)
        
        isAllocated = list(v for v in taskList)[0][3]
        if(isAllocated == None):
            isAllocated = False
        
        hasIndicated = checkHasIndicatedPreference(projectID, currentUser)
        if(hasIndicated):
            selectedRanks = getRankList(projectID, currentUser)
    else:
        
        teamName = session['teamName'] 
        projectID = session['ProjectID'] 
        projectName = session['projectName']
        currentUserRole = getUserRoleByProjectID(projectID,currentUser)[0][2]
        # Display tasks
        taskList = getTasksByProjectID(projectID)
        
        isAllocated = list(v for v in taskList)[0][3]
        if(isAllocated == None):
            isAllocated = False
    
        # get options
        selectedRanks = request.form.getlist('ddlRank')
        print(taskList)
        i = 0
        # Indicate user preference
        for task in taskList:
            insertUserPreference(currentUser, task[0], selectedRanks[i])
            i += 1
        
        hasIndicated = checkHasIndicatedPreference(projectID, currentUser)
    
    return render_template('ManageProject.html',projectName=projectName, teamName = teamName, projectID = projectID, currentUser=currentUser, currentUserRole=currentUserRole, memberEmail=memberEmail, taskList = taskList, isAllocated=isAllocated, hasResult = hasResult, selectedRanks=selectedRanks, hasIndicated = hasIndicated)
    
@app.route("/ViewMembers", methods=['GET', 'POST'])
def ViewMembers(): 
    currentUser = 'liyi@hotmail.com'
    memberEmail = ''
    
    if request.method == "GET":       
        projectID = request.args.get("projectID")   
        teamName = request.args.get("teamName")   
        projectName = request.args.get("projectName")
        session['teamName'] = teamName
        session['projectID'] = projectID
        session['projectName'] = projectName
    else:
        # POST Method, remove team member
        teamName = session['teamName']     
        projectID = session['projectID']
        projectName = session['projectName']
        purpose = request.form['purpose']
        
        if(purpose == 'deleteMember') :
            memberEmail = request.form['memberEmail']         
            removeMember(projectID,memberEmail)
        
    projectsList = getProjectsByProjectID(projectID)
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
    else:
        currentUserRole = getUserRoleByProjectID(projectID,currentUser)[0][2]

    return render_template('ViewMembers.html',projectName=projectName, teamName = teamName, projectID = projectID, projectsList = projectsList, currentUser=currentUser, currentUserRole=currentUserRole, memberEmail=memberEmail)

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

def getUserRoleByProjectID(projectId, email):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from  UserProject where ProjectID = ? and UserEmail = ?" , projectId, email)
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
        
if __name__ == '__main__':
    app.run()