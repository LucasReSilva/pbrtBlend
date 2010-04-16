# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
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

def matrix_to_list(matrix):
    '''
    matrix          Matrix
    
    Flatten a 4x4 matrix into a list
    
    Returns list[16]
    '''
    
    return [matrix[0][0], matrix[0][1], matrix[0][2], matrix[0][3],\
            matrix[1][0], matrix[1][1], matrix[1][2], matrix[1][3],\
            matrix[2][0], matrix[2][1], matrix[2][2], matrix[2][3],\
            matrix[3][0], matrix[3][1], matrix[3][2], matrix[3][3] ]
    