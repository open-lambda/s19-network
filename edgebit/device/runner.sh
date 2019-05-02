ni=10
rounds=500

for sz in "1K" "64K" "512K" "1M"; do
    for policy in "best" "worst" "cloud" "random"; do
        for i in {1..30}; do
            python -u app.py --size $sz --policy $policy --num-iters $ni --rounds $rounds --id client_${i} &
            pids[${i}]=$!
        done
        for pid in ${pids[*]}; do
                wait $pid
        done
        unset pid
        for ip in "35.224.233.42" "35.192.170.150" "35.224.57.119"; do 
            ssh -i ~/.ssh/id_rsa edgesim@$ip 'rm -f /tmp/bar_*'
        done
    done
done
