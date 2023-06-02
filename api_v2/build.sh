
#!/bin/bash

echo "👋 build.sh is running"

set -e

# Variables
C20FLAGS="-Wall -fdiagnostics-color=always -std=c++20"
C11FLAGS="-Wall -fdiagnostics-color=always -std=c++11"
CC="g++"
OUTDIR="build"
if [ -z "$1" ]; then
    OUTEXECUTABLE="voidstar"
else
    OUTEXECUTABLE="$1"
fi

mkdir -p $OUTDIR
anyRebuild=false
for f in src/*.cpp; do


    fileRoot=$(echo $f | awk -F '.' '{print $1}' | awk -F '/' '{print $2}')
    currHashVal=$(cat src/$fileRoot.hpp src/$fileRoot.cpp 2> /dev/null | md5sum | awk '{print $1}')
    if [ -f "$OUTDIR/$fileRoot.hash" ]; then
        oldHashVal=$(cat $OUTDIR/$fileRoot.hash)
        if [ "$currHashVal" = "$oldHashVal" ]; then
            echo "✅ hashes match (${currHashVal:0:6}) $fileRoot(.cpp|.hpp)"
            rebuild=false
        else
            rebuild=true
            echo "❌ hash mismatch (${currHashVal:0:6} != ${oldHashVal:0:6}) $fileRoot(.cpp|.hpp)"
        fi
    else
        rebuild=true
        echo "⚠️ hash not found for $fileRoot(.cpp|.hpp)"
    fi


    if $rebuild; then
        anyRebuild=true
        echo $currHashVal > "$OUTDIR/$fileRoot.hash"
        if [[ "$fileRoot" =~ "logging" ]]; then
            CFLAGS=$C11FLAGS
        else
            CFLAGS=$C20FLAGS
        fi
        echo "🤓 building $fileRoot.cpp with flag $(echo $CFLAGS | awk '{print $NF}') (hash=${currHashVal:0:6})"
        $CC $CFLAGS -c src/$fileRoot.cpp -o $OUTDIR/$fileRoot.o
    fi

done

echo "🤓 building executable $OUTDIR/$OUTEXECUTABLE"
$CC $C20FLAGS $OUTDIR/*.o -o $OUTDIR/$OUTEXECUTABLE

echo "👋 bye"
