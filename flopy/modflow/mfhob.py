import numpy as np
from flopy.pakbase import Package


class ModflowHob(Package):
    '''
    Head Observation package class

    Parameters
    ----------
    nh : int
        Number of head observations
    mobs : int
        Number of multilayer head observations
    maxm : int
        Maximum number of layers for multilayer heads
    iuhobsv : int
        unit number where output is saved
    hobdry : float
        Value of the simulated equivalent written to the observation output file
        when the observation is omitted because a cell is dry
    tomulth : float
        Time step multiplier for head observations. The product of tomulth and
        toffset must produce a time value in units consistent with other model
        input. tomulth can be dimensionless or can be used to convert the units
        of toffset to the time unit used in the simulation.
    obsnam : string list of length nh
        Observation name
    layer : int list of length nh
        is the layer index of the cell in which the head observation is located.
        If layer is less than zero, hydraulic heads from multiple layers are
        combined to calculate a simulated value. The number of layers equals the
        absolute value of layer, or |layer|.
    row : int list of length nh
        row index for the observation
    column : int list of length nh
        column index of the observation
    irefsp : int of length nh
        Stress period to which the observation time is referenced. The reference
        point is the beginning of the specified stress period. If the value of
        irefsp is negative, there are observations at |irefsp| times.
    toffset : float list of length nh
        Fractional offset between time steps
    roff : float list of length nh
        Fractional offset from center of cell in Y direction (between rows)
    coff : float list of length nh
        Fractional offset from center of cell in X direction (between columns)
    hob : float list of length nh
        Observed value
    fromlay : int of length nh
        Layer index where observation begins
    tolay : int of length nh
        Layer index where observation end
    mlay : int list of length (maxm,mobs)
        Layer numbers for multilayer observations
    pr : float list of length(maxm,mobs)
        Fractional value for each layer of multilayer observations
    itt : int
        Flag that identifies whether head or head changes are used as observations
        itt = 1 --> heads
        itt = 2 --> initial value is head and subsequent changes in head
    extension : string
        Filename extension (default is ['hob','obh'])
    unitnumber : int
        File unit number (default is [39, 139])


    Attributes
    ----------

    Methods
    -------

    See Also
    --------

    Notes

    '''

    def __init__(self, model, nh=0, mobs=0, maxm=0, iuhobsv=139, hobdry=0,
                 tomulth=1.0, obsnam=[], layer=[], row=[], column=[],
                 irefsp=[], toffset=[], roff=[], coff=[], hob=[],
                 fromlay=[], tolay=[], mlay=[], pr=[], itt=[],
                 extension=['hob', 'obh'], unitnumber=[39, 139]):
        # tomulth=1, obsnam=None, layer=None, row=None, column=None,
        # irefsp=None, toffset=None, roff=None, coff=None, hob=None,
        # fromlay=None,tolay=None,mlay=None, pr=None, itt=1,
        """
        Package constructor
        """
        name = ['HOB', 'DATA']
        Package.__init__(self, model, extension, name, unitnumber)

        self.url = 'hob.htm'
        self.heading = '# HOB for MODFLOW, generated by Flopy.'
        self.nh = nh
        self.mobs = mobs
        self.maxm = maxm
        self.iuhobsv = iuhobsv
        self.hobdry = hobdry
        self.tomulth = tomulth
        self.obsnam = obsnam
        self.layer = layer
        self.row = row
        self.column = column
        self.irefsp = irefsp
        self.toffset = toffset
        self.roff = roff
        self.coff = coff
        self.hob = hob
        self.fromlay = fromlay
        self.tolay = tolay
        self.mlay = mlay  # swm: not needed?
        self.pr = pr
        self.itt = itt

        # -create empty arrays of the correct size
        # self.obsnam = np.empty((self.nh), dtype='str')
        self.layer = np.zeros((self.nh), dtype='int32')
        self.row = np.zeros((self.nh), dtype='int32')
        self.column = np.zeros((self.nh), dtype='int32')
        self.irefsp = np.zeros((self.nh), dtype='int32')
        self.toffset = np.zeros((self.nh), dtype='float32')
        self.roff = np.zeros((self.nh), dtype='float32')
        self.coff = np.zeros((self.nh), dtype='float32')
        self.hob = np.zeros((self.nh), dtype='float32')
        self.fromlay = np.zeros((self.nh), dtype='int32')
        self.tolay = np.zeros((self.nh), dtype='int32')
        self.mlay = np.zeros((self.nh), dtype='int32')  # swm: not needed?
        self.pr = np.zeros((self.nh, self.maxm), dtype='float32')
        self.itt = np.ones((self.nh), dtype='int32')

        # -assign values to arrays
        # self.obsnam[:] = np.empty((self.nh), dtype='str')
        # self.layer[:] = np.zeros((self.nh), dtype='int32')
        # self.row[:] = np.zeros((self.nh), dtype='int32')
        # self.column[:] = np.zeros((self.nh), dtype='int32')
        # self.irefsp[:] = np.zeros((self.nh), dtype='int32')
        # self.toffset[:] = np.zeros((self.nh), dtype='float32')
        # self.roff[:] = np.zeros((self.nh), dtype='float32')
        # self.coff[:] = np.zeros((self.nh), dtype='float32')
        # self.hob[:] = np.zeros((self.nh), dtype='float32')
        # self.fromlay[:] = np.zeros((self.nh), dtype='int32')
        # self.tolay[:] = np.zeros((self.nh), dtype='int32')
        # self.mlay[:] = np.zeros((self.nh), dtype='int32') #swm: not needed?
        # self.pr[:,:] = np.zeros((self.nh, self.maxm), dtype='float32')
        # self.itt[:] = np.zeros((self.nh), dtype='int32')
        # self.itt[:] = np.ones((self.nh), dtype='int32')

        self.obsnam[:] = obsnam
        # self.obsnam[:] = np.array(obsnam, dtype='str')
        self.layer[:] = layer
        self.row[:] = row
        self.column[:] = column
        self.irefsp[:] = irefsp
        self.toffset[:] = toffset
        self.roff[:] = roff
        self.coff[:] = coff
        self.hob[:] = hob
        self.fromlay[:] = fromlay
        self.tolay[:] = tolay
        # self.mlay[:] = mlay #swm: not needed?
        self.pr[:, :] = pr
        self.itt[:] = itt

        # putting in some more checks here


        # add checks for input compliance (obsnam length, etc.)
        self.parent.add_package(self)

    def write_file(self):
        """
        Write the package file

        Returns
        -------
        None

        """
        # -open file for writing
        f_hob = open(self.fn_path, 'w')

        # -write header
        f_hob.write('%s\n' % (self.heading))

        # -write sections 1 & 2
        f_hob.write(
            '%10i%10i%10i%10i%10.4g\n' % (self.nh, self.mobs, self.maxm,
                                          self.iuhobsv, self.hobdry))
        f_hob.write('%10e\n' % (self.tomulth))  # check format

        # -write sections 3-6 looping through observations
        #       for i in range(self.nh):
        i = 0
        while (i < self.nh):
            if (self.fromlay[i] < self.tolay[i]):  # check if multilayer obs
                self.layer[i] = self.fromlay[i] - self.tolay[
                    i] - 1  # if true, reset layer
            f_hob.write(
                '{}{:10d}{:10d}{:10d}{:10d}{:10.4g}{:10.4g}{:10.4g}{:10.4g}\n'
                .format(self.obsnam[i], self.layer[i], self.row[i],
                        self.column[i],
                        self.irefsp[i], self.toffset[i], self.roff[i],
                        self.coff[i],
                        self.hob[i]))
            # print ('%s' %self.obsnam[i])
            # print ('{}'.format(self. obsnam[i]))


            # -write section 4 if multilayer obs

            if (self.fromlay[i] < self.tolay[i]):  # check if multilayer obs
                for j in range(self.fromlay[i],
                               self.tolay[i] + 1):  # zero indexing!
                    f_hob.write('%10i%10.4g\n' % (
                    j, self.pr[i, j - 1]))  # swm: Is this sytax correct????

                    # -write section 5 & 6. Index loop variable
            if (self.irefsp[i] < 0):
                f_hob.write('%10i\n' % (self.itt[i]))
                for j in range(0, -1 * self.irefsp[i]):
                    f_hob.write(
                        '{}{:10d}{:10.4g}{:10.4g}\n'.format(self.obsnam[i],
                                                            abs(self.irefsp[
                                                                    i]),
                                                            self.toffset[i],
                                                            self.hob[i]))
                    i += 1
            else:
                i += 1

        f_hob.close()

        # swm: BEGIN hack for writing standard file
        sfname = self.fn_path  # swm:hack
        sfname += '_ins'  # swm: hack
        # write header
        f_ins = open(sfname, 'w')  # swm: hack for standard file
        f_ins.write('jif @\n')  # swm: hack for standard file
        f_ins.write(
            'StandardFile 1 1 %s\n' % (self.nh))  # swm: hack for standard file
        for i in range(0, self.nh):
            f_ins.write(
                '{}\n'.format(self.obsnam[i]))  # swm: hack for standard file
        # swm: END hack for writing standard file

        return