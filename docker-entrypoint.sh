#!/usr/bin/env bash

cd /tribun_scripts
for script in *.py
do
	/usr/local/bin/python $script
done
