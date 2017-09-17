#/bin/sh
# Copyright: 2017 Daniel Barrows
# License: zlib/libpng
#
# The following are the prerequisite apt packages on Ubuntu 16.04. It will
# probably work for other versions and derivative distributions as well.

if which apt-get >/dev/null 2>&1; then
  sudo apt-get install python-wxgtk3.0 python-wxversion python-sqlalchemy
else
  echo "ERROR: apt-get is not available on your system." >&2
  echo "       You will need to manually install the following software:" >&2
  echo "       - python-wxgtk3.0" >&2
  echo "       - python-wxversion" >&2
  echo "       - python-sqlalchemy" >&2
fi
