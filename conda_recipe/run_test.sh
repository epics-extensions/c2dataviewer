#Smoke test: make sure that c2dv can start without errors
c2dv -h

#run any python unittests in /test
python -m unittest
