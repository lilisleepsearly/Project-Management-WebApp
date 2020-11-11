from flask import Flask, render_template, request, session, flash
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

@app.route("/NewSchedule", methods=['GET', 'POST'])
def NewSchedule():
    return render_template('NewSchedule.html')

@app.route("/ViewRequest", methods=['GET' , 'POST'])
def ViewRequest():
    return render_template('ViewRequest.html')

@app.route("/CreateProject", methods=['GET', 'POST'])
def CreateProject():
    currentUser = 'liyi@hotmail.com'
    usersList = allUser(currentUser)

    if request.method == "POST":
        allEmails = request.form["emails"]
        teamName = request.form["teamName"]
        description = request.form["description"]
        projectName = request.form["projectName"]
        
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

    return render_template('TaskDelegation.html')

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
    else:
        
        # POST Method, remove team member
        teamName = session['teamName']     
        projectID = session['projectID']
        memberEmail = request.form['memberEmail']
        projectName = request.form['projectName']
        removeMember(projectID,memberEmail)
        
    projectsList = getProjectsByProjectID(projectID)
    
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
    print(currentUserRole)
    return render_template('ViewMembers.html',projectName=projectName, teamName = teamName, projectID = projectID, projectsList = projectsList, currentUser=currentUser, currentUserRole=currentUserRole, memberEmail=memberEmail)

def getProjectsByUser(email):
    teamList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from  UserProject ut inner join Project t on ut.ProjectID = t.ProjectID where UserEmail = ?" , email) 
        data = cursor.fetchall()

        for row in data:
            teamList.append(row)

    return teamList

def getProjectsByProjectID(projectId):
    teamList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from  UserProject ut inner join Project t on ut.ProjectID = t.ProjectID inner join dbo.[User] u on u.Email = ut.UserEmail where ut.ProjectID = ?" , projectId) 
        data = cursor.fetchall()

        for row in data:
            teamList.append(row)

    return teamList

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

def insertUser(teamId, email, isManager, status):
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("INSERT INTO UserTeam(TeamID, UserEmail, isManager, Status) VALUES(?,?,?,?)", (teamId, email, isManager, status))

# def insertTeam(teamId, teamName):
#     with pyodbc.connect(conx_string) as conx:
#         cursor = conx.cursor()
#         cursor.execute("INSERT INTO Project(TeamID, TeamName) VALUES(?,?)", (teamId, teamName))

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