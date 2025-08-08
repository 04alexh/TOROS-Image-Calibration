def photoCalibration(raw_file, bias_file, flat_file, science_file, write_bkg = False, bkg_file = "",
                     write_pre_back_sub = False, prebacksub_file = "",
                     use_mask = False, cx = 0.0, cy = 0.0, r = 0.0):
    """
    This function will take in the file paths for the different images and use them for calibration

    Required Arguments
    raw_file [str]: File path to raw image fits file.
    bias_file [str]: File path to bias image fits file.
    flat_file [str]: File path to flat-fielding image fits file.
    science_file [str]: File path to which program will save the calibrated image.

    Optional Arguments
    write_bkg [bool]: Turns on/off option to save background estimation image.
    bkg_file [str]: File path to which program will save the estimated background image.
    write_pre_back_sub [bool]: Turns on/off option to save pre background-subtracted image.
    prebacksub_file [str]: File path to which program will save the pre background-subtracted image.
    use_mask [bool]: Turns on/off option to use a circular mask on image when doing background estimation.
    cx [float]: X coordinate center of circular mask.
    cy [float]: Y coordinate center of circular mask.
    r [float]: Radius of circular mask.
    """

    def clip_image(img, header):
        """ This function will clip the image and remove any overscan regions. This function is written for TOROS
        specifically, and you will need to update it for any given CCD.

        :parameter - image - The image to clip
        :parameter - header - the header of the image

        :return image_clip, header - The clipped image and the new header
        """

        # make the clipped image
        image_clip = np.zeros((10560, 10560))

        # what are the sizes of the over scan?
        ovs_x_size = 180
        ovs_y_size = 40

        # what are the sizes of each chip (not including the over scan)?
        chip_x_size = 1320
        chip_y_size = 5280

        # what is the full size of the chip (including over scan)
        full_chip_x = chip_x_size + ovs_x_size
        full_chip_y = chip_y_size + ovs_y_size

        # move through x and y
        idx = 0
        for x in range(0, 12000, full_chip_x):

            idy = 0
            for y in range(0, 10600, full_chip_y):
                # put the clipped image into the holder image
                image_clip[idy:idy + chip_y_size, idx:idx + chip_x_size] = img[y:y + chip_y_size, x:x + chip_x_size]

                # increase the size of the yclip
                idy = idy + chip_y_size

            # increase the size of the xclip
            idx = idx + chip_x_size

        # update the header
        header['OVERSCAN'] = 'removed'
        header['X_CLIP'] = ovs_x_size
        header['Y_CLIP'] = ovs_y_size

        return image_clip, header

    """
    OBSOLETE CODE
    If the images do not have the same resolution, we crop them to the minimum possible resolution for all to match

    #also will define the array sizes of the image data for error catching
    raw_dim = raw.shape
    bias_dim = bias.shape
    flat_dim = flat.shape

    shape_list = [raw_dim, bias_dim, flat_dim]
    do_i_have_to_do_more_work = raw_dim == bias_dim == flat_dim

    if not do_i_have_to_do_more_work:

        #finds minimum array dimension of all images
        min_shape = tuple(min(shape) for shape in zip(*shape_list))

        #crops every image
        raw = raw[:min_shape[0], :min_shape[1]]
        bias = bias[:min_shape[0], :min_shape[1]]
        flat = flat[:min_shape[0], :min_shape[1]]
    """
    
    
    import os
    from astropy.io import fits
    from photutils.background import Background2D
    from astropy.table import Table

    if not (os.path.exists(bias_file) and os.path.exists(flat_file) and os.path.exists(raw_file)):
        print("Missing file!")
        return

    ###Defines tuples to encode image and header data
    (raw , raw_header) = fits.getdata(raw_file, header = True)
    (bias, bias_header) = fits.getdata(bias_file, header = True)
    (flat, flat_header) = fits.getdata(flat_file, header = True)


    ###The raw image and bias image are both the same resolution initially, so we will do bias subtraction first.
    bias_raw = raw - bias
    bias_raw_header = raw_header.copy()
    bias_raw_header['CAL'] = 'bias_subtracted'


    ###Next, we will perform the image clipping.
    (clipped_bias_raw, clipped_bias_raw_header) = clip_image(bias_raw, bias_raw_header)


    ###Now the flat frame is the same size as the raw, so we can perform flat fielding.
    clipped_bias_flat_raw = clipped_bias_raw / flat
    clipped_bias_flat_raw_header = bias_raw_header.copy()
    clipped_bias_flat_raw_header['CAL'] = 'bias_subtracted, flat_fielded'


    ###In case it's desired, we can write the pre background-subtracted image as a fits.
    if write_pre_back_sub:

        hdu = fits.PrimaryHDU(data = clipped_bias_flat_raw, header = clipped_bias_flat_raw_header)
        hdu.writeto(prebacksub_file)

    ###We will now perform background subtraction
    sigma_clip = SigmaClip(sigma=3.0)
    bkg_estimator = SExtractorBackground(sigma_clip=sigma_clip)

    #Maybe this is dumb but this is to create mask around the cluster in case thats a thing i need to do
    if use_mask:

        mask = np.zeros(clipped_bias_flat_raw.shape, dtype = bool)
        (yy , xx) = np.indices(clipped_bias_flat_raw.shape)
        cluster_mask = (xx - cx)**2 + (yy - cy)**2 < r**2
        mask[cluster_mask] = True

        bkg = Background2D(clipped_bias_raw, (40 , 40), filter_size = (3 , 3), sigma_clip = sigma_clip,
                           bkg_estimator = bkg_estimator, mask = mask)

    else:

        bkg = Background2D(clipped_bias_raw, (40, 40), filter_size = (3, 3), sigma_clip=sigma_clip,
                           bkg_estimator=bkg_estimator)

    '''plt.imshow(bkg.background, origin='lower', cmap='Greys_r', interpolation='nearest')
    plt.show() #Plot the background''' #Dont rly need this that much

    ###Performs background subtraction
    science = clipped_bias_raw - bkg.background
    science_header = clipped_bias_flat_raw_header.copy()


    ###Modify header to add info about if a mask was used
    if use_mask:

        science_header['CAL'] = 'bias_subtracted, flat_fielded, background_subtracted with mask'

    else:

        science_header['CAL'] = 'bias_subtracted, flat_fielded, background_subtracted without mask'


    ###Write the calibrated image into file as a calibrated image
    hdu = fits.PrimaryHDU(data = science, header = science_header)
    hdu.writeto(science_file, overwrite = True)

    if write_bkg:
        hdu = fits.PrimaryHDU(data = bkg.background)
        hdu.writeto(bkg_file, overwrite = True)

    #Just to remind me where file ends up going.
    print(science_file)
