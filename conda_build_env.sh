#!/usr/bin/bash 


ENV=~/.conda/envs/hotspur

if !$(conda info --envs | grep $ENV);
	conda create --prefix $ENV python=3.7
fi
conda install --prefix $ENV --file conda-requirements.txt