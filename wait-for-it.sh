#!/bin/sh
# wait-for-it.sh: wait for a host and port to be available before executing a command.
# Usage: wait-for-it.sh host:port [-t timeout] [-- command args...]
#    -t TIMEOUT : Timeout in seconds, zero for no timeout
#    -- COMMAND ARGS : Execute command with args after the test finishes

TIMEOUT=15
QUIET=0
COMMAND=""

echoerr() { if [ "$QUIET" -ne 1 ]; then echo "$@" 1>&2; fi }

usage()
{
    cat << USAGE >&2
Usage:
    $0 host:port [-t timeout] [-- command args...]
    -t TIMEOUT | --timeout=TIMEOUT : Timeout in seconds, zero for no timeout
    -- COMMAND ARGS                 : Execute command with args after the test finishes
USAGE
    exit 1
}

wait_for()
{
    if [ -z "$COMMAND" ]; then
        echoerr "Error: you need to provide a command to run after waiting for $HOST:$PORT"
        usage
    fi

    for i in `seq $TIMEOUT` ; do
        nc -z "$HOST" "$PORT" > /dev/null 2>&1
        result=$?
        if [ $result -eq 0 ] ; then
            if [ $QUIET -ne 1 ] ; then echoerr "$HOST:$PORT is available after $i seconds"; fi
            exec $COMMAND
            exit 0
        fi
        sleep 1
    done
    echoerr "Timeout occurred after waiting $TIMEOUT seconds for $HOST:$PORT"
    exit 1
}

# process arguments
while [ $# -gt 0 ]
do
    case "$1" in
        *:* )
        HOST=$(printf "%s
" "$1"| cut -d : -f 1)
        PORT=$(printf "%s
" "$1"| cut -d : -f 2)
        shift 1
        ;;
        -q | --quiet)
        QUIET=1
        shift 1
        ;;
        -t)
        TIMEOUT="$2"
        if [ "$TIMEOUT" = "" ]; then break; fi
        shift 2
        ;;
        --timeout=*)
        TIMEOUT="${1#*=}"
        shift 1
        ;;
        --)
        shift
        COMMAND="$@"
        break
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Unknown argument: $1"
        usage
        ;;
    esac
done

if [ -z "$HOST" ] || [ -z "$PORT" ]; then
    echoerr "Error: you need to provide a host and port to test."
    usage
fi

wait_for
