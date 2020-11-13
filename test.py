def setTeamDetails(details): 
    fields = details.split(',')
    print(fields)
    projectName = fields[0]
    teamName = fields[1]
    a= projectName
    b= teamName+"?"
    print(a)
    print(b)  

setTeamDetails('asd'+ ','+ 'ass')