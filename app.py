from flask import Flask, render_template, request, session, flash, redirect
from flask_mail import Mail, Message
import pyodbc, string, random, hashlib

app = Flask(__name__)
app.secret_key = 'ABCDEFG'

# Database connection (change to your own connection string)
# conx_string = "driver={SQL SERVER}; server=aa14ghc88ioxf82.ci9f7zusg4md.ap-southeast-1.rds.amazonaws.com; database=CZ2006;UID=admin;PWD=9khnaai4"
# conx_string = "driver={SQL SERVER}; server=DESKTOP-6L4758E\SQLEXPRESS;database=CZ2006;"
conx_string = "Driver={SQL Server}; Server=LAPTOP-FEUAEVTE\SQLEXPRESS; Database=CZ2006; Trusted_Connection=yes;"
# Nav bar page change
@app.route("/")

# Before Login pages

@app.route("/Login", methods=['GET', 'POST'])
def Login():
    if request.method == 'POST':
        email = request.form["userEmail"]
        password = request.form["userPassword"]
        hashedpw= str2hash(password)
        print(hashedpw)
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
            print(session)
            return render_template('ViewProject.html')
        else:
            flash("Incorrect username or password", "info")
            return render_template("Login.html")
    else:
        return render_template('Login.html')


@app.route("/SignUp", methods=['GET', 'POST'])
def SignUp():
    if request.method == 'POST':
        userFirstName = request.form["userFirstName"]
        userLastName = request.form["userLastName"]
        userEmail = request.form["userEmail"]
        userPassword = request.form["userPassword"]
        session["userName"] = userFirstName

        #Store into database
        hashedpw = str2hash(userPassword)
        updateUser(userEmail,hashedpw,userFirstName,userLastName) 
        return render_template('Login.html')
    
    else:
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
        if request.form['purpose'] == "email":
            RemindTeam(projectID)
            flash("Email sent!")
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
        print(data[0][0])
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

def RemindTeam(projectID):
#    query = 'SELECT t1.UserEmail, t1.ScheduleName, t1.TeamName,  t1.Deadline, t1.ScheduleID FROM (SELECT ut.UserEmail, s.ScheduleID, ut.TeamID, t.TeamName,  s.ScheduleName, s.Deadline FROM dbo.UserTeam AS ut INNER JOIN [dbo].[Team] as t on ut.TeamID = t.TeamID INNER JOIN [dbo].[Schedule] AS s on t.TeamID = s.TeamID WHERE (GETDATE() BETWEEN DATEADD(day, -7, s.Deadline) AND s.Deadline) AND s.CheckSentMail = 0) t1 LEFT JOIN (SELECT s.TeamID, s.ScheduleID, uso.ShiftID, uso.Email FROM UserShiftOption AS uso INNER JOIN ShiftOption AS so ON uso.ShiftID = so.ShiftID INNER JOIN Schedule AS s ON so.ScheduleID = s.ScheduleID WHERE (GETDATE() BETWEEN DATEADD(day, -7, s.Deadline) AND s.Deadline) AND s.CheckSentMail = 0) t2 ON (t1.TeamID = t2.TeamID AND t1.UserEmail = t2.Email AND t1.ScheduleID = t2.ScheduleID) WHERE t2.TeamID IS NULL'
    emailList = []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select UserEmail from UserProject where ProjectID = ? and Status ='A' " , projectID) 
        data = cursor.fetchall()
        for row in data:
            emailList.append(row[0])
        print(emailList)
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select TeamName from Project where ProjectID = ?", projectID) 
        data = cursor.fetchall()
        teamName= data[0][0]
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