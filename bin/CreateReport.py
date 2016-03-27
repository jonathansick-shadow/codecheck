#!/usr/bin/env python
#
# LSST Data Management System
# Copyright 2008, 2009 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
import os
import string
import sys
import optparse
from subprocess import *
import time
import datetime

# Generate a new C++Test Report
#
# INPUT:
#       -e   <developerEmail>   e.g. robyn@LSST.org
#       -b   Select C++ BugDetective ruleset
#       -r   Select C++ LSST Required Rules
#       -d   Select C++ LSST Desirable Rules
#       -p   Select Python pylint Rules
#
# OUTPUT:
#
####################################################################################

# Following is the presumptive directory structure for C++Test processing
#
#  /home/buildbot/                        # master directory for ALL c++tests
#         globalExcludesCpptest.lst       # exclude src files based on patterns
#         template_localSettingsCpptest.def # template for developer email defn
#         cppTestbed/                          # developer's c++testing directory
#               localSettingsCpptest.def  # defines developer's email path
#               sourceSvn/                # source extracted from SVN
#                     daf_base/           # src from SVN into EUPS package name
#                           daf_base.bdf  # metadata built by cpptestscan
#                     pex_exceptions/
#                           pex_exceptions.bdf
#               reportCpptest/            # developer's c++test reports
#                     daf_base/           # reports under appr package name
#                     pex_exceptions
#               workspaceCpptest/         # developer's eclipse/c++test wkspace
#                     daf_base            # eclipse data for specific package
#                     pex_exceptions
#         <another developer>/

#=====================================================================
#                 Main Routine
#=====================================================================

usage = """%prog [ -brdp ] [ -e email ]  eupsModule"""

parser = optparse.OptionParser()
parser.add_option("-e", "--email", action="store",
                  dest="email", metavar="EMAIL",
                  default="robyn@LSST.org", help="send report to EMAIL ")

parser.add_option("-r", "--required", action="store_true",
                  dest="required", metavar="REQUIRED",
                  default=False, help="use LSST Required Rules")

parser.add_option("-d", "--desirable", action="store_true",
                  dest="desirable", metavar="DESIRABLE",
                  default=False, help="use LSST Desirable Rules")

parser.add_option("-b", "--bug", action="store_true",
                  dest="bug", metavar="BUG",
                  default=False, help="use Bug Detective Rules")

parser.add_option("-p", "--python", action="store_true",
                  dest="python", metavar="PYTHON",
                  default=False, help="use pylint")

parser.opts = {}
parser.args = []

# parse and check command line arguments
(parser.opts, parser.args) = parser.parse_args()
if len(parser.args) < 1:
    print usage
    sys.stderr.write('Syntax error\n')
    sys.exit(1)

package = parser.args[0]
email = parser.opts.email
rules = "user://LSST Required"

if parser.opts.bug:
    rules = "builtin://BugDetective (License Required)"
elif parser.opts.desirable:
    rules = "user://LSST Recommended"

developer = "cppTestbed"
home = "/home/buildbot"

developerHome = "%s/%s" % (home, developer)
workspace = "%s/workspaceCpptest" % (developerHome)
svnPackageDir = "%s/sourceSvn/%s" % (developerHome, package)
ceReports = "%s/reportCpptest" % (developerHome)

ceBdf = "%s/cpptestscan.bdf" % (svnPackageDir)
ceLocalSettings = "%s/localSettingsCpptest.def" % (developerHome)
ceExcludes = "%s/globalExcludesCpptest.lst" % (home)
nowStruct = datetime.datetime.now()
now = nowStruct.strftime("%Y%m%dT%H%M%S")
cePackageReport = "%s/%s/%s" % (ceReports, package, now)
cePackageReportCppLog = "%s/Report.log" % (cePackageReport)
cePackageReportBdfLog = "%s/Bdf.log" % (cePackageReport)
cePackageReportPythonLog = "%s/%sPython.txt" % (cePackageReport, package)

print "Developer == %s" % (developer)
print "Developer's home == %s" % (developerHome)
print "SVN Package  == C++Test Project == %s" % (package)
print ""

print "SVN Package path ==  %s" % (svnPackageDir)
print "C++Test Workspace path == %s" % (workspace)
print "CE Reports path ==  %s" % (ceReports)
print ""

