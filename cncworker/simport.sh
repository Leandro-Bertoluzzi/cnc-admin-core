#!/bin/bash
FAKETTY=/dev/ttyUSBFAKE
GRBLSIM="./grbl_sim.exe"

# Kill the socat process running in background
trap "ctrl_c" 2
ctrl_c() {
  printf "\nTerminating grbl-sim.\n"
  for child in $(jobs -p); do
    kill $child
  done
  exit
}

if [ ! -e $GRBLSIM ];then
  printf "Build grbl-sim with 'make' first.\nIf the output is not named $GRBLSIM this script needs to be updated.\n"
  exit
fi

# In Docker, we don't need sudo
socat -d-d PTY,raw,link=$FAKETTY,echo=0 "EXEC:'$GRBLSIM -n -s step.out -b block.out',pty,raw,echo=0"&

# Wait for socat to setup the link then change permission
sleep 1
# In Docker, we don't need sudo
chmod a+rw /dev/ttyUSBFAKE

printf "grbl-sim running on $FAKETTY\n"
printf "Press [CTRL+C] to stop.\n"

while true
do
  sleep 100
done
