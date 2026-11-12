/* CPython extension module wrapping the firmware's crc16_ccitt(). Plain C, no C++ binding library. */
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "crc16.h"

/* crc16(data) -> int. Accepts any bytes-like object (bytes, bytearray, memoryview, array). */
static PyObject *py_crc16(PyObject *module, PyObject *arg)
{
    (void)module;
    Py_buffer view;

    if (PyObject_GetBuffer(arg, &view, PyBUF_SIMPLE) < 0) {
        return NULL;                       /* TypeError already set, e.g. for str */
    }
    uint16_t crc = crc16_ccitt((const uint8_t *)view.buf, (size_t)view.len);
    PyBuffer_Release(&view);
    return PyLong_FromUnsignedLong(crc);
}

static PyMethodDef methods[] = {
    {"crc16", py_crc16, METH_O, "CRC-16/CCITT-FALSE of a bytes-like object."},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT, "_crc16", "Firmware CRC as a C extension.", 0, methods,
};

PyMODINIT_FUNC PyInit__crc16(void)
{
    PyObject *m = PyModule_Create(&module_def);
#ifdef Py_GIL_DISABLED
    /* Declare thread safety so free-threaded (3.13t+) builds don't re-enable the GIL */
    if (m != NULL) {
        PyUnstable_Module_SetGIL(m, Py_MOD_GIL_NOT_USED);
    }
#endif
    return m;
}
