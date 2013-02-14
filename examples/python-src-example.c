/*
    Copyright 2013 David Malcolm <dmalcolm@redhat.com>
    Copyright 2013 Red Hat, Inc.

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301
    USA
*/
#include <Python.h>

PyObject *
make_a_list_of_random_ints_badly(PyObject *self,
                                 PyObject *args)
{
    PyObject *list, *item;
    long count, i;

    if (!PyArg_ParseTuple(args, "i", &count)) {
         return NULL;
    }

    list = PyList_New(0);

    for (i = 0; i < count; i++) {
        item = PyLong_FromLong(random());
        PyList_Append(list, item);
    }

    return list;
}
