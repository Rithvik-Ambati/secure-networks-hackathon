#!/bin/sh
# GENERATED. Runs in a privileged helper container; needs PID_<name> env vars (container PIDs).
set -e
R="nsenter -t $PID_router -n"
$R sh -c 'ip link add br-user type bridge && ip addr add 10.10.10.254/24 dev br-user && ip link set br-user up'
$R sh -c 'ip link add br-dmz type bridge && ip addr add 10.10.20.254/24 dev br-dmz && ip link set br-dmz up'
$R sh -c 'ip link add br-server type bridge && ip addr add 10.10.30.254/24 dev br-server && ip link set br-server up'
$R sh -c 'ip link add br-mgmt type bridge && ip addr add 10.10.40.254/24 dev br-mgmt && ip link set br-mgmt up'
ip link del v-ws 2>/dev/null || true
ip link add v-ws type veth peer name p-ws
ip link set v-ws netns $PID_ws name eth0
ip link set p-ws netns $PID_router
$R sh -c 'ip link set p-ws master br-user && ip link set p-ws up'
nsenter -t $PID_ws -n sh -c 'ip link set lo up && ip addr add 10.10.10.10/24 dev eth0 && ip link set eth0 up && ip route add 10.10.20.0/24 via 10.10.10.254 && ip route add 10.10.30.0/24 via 10.10.10.254 && ip route add 10.10.40.0/24 via 10.10.10.254'
ip link del v-web 2>/dev/null || true
ip link add v-web type veth peer name p-web
ip link set v-web netns $PID_web name eth0
ip link set p-web netns $PID_router
$R sh -c 'ip link set p-web master br-dmz && ip link set p-web up'
nsenter -t $PID_web -n sh -c 'ip link set lo up && ip addr add 10.10.20.10/24 dev eth0 && ip link set eth0 up && ip route add 10.10.10.0/24 via 10.10.20.254 && ip route add 10.10.30.0/24 via 10.10.20.254 && ip route add 10.10.40.0/24 via 10.10.20.254'
ip link del v-app 2>/dev/null || true
ip link add v-app type veth peer name p-app
ip link set v-app netns $PID_app name eth0
ip link set p-app netns $PID_router
$R sh -c 'ip link set p-app master br-server && ip link set p-app up'
nsenter -t $PID_app -n sh -c 'ip link set lo up && ip addr add 10.10.30.10/24 dev eth0 && ip link set eth0 up && ip route add 10.10.10.0/24 via 10.10.30.254 && ip route add 10.10.20.0/24 via 10.10.30.254 && ip route add 10.10.40.0/24 via 10.10.30.254'
ip link del v-db 2>/dev/null || true
ip link add v-db type veth peer name p-db
ip link set v-db netns $PID_db name eth0
ip link set p-db netns $PID_router
$R sh -c 'ip link set p-db master br-server && ip link set p-db up'
nsenter -t $PID_db -n sh -c 'ip link set lo up && ip addr add 10.10.30.11/24 dev eth0 && ip link set eth0 up && ip route add 10.10.10.0/24 via 10.10.30.254 && ip route add 10.10.20.0/24 via 10.10.30.254 && ip route add 10.10.40.0/24 via 10.10.30.254'
ip link del v-files 2>/dev/null || true
ip link add v-files type veth peer name p-files
ip link set v-files netns $PID_files name eth0
ip link set p-files netns $PID_router
$R sh -c 'ip link set p-files master br-server && ip link set p-files up'
nsenter -t $PID_files -n sh -c 'ip link set lo up && ip addr add 10.10.30.12/24 dev eth0 && ip link set eth0 up && ip route add 10.10.10.0/24 via 10.10.30.254 && ip route add 10.10.20.0/24 via 10.10.30.254 && ip route add 10.10.40.0/24 via 10.10.30.254'
ip link del v-jump 2>/dev/null || true
ip link add v-jump type veth peer name p-jump
ip link set v-jump netns $PID_jump name eth0
ip link set p-jump netns $PID_router
$R sh -c 'ip link set p-jump master br-mgmt && ip link set p-jump up'
nsenter -t $PID_jump -n sh -c 'ip link set lo up && ip addr add 10.10.40.10/24 dev eth0 && ip link set eth0 up && ip route add 10.10.10.0/24 via 10.10.40.254 && ip route add 10.10.20.0/24 via 10.10.40.254 && ip route add 10.10.30.0/24 via 10.10.40.254'
echo "wired $(echo $PID_router | wc -l) router and 6 hosts"
