spawn_many() {
    start=8080
    for i in {0..15};
    do
        port=$((start + i))
        python server.py --host 0.0.0.0 --port $port > ${port}.log 2>&1 &
        echo "Started server with port $port"
    done
}

kill_many() {
    ps -ef | grep server.py | awk '{ print $2 }'  | xargs kill -9
}
