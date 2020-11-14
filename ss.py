from scipy.optimize import linear_sum_assignment as la
import numpy as np
import scipy
import pyodbc
conx_string = "driver={SQL SERVER}; server=DESKTOP-6LENMH4\SQLEXPRESS;database=CZ2006;"


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
    print("preferencelist ="+ str(preferencelist))
    # print("prefdict ="+ str(prefdict)
    return preferencelist  


cost = np.array([[0, 0, 5], [0, 1, 3], [3, 2, 2]])
preferencelist =np.array(getPrefByProjectID('2'))
print(preferencelist)

row_id, col_id = la(preferencelist)
print("member list ="+ str(row_id))
print("task list ="+ str(col_id))