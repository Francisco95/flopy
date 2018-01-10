"""
mfmodel module.  Contains the MFModel class

"""
import os
from .mfbase import PackageContainer, ExtFileAction, PackageContainerType
from .mfpackage import MFPackage
from .modflow import mfgwfnam
from .coordinates import modeldimensions
from .utils.reference import SpatialReference, StructuredSpatialReference, \
                             VertexSpatialReference
from .data import mfstructure, mfdatautil


class MFModel(PackageContainer):
    """
    MODFLOW Model Class.  Represents a single model in a simulation.

    Parameters
    ----------
    simulation_data : MFSimulationData
        simulation data object
    structure : MFModelStructure
        structure of this type of model
    model_name : string
        name of the model
    model_nam_file : string
        relative path to the model name file from model working folder
    version : string
        version of modflow
    exe_name : string
        model executable name
    model_ws : string
        model working folder path
    disfile : string
        relative path to dis file from model working folder
    grid_type : string
        type of grid the model will use (structured, unstructured, vertices)

    Attributes
    ----------
    model_name : string
        name of the model
    exe_name : string
        model executable name
    packages : OrderedDict(MFPackage)
        dictionary of model packages
    _name_file_io : MFNameFile
        name file

    Methods
    -------
    load : (simulation : MFSimulationData, model_name : string,
      namfile : string, type : string, version : string, exe_name : string,
      model_ws : string, strict : boolean) : MFSimulation
        a class method that loads a model from files
    write
        writes the simulation to files
    set_model_relative_path : (path : string)
        sets the file path to the model folder and updates all model file paths
    is_valid : () : boolean
        checks the validity of the model and all of its packages

    See Also
    --------

    Notes
    -----

    Examples
    --------

    """
    def __init__(self, simulation, model_type='gwf', model_name='modflowtest',
                 model_nam_file=None, ims_file_name=None, version='mf6',
                 exe_name='mf6.exe', add_to_simulation = True,
                 structure = None, model_rel_path='.', **kwargs):
        super(MFModel, self).__init__(simulation.simulation_data, model_name)
        self.simulation = simulation
        self.simulation_data = simulation.simulation_data
        self.name = model_name
        self.name_file = None

        self.set_model_relative_path(model_rel_path)
        if add_to_simulation:
            self.structure = simulation.register_model(self, model_type,
                                                       model_name,
                                                       model_nam_file)
        else:
            self.structure = structure
        self.exe_name = exe_name
        self.dimensions = modeldimensions.ModelDimensions(self.name,
                                                          self.simulation_data)
        self.simulation_data.model_dimensions[model_name] = self.dimensions
        self._ftype_num_dict = {}
        self._package_paths = {}

        if model_nam_file is None:
            self.model_nam_file = '{}.nam'.format(model_name)
        else:
            self.model_nam_file = model_nam_file

        # check for spatial reference info in kwargs
        xul = kwargs.pop("xul", None)
        yul = kwargs.pop("yul", None)
        rotation = kwargs.pop("rotation", 0.)
        proj4_str = kwargs.pop("proj4_str", "EPSG:4326")
        self.sr = SpatialReference(xul=xul, yul=yul, rotation=rotation,
                                   proj4_str=proj4_str)

        # build model name file
        # create name file based on model type - support different model types
        package_obj = self.package_factory('nam', model_type[0:3])
        if not package_obj:
            excpt_str = 'Name file could not be found for model' \
                        '{}.'.format(model_type[0:3])
            print(excpt_str)
            raise mfstructure.StructException(excpt_str)

        self.name_file = package_obj(self, fname=self.model_nam_file,
                                     pname=self.name)
        self.verbose = simulation.verbose

    def __getattr__(self, item):
        """
        __getattr__ - used to allow for getting packages as if they are
                      attributes

        Parameters
        ----------
        item : str
            3 character package name (case insensitive)


        Returns
        -------
        pp : Package object
            Package object of type :class:`flopy.pakbase.Package`

        """
        return self.get_package(item)

    def __setattr__(self, key, value):
        if key == "sr":
            assert isinstance(value, SpatialReference) or \
                   isinstance(value, StructuredSpatialReference) or \
                   isinstance(value, VertexSpatialReference)
        super(MFModel, self).__setattr__(key, value)

    @classmethod
    def load(cls, simulation, simulation_data, structure,
             model_name='NewModel', model_nam_file='modflowtest.nam',
             type='gwf', version='mf6', exe_name='mf6.exe', strict=True,
             model_rel_path='.'):
        """
        Load an existing model.

        Parameters
        ----------
        simulation : MFSimulation
            simulation object that this model is a part of
        simulation_data : MFSimulationData
            simulation data object
        structure : MFModelStructure
            structure of this type of model
        model_name : string
            name of the model
        model_nam_file : string
            relative path to the model name file from model working folder
        version : string
            version of modflow
        exe_name : string
            model executable name
        model_ws : string
            model working folder relative to simulation working folder
        strict : boolean
            strict mode when loading files
        model_rel_path : string
            relative path of model folder to simulation folder
        Returns
        -------
        model : MFModel

        Examples
        --------
        """

        instance = cls(simulation, type, model_name,
                       model_nam_file=model_nam_file, ims_file_name=None,
                       version=version, exe_name=exe_name,
                       add_to_simulation=False, structure=structure,
                       model_rel_path=model_rel_path)
        # load name file
        instance.name_file.load(strict)

        # order packages
        vnum = mfstructure.MFStructure().get_version_string()
        # FIX: Transport - Priority packages maybe should not be hard coded
        priority_packages = {'dis{}'.format(vnum): 1,'disv{}'.format(vnum): 1,
                             'disu{}'.format(vnum): 1}
        packages_ordered = []
        package_recarray = instance.simulation_data.mfdata[(model_name, 'nam',
                                                            'packages',
                                                            'packagerecarray')]
        for item in package_recarray.get_data():
            if item[0] in priority_packages:
                packages_ordered.insert(0, (item[0], item[1], item[2]))
            else:
                packages_ordered.append((item[0], item[1], item[2]))

        # load packages
        sim_struct = mfstructure.MFStructure().sim_struct
        instance._ftype_num_dict = {}
        for ftype, fname, pname in packages_ordered:
            ftype = ftype[0:-1].lower()
            if ftype in structure.package_struct_objs or ftype in \
              sim_struct.utl_struct_objs:
                if model_rel_path and model_rel_path != '.':
                    # strip off model relative path from the file path
                    filemgr = simulation.simulation_data.mfpath
                    fname = filemgr.strip_model_relative_path(model_name,
                                                              fname)
                # load package
                instance.load_package(ftype, fname, pname, strict, None)

        # load referenced packages
        if model_name in instance.simulation_data.referenced_files:
            for index, ref_file in \
              instance.simulation_data.referenced_files[model_name].items():
                if (ref_file.file_type in structure.package_struct_objs or
                  ref_file.file_type in sim_struct.utl_struct_objs) and \
                  not ref_file.loaded:
                    instance.load_package(ref_file.file_type,
                                          ref_file.file_name, None, strict,
                                          ref_file.reference_path)
                    ref_file.loaded = True

        # TODO: fix jagged lists where appropriate

        return instance

    def write(self, ext_file_action=ExtFileAction.copy_relative_paths):
        """
        write model to model files

        Parameters
        ----------
        ext_file_action : ExtFileAction
            defines what to do with external files when the simulation path has
            changed.  defaults to copy_relative_paths which copies only files
            with relative paths, leaving files defined by absolute paths fixed.

        Returns
        -------

        Examples
        --------
        """

        # write name file
        self.name_file.write(ext_file_action=ext_file_action)

        # write packages
        for pp in self.packages:
            pp.write(ext_file_action=ext_file_action)

    def is_valid(self):
        """
        checks the validity of the model and all of its packages

        Parameters
        ----------

        Returns
        -------
        valid : boolean

        Examples
        --------
        """

        # valid name file
        if not self.name_file.is_valid():
            return False

        # valid packages
        for pp in self.packages:
            if not pp.is_valid():
                return False

        # required packages exist
        for key, package_struct in self.structure.package_struct_objs.items():
            if not package_struct.optional and not package_struct.file_type \
              in self.package_type_dict:
                return False

        return True

    def set_model_relative_path(self, model_ws):
        """
        sets the file path to the model folder relative to the simulation
        folder and updates all model file paths, placing them in the model
        folder

        Parameters
        ----------
        model_ws : string
            model working folder relative to simulation working folder

        Returns
        -------

        Examples
        --------
        """
        # update path in the file manager
        file_mgr = self.simulation_data.mfpath
        path = file_mgr.string_to_file_path(model_ws)
        file_mgr.model_relative_path[self.name] = path
        file_mgr.set_last_accessed_path()

        if model_ws and model_ws != '.' and self.simulation.name_file is not \
                None:
            # update model name file location in simulation name file
            models = self.simulation.name_file.modelrecarray
            models_data = models.get_data()
            for index, entry in enumerate(models_data):
                old_model_path, old_model_file_name = os.path.split(entry[1])
                old_model_base_name = os.path.splitext(old_model_file_name)[0]
                if old_model_base_name.lower() == self.name.lower() or \
                        self.name == entry[2]:
                    models_data[index][1] = os.path.join(path, old_model_file_name)
                    break
            models.set_data(models_data)

            if self.name_file is not None:
                # update listing file location in model name file
                list_file = self.name_file.list.get_data()
                if list_file:
                    path, list_file_name = os.path.split(list_file)
                    self.name_file.list.set_data(os.path.join(path, list_file_name))

                # update package file locations in model name file
                packages = self.name_file.packagerecarray
                packages_data = packages.get_data()
                for index, entry in enumerate(packages_data):
                    old_package_path, old_package_name = os.path.split(entry[1])
                    packages_data[index][1] = os.path.join(path, old_package_name)
                packages.set_data(packages_data)

                # update files referenced from within packages
                for package in self.packages:
                    package.set_model_relative_path(model_ws)

    def register_package(self, package, add_to_package_list=True,
                         set_package_name=True, set_package_filename=True):
        """
        registers a package with the model

        Parameters
        ----------
        package : MFPackage
            package to register
        add_to_package_list : bool
            add package to lookup list
        set_package_name : bool
            produce a package name for this package
        set_package_filename : bool
            produce a filename for this package

        Returns
        -------
        (path : tuple, package structure : MFPackageStructure)

        Examples
        --------
        """
        package.container_type = [PackageContainerType.model]
        if package.parent_file is not None:
            path = package.parent_file.path + (package.package_type,)
        else:
            path = (self.name, package.package_type)

        # make sure path is unique
        if path in self._package_paths:
            path_iter = mfdatautil.PathIter(path)
            for new_path in path_iter:
                if new_path not in self._package_paths:
                    path = new_path
                    break
        self._package_paths[path] = 1

        if package.package_type.lower() == 'nam':
            return path, self.structure.name_file_struct_obj

        package_struct = \
          self.structure.get_package_struct(package.package_type)
        if set_package_name:
            # produce a default package name
            if package_struct is not None and \
              package_struct.multi_package_support:
                # check for other registered packages of this type
                name_iter = mfdatautil.NameIter(package.package_type, False)
                for package_name in name_iter:
                    if package_name not in self.package_name_dict:
                        package.package_name = package_name
                        break
            else:
                package.package_name = package.package_type

        if set_package_filename:
            package.filename = '{}.{}'.format(self.name, package.package_type)

        if add_to_package_list:
            self._add_package(package, path)

            # add obs file to name file if it does not have a parent
            if package.package_type in self.structure.package_struct_objs or \
              (package.package_type == 'obs' and package.parent_file is None):
                # update model name file
                pkg_type = package.package_type.upper()
                if len(pkg_type) > 3 and pkg_type[-1] == 'A':
                    pkg_type = pkg_type[0:-1]
                # Model Assumption - assuming all name files have a package
                # rec array
                self.name_file.packagerecarray.\
                  update_record(['{}6'.format(pkg_type), package.filename,
                  package.package_name], 0)
        if package_struct is not None:
            return (path, package_struct)
        else:
            print('WARNING: Unable to register unsupported file type {} for '
                  'model {}.'.format(package.package_type, self.name))
        return (None, None)

    def load_package(self, ftype, fname, pname, strict, ref_path,
                     dict_package_name=None, parent_package=None):
        """
        loads a package from a file

        Parameters
        ----------
        ftype : string
            the file type
        fname : string
            the name of the file containing the package input
        pname : string
            the user-defined name for the package
        strict : bool
            strict mode when loading the file
        ref_path : string
            path to the file. uses local path if set to None
        dict_package_name : string
            package name for dictionary lookup
        parent_package : MFPackage
            parent package

        Examples
        --------
        """
        sim_struct = mfstructure.MFStructure().sim_struct
        if (ftype in self.structure.package_struct_objs and
          self.structure.package_struct_objs[ftype].multi_package_support) or \
          (ftype in sim_struct.utl_struct_objs and
          sim_struct.utl_struct_objs[ftype].multi_package_support):
            # resolve dictionary name for package
            if dict_package_name is not None:
                if parent_package is not None:
                    dict_package_name = '{}_{}'.format(parent_package.path[-1],
                                                       ftype)
                else:
                    # use dict_package_name as the base name
                    if ftype in self._ftype_num_dict:
                        self._ftype_num_dict[dict_package_name] += 1
                    else:
                        self._ftype_num_dict[dict_package_name] = 0
                    dict_package_name = '{}_{}'.format(dict_package_name,
                                                       self._ftype_num_dict[
                                                         dict_package_name])
            else:
                # use ftype as the base name
                if ftype in self._ftype_num_dict:
                    self._ftype_num_dict[ftype] += 1
                else:
                    self._ftype_num_dict[ftype] = 0
                if pname is not None:
                    dict_package_name = pname
                else:
                    dict_package_name = '{}_{}'.format(ftype,
                                                       self._ftype_num_dict[
                                                       ftype])
        else:
            dict_package_name = ftype

        # clean up model type text
        model_type = self.structure.model_type
        while mfdatautil.DatumUtil.is_int(model_type[-1]):
            model_type = model_type[0:-1]

        # create package
        package_obj = self.package_factory(ftype, model_type)
        package = package_obj(self, fname=fname, pname=dict_package_name,
                              add_to_package_list=False,
                              parent_file=parent_package)
        try:
            package.load(strict)
        except mfstructure.ReadAsArraysException:
            #  create ReadAsArrays package and load it instead
            package_obj = self.package_factory('{}a'.format(ftype), model_type)
            package = package_obj(self, fname=fname, pname=dict_package_name,
                                  add_to_package_list=False,
                                  parent_file=parent_package)
            package.load(strict)

        # register child package with the model
        self._add_package(package, package.path)
        if parent_package is not None:
            # register child package with the parent package
            parent_package._add_package(package, package.path)