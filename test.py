import pyodbc
from datetime import datetime
conx_string = "driver={SQL SERVER}; server=DESKTOP-6LENMH4\SQLEXPRESS;database=CZ2006;"


def insertTaskLog(taskId, log):
    currentdate = datetime.today().strftime('%Y-%m-%d')
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("INSERT INTO ProjectLog(TaskID,[Log],CreationDate) VALUES(?,?,?)", (taskId, log, currentdate))

def getProjectLog(ProjectId):
    projectlog= []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Task t inner join ProjectLog pl on t.TaskID=pl.TaskID where ProjectID=? order by CreationDate", ProjectId)
        data = cursor.fetchall()
        # print(data)
        for row in data:
            log = [row[2]]
            log.append(row[6])
            log.append(row[7])
            projectlog.append(log)
        print(projectlog)

def getMemberProjectLog(ProjectId,memberemail):
    projectlog= []
    with pyodbc.connect(conx_string) as conx:
        cursor = conx.cursor()
        cursor.execute("select * from Task t inner join ProjectLog pl on t.TaskID=pl.TaskID where ProjectID=? and UserAllocated=? order by CreationDate", ProjectId, memberemail)
        data = cursor.fetchall()
        # print(data)
        for row in data:
            log = [row[2]]
            log.append(row[6])
            log.append(row[7])
            projectlog.append(log)
        print(projectlog)



getProjectLog('1')
getMemberProjectLog('1','qw@gmail.com')