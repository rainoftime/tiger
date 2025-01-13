#!/usr/bin/env bash
# Adjunct the commands based on the current environment?
# (e.g., Arch, OS, C compiler, etc.)

python3 main.py "$1"
if [ $? -eq 0 ]; then
  gcc -c putting_it_all_together/runtime.c
  gcc -no-pie -g output.s runtime.o

  rm "output.s"
  rm "runtime.o"
fi