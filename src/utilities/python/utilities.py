##############################################################################
# @file  utilities.py
# @brief Main module of project-independent BASIS utilities.
#
# This module defines the BASIS Utilities whose implementations are not
# project-specific, i.e., do not make use of particular project attributes such
# as the name or version of the project. The utility functions defined by this
# module are intended for use in Python scripts and modules that are not build
# as part of a particular BASIS project. Otherwise, the project-specific
# implementations should be used instead, i.e., those defined by the basis.py
# module of the project. The basis.py module and the submodules imported by
# it are generated from template modules which are customized for the particular
# project that is being build.
#
# Copyright (c) 2011, 2012 University of Pennsylvania. All rights reserved.<br />
# See http://www.rad.upenn.edu/sbia/software/license.html or COPYING file.
#
# Contact: SBIA Group <sbia-software at uphs.upenn.edu>
#
# @ingroup BasisPythonUtilities
##############################################################################

__all__ = [] # use of import * is discouraged

import os
import sys
import re
import shlex
import subprocess

from . import which


# ============================================================================
# constants
# ============================================================================

## @brief Default copyright of executables.
COPYRIGHT = "@COPYRIGHT@"
## @brief Default license of executables.
LICENSE = "@LICENSE@"
## @brief Default contact to use for help output of executables.
CONTACT = "@CONTACT@"


# used to make paths relative to this module absolute
_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))

# ============================================================================
# executable information
# ============================================================================

# ----------------------------------------------------------------------------
## @brief Print contact information.
#
# @param [in] contact Name of contact.
def print_contact(contact=CONTACT):
    sys.stdout.write("Contact:\n  " + contact + "\n")

# ----------------------------------------------------------------------------
## @brief Print version information including copyright and license notices.
#
# @param [in] name      Name of executable. Should not be set programmatically
#                       to the first argument of the @c __main__ module, but
#                       a string literal instead.
# @param [in] version   Version of executable, e.g., release of project
#                       this executable belongs to.
# @param [in] project   Name of project this executable belongs to.
#                       If @c None, or an empty string, no project
#                       information is printed.
# @param [in] copyright The copyright notice, excluding the common prefix
#                       "Copyright (c) " and suffix ". All rights reserved.".
#                       If @c None, or an empty string, no copyright notice
#                       is printed.
# @param [in] license   Information regarding licensing. If @c None or an
#                       empty string, no license information is printed.
def print_version(name, version=None, project=None, copyright=COPYRIGHT, license=LICENSE):
    if not version: raise Exception('print_version(): Missing version argument')
    # program identification
    sys.stdout.write(name)
    if project:
        sys.stdout.write(' (')
        sys.stdout.write(project)
        sys.stdout.write(')')
    sys.stdout.write(' ')
    sys.stdout.write(version)
    sys.stdout.write('\n')
    # copyright notice
    if copyright:
        sys.stdout.write("Copyright (c) ");
        sys.stdout.write(copyright)
        sys.stdout.write(". All rights reserved.\n")
    # license information
    if license:
        sys.stdout.write(license)
        sys.stdout.write('\n')

# ----------------------------------------------------------------------------
## @brief Get UID of build target.
#
# The UID of a build target is its name prepended by a namespace identifier
# which should be unique for each project.
#
# @param [in] name    Name of build target.
# @param [in] prefix  Common prefix of targets belonging to this project.
# @param [in] targets Dictionary mapping target UIDs to executable paths.
#
# @returns UID of named build target.
def targetuid(name, prefix=None, targets=None):
    # handle invalid arguments
    if not name: return None
    # in case of a leading namespace separator, do not modify target name
    if name.startswith('.'): return name
    # common target UID prefix of project
    if prefix is None or not targets: return name
    # try prepending namespace or parts of it until target is known
    separator = '.'
    while True:
        if separator.join([prefix, name]) in targets:
            return separator.join([prefix, name])
        parts = prefix.split(separator, 1)
        if len(parts) == 1: break
        prefix = parts[0]
    # otherwise, return target name unchanged
    return name

