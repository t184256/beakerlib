# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Name: libraries.sh - part of the BeakerLib project
#   Description: Functions for importing separate libraries
#
#   Author: Petr Muller <muller@redhat.com>
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#
#   This copyrighted material is made available to anyone wishing
#   to use, modify, copy, or redistribute it subject to the terms
#   and conditions of the GNU General Public License version 2.
#
#   This program is distributed in the hope that it will be
#   useful, but WITHOUT ANY WARRANTY; without even the implied
#   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE. See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public
#   License along with this program; if not, write to the Free
#   Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
#   Boston, MA 02110-1301, USA.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

: <<'=cut'
=pod

=head1 NAME

=head1 DESCRIPTION

=head1 FUNCTIONS

=cut

__INTERNAL_rlLibrarySearch() {
  local DIRECTORY="$1"
  local COMPONENT="$2"
  local LIBRARY="$3"

  while [ "$DIRECTORY" != "/" ]
  do
    DIRECTORY="$( dirname $DIRECTORY )"
    if [ -d "$DIRECTORY/$COMPONENT" ]
    then
      if [ -f "$DIRECTORY/$COMPONENT/Library/$LIBRARY/lib.sh" ]
      then
        echo "$DIRECTORY/$COMPONENT/Library/$LIBRARY/lib.sh"
        break
      fi
    fi
  done
}


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# rlImport
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
: <<'=cut'
=pod

=head3 rlImport

Here be a description

    rlImport LIBRARY [LIBRARY2...]

=over

=item LIBRARY

Here be a description

=back

=cut

rlImport() {
  local RESULT=0

  if [ -z "$1" ]
  then
    rlLogError "rlImport: At least one argument needs to be provided"
    return 1
  fi

  # Process all arguments
  while [ -n "$1" ]
  do

    # Extract two identifiers from an 'component/library' argument
    local COMPONENT=$( echo $1 | cut -d '/' -f 1 )
    local LIBRARY=$( echo $1 | cut -d '/' -f 2 )

    if [ -z "$COMPONENT" ] || [ -z "$LIBRARY" ] || [ "$COMPONENT/$LIBRARY" != "$1" ]
    then
      rlLogError "rlImport: Malformed argument [$1]"
      RESULT=1
      shift; continue;
    fi

    rlLogDebug "rlImport: Searching for library $COMPONENT/$LIBRARY"
    rlLogDebug "rlImport: Starting search at $(pwd)"
    local LIBFILE="$(  __INTERNAL_rlLibrarySearch $( pwd ) $COMPONENT $LIBRARY )"

    if [ -z "$LIBFILE" ]
    then
      rlLogError "rlImport: Could not find library $1"
      RESULT=1
      shift; continue;
    fi

    # Try to extract a prefix comment from the file found
    # Prefix comment looks like this:
    # library-prefix = wee
    local PREFIX="$( grep -E "library-prefix = [a-zA[z_][a-zA-Z0-9_]*.*" $LIBFILE | sed 's|.*library-prefix = \([a-zA-Z_][a-zA-Z0-9_]*\).*|\1|')"
    if [ -z "$PREFIX" ]
    then
      rlLogError "rlImport: Could not extract prefix from library $1"
      RESULT=1
      shift; continue;
    fi

    # Construct the validating function
    # Its supposed to be called 'prefixVerify'
    local VERIFIER="${PREFIX}Verify"
    rlLogDebug "Constructed verifier function: $VERIFIER"

    # Cycle detection: if validating function is available, the library
    # is imported already
    if eval $VERIFIER &>/dev/null
    then
      rlLogInfo "rlImport: Library $1 imported already"
      shift; continue;
    fi

    # Try to source the library
    . $LIBFILE

    # Call the validation callback of the function
    if ! eval $VERIFIER
    then
      rlLogError "rlImport: Import of library $1 was not successful (callback failed)"
      RESULT=1
      shift; continue;
    fi

    shift;
  done

  return $RESULT
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# AUTHORS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
: <<'=cut'
=pod

=head1 AUTHORS

=over

=item *

Petr Muller <muller@redhat.com>

=back

=cut