# TOROS-Image-Calibration
This program calibrates TOROS images by performing flat fielding, bias subtraction, and background subtraction.

## Use
This section will explain the function parameters. (**function parameter** [data type]: Explanation of parameter)
\
\
\
**raw_file** [str]: Path of the raw image.
\
\
**bias_file** [str]: Path of the bias frame for bias subtraction.
\
\
**flat_file** [str]: Path of the flat frame for flat fielding.
\
\
**science_file** [str]: Path of the fully calibrated image.
\
\
**write_bkg** [bool]: If true, program will save the generated 2D background to *bkg_file*. Set to FALSE by default.
\
\
**bkg_file** [str]: Path of the background image if it gets saved. Set to an empty string by default.
\
\
**write_pre_back_sub** [bool]: If true, program will also save a copy of the image after flat fielding and bias subtraction have been done, but before background subtraction. Set to FALSE by default.
\
\
**prebacksub_file** [str]: Path of the prebackground-subtracted image. Set to an empty string by default.
\
\
**use_mask** [bool]: If true, program will mask an area of the image before doing the background subtraction. Set to FALSE by default.
\
\
**cx** [float]: X-Pixel center of circular mask. Set to 0.0 by default.
\
\
**cy** [float]: Y-Pixel center of circular mask. Set to 0.0 by default.
\
\
**r** [float]: Radius of circular mask. Set to 0.0 by default.
