ps -ef | grep 'python app.py' | awk '{ print $2 }' | xargs sudo kill -9 