# ----------------------------------------------------------------------------
## @brief Determine whether a given build target is known.
#
# @param [in] name    Name of build target.
# @param [in] prefix  Common prefix of targets belonging to this project.
# @param [in] targets Dictionary mapping target UIDs to executable paths.
#
# @returns Whether the named target is a known executable target.
def istarget(name, prefix=None, targets=None):
    uid = targetuid(name, prefix=prefix, targets=targets)
    if not uid or not targets: return False
    if uid.startswith('.'): uid = uid[1:]
    return uid in targets

# ----------------------------------------------------------------------------
## @brief Get absolute path of executable file.
#
# This function determines the absolute file path of an executable. If no
# arguments are given, the absolute path of this executable is returned.
# If the command names a known executable build target, the absolute path to
# the corresonding built (and installed) executable file is returned.
# Otherwise, the named command is searched in the system @c PATH and its
# absolute path returned if found. If the executable is not found, @c None
# is returned.
#
# @param [in] name    Name of command or @c None.
# @param [in] prefix  Common prefix of targets belonging to this project.
# @param [in] targets Dictionary mapping target UIDs to executable paths.
#
# @returns Absolute path of executable or @c None if not found.
#          If @p name is @c None, the path of this executable is returned.
def exepath(name=None, prefix=None, targets=None):
    path = None
    if name is None:
        path = os.path.realpath(sys.argv[0])
    elif istarget(name, prefix=prefix, targets=targets):
        uid = targetuid(name, prefix=prefix, targets=targets)
        if uid.startswith('.'): uid = uid[1:]
        path = os.path.normpath(os.path.join(_MODULE_DIR, targets[uid]))
        if '$(IntDir)' in path:
            for intdir in ['Release', 'Debug', 'RelWithDebInfo', 'MinSizeRel']:
                tmppath = path.replace('$(IntDir)', intdir)
                if os.path.isfile(tmppath):
                    path = tmppath
                    break
            path = path.replace('$(IntDir)', '')
    else:
        try:
            path = which.which(name)
        except which.WhichError:
            pass
    return path

# ----------------------------------------------------------------------------
## @brief Get name of executable file.
#
# @param [in] name    Name of command or @c None.
# @param [in] prefix  Common prefix of targets belonging to this project.
# @param [in] targets Dictionary mapping target UIDs to executable paths.
#
# @returns Name of executable file or @c None if not found.
#          If @p name is @c None, the name of this executable is returned.
def exename(name=None, prefix=None, targets=None):
    path = exepath(name, prefix, targets)
    if path is None: return None
    name = os.path.basename(path)
    if os.name == 'nt' and (name.endswith('.exe') or name.endswith('.com')):
        name = name[:-4]
    return name

# ----------------------------------------------------------------------------
## @brief Get directory of executable file.
#
# @param [in] name    Name of command or @c None.
# @param [in] prefix  Common prefix of targets belonging to this project.
# @param [in] targets Dictionary mapping target UIDs to executable paths.
#
# @returns Absolute path of directory containing executable or @c None if not found.
#         If @p name is @c None, the directory of this executable is returned.
def exedir(name=None, prefix=None, targets=None):
    path = exepath(name, prefix, targets)
    if path is None: return None
    return os.path.dirname(path)

# ============================================================================
# command execution
# ============================================================================

# ----------------------------------------------------------------------------
## @brief Exception thrown when command execution failed.
class SubprocessError(Exception):
    ## @brief Initialize exception, i.e., set message describing failure.
    def __init__(self, msg):
        self._message = msg
    ## @brief Return string representation of exception message.
    def __str__(self):
        return self._message

