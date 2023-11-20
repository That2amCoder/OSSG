import codegrade
import os
from getpass import getpass
import requests
import rich

def write_into_temp(content):
    with open("temp.txt", "a") as f:
        f.write(content)

def download_asg_setup():
    ghrepo = input("Enter the github repo of the framework: ")
    os.system("git clone " + ghrepo + " ./sandbox")
    # Copy the "./sandbox/repo/framework" folder to "./sandbox/framework"
    os.system("cp -r ./sandbox/" + os.listdir("./sandbox")[0] + "/framework ./sandbox/framework")
    os.system("rm -rf ./sandbox/" + os.listdir("./sandbox")[0])

print("NOTE: If you are using this script post codegrade disaster")
print("Then you need to use your username with a (1) at the end")
print("E.g if your username is 'johndoe', then your username is 'johndoe (1)'")

# Create a directory called "sandbox" in the current directory
#If it already exists, delete it and create a new one
if not os.path.exists("sandbox"):
    print("--- INSTALLING ---")
    print("NOTE: If you are using this script for the first time")
    print("Then you need to set a codegrade password at:")
    rich.print("https://vu.codegra.de/forgot/2f5725ae-4aac-461c-85f5-751ed7ca1342")
    os.mkdir("sandbox")
    input("Press enter to continue")
    open("temp.txt", "w").close()
    download_asg_setup()
    print("Done!")




print("")
usr = input("Enter your vunet username: ")
pwd = getpass("Enter your vunet password: ")
namedict = {}
frameworkpath = "./sandbox/framework"

with codegrade.login(
    username=usr,
    password=pwd,
    host="vu.codegra.de",
    tenant="Vrije Universiteit"
) as client:
    print("Logged in as", client.user.get().name)

    print("Do you want to restart the sandbox? (y/n):")
    if input("Enter y or n: ") == "y":
        os.system("rm -rf ./sandbox")
        download_asg_setup()
        print("Done!")
    
    # Get available ASSIGNMENTS
    assignments = client.assignment.get_all()
    print("Available assignments (From recent to oldest): ")
    x = 0
    for assignment in assignments:
        print("["+str(x)+"] "+assignment.name)
        x += 1
    id = int(input("Enter the number of the assignment you want to grade: "))
    if id > len(assignments):
        id = int(input("Enter the one which is in [x]"))

    assignment = assignments[id]
    subname = assignment.name.split(" ")[1]
    if subname == "fs":
        subname = "sfs"
    # Get submissions assigned to grade for this assignment
    submissions = client.assignment.get_all_submissions(assignment_id=assignment.id)

    print("Enter function: ")
    print("[1] - Grade all assigned submissions")
    print("[2] - Search for a specific student")
    if input("Enter the number of the function you want to use: ") == "2":
        search = input("Enter the vu-net id of the student you want to grade: ")
        submissions = [x for x in submissions if search in x.user.username]
    else:
        try:
            submissions = [x for x in submissions if x.assignee.name == client.user.get().name]
        except:
            print("You are not assigned to grade any submissions for this assignment. Bye!")
            exit()

    print("Submissions to grade: ", len(submissions))
    for submission in submissions:
        if submission is None:
            continue
        # Clear the terminal
        os.system("cls" if os.name == "nt" else "clear")
            
        print("Submission by", submission.user.name)
        # Download the submission
        subm = client.submission.get(submission_id=submission.id,type="zip")
        res = subm.url

        #Download the submission from the url
        r = requests.get(res, allow_redirects=True)
        strid = str(submission.user.id)
        open("sandbox/"+strid+".zip", 'wb').write(r.content)

        #unzip the submission
        os.system("unzip ./sandbox/"+strid+".zip -d ./sandbox/"+strid)
        #Delete the zip file
        os.system("rm ./sandbox/"+strid+".zip")

        #Read the shell.c file
        #get the directories in the sandbox
        dir = "./sandbox/"+strid+"/"
        dir += os.listdir(dir)[0] + "/" # Its either /top/ or /shell asg/ so get whatever is submitted
        dirs = os.listdir(dir)
        # If there are no .c files, then it is a tar.gz file
        if not any(x.endswith(".c") for x in dirs):
            # Get the .tar.gz file name
            tarfile = [x for x in dirs if x.endswith(".tar.gz")][0]
            dirs += os.listdir("./sandbox/"+strid+"/"+tarfile+"/" +dirs[0])

        #get the directory that contains the shell.c file
        dirpath = dir
        dir += [x for x in dirs if x.startswith(subname+".c")][0]
        #Get the path of the last folder
        #Print the contents of the file using rich
        rich.print(open(dir).read())
        if "/top/" in dir:
            os.system("cp " + dir + " " + frameworkpath + "/"+subname+".c")
            dirpath = frameworkpath
        #Ask the grader if the submission is correct
        correct = input("Should this submission be run? (y/n): ")
        if correct == "y":
            #Run "make docker-check" and get the output
            os.system("sudo make docker-check -C "+dirpath+"/")
            #Ask the grader if the submission is correct
            print("CODEGRADE GRADE: ", submission.grade)
            correct = input("Is this submission correct? (y/n): ")
            if correct == "y":
                namedict[submission.user.name] = str(submission.grade)
            else:
                newgrade = input("Enter the new grade: ")
                newcomment = input("Reason for the new grade: ")
                namedict[submission.user.name] = newgrade + " | " + newcomment
            write_into_temp(submission.user.name + " | " + str(namedict[submission.user.name]) + "\n")

    print("Done!")
    with open("grades.txt", "w") as f:
        for key, value in namedict.items():
            f.write("%s:,%s \n" % (key, value))