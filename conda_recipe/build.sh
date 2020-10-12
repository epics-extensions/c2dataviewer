# Assert that working directory is clean
#if output=$(git status --porcelain -uno) && [ -z "$output" ]; then
#    echo "Working directory is clean; build may proceed."
#else
#    echo "*****************************************"
#    echo "* ERROR: Working directory is not clean *"
#    echo "*****************************************"
#    exit 1
#fi

# Run python packaging
python setup.py install
