#!/bin/bash
# usage: run7b.sh SERVED_NAME PORT TAG -- pristine staging from pub7.tgz, one pi attempt on each of the 7 VSC tasks
H=$(hostname -s); L=/lfs/$H/0/brando9; W=$L/at979; N=$1; PORT=$2; TAG=$3; TO=2700
export PATH=/dfs/scratch0/brando9/.nvm/versions/node/v24.14.0/bin:$L/.local/bin:$HOME/envs/cc/bin:$PATH
export PI_CODING_AGENT_DIR=$W/pi_$TAG; mkdir -p $PI_CODING_AGENT_DIR
echo "{\"providers\":{\"vllm\":{\"baseUrl\":\"http://127.0.0.1:$PORT/v1\",\"api\":\"openai-completions\",\"apiKey\":\"none\",\"models\":[{\"id\":\"$N\",\"contextWindow\":40960,\"maxTokens\":8192}]}}}" > $PI_CODING_AGENT_DIR/models.json
cp $HOME/.pi/agent/settings.json $PI_CODING_AGENT_DIR/ 2>/dev/null
R=$W/run_$TAG; rm -rf $R $W/logs_$TAG; mkdir -p $R $W/logs_$TAG; tar xzf $W/pub7.tgz -C $R
P="Your working folder is the current directory: it has public/ (INSTRUCTION.md and the code in public/src/) and an empty out/. Read public/INSTRUCTION.md first and follow it exactly; wherever it says src/, that is public/src/. Write the deliverables under out/ (out/patch/, out/tests/, out/REPORT.md) as it says. gcc is on PATH for C tasks, python3 for Python tasks. Work only in this folder. One attempt, then stop."
for t in $R/tasks/*; do ID=$(basename $t); D=$R/$ID; mv $t $D; mkdir -p $D/out
 ( cd $D; s=$(date +%s)
   timeout -s KILL $TO setsid pi -p --no-session --no-extensions --no-skills --provider vllm --model $N "$P" > $W/logs_$TAG/$ID.pi.out 2> $W/logs_$TAG/$ID.pi.err
   echo "exit=$? wall_s=$(( $(date +%s)-s ))" > $W/logs_$TAG/$ID.done ) &
done
wait; echo ALL_DONE > $W/logs_$TAG/ALL_DONE
