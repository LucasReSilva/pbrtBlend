# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# LuxFire Distributed Rendering System
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
#

import Pyro.errors

#------------------------------------------------------------------------------ 
class ClientException(Exception):
    '''
    Exception raised by client objects
    '''
    pass
#------------------------------------------------------------------------------ 


class ServerLocator(object):
    '''
    Locate a remote pyro service by name using a pyro NS
    '''
    
#===============================================================================
#   ATTRIBUTES
#===============================================================================

    # Pyro Name server
    ns = None
    
#================================================================================
#   INITIALISATION
#================================================================================
    
    def __init__(self):
        '''
        Locate the NS
        '''
        
        import Pyro.core
        import Pyro.naming
        try:
            self.ns = Pyro.naming.locateNS()
        except Pyro.errors.NamingError as err:
            raise ClientException('FATAL ERROR: Cannot find Pyro NameServer')
    
#================================================================================
#   METHODS
#================================================================================
    
    def get_by_name(self, name):
        '''
        Get a remote service by name
        '''
        
        if self.ns is not None:
            return Pyro.core.Proxy( self.ns.lookup(name) )
    
    def get_list(self, group):
        '''
        Get the list of all found services
        '''
        
        if self.ns is not None:
            return self.ns.list(group)
#===============================================================================
#   END
#===============================================================================

# Turn the class definition into a global instance
ServerLocator = ServerLocator()


#===============================================================================
# 
#===============================================================================

from . import ServerLocator

def ListLuxFireGroup(grp='Renderer'):
    try:
        LuxSlaves = ServerLocator.get_list('Lux.%s'%grp)
        return LuxSlaves
    except Pyro.errors.NamingError as err:
        print('Lux Pyro NS group Lux.%s not found - No LuxFire components are running ?'%grp)
        return []
