#!/bin/bash

module load imod

edmont -imin $1.mrc -plout plist_tmp -imout tmp_mont.mrc
blendmont -imin tmp_mont.mrc -imout tmp_blend.mrc -plin plist_tmp -roo tmp -bin 8
mrc2tif -p tmp_blend.mrc $1.png
rm tmp_mont.mrc tmp_blend.mrc plist_tmp



