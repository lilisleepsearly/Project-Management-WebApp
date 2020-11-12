from flask import Flask, render_template, request, session, flash, redirect, url_for
import pyodbc, string, random, hashlib

app = Flask(__name__)
app.secret_key = 'ABCDEFG'

# Database connection (change to your own connection string)
# conx_string = "driver={SQL SERVER}; server=aa14ghc88ioxf82.ci9f7zusg4md.ap-southeast-1.rds.amazonaws.com; database=CZ2006;UID=admin;PWD=9khnaai4"
conx_string = "driver={SQL SERVER}; server=LAPTOP-FEUAEVTE\SQLEXPRESS;database=CZ2006;"

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
            session["userName"] = getFullName(userEmail)
            session["email"] = userEmail

            #Store into database
            hashedpw = str2hash(userPassword)
            updateUser(userEmail,hashedpw,userFirstName,userLastName) 
            flash('Account Created!')
            return render_template('ViewProject.html')
    
    else:
        return render_template('SignUp.html')


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
            projectID = session['projectID']
            deleteUserProject(projectID)
            projectsList = getProjectsByUser(session['email'])

    return render_template('ViewProject.html', projectsList = projectsList, roleType = roleType)

@app.route("/ViewRequest", methods=['GET' , 'POST'])
def ViewRequest():
    if request.method == "POST":
        ProjectID = request.form['ProjectID']
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

                noOfMembers = len(allEmails) + 1
                session['ProjectID'] = projectId
                session['projectName'] = projectName
                session['teamName'] = teamName

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
    currentUser = session['email']
    memberEmail = ''
    hasResult = False
    taskList = ''
    selectedRanks = ''

    if request.method == "GET":    
        projectID = request.args.get("projectID")
        # on click from the manage/view project info page
        
        # if project id is not null, from view project's page
        if(projectID != None):   
            teamName = request.args.get("teamName")   
            projectName = request.args.get("projectName")
            session['teamName'] = teamName

            # current onclick project
            session['projectID'] = projectID
            session['ProjectID'] = projectID
            session['projectName'] = projectName
        else:
            teamName = session['teamName']            
            projectID = session['ProjectID'] 
            projectName = session['projectName']
            
        if(projectID == None):
            projectID = session['ProjectID']
        
    
        # back button

        # Get project member
        currentUserRole = getUserRoleByProjectID(projectID,currentUser)[0][2]

        # Display tasks
        taskList = getTasksByProjectID(projectID)
        
        isAllocated = list(v for v in taskList)[0][3]
        if(isAllocated == None):
            isAllocated = False
        
        hasIndicated = checkHasIndicatedPreference(projectID, currentUser)
        if(hasIndicated):
            selectedRanks = getRankList(projectID, currentUser)
        
        hasAllIndicated = checkHasAllUserIndicate(projectID)
        print("get")
        print(projectID, hasAllIndicated, hasIndicated)
    else:
        
        purpose = request.form['purpose']
        teamName = session['teamName'] 
        
        if(purpose == "delegateTask"):
            projectID = session['ProjectID'] 
            print("deletgateTask" , projectID)
        else:
            projectID = session['ProjectID'] 
            print("other project" , projectID)

        projectName = session['projectName']
        print(projectID)
        userRoleTemp = getUserRoleByProjectID(projectID,currentUser)
       
        if(len(userRoleTemp) == 0):
            pass
        else:
            currentUserRole = getUserRoleByProjectID(projectID,currentUser)[0][2]
        # Display tasks
        taskList = getTasksByProjectID(projectID)
        hasAllIndicated = checkHasAllUserIndicate(projectID)
        
        isAllocated = list(v for v in taskList)[0][3]
        if(isAllocated == None):
            isAllocated = False
    
        # get options
        selectedRanks = request.form.getlist('ddlRank')
       
        i = 0
        # Indicate user preference
        for task in taskList:
            insertUserPreference(currentUser, task[0], selectedRanks[i])
            i += 1
        
        hasIndicated = checkHasIndicatedPreference(projectID, currentUser)
        print("post")
        print(projectID, hasAllIndicated, hasIndicated)
    
    return render_template('ManageProject.html',projectName=projectName, teamName = teamName, projectID = projectID, currentUser=currentUser, currentUserRole=currentUserRole, memberEmail=memberEmail, taskList = taskList, isAllocated=isAllocated, hasResult = hasResult, selectedRanks=selectedRanks, hasIndicated = hasIndicated, hasAllIndicated=hasAllIndicated)
    
