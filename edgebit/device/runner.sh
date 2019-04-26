sz='512K'
policy='cloud'
ni=50
rounds=500

for i in {1..50}; do
    python -u app.py --size $sz --policy $policy --num-iters $ni --rounds $rounds --id client_${i} &
done
