#!/bin/bash
# Lab control. Run inside WSL2 Ubuntu:  ./lab.sh build | flat | seg | down
cd "$(dirname "$0")"
case "$1" in
  build) python3 gen.py && docker build -q -t ps2-node docker ;;
  flat)  docker compose -f generated/compose.flat.yml up -d && sleep 12 ;;
  seg)
    docker compose -f generated/compose.seg.yml up -d
    envs=""
    for n in router ws web app db files jump; do envs="$envs -e PID_$n=$(docker inspect -f '{{.State.Pid}}' ps2-$n)"; done
    docker run --rm --privileged --pid=host --net=host $envs -v "$PWD/generated/wire.sh:/wire.sh:ro" \
      --entrypoint sh ps2-node /wire.sh && sleep 8 ;;
  down)
    docker compose -f generated/compose.flat.yml down 2>/dev/null
    docker compose -f generated/compose.seg.yml down 2>/dev/null ;;
  *) echo "usage: $0 build|flat|seg|down"; exit 1 ;;
esac
