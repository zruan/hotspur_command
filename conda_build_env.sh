#!/usr/bin/bash 

ENV=~/.conda/envs/hotspur
YML=hotspur_conda_env.yml

if [ !$(conda info --envs | grep $ENV) ]
then
	conda create --prefix $ENV python=3.7 --file $YML
fi

conda install --prefix $ENV --file $YML