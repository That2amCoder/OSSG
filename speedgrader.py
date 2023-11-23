import codegrade
import os
from getpass import getpass
import requests
import rich
import csv
import subprocess
import re
import difflib

def write_to_csv(vunetid, name, codegrade_grade, new_grade, comment):
    with open("grades.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow([vunetid, name, codegrade_grade, new_grade, comment])


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
    print("NOTE 2: You will need bitbucket credentials to download the framework!")
    input("Press enter to continue")
    open("temp.txt", "w").close()
    download_asg_setup()

    print("--- Do you want to save your codegrade password? ---")
    #print NOTE: !THEY WILL BE STORED IN PLAINTEXT!") in red
    rich.print("[red]NOTE: THEY WILL BE STORED IN PLAINTEXT!")

    if (input("Enter y or n: ") == "y"):
        # Create a creds.txt file
        with open("creds.txt", "w") as f:
            f.write("")

    print("Done!")

usr = ""
pwd = ""
# Check if there is a creds.txt file in the current directory
if os.path.exists("creds.txt"):
    # If its empty then ask the user for their codegrade credentials
    if os.stat("creds.txt").st_size == 0:
        usr = input("Enter your vunet username: ")
        pwd = getpass("Enter your vunet password: ")
        # Write the credentials to the creds.txt file
        with open("creds.txt", "w") as f:
            f.write(usr + "\n")
            f.write(pwd)
    # If its not empty then read the credentials from the file
    else:
        with open("creds.txt", "r") as f:
            usr = f.readline().strip()
            pwd = f.readline().strip()
else:
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

    print("Do you want to change assignment? (y/n):")
    if input("Enter y or n: ") == "y":
        os.system("rm -rf ./sandbox")
        os.mkdir("sandbox")
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
    print("[3] - AutoGrade everything and output to csv (will take a while)")

    option = input("Enter the number of the function you want to use: ")
    if option == "2":
        search = input("Enter the vu-net id of the student you want to grade: ")
        submissions = [x for x in submissions if search in x.user.username]
    elif option == "1":
        try:
            # This assumes everyone is assigned to a grader
            submissions = [x for x in submissions if x.assignee]
            submissions = [x for x in submissions if x.assignee.name == client.user.get().name]
        except:
            print("You are not assigned to grade any submissions for this assignment. Bye!")
            exit()

    autograde = option == "3"
    print("Submissions to grade: ", len(submissions))
    # Initialise the csv file
    with open("grades.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["VUNETID", "NAME", "CODEGRADE GRADE", "NEW GRADE", "COMMENT"])

    for submission in submissions:
        if submission is None:
            continue
        # Clear the terminal
        os.system("cls" if os.name == "nt" else "clear")
            
        print("Submission by", submission.user.name)
        # get the autotest output using the codegrade api
        auttest = client.auto_test.get(auto_test_id=assignment.auto_test_id)
        submres = client.auto_test.get_result_by_submission(auto_test_id=assignment.auto_test_id, submission_id=submission.id, run_id=auttest.runs[0].id)
        codegradeoutput = submres.step_results[0].log.haystack.value

        # Get the submission url
        subm = client.submission.get(submission_id=submission.id,type="zip")
        res = subm.url

        # Download the submission from the url
        r = requests.get(res, allow_redirects=True)
        strid = str(submission.user.id)
        open("sandbox/"+strid+".zip", 'wb').write(r.content)

        # unzip the submission
        os.system("unzip ./sandbox/"+strid+".zip -d ./sandbox/"+strid)
        # Delete the zip file
        os.system("rm ./sandbox/"+strid+".zip")

        # Get the directories in the sandbox
        dir = "./sandbox/"+strid+"/"
        dir += os.listdir(dir)[0] + "/" # Its either /top/ or /asg name/ 
        dirs = os.listdir(dir)

        # If there are no .c files, then it is a tar.gz file
        if not any(x.endswith(".c") for x in dirs):
            # Get the .tar.gz file name
            tarfile = [x for x in dirs if x.endswith(".tar.gz")][0]
            dir += tarfile + "/"
            dirs = os.listdir(dir)

        # Get the directory that contains the assignment .c file
        dirpath = dir
        dir += [x for x in dirs if x.startswith(subname+".c")][0]
        # TODO: If there are multiple c files included, it makes our life harder so I'll fix that later
        
        # Get the path of the last folder
        # Print the contents of the file using rich
        rich.print(open(dir).read())
        if "/top/" in dir:
            os.system("cp " + dir + " " + frameworkpath + "/"+subname+".c")
            dirpath = frameworkpath

        # Ask the grader if the submission is malware
        correct = "n"
        if not autograde:
            correct = input("Should this submission be run? (y/n): ")
        if correct == "y" or autograde:

            # Run "make docker-check" and get the output
            output = subprocess.check_output(["make", "docker-check"], cwd=dirpath, universal_newlines=True)
            grade = "NA"
            grade = re.search("Executed all tests, got (.*)\/", output).group(1)
            # Remove whitespace
            grade = grade.replace(" ", "")
            try:
                grade = float(grade)
            except:
                grade = 0.0
            # Ask the grader if the submission is correct
            discrepancy = submission.grade != grade
            if not discrepancy:
                print("GRADE: ", submission.grade)
            else:
                # Remove all color codes from the codegrade output
                plaintextoutput = re.sub(r"\x1b\[[0-9;]*m", "", output)

                # Get the diff between the codegrade output and the local output
                diff = difflib.Differ().compare(codegradeoutput.splitlines(), plaintextoutput.splitlines())

                # Print legend of the diff output
                print("LEGEND:")
                # - is codegrade output (red)
                rich.print("[red]- CODEGRADE OUTPUT")
                # + is local output (green)
                rich.print("[green]+ LOCAL OUTPUT")
                rich.print("-----------------------------------")
                for line in diff:
                    # If there is a + or - in the line, then print it in the respective color
                    if line.startswith("+"):
                        rich.print('[green]'+line)
                    elif line.startswith("-"):
                        rich.print('[red]'+line)
                    else:
                        rich.print(line)

                rich.print("DISCREPANCY!\n [red] CODEGRADE: ", submission.grade, " | [green] LOCALGRADE: ", grade)

            
            newgrade = "NA"
            newcomment = ""
            if discrepancy:
                newcomment = "GDIF: " + str(grade - submission.grade) + "\n"
            if not autograde or discrepancy:
                change = input("Override Grade? (y/N): ")
                if change == "y":
                    newgrade = input("Enter the new grade: ")
                    newcomment = input("Reason for the new grade: ")
                else:
                    grade = str(submission.grade)
                    newgrade = grade


            write_to_csv(submission.user.username, submission.user.name, submission.grade, grade, newcomment)
        # Clean up the sandbox
        os.system("rm -rf ./sandbox/"+strid)

    print("Done!")