# ----------------------------------------------------------------------------
## @brief Convert array of arguments to quoted string.
#
# @param [in] args Array of arguments.
#
# @returns Double quoted string, i.e., string where arguments are separated
#          by a space character and surrounded by double quotes if necessary.
#          Double quotes within an argument are escaped with a backslash.
#
# @sa split_quoted_string()
def tostring(args):
    qargs = []
    re_quote_or_not = re.compile(r"'|\s|^$")
    for arg in args:
        # escape double quotes
        arg = arg.replace('"', '\\"')
        # surround element by double quotes if necessary
        if re_quote_or_not.search(arg): qargs.append(''.join(['"', arg, '"']))
        else:                           qargs.append(arg)
    return ' '.join(qargs)

# ----------------------------------------------------------------------------
## @brief Split quoted string of arguments.
#
# @param [in] args Quoted string of arguments.
#
# @returns Array of arguments.
#
# @sa to_quoted_string()
def qsplit(args):
    return shlex.split(args)

# ----------------------------------------------------------------------------
## @brief Execute command as subprocess.
#
# @param [in] args       Command with arguments given either as quoted string
#                        or array of command name and arguments. In the latter
#                        case, the array elements are converted to strings
#                        using the built-in str() function. Hence, any type
#                        which can be converted to a string is permitted.
#                        The first argument must be the name or path of the
#                        executable of the command.
# @param [in] quiet      Turns off output of @c stdout of child process to
#                        stdout of parent process.
# @param [in] stdout     Whether to return the command output.
# @param [in] allow_fail If true, does not raise an exception if return
#                        value is non-zero. Otherwise, a @c SubprocessError is
#                        raised by this function.
# @param [in] verbose    Verbosity of output messages.
#                        Does not affect verbosity of executed command.
# @param [in] simulate   Whether to simulate command execution only.
# @param [in] prefix     Common prefix of targets belonging to this project.
# @param [in] targets    Dictionary mapping target UIDs to executable paths.
#
# @return The exit code of the subprocess if @p stdout is false (the default).
#         Otherwise, if @p stdout is true, a tuple consisting of exit code
#         command output is returned. Note that if @p allow_fail is false,
#         the returned exit code will always be 0.
#
# @throws SubprocessError If command execution failed. This exception is not
#                         raised if the command executed with non-zero exit
#                         code but @p allow_fail set to @c True.
def execute(args, quiet=False, stdout=False, allow_fail=False, verbose=0, simulate=False,
                  prefix=None, targets=None):
    # convert args to list of strings
    if   type(args) is list:            args = [str(i) for i in args]
    elif type(args) in (str, unicode):  args = qsplit(args);
    else:              raise Exception("execute(): Argument args must be either list or string, but %s given" % type(args))
    if len(args) == 0: raise Exception("execute(): No command specified for execution")
    # get absolute path of executable
    path = exepath(args[0], prefix=prefix, targets=targets)
    if not path: raise SubprocessError(args[0] + ": Command not found")
    args[0] = path
    # some verbose output
    if verbose > 0 or simulate:
        sys.stdout.write('$ ')
        sys.stdout.write(tostring(args))
        if simulate: sys.stdout.write(' (simulated)')
        sys.stdout.write('\n')
    # execute command
    status = 0
    output = ''
    if not simulate:
        try:
            # open subprocess
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # read stdout until EOF
            for line in process.stdout:
                if stdout:
                    output = ''.join([output, line])
                if not quiet:
                    print line.rstrip()
                    sys.stdout.flush()
            # wait until subprocess terminated and set exit code
            (out, err) = process.communicate()
            # print error messages of subprocess
            for line in err: sys.stderr.write(line);
            # get exit code
            status = process.returncode
        except OSError, e:
            raise SubprocessError(args[0] + ': ' + str(e))
        except Exception, e:
            msg  = "Exception while executing \"" + args[0] + "\"!\n"
            msg += "\tArguments: " + tostring(args[1:]) + '\n'
            msg += '\t' + str(e)
            raise SubprocessError(msg)
    # if command failed, throw an exception
    if status != 0 and not allow_fail:
        raise SubprocessError("** Failed: " + tostring(args))
    # return
    if stdout: return (status, output)
    else:      return status


## @}
# end of Doxygen group