@app.route("/ViewMembers", methods=['GET', 'POST'])
def ViewMembers(): 
    currentUser = session['email']
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

        print(projectsList)
        currentUserRole = list(v[2] for v in projectsList if v[1] == currentUser)[0]
    # else:
    #     currentUserRole = getUserRoleByProjectID(projectID,currentUser)[0][2]

    return render_template('ViewMembers.html',projectName=projectName, teamName = teamName, projectID = projectID, projectsList = projectsList, currentUser=currentUser, currentUserRole=currentUserRole, memberEmail=memberEmail)

def checkEmailExists(email):
    emailList=[]
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute('SELECT Email FROM CZ2006.dbo.[User]')
        data = cursor.fetchall()
        for row in data:
            emailList.append(row[0])
        print(emailList)
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
        
def getMemberInProject(projectId):
    userPreferenceList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from UserProject up where up.ProjectID = ? and Status = ?", projectId, 'A') 
        data = cursor.fetchall()

        for row in data:
            userPreferenceList.append(row)
    
    return userPreferenceList

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
    # with pyodbc.connect(conx_string) as conx:
    #     cursor = conx.cursor()
    #     cursor.execute("select * from Task t left join UserPreference up on t.TaskID=up.TaskID where ProjectID = ?", projectId) 
    #     data = cursor.fetchall()
    #     for row in data: 
    #         print(row[3])   
    #         if(row[3] is None):
    #             return False
    # return True
    membersList = getALLMemberInProject(projectId)
    print(membersList)
    indicatedUserList = getUsersInPreference(projectId)
    print(indicatedUserList)
    
    for member in membersList:
        if(member[1] not in indicatedUserList):
            return False
            # print(member[1])

    return True

def RemindTeam(teamName, email):
#    query = 'SELECT t1.UserEmail, t1.ScheduleName, t1.TeamName,  t1.Deadline, t1.ScheduleID FROM (SELECT ut.UserEmail, s.ScheduleID, ut.TeamID, t.TeamName,  s.ScheduleName, s.Deadline FROM dbo.UserTeam AS ut INNER JOIN [dbo].[Team] as t on ut.TeamID = t.TeamID INNER JOIN [dbo].[Schedule] AS s on t.TeamID = s.TeamID WHERE (GETDATE() BETWEEN DATEADD(day, -7, s.Deadline) AND s.Deadline) AND s.CheckSentMail = 0) t1 LEFT JOIN (SELECT s.TeamID, s.ScheduleID, uso.ShiftID, uso.Email FROM UserShiftOption AS uso INNER JOIN ShiftOption AS so ON uso.ShiftID = so.ShiftID INNER JOIN Schedule AS s ON so.ScheduleID = s.ScheduleID WHERE (GETDATE() BETWEEN DATEADD(day, -7, s.Deadline) AND s.Deadline) AND s.CheckSentMail = 0) t2 ON (t1.TeamID = t2.TeamID AND t1.UserEmail = t2.Email AND t1.ScheduleID = t2.ScheduleID) WHERE t2.TeamID IS NULL'
    emailList = [email]
    print(emailList)
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


def getRequestList(email):
    reqList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        # cursor.execute("SELECT * FROM CZ2006.dbo.UserProject Where UserEmail=? AND isLeader = 0 AND Status='P'" , email )
        cursor.execute("select Name,TeamName,UserEmail, p.ProjectID from Project p inner join UserProject up on p.ProjectId = up.ProjectID where p.ProjectID in ( SELECT p1.ProjectID FROM UserProject u1 inner join Project p1 on u1.ProjectID=p1.ProjectID Where UserEmail=? AND isLeader = 0 AND Status='P') and up.isLeader = 'true'", email)
        # cursor.execute("SELECT p1.Name, p1.TeamName, p1.LeaderEmail FROM UserProject u1 inner join Project p1 on u1.ProjectID=p1.ProjectID Where UserEmail=? AND isLeader = 0 AND Status='P'" , email )
        # not sure how to access TeamName with a nested query so im just using TeamID now
        # cursor.execute('SELECT TeamName FROM CZ2006.dbo.Team WHERE TeamID= (SELECT TeamID FROM CZ2006.dbo.UserTeam Where UserEmail=? AND isManager = 1)', email)
        data = cursor.fetchall()
        for row in data:
            reqList.append(row)
        print(reqList)
    return reqList


if __name__ == '__main__':
    app.run()