# OSSG
Operating Systems Speed Grader

## What does it do

It automatically downloads all submissions that you need to grade, shows them to you for that quick check and then runs them in docker containers to grade them. 
If the result is different, then you may adjust the grade and add a comment and *writes everything to a file*.

## Requirements 
linux
docker 
python3
unzip
``pip3 install codegrade rich requests``