print "CE Build Data file ==  %s" % (ceBdf)
print "CE Local Settings file == %s" % (ceLocalSettings)
print "CE Exclude Pattern file == %s" % (ceExcludes)
print "CE Package Report == %s" % (cePackageReport)
print "CE Package Report C++ Log == %s" % (cePackageReportCppLog)
print "CE Package Report Python Log == %s" % (cePackageReportPythonLog)
print ""

# Build the DateTime-stamped Report subdirectory
cmd = "mkdir %s" % (cePackageReport)
print "COMMAND: %s" % (cmd)


try:
    retcode = call(cmd, shell=True)
    if retcode < 0:
        print >>sys.stderr, "Report Directory not created", -retcode
        sys.exit(0)
    else:
        print >>sys.stderr, "Report Directory created OK", retcode
except OSError, e:
    print >>sys.stderr, "Creation of Report directory failed:", e
    sys.exit(0)


if parser.opts.python:
    # Generate the appropriate Python Standards Checking report
    cmd = 'cd %s; find . -name .tests -prune -o -name "*[^Lib].py" -exec pylint \{\} \\; &> %s' % (
        svnPackageDir, cePackageReportPythonLog)

    print "COMMAND: %s" % (cmd)

    try:
        retcode = call(cmd, shell=True)
        if retcode < 0:
            print >>sys.stderr, "Python Report generation was terminated by signal", -retcode
            sys.exit(0)
        else:
            print >>sys.stderr, "Python Report Generation returned OK", retcode
    except OSError, e:
        print >>sys.stderr, "Python Report Generation failed:", e
        sys.exit(0)

    # mail the Python Report to the user
    cmd = 'mail -s "%s Python Standards Check" %s < %s' % (package, email, cePackageReportPythonLog)
    print "COMMAND: %s" % (cmd)

    try:
        retcode = call(cmd, shell=True)
        if retcode < 0:
            print >>sys.stderr, "Mailing of Python Report was terminated by signal", -retcode
            sys.exit(0)
        else:
            print >>sys.stderr, "Mailing of Python Report returned OK", retcode
    except OSError, e:
        print >>sys.stderr, "Mailing of Python Report failed:", e
        sys.exit(0)

else:
    # Process C++ Standards Check

    # First create a clean cpptest *.bdf file
    cmd = 'cd %s; rm -f %s; scons -c; scons setenv=1 CXX="cpptestscan g++" &> %s' % (
        svnPackageDir, ceBdf, cePackageReportBdfLog)

    print "COMMAND: %s" % (cmd)

    try:
        retcode = call(cmd, shell=True)
        if retcode < 0:
            print >>sys.stderr, "Generation of new .bdf file terminated by signal", -retcode
            sys.exit(0)
        else:
            print >>sys.stderr, "Generation of new .bdf file returned OK", retcode
    except OSError, e:
        print >>sys.stderr, "Generation of new .bdf file failed:", e
        sys.exit(0)

    # Generate the appropriate C++ Standards Checking report
    cmd = 'cpptestcli -bdf %s -data %s -resource %s -config "%s" -exclude %s -localsettings %s -report %s -showdetails -appconsole stdout -publish -nobuild &> %s' % (
        ceBdf, workspace, package, rules, ceExcludes, ceLocalSettings, cePackageReport, cePackageReportCppLog)

    print "COMMAND: %s" % (cmd)

    try:
        retcode = call(cmd, shell=True)
        if retcode < 0:
            print >>sys.stderr, "C++ Report generation was terminated by signal", -retcode
            sys.exit(0)
        else:
            print >>sys.stderr, "C++ Report Generation returned OK", retcode
    except OSError, e:
        print >>sys.stderr, "C++ Report Generation failed:", e
        sys.exit(0)

    # mail the C++ Report Generation Log to the user
    cmd = 'mail -s "%s C++ Standards Check Log" %s < %s' % (package, email, cePackageReportCppLog)
    print "COMMAND: %s" % (cmd)

    try:
        retcode = call(cmd, shell=True)
        if retcode < 0:
            print >>sys.stderr, "Mailing of C++ Report was terminated by signal", -retcode
            sys.exit(0)
        else:
            print >>sys.stderr, "Mailing of C++ Report returned OK", retcode
    except OSError, e:
        print >>sys.stderr, "Mailing of C++ Report failed:", e
        sys.exit(0)

