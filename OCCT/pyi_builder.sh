#!/bin/bash

SO_FILES=$(find ./ -type f -name "*.so")

for FILE in $SO_FILES; do
    FILE=$(echo $FILE | sed 's/^\.\///')
    FILE=$(echo $FILE | sed 's/\.so$//')
    echo "Processing $FILE"
    pybind11-stubgen "OCCT.$FILE" -o .
done