ps -ef | grep 'python -u app.py' | awk '{ print $2 }' | xargs sudo kill -9 
