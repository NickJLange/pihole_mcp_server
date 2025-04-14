curl -k https://localhost:9443/api/docs/specs/main.yaml | grep \$ref | cut -d ":" -f 2 | cut -d "#" -f 1 | sort -u | sed "s/\'//g" | while read endpoint; do curl -k https://localhost:9443/api/docs/specs/$endpoint; done | tee ./output.yaml
llm -m gemini-2.5-pro-exp-03-25 < genesis-prompt.txt  < output.yaml
while `cat prompt-dialogue.txt' | read line; 
do echo llm -c \'$line\';done
