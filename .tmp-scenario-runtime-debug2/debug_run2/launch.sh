#!/usr/bin/env bash
set +e
echo $$ > /home/matheusalves/Dev/random/drone-sim-complete/.tmp-scenario-runtime-debug2/debug_run2/scenario.pid
bash /home/matheusalves/Dev/random/drone-sim-complete/scripts/scenarios/run_scenario.sh /home/matheusalves/Dev/random/drone-sim-complete/simulation/scenarios/takeoff_land.json --output json --backend fake-success > /home/matheusalves/Dev/random/drone-sim-complete/.tmp-scenario-runtime-debug2/debug_run2/result.json 2> /home/matheusalves/Dev/random/drone-sim-complete/.tmp-scenario-runtime-debug2/debug_run2/stderr.log
status=$?
printf '%s' "$status" > /home/matheusalves/Dev/random/drone-sim-complete/.tmp-scenario-runtime-debug2/debug_run2/exit_code.txt
exit "$status"
